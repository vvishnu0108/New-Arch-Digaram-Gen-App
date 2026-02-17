"""
Diagram validation service for the re-validation loop
"""
import os
import uuid
from typing import List, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from services.sessions import session_manager

load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    api_key=os.getenv("llm_api_key", None),
    base_url=os.getenv("llm_api_base_url", "http://localhost:8080/v1"),
    model=os.getenv("llm_model_name", "meta/llama-3.3-70b-instruct"),
    streaming=os.getenv("llm_stream_usage", "false").lower() == "true",
    temperature=float(os.getenv("llm_temperature", "0.2")),
    max_tokens=int(os.getenv("llm_max_tokens", "4096")),
    timeout=float(os.getenv("llm_timeout", "120")) if os.getenv("llm_timeout") else None,
    max_retries=int(os.getenv("llm_max_retries", "3")),
)

VALIDATION_PROMPT = """
You are a senior cloud architect reviewing an architecture diagram for production readiness.

Analyze the following architecture and provide a comprehensive validation report.

For each issue found, categorize it as:
- **security**: Security vulnerabilities or concerns
- **scalability**: Scaling limitations or improvements
- **cost**: Cost optimization opportunities
- **best_practice**: Industry best practices not followed

And assign a severity:
- **critical**: Must fix before production
- **warning**: Should address soon
- **info**: Nice to have improvements

Provide your response in the following JSON format:
{
    "overall_score": <0-100>,
    "summary": "<brief summary of the architecture quality>",
    "explanation": "<detailed explanation of the architecture and its strengths/weaknesses>",
    "suggestions": [
        {
            "category": "<security|scalability|cost|best_practice>",
            "severity": "<critical|warning|info>",
            "title": "<short title>",
            "description": "<what the issue is>",
            "recommendation": "<how to fix it>"
        }
    ]
}

Be constructive and specific with recommendations.
"""

REVALIDATION_PROMPT = """
You are a senior cloud architect reviewing an updated architecture diagram.

The user has provided feedback on your previous validation:
{feedback}

The user accepted these suggestions: {accepted_suggestions}

Please re-analyze the architecture considering:
1. Changes made based on accepted suggestions
2. User's feedback and constraints
3. Any new considerations

Provide an updated validation report in the same JSON format.
"""


def validate_diagram(session_id: str) -> Tuple[bool, dict]:
    """
    Validate a diagram and return suggestions.
    Returns: (success, validation_result)
    """
    session = session_manager.get_session(session_id)
    if not session:
        return False, {"error": "Session not found"}
    
    if not session.diagram_description:
        return False, {"error": "No diagram description available"}
    
    # Build context from conversation history
    context_parts = []
    context_parts.append(f"Architecture: {session.diagram_description}")
    
    for msg in session.conversation_history:
        if msg["role"] == "user":
            context_parts.append(f"Requirement: {msg['content']}")
    
    context = "\n".join(context_parts)
    
    # Generate validation
    messages = [
        ("system", VALIDATION_PROMPT),
        ("human", f"Validate this architecture:\n\n{context}")
    ]
    
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | llm
    
    try:
        response = chain.invoke({})
        result = parse_validation_response(response.content)
        
        # Add IDs to suggestions
        for suggestion in result.get("suggestions", []):
            suggestion["id"] = str(uuid.uuid4())[:8]
        
        result["success"] = True
        result["session_id"] = session_id
        
        return True, result
    except Exception as e:
        return False, {"error": f"Error validating diagram: {str(e)}"}


def revalidate_diagram(
    session_id: str,
    feedback: str,
    accepted_suggestions: List[str]
) -> Tuple[bool, dict]:
    """
    Re-validate a diagram with user feedback.
    Returns: (success, validation_result)
    """
    session = session_manager.get_session(session_id)
    if not session:
        return False, {"error": "Session not found"}
    
    # Build context
    context_parts = []
    context_parts.append(f"Architecture: {session.diagram_description}")
    
    for msg in session.conversation_history:
        if msg["role"] == "user":
            context_parts.append(f"Requirement: {msg['content']}")
    
    context = "\n".join(context_parts)
    
    # Build re-validation prompt
    revalidation_text = REVALIDATION_PROMPT.format(
        feedback=feedback,
        accepted_suggestions=", ".join(accepted_suggestions) if accepted_suggestions else "None"
    )
    
    messages = [
        ("system", revalidation_text),
        ("human", f"Re-validate this architecture:\n\n{context}")
    ]
    
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | llm
    
    try:
        response = chain.invoke({})
        result = parse_validation_response(response.content)
        
        # Add IDs to suggestions
        for suggestion in result.get("suggestions", []):
            suggestion["id"] = str(uuid.uuid4())[:8]
        
        result["success"] = True
        result["session_id"] = session_id
        
        return True, result
    except Exception as e:
        return False, {"error": f"Error re-validating diagram: {str(e)}"}


def parse_validation_response(response: str) -> dict:
    """Parse the validation response from LLM"""
    import json
    
    # Try to extract JSON from the response
    try:
        # Look for JSON block
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "{" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
        else:
            json_str = response
        
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Return a default structure if parsing fails
        return {
            "overall_score": 70,
            "summary": "Unable to parse validation response",
            "explanation": response,
            "suggestions": []
        }
