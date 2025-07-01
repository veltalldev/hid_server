#!/usr/bin/env python3
"""
Enhanced HID Server v3.0 - Post-Migration
Supports semantic script naming and modular action endpoints
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import os
import signal
import datetime
from pathlib import Path
from typing import Optional, List
import asyncio
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced HID Server v3.0 - Post-Migration",
    description="Control Raspberry Pi HID with semantic script organization",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
SCRIPT_DIR = Path.cwd() / "scripts"
ACTIONS_DIR = Path.cwd() / "actions"
IMAGES_DIR = Path.cwd() / "images"
CERT_DIR = Path.cwd() / "certs"
MAX_FILE_SIZE = 16 * 1024 * 1024

# Global macro state
current_process: Optional[subprocess.Popen] = None
current_script: Optional[str] = None
macro_paused: bool = False

# === PYDANTIC MODELS ===

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

class ServerInfo(BaseModel):
    message: str
    version: str
    status: str
    script_directory: str
    actions_directory: str
    images_directory: str
    mouse_enabled: bool
    class_map_combinations: List[ClassMapCombination]

# === UTILITY FUNCTIONS ===

def parse_script_metadata(script_name: str) -> tuple[Optional[str], Optional[str]]:
    """Parse class and map from semantic script name"""
    # Example: drk_bottom_deck_passage_3.ahk -> ("drk", "bottom_deck_passage_3")
    if not script_name.endswith('.ahk'):
        return None, None
    
    base_name = script_name[:-4]  # Remove .ahk
    parts = base_name.split('_', 1)  # Split on first underscore only
    
    if len(parts) == 2:
        class_name = parts[0]
        map_name = parts[1]
        return class_name, map_name
    
    return None, None

def get_class_display_name(class_code: str) -> str:
    """Convert class code to display name"""
    class_names = {
        'drk': 'Dark Knight',
        'nw': 'Night Walker',
        # Add more as needed
    }
    return class_names.get(class_code, class_code.upper())

def get_map_display_name(map_code: str) -> str:
    """Convert map code to display name"""
    # Convert underscores to spaces and title case
    return map_code.replace('_', ' ').title()

async def send_key(key: str, hold_ms: int = 100):
    """Send a key press via HID emulator"""
    try:
        # Create temporary AHK script for single key press
        ahk_content = f"""
Send, {{{key} Down}}
Sleep, {hold_ms}
Send, {{{key} Up}}
Sleep, 100
"""
        temp_file = Path("/tmp/temp_key.ahk")
        temp_file.write_text(ahk_content)
        
        process = await asyncio.create_subprocess_exec(
            'python3', 'ahk_to_hid_v2.py', str(temp_file),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await asyncio.wait_for(process.communicate(), timeout=5.0)
        temp_file.unlink(missing_ok=True)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Key press failed: {str(e)}"
        )

async def click_coordinates(x: int, y: int):
    """Click at specific coordinates via mouse control"""
    try:
        process = await asyncio.create_subprocess_exec(
            'python3', 'mouse_control.py', 'click', str(x), str(y),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else stdout.decode()
            raise Exception(f"Mouse click failed: {error_msg}")
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Click failed: {str(e)}"
        )

# === MAIN ROUTES ===

@app.get("/", response_model=ServerInfo)
async def root():
    """Get server information and available combinations"""
    combinations = []
    
    # Scan scripts directory for farming scripts
    if SCRIPT_DIR.exists():
        for script_file in SCRIPT_DIR.glob("*.ahk"):
            class_code, map_code = parse_script_metadata(script_file.name)
            if class_code and map_code:
                # Check if image exists
                image_exists = False
                script_base = script_file.stem  # filename without .ahk
                for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                    if (IMAGES_DIR / f"{script_base}{ext}").exists():
                        image_exists = True
                        break
                
                combinations.append(ClassMapCombination(
                    id=f"{class_code}_{map_code}",
                    class_name=get_class_display_name(class_code),
                    map_name=get_map_display_name(map_code),
                    script_name=script_file.name,
                    has_image=image_exists
                ))
    
    mouse_script_exists = (Path.cwd() / "mouse_control.py").exists()
    
    return ServerInfo(
        message="Enhanced HID Server v3.0 - Post-Migration",
        version="3.0.0",
        status="running",
        script_directory=str(SCRIPT_DIR),
        actions_directory=str(ACTIONS_DIR),
        images_directory=str(IMAGES_DIR),
        mouse_enabled=mouse_script_exists,
        class_map_combinations=combinations
    )

@app.get("/scripts", response_model=ScriptsResponse)
async def list_scripts():
    """List only farming scripts (excludes action scripts)"""
    try:
        scripts = []
        
        # Only scan main scripts directory, not actions
        for filepath in SCRIPT_DIR.glob("*.ahk"):
            # Skip if it's in old/ subdirectory
            if "old" in str(filepath):
                continue
                
            stat = filepath.stat()
            class_code, map_code = parse_script_metadata(filepath.name)
            
            scripts.append(ScriptInfo(
                name=filepath.name,
                size=stat.st_size,
                modified=datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                class_name=get_class_display_name(class_code) if class_code else None,
                map_name=get_map_display_name(map_code) if map_code else None
            ))
        
        scripts.sort(key=lambda x: x.modified, reverse=True)
        
        return ScriptsResponse(success=True, scripts=scripts)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scripts: {str(e)}"
        )

@app.get("/image/{script_name}")
async def get_script_image(script_name: str):
    """Get background image for a script"""
    # Remove .ahk extension if present
    if script_name.endswith('.ahk'):
        script_name = script_name[:-4]
    
    safe_script_name = "".join(c for c in script_name if c.isalnum() or c in "._-")
    
    for extension in ['.webp', '.png', '.jpg', '.jpeg', '.gif']:
        image_path = IMAGES_DIR / f"{safe_script_name}{extension}"
        
        if image_path.exists() and image_path.is_file():
            file_size = image_path.stat().st_size
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                raise HTTPException(status_code=413, detail="Image file too large")
            
            media_type = _get_media_type(extension)
            return FileResponse(
                path=str(image_path),
                media_type=media_type,
                filename=f"{safe_script_name}{extension}"
            )
    
    raise HTTPException(status_code=404, detail=f"No image found for script '{script_name}'")

def _get_media_type(extension: str) -> str:
    """Get media type for image extension"""
    extension = extension.lower()
    media_types = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
        '.gif': 'image/gif', '.webp': 'image/webp'
    }
    return media_types.get(extension, 'image/jpeg')

# === MACRO CONTROL ROUTES ===

@app.post("/start_macro", response_model=MacroResponse)
async def start_macro(request: MacroRequest):
    """Start macro execution"""
    global current_process, current_script, macro_paused
    
    script_path = SCRIPT_DIR / request.script_name
    
    if not script_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script file not found"
        )
    
    # Stop current macro if running
    if current_process and current_process.poll() is None:
        await stop_current_macro()
    
    try:
        current_process = subprocess.Popen([
            'python3', 'ahk_to_hid_v2.py', str(script_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        current_script = request.script_name
        macro_paused = False
        
        return MacroResponse(
            success=True,
            message="Macro started successfully",
            script=request.script_name,
            pid=current_process.pid
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start macro: {str(e)}"
        )

@app.post("/pause_macro", response_model=MacroResponse)
async def pause_macro():
    """Pause current macro"""
    global current_process, macro_paused
    
    if not current_process or current_process.poll() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No macro currently running"
        )
    
    if macro_paused:
        return MacroResponse(success=True, message="Macro is already paused")
    
    try:
        current_process.send_signal(signal.SIGUSR1)
        macro_paused = True
        return MacroResponse(success=True, message="Macro paused successfully")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause macro: {str(e)}"
        )

@app.post("/resume_macro", response_model=MacroResponse)
async def resume_macro():
    """Resume paused macro"""
    global current_process, macro_paused
    
    if not current_process or current_process.poll() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No macro currently running"
        )
    
    if not macro_paused:
        return MacroResponse(success=True, message="Macro is not paused")
    
    try:
        current_process.send_signal(signal.SIGUSR2)
        macro_paused = False
        return MacroResponse(success=True, message="Macro resumed successfully")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume macro: {str(e)}"
        )

@app.post("/stop_macro", response_model=MacroResponse)
async def stop_macro():
    """Stop current macro"""
    if not current_process or current_process.poll() is None:
        return MacroResponse(success=True, message="No macro currently running")
    
    try:
        await stop_current_macro()
        return MacroResponse(success=True, message="Macro stopped successfully")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop macro: {str(e)}"
        )

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current macro status"""
    global current_process, current_script, macro_paused
    
    if current_process:
        if current_process.poll() is None:
            status_val = 'paused' if macro_paused else 'running'
        else:
            status_val = 'stopped'
            current_process = None
            current_script = None
            macro_paused = False
    else:
        status_val = 'idle'
    
    return StatusResponse(
        status=status_val,
        current_script=current_script,
        pid=current_process.pid if current_process and status_val in ['running', 'paused'] else None
    )

async def stop_current_macro():
    """Helper to stop current macro process"""
    global current_process, current_script, macro_paused
    
    if current_process:
        try:
            current_process.send_signal(signal.SIGTERM)
            
            for _ in range(50):  # 5 second timeout
                if current_process.poll() is not None:
                    break
                await asyncio.sleep(0.1)
            else:
                current_process.kill()
                current_process.wait()
                
        except ProcessLookupError:
            pass
        finally:
            current_process = None
            current_script = None
            macro_paused = False

# === MODULAR ACTION ENDPOINTS ===

@app.post("/action/movement/double_jump", response_model=MacroResponse)
async def action_double_jump():
    """Execute double jump action"""
    try:
        await send_key("Space", 50)
        await asyncio.sleep(0.1)
        await send_key("Space", 50)
        await asyncio.sleep(0.3)
        
        return MacroResponse(success=True, message="Double jump executed")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Double jump failed: {str(e)}"
        )

@app.post("/action/movement/jump_down", response_model=MacroResponse)
async def action_jump_down():
    """Execute jump down action"""
    try:
        await send_key("Down", 50)
        await send_key("Space", 50)
        await asyncio.sleep(0.05)
        await send_key("Down", 0)  # Release down
        await asyncio.sleep(1.0)
        
        return MacroResponse(success=True, message="Jump down executed")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Jump down failed: {str(e)}"
        )

@app.post("/action/movement/rope_up", response_model=MacroResponse)
async def action_rope_up():
    """Execute rope/platform ascent"""
    try:
        await send_key("End", 200)
        await asyncio.sleep(2.0)
        
        return MacroResponse(success=True, message="Rope up executed")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rope up failed: {str(e)}"
        )

@app.post("/action/movement/interact", response_model=MacroResponse)
async def action_interact():
    """Execute interact (Y key)"""
    try:
        await send_key("y", 100)
        await asyncio.sleep(0.1)
        
        return MacroResponse(success=True, message="Interact executed")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interact failed: {str(e)}"
        )

# Movement directions with configurable step sizes
@app.post("/action/movement/{direction}", response_model=MacroResponse)
async def action_movement(direction: str, step_size: str = "medium"):
    """Execute directional movement with step size"""
    valid_directions = ["up", "down", "left", "right"]
    if direction not in valid_directions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid direction. Must be one of: {valid_directions}"
        )
    
    # Step size mapping to hold duration
    step_durations = {
        "small": 100,
        "medium": 300, 
        "large": 800
    }
    
    if step_size not in step_durations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid step size. Must be one of: {list(step_durations.keys())}"
        )
    
    try:
        hold_duration = step_durations[step_size]
        await send_key(direction.title(), hold_duration)  # Up, Down, Left, Right
        await asyncio.sleep(0.1)
        
        return MacroResponse(
            success=True, 
            message=f"{step_size.title()} {direction} movement executed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Movement failed: {str(e)}"
        )

# === UTILITY ACTION ENDPOINTS ===

@app.post("/action/utility/go_to_town", response_model=MacroResponse)
async def action_go_to_town():
    """Go to town sequence"""
    try:
        await send_key("=", 100)
        await asyncio.sleep(0.5)
        await click_coordinates(1150, 642)  # Town button
        await asyncio.sleep(5.0)  # Loading time
        await send_key("Escape", 100)
        
        return MacroResponse(success=True, message="Go to town executed")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Go to town failed: {str(e)}"
        )

@app.post("/action/utility/go_to_hunting", response_model=MacroResponse)
async def action_go_to_hunting():
    """Go to hunting ground sequence"""
    try:
        await send_key("=", 100)
        await asyncio.sleep(0.5)
        await send_key("=", 100)
        await asyncio.sleep(0.5)
        await click_coordinates(725, 1075)  # Hunting ground button
        await asyncio.sleep(1.0)
        await click_coordinates(1180, 986)  # Confirm button
        await asyncio.sleep(5.0)  # Loading time
        await send_key("Escape", 100)
        
        return MacroResponse(success=True, message="Go to hunting executed")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Go to hunting failed: {str(e)}"
        )

@app.post("/action/utility/use_consumables", response_model=MacroResponse)
async def action_use_consumables():
    """Use all consumable items"""
    try:
        await send_key("i", 100)  # Open inventory
        await asyncio.sleep(0.5)
        
        # Item slot coordinates
        slots = [
            (1538, 600), (1435, 600), (1360, 600),  # Top row
            (1360, 525), (1435, 525), (1538, 525)   # Bottom row
        ]
        
        for x, y in slots:
            # Double-click each slot
            await click_coordinates(x, y)
            await asyncio.sleep(0.1)
            await click_coordinates(x, y)
            await asyncio.sleep(0.2)
        
        await send_key("i", 100)  # Close inventory
        
        return MacroResponse(success=True, message="Use consumables executed")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Use consumables failed: {str(e)}"
        )

# === DEBUG ENDPOINT ===

@app.get("/debug")
async def debug_info():
    """Debug server state"""
    return {
        "working_directory": str(Path.cwd()),
        "directories": {
            "scripts": str(SCRIPT_DIR),
            "actions": str(ACTIONS_DIR), 
            "images": str(IMAGES_DIR)
        },
        "directories_exist": {
            "scripts": SCRIPT_DIR.exists(),
            "actions": ACTIONS_DIR.exists(),
            "images": IMAGES_DIR.exists()
        },
        "file_counts": {
            "farming_scripts": len(list(SCRIPT_DIR.glob("*.ahk"))) if SCRIPT_DIR.exists() else 0,
            "action_scripts": len(list(ACTIONS_DIR.glob("**/*.ahk"))) if ACTIONS_DIR.exists() else 0,
            "images": len(list(IMAGES_DIR.glob("*"))) if IMAGES_DIR.exists() else 0
        },
        "current_macro": {
            "pid": current_process.pid if current_process else None,
            "script": current_script,
            "paused": macro_paused
        },
        "hid_devices": {
            "keyboard": Path("/dev/hidg0").exists(),
            "mouse": Path("/dev/hidg1").exists()
        }
    }

# === STARTUP ===

@app.on_event("startup")
async def startup_event():
    """Initialize server"""
    print("🚀 Enhanced HID Server v3.0 starting...")
    print(f"📁 Scripts: {SCRIPT_DIR}")
    print(f"🎮 Actions: {ACTIONS_DIR}")
    print(f"🖼️  Images: {IMAGES_DIR}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown"""
    global current_process
    if current_process and current_process.poll() is None:
        print("🛑 Stopping running macro...")
        await stop_current_macro()
    print("👋 Server shutdown complete")

def main():
    """Run server"""
    print("Enhanced HID Server v3.0 - Post-Migration")
    
    # Generate or use existing certificates
    cert_file, key_file = generate_self_signed_cert()
    
    if cert_file and key_file:
        print("🔐 Starting HTTPS server on port 8444...")
        print("📚 API Documentation: https://localhost:8444/docs")
        print("🎮 New action endpoints: /action/movement/*, /action/utility/*")
        print("⚠️  You'll need to accept the self-signed certificate warning")
        
        # Run with SSL
        uvicorn.run(
            "enhanced_server_v3:app",
            host="0.0.0.0",
            port=8444,
            ssl_keyfile=key_file,
            ssl_certfile=cert_file,
            reload=True,
            log_level="info"
        )
    else:
        print("⚠️  SSL certificate generation failed, falling back to HTTP...")
        print("🌐 Starting HTTP server on port 8444...")
        print("📚 API Documentation: http://localhost:8444/docs")
        
        # Fallback to HTTP
        uvicorn.run(
            "enhanced_server_v3:app",
            host="0.0.0.0",
            port=8444,
            reload=True,
            log_level="info"
        )

if __name__ == "__main__":
    main()
