# === app/models/macro.py ===
"""
Macro execution models
"""

from typing import Optional
from pydantic import BaseModel

class MacroRequest(BaseModel):
    script_name: str

class MacroResponse(BaseModel):
    success: bool
    message: str
    script: Optional[str] = None
    pid: Optional[int] = None

class StatusResponse(BaseModel):
    status: str
    current_script: Optional[str] = None
    pid: Optional[int] = None
