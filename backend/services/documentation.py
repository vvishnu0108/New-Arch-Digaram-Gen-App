"""
Documentation generation service
"""
import os
from typing import Optional
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
    temperature=float(os.getenv("llm_temperature", "0.3")),
    max_tokens=int(os.getenv("llm_max_tokens", "4096")),
    timeout=float(os.getenv("llm_timeout", "120")) if os.getenv("llm_timeout") else None,
    max_retries=int(os.getenv("llm_max_retries", "3")),
)

DOCUMENTATION_PROMPT = """
You are a senior solutions architect tasked with creating comprehensive documentation for an architecture diagram.

Based on the following architecture description and conversation history, generate detailed documentation that explains:

1. **Architecture Overview**
   - High-level summary of the architecture
   - Key components and their purpose

2. **Component Details**
   - Detailed explanation of each component
   - Why each component was chosen
   - How components interact with each other

3. **Design Decisions & Rationale**
   - Why this architecture pattern was selected
   - Trade-offs considered
   - Alternatives that were evaluated

4. **Scalability & Performance**
   - How the architecture handles scaling
   - Performance considerations
   - Bottlenecks and mitigation strategies

5. **Security Considerations**
   - Security measures in place
   - Data flow and protection
   - Access control and authentication

6. **Cost Considerations**
   - Cost optimization strategies
   - Resource utilization patterns

7. **Best Practices Applied**
   - Industry best practices incorporated
   - Cloud provider recommendations followed

8. **Recommendations**
   - Potential improvements
   - Future considerations

Format the output as clean, well-structured Markdown.
"""


def generate_documentation(session_id: str) -> tuple[bool, str, list]:
    """
    Generate documentation for a diagram session.
    Returns: (success, documentation_markdown, sections)
    """
    session = session_manager.get_session(session_id)
    if not session:
        return False, "Session not found", []
    
    if not session.diagram_description:
        return False, "No diagram description available", []
    
    # Build context from conversation history
    context_parts = []
    context_parts.append(f"Main Architecture Request: {session.diagram_description}")
    
    for msg in session.conversation_history:
        if msg["role"] == "user":
            context_parts.append(f"User Request: {msg['content']}")
        elif msg["role"] == "assistant":
            context_parts.append(f"System Response: {msg['content']}")
    
    context = "\n\n".join(context_parts)
    
    # Generate documentation
    messages = [
        ("system", DOCUMENTATION_PROMPT),
        ("human", f"Generate documentation for this architecture:\n\n{context}")
    ]
    
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | llm
    
    try:
        response = chain.invoke({})
        documentation = response.content
        
        # Parse sections from the documentation
        sections = parse_documentation_sections(documentation)
        
        return True, documentation, sections
    except Exception as e:
        return False, f"Error generating documentation: {str(e)}", []


def parse_documentation_sections(documentation: str) -> list:
    """Parse documentation into sections"""
    sections = []
    current_section = None
    current_content = []
    
    for line in documentation.split("\n"):
        if line.startswith("## "):
            # Save previous section
            if current_section:
                sections.append({
                    "title": current_section,
                    "content": "\n".join(current_content).strip()
                })
            current_section = line[3:].strip()
            current_content = []
        elif line.startswith("# "):
            # Top-level heading (overview)
            if current_section:
                sections.append({
                    "title": current_section,
                    "content": "\n".join(current_content).strip()
                })
            current_section = line[2:].strip()
            current_content = []
        else:
            current_content.append(line)
    
    # Don't forget the last section
    if current_section:
        sections.append({
            "title": current_section,
            "content": "\n".join(current_content).strip()
        })
    
    return sections
