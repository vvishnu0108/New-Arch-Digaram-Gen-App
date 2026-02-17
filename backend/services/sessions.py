"""
Session management service for conversation history
"""
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class Session:
    """Represents a diagram generation session"""
    session_id: str
    created_at: datetime
    updated_at: datetime
    conversation_history: List[dict] = field(default_factory=list)
    current_diagram_xml: Optional[str] = None
    current_base_filename: Optional[str] = None
    diagram_description: Optional[str] = None
    last_generated_code: Optional[str] = None  # Store the last successful Python code



class SessionManager:
    """Manages diagram generation sessions with conversation history"""
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
    
    def create_session(self) -> Session:
        """Create a new session"""
        session_id = str(uuid.uuid4())[:8]  # Short UUID for convenience
        now = datetime.now()
        session = Session(
            session_id=session_id,
            created_at=now,
            updated_at=now
        )
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get an existing session by ID"""
        return self._sessions.get(session_id)
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
        """Get an existing session or create a new one"""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create_session()
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """Add a message to the conversation history"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        session.updated_at = datetime.now()
        return True
    
    def update_diagram(self, session_id: str, diagram_xml: str, base_filename: str, description: str = None, code: str = None):
        """Update the current diagram for a session"""
        session = self.get_session(session_id)
        if session:
            session.current_diagram_xml = diagram_xml
            session.current_base_filename = base_filename
            if description:
                session.diagram_description = description
            if code:
                session.last_generated_code = code
            session.updated_at = datetime.now()
    
    def get_conversation_for_llm(self, session_id: str) -> List[tuple]:
        """Get conversation history formatted for LangChain"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = []
        for msg in session.conversation_history:
            role = "human" if msg["role"] == "user" else "ai"
            messages.append((role, msg["content"]))
        return messages
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions older than max_age_hours"""
        now = datetime.now()
        expired = []
        for session_id, session in self._sessions.items():
            age = (now - session.updated_at).total_seconds() / 3600
            if age > max_age_hours:
                expired.append(session_id)
        
        for session_id in expired:
            self.delete_session(session_id)


# Global session manager instance
session_manager = SessionManager()
