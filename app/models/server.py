# === app/models/server.py ===
"""
Server info models
"""

from typing import List
from pydantic import BaseModel
from app.models.script import ClassMapCombination

class ServerInfo(BaseModel):
    message: str
    version: str
    status: str
    script_directory: str
    actions_directory: str
    images_directory: str
    mouse_enabled: bool
    keyboard_enabled: bool
    class_map_combinations: List[ClassMapCombination]
