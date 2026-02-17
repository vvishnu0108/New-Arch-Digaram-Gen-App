"""
API routes for documentation generation
"""
from io import BytesIO
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from models.schemas import (
    GenerateDocumentationRequest,
    DocumentationResponse
)
from services.documentation import generate_documentation
from services.docx_generator import create_architecture_document
from services.sessions import session_manager

router = APIRouter(prefix="/api/docs", tags=["Documentation"])


@router.post("/generate", response_model=DocumentationResponse)
async def create_documentation(request: GenerateDocumentationRequest):
    """Generate documentation for a diagram session"""
    try:
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        success, documentation, sections = generate_documentation(request.session_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=documentation)
        
        return DocumentationResponse(
            success=True,
            session_id=request.session_id,
            documentation=documentation,
            sections=sections
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=DocumentationResponse)
async def get_documentation(session_id: str):
    """Get documentation for a diagram session (generates if not cached)"""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        success, documentation, sections = generate_documentation(session_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=documentation)
        
        return DocumentationResponse(
            success=True,
            session_id=session_id,
            documentation=documentation,
            sections=sections
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/download")
async def download_documentation(
    session_id: str,
    title: str = Query(default=None, description="Custom document title"),
    author: str = Query(default="Diagram Agent", description="Document author")
):
    """
    Download architecture documentation as a Word document (.docx).
    
    Returns a professionally formatted document with:
    - Title page
    - Table of contents
    - Architecture diagram (embedded PNG)
    - Component details table
    - Design decisions from conversation
    - Appendix with Python source code
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        success, doc_bytes, filename = create_architecture_document(
            session_id,
            title=title,
            author=author
        )
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Failed to generate document. Ensure a diagram has been created."
            )
        
        return StreamingResponse(
            BytesIO(doc_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(doc_bytes))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
