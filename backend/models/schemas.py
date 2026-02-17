"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DiagramFormat(str, Enum):
    PNG = "png"
    DOT = "dot"
    DRAWIO = "drawio"


# Request Models
class GenerateDiagramRequest(BaseModel):
    """Request to generate a new diagram"""
    prompt: str = Field(..., description="Natural language description of the architecture")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class UpdateDiagramRequest(BaseModel):
    """Request to update an existing diagram"""
    session_id: str = Field(..., description="Session ID of the diagram to update")
    prompt: str = Field(..., description="Follow-up prompt describing the changes")
    current_diagram_xml: Optional[str] = Field(None, description="Current diagram XML from Draw.IO if modified")


class ImportDiagramRequest(BaseModel):
    """Request to import diagram XML from Draw.IO"""
    session_id: str = Field(..., description="Session ID")
    diagram_xml: str = Field(..., description="Draw.IO diagram XML content")


class GenerateDocumentationRequest(BaseModel):
    """Request to generate documentation"""
    session_id: str = Field(..., description="Session ID of the diagram")


class ValidateDiagramRequest(BaseModel):
    """Request to validate a diagram"""
    session_id: str = Field(..., description="Session ID of the diagram")


class ValidationFeedbackRequest(BaseModel):
    """Request to provide feedback on validation"""
    session_id: str = Field(..., description="Session ID")
    feedback: str = Field(..., description="User feedback on validation suggestions")
    accepted_suggestions: List[str] = Field(default=[], description="List of accepted suggestion IDs")


# Response Models
class DiagramFile(BaseModel):
    """Information about a generated diagram file"""
    format: DiagramFormat
    filename: str
    url: str


class DiagramResponse(BaseModel):
    """Response after diagram generation"""
    success: bool
    session_id: str
    message: str
    diagram_xml: Optional[str] = None
    files: List[DiagramFile] = []
    python_code: Optional[str] = None
    architectural_reasoning: Optional[str] = Field(None, description="Explanation of architectural decisions")
    design_explanation: Optional[str] = Field(None, description="Summary of architecture components and layers")
    quality_score: Optional[int] = Field(None, ge=0, le=100, description="Code quality score")
    quality_feedback: Optional[dict] = Field(None, description="Quality validation feedback")


class ConversationMessage(BaseModel):
    """A message in the conversation history"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


class SessionResponse(BaseModel):
    """Response with session information"""
    session_id: str
    conversation_history: List[ConversationMessage]
    current_diagram_xml: Optional[str] = None
    files: List[DiagramFile] = []


class DocumentationResponse(BaseModel):
    """Response with generated documentation"""
    success: bool
    session_id: str
    documentation: str
    sections: List[dict] = []


class ValidationSuggestion(BaseModel):
    """A validation suggestion"""
    id: str
    category: str  # "security", "scalability", "cost", "best_practice"
    severity: str  # "info", "warning", "critical"
    title: str
    description: str
    recommendation: str


class ValidationResponse(BaseModel):
    """Response from diagram validation"""
    success: bool
    session_id: str
    overall_score: int = Field(..., ge=0, le=100)
    summary: str
    suggestions: List[ValidationSuggestion] = []
    explanation: str


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    details: Optional[str] = None
