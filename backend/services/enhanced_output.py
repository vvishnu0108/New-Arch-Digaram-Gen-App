"""
Enhanced LLM Output Module
Provides utilities for improving LLM response quality, formatting, and explanations
"""
import re
from typing import Dict, Any, Tuple
from core.logging import get_logger

logger = get_logger("enhanced_output")


def extract_architectural_reasoning(llm_response: str) -> Tuple[str, str]:
    """
    Extract architectural reasoning/explanation from LLM response if present.
    Returns: (reasoning, code)
    """
    # Look for common patterns indicating architectural explanation
    patterns = [
        r'(?:Architecture(?:al)?\s+(?:Reasoning|Decision|Explanation|Design)s?:?\s*)(.*?)(?=```|import\s+subprocess|from\s+diagrams)',
        r'(?:Design\s+Rationale:?\s*)(.*?)(?=```|import\s+subprocess|from\s+diagrams)',
        r'(?:Key\s+Decisions:?\s*)(.*?)(?=```|import\s+subprocess|from\s+diagrams)',
    ]
    
    reasoning = ""
    code = llm_response
    
    for pattern in patterns:
        match = re.search(pattern, llm_response, re.DOTALL | re.IGNORECASE)
        if match:
            reasoning = match.group(1).strip()
            # Remove the reasoning from code
            code = llm_response.replace(match.group(0), "").strip()
            break
    
    # If no explicit reasoning found, check if there's explanatory text before code
    if not reasoning:
        # Look for text before first import or code block
        text_before_code = re.split(r'```|import\s+subprocess|from\s+diagrams', llm_response, 1)
        if len(text_before_code) > 1 and len(text_before_code[0].strip()) > 20:
            potential_reasoning = text_before_code[0].strip()
            # Check if it looks like an explanation (has common explanation keywords)
            if any(keyword in potential_reasoning.lower() for keyword in 
                   ['architecture', 'design', 'because', 'ensure', 'provide', 'layer', 'component']):
                reasoning = potential_reasoning
                code = llm_response[len(potential_reasoning):].strip()
    
    # Clean up code
    code = code.replace("```python", "").replace("```", "").strip()
    
    return reasoning, code


def generate_architecture_explanation(user_request: str, code: str, success: bool) -> str:
    """
    Generate a structured explanation of the architecture based on the request and generated code.
    This provides additional context about the design decisions.
    """
    if not success:
        return ""
    
    explanation_parts = []
    
    # Analyze the code to identify key components
    clusters = re.findall(r'with\s+Cluster\(["\']([^"\']+)["\']\)', code)
    imports = re.findall(r'from\s+diagrams\.[\w.]+\s+import\s+([\w,\s]+)', code)
    
    if clusters:
        explanation_parts.append(f"**Architecture Layers**: {len(clusters)} logical layers organized as: {', '.join(clusters[:5])}")
    
    # Count components
    component_count = len(re.findall(r'=\s*\w+\(["\']', code))
    if component_count > 0:
        explanation_parts.append(f"**Components**: {component_count} infrastructure components")
    
    # Identify cloud provider
    cloud_providers = []
    if 'diagrams.aws' in code:
        cloud_providers.append('AWS')
    if 'diagrams.gcp' in code:
        cloud_providers.append('GCP')
    if 'diagrams.azure' in code:
        cloud_providers.append('Azure')
    if 'diagrams.onprem' in code:
        cloud_providers.append('On-Premises')
    
    if cloud_providers:
        explanation_parts.append(f"**Platform**: {', '.join(cloud_providers)}")
    
    explanation = "\n".join(explanation_parts)
    return explanation


def validate_code_quality(code: str) -> Dict[str, Any]:
    """
    Validate the quality of generated code and provide quality metrics.
    Returns validation results with suggestions for improvement.
    """
    validation = {
        "is_valid": True,
        "score": 100,
        "issues": [],
        "warnings": [],
        "suggestions": []
    }
    
    # Check for required imports
    if "from diagrams import Diagram" not in code:
        validation["issues"].append("Missing required import: from diagrams import Diagram")
        validation["is_valid"] = False
        validation["score"] -= 30
    
    # Check for outformat parameter
    if 'outformat=' not in code and 'outformat =' not in code:
        validation["warnings"].append("Missing outformat parameter - diagram may not generate all formats")
        validation["score"] -= 10
    
    # Check for graphviz2drawio conversion
    if 'graphviz2drawio' not in code:
        validation["warnings"].append("Missing graphviz2drawio conversion - Draw.IO file won't be generated")
        validation["score"] -= 15
    
    # Check for clustering
    cluster_count = len(re.findall(r'with\s+Cluster\(', code))
    if cluster_count == 0:
        validation["suggestions"].append("Consider adding Cluster blocks to organize components logically")
        validation["score"] -= 5
    elif cluster_count < 2:
        validation["suggestions"].append("Consider adding more clusters for better organization")
        validation["score"] -= 3
    
    # Check component count
    component_count = len(re.findall(r'=\s*\w+\(["\']', code))
    if component_count < 5:
        validation["warnings"].append(f"Only {component_count} components detected - consider adding more for a complete architecture")
        validation["score"] -= 10
    
    # Check for connections
    if '>>' not in code:
        validation["warnings"].append("No connections found - components should be connected to show data flow")
        validation["score"] -= 10
    
    return validation


def format_enhanced_response(
    code: str,
    reasoning: str,
    explanation: str,
    validation: Dict[str, Any],
    execution_success: bool
) -> Dict[str, Any]:
    """
    Format the complete enhanced response with all metadata.
    This provides a rich, structured response for the frontend.
    """
    response = {
        "code": code,
        "success": execution_success,
        "enhancement": {
            "architectural_reasoning": reasoning,
            "design_explanation": explanation,
            "quality_score": validation.get("score", 0),
            "validation": {
                "is_valid": validation.get("is_valid", True),
                "issues": validation.get("issues", []),
                "warnings": validation.get("warnings", []),
                "suggestions": validation.get("suggestions", [])
            }
        }
    }
    
    return response


def create_enhanced_system_prompt_addition() -> str:
    """
    Additional prompt instructions to encourage better LLM output with reasoning.
    This should be appended to existing system prompts.
    """
    return """

## ENHANCED OUTPUT REQUIREMENTS (CRITICAL)

Your response must include architectural reasoning to help users understand your design decisions.

**Response Structure:**

1. **Brief Architectural Reasoning** (2-4 sentences):
   - Explain the key architectural decisions
   - Why you chose specific components
   - How the architecture addresses the requirements
   - Any trade-offs or considerations

2. **Python Code**:
   - Clean, well-structured code
   - Comprehensive architecture with all necessary layers
   - Proper clustering and organization

**Example Response Format:**

```
Architectural Reasoning: This design implements a three-tier architecture for high availability and scalability. 
The load balancer distributes traffic across multiple application servers in the compute layer, while the database 
uses read replicas for improved performance. Security is enforced through VPC isolation and firewall rules at the 
network perimeter.

[Your Python code here]
```

Remember: Users value understanding WHY you made certain choices, not just WHAT components you selected.
"""


def enhance_streaming_message(message: str, step: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Enhance streaming messages with more detailed, user-friendly information.
    Provides better feedback during the generation process.
    """
    enhanced_messages = {
        "init": "🧠 Analyzing your architecture requirements and gathering context...",
        "researching": "📚 Researching best practices and architecture patterns...",
        "tools": "🔧 Using architecture knowledge tools to inform design decisions...",
        "designing": "🎨 Designing complete architecture with all required layers...",
        "generating": "⚡ Generating Python code for diagram visualization...",
        "executing": "▶️ Executing code and creating diagram files...",
        "validating": "✅ Validating output quality and checking for improvements...",
        "success": "🎉 Success! Your architecture diagram is ready with detailed explanations.",
        "error": "⚠️ Encountered an issue - analyzing and attempting to correct...",
        "retrying": "🔄 Refining the approach based on feedback..."
    }
    
    display_message = enhanced_messages.get(step, message)
    
    return {
        "message": display_message,
        "step": step,
        "metadata": metadata or {},
        "timestamp": None  # Will be added by the caller
    }


def improve_error_message(error_output: str) -> str:
    """
    Transform technical error messages into user-friendly, actionable feedback.
    Provides clearer guidance on what went wrong and how to fix it.
    """
    # Extract key error information
    if "ImportError" in error_output or "cannot import name" in error_output:
        return (
            "⚠️ **Import Error Detected**\n\n"
            "The diagram generation attempted to use a component that's not available in the diagrams library. "
            "This typically happens when:\n"
            "- A component name was misspelled\n"
            "- A deprecated component was used\n"
            "- The library version doesn't include that component\n\n"
            "I'm automatically correcting this and generating a new version with valid components..."
        )
    
    if "ModuleNotFoundError" in error_output:
        return (
            "⚠️ **Missing Module**\n\n"
            "A required Python module is not installed. "
            "This is being resolved automatically..."
        )
    
    if "SyntaxError" in error_output:
        return (
            "⚠️ **Code Syntax Issue**\n\n"
            "The generated code had a syntax error. "
            "I'm reviewing and correcting the code structure..."
        )
    
    if "subprocess" in error_output and "graphviz2drawio" in error_output:
        return (
            "⚠️ **Diagram Conversion Issue**\n\n"
            "The diagram was generated but couldn't be converted to Draw.IO format. "
            "Attempting alternative conversion method..."
        )
    
    # Generic error
    return (
        "⚠️ **Generation Issue**\n\n"
        "Encountered an unexpected issue during diagram generation. "
        "Analyzing the problem and adjusting the approach..."
    )
