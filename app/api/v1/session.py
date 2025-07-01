# === Add to app/api/v1/session.py (NEW FILE) ===
"""
Session state endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from app.models.session import SessionStateRequest, SessionStateResponse
from app.services.session_service import SessionService
from app.core.exceptions import HIDServerException

router = APIRouter()

# Global session service instance
_session_service = SessionService()

def get_session_service() -> SessionService:
    """Get the global session service instance"""
    return _session_service

@router.get("/session_state", response_model=SessionStateResponse)
async def get_session_state(
    session_service: SessionService = Depends(get_session_service)
):
    """Get current session state"""
    session_state = session_service.get_session_state()
    return SessionStateResponse(success=True, session_state=session_state)

@router.post("/session_state", response_model=SessionStateResponse)
async def update_session_state(
    request: SessionStateRequest,
    session_service: SessionService = Depends(get_session_service)
):
    """Update session state"""
    try:
        session_state = session_service.update_session_state(request)
        return SessionStateResponse(success=True, session_state=session_state)
    except HIDServerException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/session_state", response_model=SessionStateResponse)
async def clear_session_state(
    session_service: SessionService = Depends(get_session_service)
):
    """Clear session state"""
    session_state = session_service.clear_session_state()
    return SessionStateResponse(success=True, session_state=session_state)

