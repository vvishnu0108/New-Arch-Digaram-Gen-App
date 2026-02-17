"""
API routes for diagram generation and updates
"""
import os
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from models.schemas import (
    GenerateDiagramRequest,
    UpdateDiagramRequest,
    ImportDiagramRequest,
    DiagramResponse,
    DiagramFile,
    DiagramFormat,
    SessionResponse,
    ConversationMessage,
    ErrorResponse
)
from services.agent import (
    generate_diagram_code,
    generate_diagram_code_with_tools,
    update_diagram_code,
    generate_diagram_code_streaming
)
from services.sessions import session_manager
from services.enhanced_output import (
    extract_architectural_reasoning,
    generate_architecture_explanation,
    validate_code_quality
)
from utils import get_latest_files, read_drawio_xml, save_drawio_xml

router = APIRouter(prefix="/api/diagrams", tags=["Diagrams"])


@router.post("/generate", response_model=DiagramResponse)
async def generate_diagram(request: GenerateDiagramRequest, use_tools: bool = Query(default=True)):
    """
    Generate a new architecture diagram from a natural language prompt.
    
    Args:
        request: The diagram generation request with prompt
        use_tools: If True (default), use tool-calling for architecture knowledge.
                   Set to False to use the traditional prompt-only approach.
    """
    try:
        # Use tool-based generation by default
        if use_tools:
            code, status, success, session_id, base_filename = generate_diagram_code_with_tools(
                request.prompt,
                request.session_id
            )
        else:
            code, status, success, session_id, base_filename = generate_diagram_code(
                request.prompt,
                request.session_id
            )

        
        if not success:
            return DiagramResponse(
                success=False,
                session_id=session_id,
                message=status,
                python_code=code
            )
        
        # Get generated files
        files_dict = get_latest_files(base_filename)
        files = []
        
        for fmt, filepath in files_dict.items():
            files.append(DiagramFile(
                format=DiagramFormat(fmt),
                filename=os.path.basename(filepath),
                url=f"/api/diagrams/files/{base_filename}.{fmt}"
            ))
        
        # Get diagram XML
        diagram_xml = ""
        if "drawio" in files_dict:
            diagram_xml = read_drawio_xml(files_dict["drawio"])
        
        # Extract architectural reasoning and validate quality
        reasoning, clean_code = extract_architectural_reasoning(code)
        explanation = generate_architecture_explanation(request.prompt, clean_code, success)
        validation = validate_code_quality(clean_code)
        
        return DiagramResponse(
            success=True,
            session_id=session_id,
            message="Diagram generated successfully with enhanced explanations",
            diagram_xml=diagram_xml,
            files=files,
            python_code=clean_code,
            architectural_reasoning=reasoning if reasoning else "Architecture designed with best practices for scalability, security, and maintainability.",
            design_explanation=explanation,
            quality_score=validation.get("score", 100),
            quality_feedback={
                "issues": validation.get("issues", []),
                "warnings": validation.get("warnings", []),
                "suggestions": validation.get("suggestions", [])
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/stream")
async def generate_diagram_stream(request: GenerateDiagramRequest):
    """
    Generate a new architecture diagram with streaming status updates (SSE).
    Returns Server-Sent Events with real-time progress information.
    """
    def event_generator():
        for event in generate_diagram_code_streaming(
            request.prompt,
            request.session_id
        ):
            yield event
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/update", response_model=DiagramResponse)
async def update_diagram(request: UpdateDiagramRequest):
    """Update an existing diagram with a follow-up prompt"""
    try:
        # If user provided modified XML from Draw.IO, save it first
        if request.current_diagram_xml:
            session = session_manager.get_session(request.session_id)
            if session and session.current_base_filename:
                drawio_path = os.path.join("generated", f"{session.current_base_filename}.drawio")
                save_drawio_xml(drawio_path, request.current_diagram_xml)
        
        code, status, success, base_filename = update_diagram_code(
            request.session_id,
            request.prompt
        )
        
        if not success:
            return DiagramResponse(
                success=False,
                session_id=request.session_id,
                message=status,
                python_code=code
            )
        
        # Get generated files
        files_dict = get_latest_files(base_filename)
        files = []
        
        for fmt, filepath in files_dict.items():
            files.append(DiagramFile(
                format=DiagramFormat(fmt),
                filename=os.path.basename(filepath),
                url=f"/api/diagrams/files/{base_filename}.{fmt}"
            ))
        
        # Get diagram XML
        diagram_xml = ""
        if "drawio" in files_dict:
            diagram_xml = read_drawio_xml(files_dict["drawio"])
        
        return DiagramResponse(
            success=True,
            session_id=request.session_id,
            message="Diagram updated successfully",
            diagram_xml=diagram_xml,
            files=files,
            python_code=code
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_diagram(request: ImportDiagramRequest):
    """Import diagram XML from Draw.IO edits"""
    try:
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.current_base_filename:
            drawio_path = os.path.join("generated", f"{session.current_base_filename}.drawio")
            success = save_drawio_xml(drawio_path, request.diagram_xml)
            
            if success:
                session_manager.update_diagram(
                    request.session_id,
                    request.diagram_xml,
                    session.current_base_filename
                )
                return {"success": True, "message": "Diagram imported successfully"}
        
        raise HTTPException(status_code=400, detail="No diagram to update")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get diagram session information"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get files
    files = []
    if session.current_base_filename:
        files_dict = get_latest_files(session.current_base_filename)
        for fmt, filepath in files_dict.items():
            files.append(DiagramFile(
                format=DiagramFormat(fmt),
                filename=os.path.basename(filepath),
                url=f"/api/diagrams/files/{session.current_base_filename}.{fmt}"
            ))
    
    # Convert conversation history
    conversation = [
        ConversationMessage(
            role=msg["role"],
            content=msg["content"],
            timestamp=msg["timestamp"]
        )
        for msg in session.conversation_history
    ]
    
    return SessionResponse(
        session_id=session_id,
        conversation_history=conversation,
        current_diagram_xml=session.current_diagram_xml,
        files=files
    )


@router.get("/files/{filename}")
async def get_diagram_file(filename: str):
    """Download a generated diagram file"""
    filepath = os.path.join("generated", filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type
    ext = filename.split(".")[-1].lower()
    media_types = {
        "png": "image/png",
        "dot": "text/plain",
        "drawio": "application/xml"
    }
    
    return FileResponse(
        filepath,
        media_type=media_types.get(ext, "application/octet-stream"),
        filename=filename
    )
