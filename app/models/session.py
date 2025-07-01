# === Add to app/models/session.py (NEW FILE) ===
"""
Session state models
"""

from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class SessionState(BaseModel):
    selected_combination_id: Optional[str] = None
    step_size: float = 1.0  # Default medium
    last_updated: str

class SessionStateRequest(BaseModel):
    selected_combination_id: Optional[str] = None
    step_size: Optional[float] = None

class SessionStateResponse(BaseModel):
    success: bool
    session_state: SessionState
