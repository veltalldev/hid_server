# === app/models/script.py ===
"""
Script-related Pydantic models
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ScriptInfo(BaseModel):
    name: str
    size: int
    modified: str
    class_name: Optional[str] = None
    map_name: Optional[str] = None

class ScriptsResponse(BaseModel):
    success: bool
    scripts: List[ScriptInfo]

class ClassMapCombination(BaseModel):
    id: str
    class_name: str
    map_name: str
    script_name: str
    has_image: bool

class UploadResponse(BaseModel):
    success: bool
    message: str
    filename: str
    path: str
