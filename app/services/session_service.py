# === Add to app/services/session_service.py (NEW FILE) ===
"""
Session state management service
"""

from datetime import datetime
from app.models.session import SessionState, SessionStateRequest
from app.core.exceptions import HIDServerException

class SessionService:
    """Handles session state management (in-memory, resets on server restart)"""
    
    def __init__(self):
        self._session_state = SessionState(
            selected_combination_id=None,
            step_size=1.0,
            last_updated=datetime.now().isoformat()
        )
    
    def get_session_state(self) -> SessionState:
        """Get current session state"""
        return self._session_state
    
    def update_session_state(self, request: SessionStateRequest) -> SessionState:
        """Update session state with provided values"""
        updated = False
        
        if request.selected_combination_id is not None:
            self._session_state.selected_combination_id = request.selected_combination_id
            updated = True
            
        if request.step_size is not None:
            # Validate step size (0.1 to 3.0 range for slider)
            if 0.1 <= request.step_size <= 3.0:
                self._session_state.step_size = request.step_size
                updated = True
            else:
                raise HIDServerException("Step size must be between 0.1 and 3.0")
        
        if updated:
            self._session_state.last_updated = datetime.now().isoformat()
            
        return self._session_state
    
    def clear_session_state(self) -> SessionState:
        """Clear session state"""
        self._session_state = SessionState(
            selected_combination_id=None,
            step_size=1.0,
            last_updated=datetime.now().isoformat()
        )
        return self._session_state
