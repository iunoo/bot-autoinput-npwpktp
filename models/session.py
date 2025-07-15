"""
Session management models for tracking user interactions.
Provides structured session state management with persistence and expiration.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum

from .document import DocumentData
from config.settings import settings


class SessionState(Enum):
    """Enum for session states."""
    IDLE = "idle"
    AWAITING_BRANCH = "awaiting_branch"
    AWAITING_NPWP_TYPE = "awaiting_npwp_type"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    AWAITING_EDIT_INPUT = "awaiting_edit_input"
    AWAITING_PDF_NAME = "awaiting_pdf_name"
    AWAITING_BRANCH_EDIT = "awaiting_branch_edit"
    SELECTING_EDIT_FIELD = "selecting_edit_field"
    AWAITING_DUPLICATE_CONFIRMATION = "awaiting_duplicate_confirmation"
    PROCESSING_AI = "processing_ai"
    SAVING_DATA = "saving_data"


class WorkflowType(Enum):
    """Enum for workflow types."""
    PHOTO = "photo"
    PDF = "pdf"


@dataclass
class UserSession:
    """
    User session model with comprehensive state management.
    Tracks user workflow progress and maintains context.
    """
    user_id: int
    state: SessionState = SessionState.IDLE
    workflow_type: Optional[WorkflowType] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    # File information
    file_id: Optional[str] = None
    file_size: Optional[int] = None
    original_filename: Optional[str] = None
    custom_filename: Optional[str] = None
    
    # Workflow data
    branch: Optional[str] = None
    sheet_name: Optional[str] = None
    nama_toko: Optional[str] = None
    
    # Document processing
    document_data: Optional[DocumentData] = None
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    npwp_type: Optional[str] = None
    
    # Edit workflow
    edit_field: Optional[str] = None
    last_bot_message_id: Optional[int] = None
    
    # Custom data storage
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    total_interactions: int = 0
    error_count: int = 0
    
    def __post_init__(self):
        """Post-initialization setup."""
        self.update_activity()
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
        self.total_interactions += 1
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        timeout = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
        return datetime.now() - self.last_activity > timeout
    
    def get_age(self) -> timedelta:
        """Get session age."""
        return datetime.now() - self.created_at
    
    def get_idle_time(self) -> timedelta:
        """Get time since last activity."""
        return datetime.now() - self.last_activity
    
    def set_state(self, new_state: SessionState) -> None:
        """Set new state and update activity."""
        self.state = new_state
        self.update_activity()
    
    def set_workflow(self, workflow_type: WorkflowType) -> None:
        """Set workflow type and update activity."""
        self.workflow_type = workflow_type
        self.set_state(SessionState.AWAITING_BRANCH)
    
    def clear_workflow_data(self) -> None:
        """Clear workflow-specific data."""
        self.workflow_type = None
        self.file_id = None
        self.file_size = None
        self.original_filename = None
        self.custom_filename = None
        self.branch = None
        self.sheet_name = None
        self.nama_toko = None
        self.document_data = None
        self.extracted_data = {}
        self.npwp_type = None
        self.edit_field = None
        self.last_bot_message_id = None
        self.state = SessionState.IDLE
    
    def reset_session(self) -> None:
        """Reset entire session."""
        self.clear_workflow_data()
        self.custom_data.clear()
        self.total_interactions = 0
        self.error_count = 0
        self.created_at = datetime.now()
        self.update_activity()
    
    def increment_error_count(self) -> None:
        """Increment error count."""
        self.error_count += 1
        self.update_activity()
    
    def has_active_workflow(self) -> bool:
        """Check if session has an active workflow."""
        return (
            self.workflow_type is not None and 
            self.state != SessionState.IDLE and
            not self.is_expired()
        )
    
    def can_transition_to(self, new_state: SessionState) -> bool:
        """Check if transition to new state is valid."""
        # Define valid state transitions
        valid_transitions = {
            SessionState.IDLE: [
                SessionState.AWAITING_BRANCH
            ],
            SessionState.AWAITING_BRANCH: [
                SessionState.AWAITING_NPWP_TYPE,
                SessionState.AWAITING_CONFIRMATION,
                SessionState.AWAITING_PDF_NAME,
                SessionState.PROCESSING_AI,
                SessionState.IDLE
            ],
            SessionState.PROCESSING_AI: [
                SessionState.AWAITING_NPWP_TYPE,
                SessionState.AWAITING_CONFIRMATION,
                SessionState.IDLE
            ],
            SessionState.AWAITING_NPWP_TYPE: [
                SessionState.AWAITING_CONFIRMATION,
                SessionState.IDLE
            ],
            SessionState.AWAITING_CONFIRMATION: [
                SessionState.SELECTING_EDIT_FIELD,
                SessionState.AWAITING_DUPLICATE_CONFIRMATION,
                SessionState.SAVING_DATA,
                SessionState.IDLE
            ],
            SessionState.SELECTING_EDIT_FIELD: [
                SessionState.AWAITING_EDIT_INPUT,
                SessionState.AWAITING_BRANCH_EDIT,
                SessionState.AWAITING_CONFIRMATION,
                SessionState.IDLE
            ],
            SessionState.AWAITING_EDIT_INPUT: [
                SessionState.AWAITING_CONFIRMATION,
                SessionState.IDLE
            ],
            SessionState.AWAITING_BRANCH_EDIT: [
                SessionState.AWAITING_CONFIRMATION,
                SessionState.IDLE
            ],
            SessionState.AWAITING_PDF_NAME: [
                SessionState.SAVING_DATA,
                SessionState.IDLE
            ],
            SessionState.AWAITING_DUPLICATE_CONFIRMATION: [
                SessionState.SAVING_DATA,
                SessionState.IDLE
            ],
            SessionState.SAVING_DATA: [
                SessionState.IDLE
            ]
        }
        
        allowed_states = valid_transitions.get(self.state, [])
        return new_state in allowed_states or new_state == SessionState.IDLE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for storage."""
        data = asdict(self)
        
        # Convert datetime objects to ISO strings
        data['created_at'] = self.created_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        
        # Convert enums to strings
        data['state'] = self.state.value
        if self.workflow_type:
            data['workflow_type'] = self.workflow_type.value
        
        # Convert document data if present
        if self.document_data:
            data['document_data'] = self.document_data.to_dict()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSession':
        """Create session from dictionary."""
        # Convert datetime strings back to datetime objects
        created_at = datetime.fromisoformat(data['created_at'])
        last_activity = datetime.fromisoformat(data['last_activity'])
        
        # Convert string enums back to enum objects
        state = SessionState(data['state'])
        workflow_type = None
        if data.get('workflow_type'):
            workflow_type = WorkflowType(data['workflow_type'])
        
        # Convert document data if present
        document_data = None
        if data.get('document_data'):
            document_data = DocumentData.from_dict(data['document_data'])
        
        return cls(
            user_id=data['user_id'],
            state=state,
            workflow_type=workflow_type,
            created_at=created_at,
            last_activity=last_activity,
            file_id=data.get('file_id'),
            file_size=data.get('file_size'),
            original_filename=data.get('original_filename'),
            custom_filename=data.get('custom_filename'),
            branch=data.get('branch'),
            sheet_name=data.get('sheet_name'),
            nama_toko=data.get('nama_toko'),
            document_data=document_data,
            extracted_data=data.get('extracted_data', {}),
            npwp_type=data.get('npwp_type'),
            edit_field=data.get('edit_field'),
            last_bot_message_id=data.get('last_bot_message_id'),
            custom_data=data.get('custom_data', {}),
            total_interactions=data.get('total_interactions', 0),
            error_count=data.get('error_count', 0)
        )
    
    def get_status_summary(self) -> str:
        """Get human-readable status summary."""
        age_minutes = int(self.get_age().total_seconds() / 60)
        idle_minutes = int(self.get_idle_time().total_seconds() / 60)
        
        status = [
            f"👤 User: {self.user_id}",
            f"📊 State: {self.state.value}",
            f"⏰ Age: {age_minutes} minutes",
            f"💤 Idle: {idle_minutes} minutes"
        ]
        
        if self.workflow_type:
            status.append(f"🔄 Workflow: {self.workflow_type.value}")
        
        if self.branch:
            status.append(f"🏢 Branch: {self.branch}")
        
        status.extend([
            f"🔄 Interactions: {self.total_interactions}",
            f"❌ Errors: {self.error_count}"
        ])
        
        return "\n".join(status)
    
    def __str__(self) -> str:
        """String representation."""
        return f"UserSession(user_id={self.user_id}, state={self.state.value}, workflow={self.workflow_type.value if self.workflow_type else None})"


class SessionManager:
    """
    Manager class for handling multiple user sessions.
    Provides session lifecycle management and cleanup.
    """
    
    def __init__(self):
        self._sessions: Dict[int, UserSession] = {}
    
    def get_session(self, user_id: int) -> UserSession:
        """Get or create user session."""
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession(user_id=user_id)
        
        session = self._sessions[user_id]
        
        # Check if session is expired
        if session.is_expired():
            # Create new session if expired
            self._sessions[user_id] = UserSession(user_id=user_id)
            return self._sessions[user_id]
        
        return session
    
    def clear_session(self, user_id: int) -> None:
        """Clear user session."""
        if user_id in self._sessions:
            del self._sessions[user_id]
    
    def reset_session(self, user_id: int) -> UserSession:
        """Reset user session."""
        session = self.get_session(user_id)
        session.reset_session()
        return session
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count of removed sessions."""
        expired_users = [
            user_id for user_id, session in self._sessions.items()
            if session.is_expired()
        ]
        
        for user_id in expired_users:
            del self._sessions[user_id]
        
        return len(expired_users)
    
    def get_active_sessions_count(self) -> int:
        """Get count of active (non-expired) sessions."""
        return sum(
            1 for session in self._sessions.values()
            if not session.is_expired()
        )
    
    def get_sessions_by_state(self, state: SessionState) -> List[UserSession]:
        """Get all sessions in a specific state."""
        return [
            session for session in self._sessions.values()
            if session.state == state and not session.is_expired()
        ]
    
    def get_all_sessions(self) -> List[UserSession]:
        """Get all active sessions."""
        return [
            session for session in self._sessions.values()
            if not session.is_expired()
        ]
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        active_sessions = self.get_all_sessions()
        
        # Count by state
        state_counts = {}
        for state in SessionState:
            state_counts[state.value] = len(self.get_sessions_by_state(state))
        
        # Count by workflow type
        workflow_counts = {}
        for workflow in WorkflowType:
            workflow_counts[workflow.value] = sum(
                1 for session in active_sessions
                if session.workflow_type == workflow
            )
        
        return {
            'total_sessions': len(self._sessions),
            'active_sessions': len(active_sessions),
            'expired_sessions': len(self._sessions) - len(active_sessions),
            'state_distribution': state_counts,
            'workflow_distribution': workflow_counts,
            'average_interactions': sum(s.total_interactions for s in active_sessions) / len(active_sessions) if active_sessions else 0,
            'total_errors': sum(s.error_count for s in active_sessions)
        }


# Global session manager instance
session_manager = SessionManager()