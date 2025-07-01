# === app/api/v1/server.py ===
"""
Server information and status endpoints
"""

from fastapi import APIRouter, Depends
from app.models.server import ServerInfo
from app.services.script_service import ScriptService
from app.core.config import settings
from pathlib import Path

router = APIRouter()

@router.get("/", response_model=ServerInfo)
async def get_server_info(
    script_service: ScriptService = Depends(lambda: ScriptService())
):
    """Get server information and available class+map combinations"""
    
    # Get class+map combinations
    combinations = await script_service.get_class_map_combinations()
    
    # Check if HID devices and scripts exist
    mouse_enabled = Path(settings.MOUSE_DEVICE).exists() and (Path.cwd() / "mouse_control.py").exists()
    keyboard_enabled = Path(settings.KEYBOARD_DEVICE).exists()
    
    return ServerInfo(
        message="HID Server v4.0 - Organized Application",
        version="4.0.0",
        status="running",
        script_directory=str(settings.SCRIPT_DIR),
        actions_directory=str(settings.ACTIONS_DIR),
        images_directory=str(settings.IMAGES_DIR),
        mouse_enabled=mouse_enabled,
        keyboard_enabled=keyboard_enabled,
        class_map_combinations=combinations
    )

@router.get("/debug")
async def debug_info():
    """Debug server state"""
    return {
        "working_directory": str(Path.cwd()),
        "directories": {
            "scripts": str(settings.SCRIPT_DIR),
            "actions": str(settings.ACTIONS_DIR),
            "images": str(settings.IMAGES_DIR),
            "certs": str(settings.CERT_DIR)
        },
        "directories_exist": {
            "scripts": settings.SCRIPT_DIR.exists(),
            "actions": settings.ACTIONS_DIR.exists(),
            "images": settings.IMAGES_DIR.exists(),
            "certs": settings.CERT_DIR.exists()
        },
        "file_counts": {
            "farming_scripts": len(list(settings.SCRIPT_DIR.glob("*.ahk"))),
            "action_scripts": len(list(settings.ACTIONS_DIR.glob("**/*.ahk"))),
            "images": len(list(settings.IMAGES_DIR.glob("*")))
        },
        "hid_devices": {
            "keyboard": Path(settings.KEYBOARD_DEVICE).exists(),
            "mouse": Path(settings.MOUSE_DEVICE).exists()
        }
    }
