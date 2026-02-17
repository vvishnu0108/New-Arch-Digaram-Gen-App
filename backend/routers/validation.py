"""
API routes for diagram validation
"""
from fastapi import APIRouter, HTTPException

from models.schemas import (
    ValidateDiagramRequest,
    ValidationFeedbackRequest,
    ValidationResponse,
    ValidationSuggestion
)
from services.validator import validate_diagram, revalidate_diagram
from services.sessions import session_manager

router = APIRouter(prefix="/api/validate", tags=["Validation"])


@router.post("", response_model=ValidationResponse)
async def validate(request: ValidateDiagramRequest):
    """Validate a diagram and get suggestions"""
    try:
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        success, result = validate_diagram(request.session_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=result.get("error", "Validation failed"))
        
        # Convert suggestions to ValidationSuggestion objects
        suggestions = [
            ValidationSuggestion(
                id=s.get("id", ""),
                category=s.get("category", "best_practice"),
                severity=s.get("severity", "info"),
                title=s.get("title", ""),
                description=s.get("description", ""),
                recommendation=s.get("recommendation", "")
            )
            for s in result.get("suggestions", [])
        ]
        
        return ValidationResponse(
            success=True,
            session_id=request.session_id,
            overall_score=result.get("overall_score", 70),
            summary=result.get("summary", ""),
            suggestions=suggestions,
            explanation=result.get("explanation", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback", response_model=ValidationResponse)
async def validation_feedback(request: ValidationFeedbackRequest):
    """Submit feedback on validation and trigger re-validation"""
    try:
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        success, result = revalidate_diagram(
            request.session_id,
            request.feedback,
            request.accepted_suggestions
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=result.get("error", "Re-validation failed"))
        
        # Convert suggestions to ValidationSuggestion objects
        suggestions = [
            ValidationSuggestion(
                id=s.get("id", ""),
                category=s.get("category", "best_practice"),
                severity=s.get("severity", "info"),
                title=s.get("title", ""),
                description=s.get("description", ""),
                recommendation=s.get("recommendation", "")
            )
            for s in result.get("suggestions", [])
        ]
        
        return ValidationResponse(
            success=True,
            session_id=request.session_id,
            overall_score=result.get("overall_score", 70),
            summary=result.get("summary", ""),
            suggestions=suggestions,
            explanation=result.get("explanation", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
