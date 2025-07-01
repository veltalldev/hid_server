#!/usr/bin/env python3
"""
Enhanced HID Keyboard + Mouse Control Server
Now includes single key press and file-based action system
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
import subprocess
import os
import signal
import datetime
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import asyncio
import uvicorn
import ssl

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced HID Keyboard + Mouse Control Server",
    description="Control Raspberry Pi HID keyboard and mouse macros remotely",
    version="2.6.0",
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
ACTIONS_DIR = Path.cwd() / "actions"  # New directory for action files
CERT_DIR = Path.cwd() / "certs"
IMAGES_DIR = Path.cwd() / "images"
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Global variables to track current macro
current_process: Optional[subprocess.Popen] = None
current_script: Optional[str] = None
macro_paused: bool = False

# Ensure directories exist
SCRIPT_DIR.mkdir(exist_ok=True, mode=0o755)
ACTIONS_DIR.mkdir(exist_ok=True, mode=0o755)  # Create actions directory
CERT_DIR.mkdir(exist_ok=True, mode=0o755)
IMAGES_DIR.mkdir(exist_ok=True, mode=0o755)

# Support
SUPPORTED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']

# Valid keys for key press endpoint (whitelist for security)
VALID_KEYS = {
    # Letters
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    # Numbers
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    # Special keys (using AHK names from documentation)
    'space', 'enter', 'escape', 'tab', 'backspace', 'delete',
    'up', 'down', 'left', 'right', 'end', 'home', 'pgup', 'pgdn',
    'insert', 'scrolllock', 'capslock', 'numlock', 'printscreen', 'pause',
    # Function keys
    'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
    # Special characters (direct from keyboard, no mapping needed)
    '=', '-', '[', ']', ';', "'", ',', '.', '/', '\\', '`',
    # Modifier keys
    'ctrl', 'alt', 'shift', 'lwin', 'rwin'
}

# === PYDANTIC MODELS ===

# Existing models...
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

class ScriptsResponse(BaseModel):
    success: bool
    scripts: List[ScriptInfo]

class UploadResponse(BaseModel):
    success: bool
    message: str
    filename: str
    path: str

class ServerInfo(BaseModel):
    message: str
    version: str
    status: str
    docs_url: str
    script_directory: str
    actions_directory: str
    ssl_enabled: bool
    mouse_enabled: bool

class MouseClickRequest(BaseModel):
    x: int
    y: int
    button: str = "left"
    double: bool = False

class MouseMoveRequest(BaseModel):
    x: int
    y: int

class MouseResponse(BaseModel):
    success: bool
    message: str
    coordinates: Optional[dict] = None

# New models for key press and actions
class KeyPressRequest(BaseModel):
    key: str
    hold_ms: int = 100  # How long to hold the key

class KeyResponse(BaseModel):
    success: bool
    message: str
    key: Optional[str] = None

class ActionInfo(BaseModel):
    name: str
    description: str
    step_count: int

class ActionsResponse(BaseModel):
    success: bool
    actions: List[ActionInfo]

class ActionResponse(BaseModel):
    success: bool
    message: str
    action_name: Optional[str] = None
    steps_executed: Optional[int] = None

# === EXISTING KEYBOARD ROUTES ===

@app.get("/", response_model=ServerInfo)
async def root():
    """Get server information and status"""
    mouse_script_exists = (Path.cwd() / "mouse_control.py").exists()
    
    return ServerInfo(
        message="Enhanced HID Keyboard + Mouse Control Server",
        version="2.6.0",
        status="running",
        docs_url="/docs",
        script_directory=str(SCRIPT_DIR),
        actions_directory=str(ACTIONS_DIR),
        ssl_enabled=True,
        mouse_enabled=mouse_script_exists
    )

# [Keep all existing keyboard routes: upload_script, start_macro, pause_macro, 
#  resume_macro, stop_macro, get_status, list_scripts, delete_script, get_script_image]

@app.post("/upload_script", response_model=UploadResponse)
async def upload_script(file: UploadFile = File(...)):
    """Upload an AHK script file"""
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected"
        )
    
    if not file.filename.endswith('.ahk'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only .ahk files allowed"
        )
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    try:
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-")
        if not safe_filename.endswith('.ahk'):
            safe_filename += '.ahk'
            
        filepath = SCRIPT_DIR / safe_filename
        
        with open(filepath, 'wb') as f:
            f.write(content)
        
        return UploadResponse(
            success=True,
            message="Script uploaded successfully",
            filename=safe_filename,
            path=str(filepath)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

@app.post("/start_macro", response_model=MacroResponse)
async def start_macro(request: MacroRequest):
    """Start macro execution"""
    global current_process, current_script
    
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
            'python3',
            'ahk_to_hid_v2.py',
            str(script_path)
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
    """Pause current macro execution"""
    global current_process, macro_paused
    
    if not current_process or current_process.poll() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No macro currently running"
        )
    
    if macro_paused:
        return MacroResponse(
            success=True,
            message="Macro is already paused"
        )
    
    try:
        current_process.send_signal(signal.SIGUSR1)
        macro_paused = True
        return MacroResponse(
            success=True,
            message="Macro paused successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause macro: {str(e)}"
        )

@app.post("/resume_macro", response_model=MacroResponse)
async def resume_macro():
    """Resume paused macro execution"""
    global current_process, macro_paused
    
    if not current_process or current_process.poll() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No macro currently running"
        )
    
    if not macro_paused:
        return MacroResponse(
            success=True,
            message="Macro is not paused"
        )
    
    try:
        current_process.send_signal(signal.SIGUSR2)
        macro_paused = False
        return MacroResponse(
            success=True,
            message="Macro resumed successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume macro: {str(e)}"
        )

@app.post("/stop_macro", response_model=MacroResponse)
async def stop_macro():
    """Stop current macro execution"""
    global current_process, current_script
    
    if not current_process or current_process.poll() is None:
        return MacroResponse(
            success=True,
            message="No macro currently running"
        )
    
    try:
        await stop_current_macro()
        return MacroResponse(
            success=True,
            message="Macro stopped successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop macro: {str(e)}"
        )

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current macro execution status"""
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

@app.get("/scripts", response_model=ScriptsResponse)
async def list_scripts():
    """List available AHK scripts"""
    try:
        scripts = []
        
        for filepath in SCRIPT_DIR.glob("*.ahk"):
            stat = filepath.stat()
            scripts.append(ScriptInfo(
                name=filepath.name,
                size=stat.st_size,
                modified=datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
            ))
        
        scripts.sort(key=lambda x: x.modified, reverse=True)
        
        return ScriptsResponse(success=True, scripts=scripts)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scripts: {str(e)}"
        )

@app.delete("/delete_script/{script_name}", response_model=MacroResponse)
async def delete_script(script_name: str):
    """Delete an AHK script"""
    global current_script, current_process
    
    script_path = SCRIPT_DIR / script_name
    
    if not script_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    if (current_script == script_name and 
        current_process and 
        current_process.poll() is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete script while it is running"
        )
    
    try:
        script_path.unlink()
        return MacroResponse(
            success=True,
            message=f"Script {script_name} deleted successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete script: {str(e)}"
        )

@app.get("/image/{script_name}")
async def get_script_image(script_name: str):
    """Get background image for a script"""
    safe_script_name = "".join(c for c in script_name if c.isalnum() or c in "._-")
    
    for extension in SUPPORTED_IMAGE_EXTENSIONS:
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

# === MOUSE ROUTES ===

@app.post("/mouse/click", response_model=MouseResponse)
async def mouse_click(request: MouseClickRequest):
    """Click at specific screen coordinates"""
    try:
        # Validate coordinates (assuming 2560x1600 screen)
        if not (0 <= request.x <= 2560 and 0 <= request.y <= 1600):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Coordinates ({request.x}, {request.y}) out of screen bounds"
            )
        
        if request.button != "left":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only left mouse button currently supported"
            )
        
        # Execute mouse click using mouse_control.py
        cmd = ["python3", "mouse_control.py", "click", str(request.x), str(request.y)]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
        
        if process.returncode == 0:
            click_type = "double-clicked" if request.double else "clicked"
            return MouseResponse(
                success=True,
                message=f"Successfully {click_type} at ({request.x}, {request.y})",
                coordinates={"x": request.x, "y": request.y}
            )
        else:
            error_msg = stderr.decode() if stderr else stdout.decode()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Mouse click failed: {error_msg}"
            )
            
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Mouse click command timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mouse click error: {str(e)}"
        )

@app.post("/mouse/move", response_model=MouseResponse)
async def mouse_move(request: MouseMoveRequest):
    """Move mouse to specific screen coordinates"""
    try:
        if not (0 <= request.x <= 2560 and 0 <= request.y <= 1600):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Coordinates ({request.x}, {request.y}) out of screen bounds"
            )
        
        cmd = ["python3", "mouse_control.py", "move", str(request.x), str(request.y)]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
        
        if process.returncode == 0:
            return MouseResponse(
                success=True,
                message=f"Successfully moved to ({request.x}, {request.y})",
                coordinates={"x": request.x, "y": request.y}
            )
        else:
            error_msg = stderr.decode() if stderr else stdout.decode()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Mouse move failed: {error_msg}"
            )
            
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Mouse move command timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mouse move error: {str(e)}"
        )

@app.post("/mouse/center", response_model=MouseResponse)
async def mouse_center():
    """Move mouse to screen center"""
    try:
        cmd = ["python3", "mouse_control.py", "center"]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
        
        if process.returncode == 0:
            return MouseResponse(
                success=True,
                message="Successfully moved to screen center",
                coordinates={"x": 1280, "y": 800}
            )
        else:
            error_msg = stderr.decode() if stderr else stdout.decode()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Mouse center failed: {error_msg}"
            )
            
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Mouse center command timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mouse center error: {str(e)}"
        )

@app.get("/mouse/status", response_model=MouseResponse)
async def mouse_status():
    """Get mouse control status"""
    mouse_script_exists = (Path.cwd() / "mouse_control.py").exists()
    hid_device_exists = Path("/dev/hidg1").exists()
    
    if not mouse_script_exists:
        return MouseResponse(
            success=False,
            message="Mouse control script not found"
        )
    
    if not hid_device_exists:
        return MouseResponse(
            success=False,
            message="Mouse HID device (/dev/hidg1) not available"
        )
    
    return MouseResponse(
        success=True,
        message="Mouse control ready",
        coordinates={
            "screen_resolution": "2560x1600",
            "hid_device": "/dev/hidg1",
            "script_available": True
        }
    )

# === NEW KEY PRESS ENDPOINT ===

@app.post("/key/press", response_model=KeyResponse)
async def press_key(request: KeyPressRequest):
    """Press a single key using HID emulator"""
    try:
        # Normalize the key input
        input_key = request.key.lower()
        
        # Validate key against whitelist
        if input_key not in VALID_KEYS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid key '{request.key}'. Must be one of: {', '.join(sorted(VALID_KEYS))}"
            )
        
        # Validate hold duration (reasonable bounds)
        if not (10 <= request.hold_ms <= 5000):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="hold_ms must be between 10 and 5000 milliseconds"
            )
        
        # Create temporary AHK content for single key press
        ahk_content = f"""#NoEnv
SetWorkingDir %A_ScriptDir%
CoordMode, Mouse, Window
SendMode Input
#SingleInstance Force
SetTitleMatchMode 2
#WinActivateForce
SetControlDelay 1
SetWinDelay 0
SetKeyDelay -1
SetMouseDelay -1
SetBatchLines -1

Send, {{{input_key} Down}}
Sleep, {request.hold_ms}
Send, {{{input_key} Up}}
Sleep, 100
"""
        
        # Write to temporary file
        temp_file = Path("/tmp/temp_key_press.ahk")
        with open(temp_file, 'w') as f:
            f.write(ahk_content)
        
        print(f"🔑 Pressing key '{request.key}' for {request.hold_ms}ms")
        
        # Execute using existing HID emulator
        cmd = ["python3", "ahk_to_hid_v2.py", str(temp_file)]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
        
        # Clean up temp file
        temp_file.unlink(missing_ok=True)
        
        if process.returncode == 0:
            return KeyResponse(
                success=True,
                message=f"Successfully pressed key '{request.key}' for {request.hold_ms}ms",
                key=request.key
            )
        else:
            error_msg = stderr.decode() if stderr else stdout.decode()
            print(f"❌ Key press failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Key press failed: {error_msg}"
            )
            
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Key press command timed out"
        )
    except Exception as e:
        print(f"❌ Key press exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Key press error: {str(e)}"
        )

# === NEW ACTION SYSTEM ENDPOINTS ===

@app.get("/actions", response_model=ActionsResponse)
async def list_actions():
    """List available predefined actions"""
    try:
        actions = []
        
        for action_file in ACTIONS_DIR.glob("*.json"):
            try:
                with open(action_file, 'r') as f:
                    action_data = json.load(f)
                
                actions.append(ActionInfo(
                    name=action_data.get('name', action_file.stem),
                    description=action_data.get('description', 'No description'),
                    step_count=len(action_data.get('steps', []))
                ))
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Invalid action file {action_file}: {e}")
                continue
        
        return ActionsResponse(success=True, actions=actions)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list actions: {str(e)}"
        )

@app.post("/action/{action_name}", response_model=ActionResponse)
async def execute_action(action_name: str):
    """Execute a predefined action sequence"""
    try:
        action_file = ACTIONS_DIR / f"{action_name}.json"
        
        if not action_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action '{action_name}' not found"
            )
        
        # Load action definition
        with open(action_file, 'r') as f:
            action_data = json.load(f)
        
        steps = action_data.get('steps', [])
        if not steps:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Action '{action_name}' has no steps defined"
            )
        
        # Execute each step in sequence
        steps_executed = 0
        for step in steps:
            try:
                await _execute_action_step(step)
                steps_executed += 1
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed at step {steps_executed + 1}: {str(e)}"
                )
        
        return ActionResponse(
            success=True,
            message=f"Successfully executed action '{action_name}' ({steps_executed} steps)",
            action_name=action_name,
            steps_executed=steps_executed
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON in action file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action execution error: {str(e)}"
        )

async def _execute_action_step(step: Dict[str, Any]):
    """Execute a single action step"""
    step_type = step.get('type')
    
    print(f"🔄 Executing step: {step}")
    
    if step_type == 'key':
        # Key press step
        key = step.get('key')
        hold_ms = step.get('hold_ms', 100)
        
        # Normalize the key input
        input_key = key.lower()
        
        if not key or input_key not in VALID_KEYS:
            raise ValueError(f"Invalid key in step: '{key}'. Must be one of: {', '.join(sorted(VALID_KEYS))}")
        
        # Use the same logic as press_key endpoint with full AHK header
        ahk_content = f"""#NoEnv
SetWorkingDir %A_ScriptDir%
CoordMode, Mouse, Window
SendMode Input
#SingleInstance Force
SetTitleMatchMode 2
#WinActivateForce
SetControlDelay 1
SetWinDelay 0
SetKeyDelay -1
SetMouseDelay -1
SetBatchLines -1

Send, {{{input_key} Down}}
Sleep, {hold_ms}
Send, {{{input_key} Up}}
Sleep, 100
"""
        
        temp_file = Path("/tmp/temp_action_key.ahk")
        with open(temp_file, 'w') as f:
            f.write(ahk_content)
        
        print(f"🔑 Action: Pressing key '{key}' for {hold_ms}ms")
        
        cmd = ["python3", "ahk_to_hid_v2.py", str(temp_file)]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
        temp_file.unlink(missing_ok=True)
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else stdout.decode()
            print(f"❌ Key press failed: {error_msg}")
            raise ValueError(f"Key press failed for key '{key}': {error_msg}")
        else:
            print(f"✅ Key press successful for '{key}'")
    
    elif step_type == 'click':
        # Mouse click step
        x = step.get('x')
        y = step.get('y')
        double = step.get('double', False)
        
        if x is None or y is None:
            raise ValueError("Click step missing x or y coordinates")
        
        if not (0 <= x <= 2560 and 0 <= y <= 1600):
            raise ValueError(f"Click coordinates ({x}, {y}) out of bounds")
        
        print(f"🖱️  Action: Clicking at ({x}, {y}), double={double}")
        
        cmd = ["python3", "mouse_control.py", "click", str(x), str(y)]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else stdout.decode()
            print(f"❌ Mouse click failed: {error_msg}")
            raise ValueError(f"Mouse click failed at ({x}, {y}): {error_msg}")
        else:
            print(f"✅ Mouse click successful at ({x}, {y})")
    
    elif step_type == 'wait':
        # Wait/sleep step
        ms = step.get('ms', 1000)
        
        if not (10 <= ms <= 30000):  # Max 30 second wait
            raise ValueError(f"Wait duration {ms}ms out of reasonable bounds (10-30000)")
        
        print(f"⏱️  Action: Waiting {ms}ms")
        await asyncio.sleep(ms / 1000.0)
        print(f"✅ Wait completed")
    
    else:
        raise ValueError(f"Unknown step type: '{step_type}'")

# === UTILITY FUNCTIONS ===

async def stop_current_macro():
    """Helper function to stop current macro process"""
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

def _get_media_type(extension: str) -> str:
    """Get the appropriate media type for image extension"""
    extension = extension.lower()
    media_types = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
        '.gif': 'image/gif', '.webp': 'image/webp', '.bmp': 'image/bmp'
    }
    return media_types.get(extension, 'image/jpeg')

def generate_self_signed_cert():
    """Generate self-signed certificate for HTTPS"""
    cert_file = CERT_DIR / "cert.pem"
    key_file = CERT_DIR / "key.pem"
    
    if cert_file.exists() and key_file.exists():
        print(f"📜 Using existing SSL certificates")
        return str(cert_file), str(key_file)
    
    print("🔐 Generating self-signed SSL certificate...")
    
    try:
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:4096", 
            "-keyout", str(key_file), "-out", str(cert_file),
            "-days", "365", "-nodes", "-subj", 
            "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        ], check=True, capture_output=True)
        
        print(f"✅ SSL certificate generated: {cert_file}")
        return str(cert_file), str(key_file)
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ OpenSSL not found or failed")
        return None, None

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check server state"""
    return {
        "working_directory": str(Path.cwd()),
        "script_directory": str(SCRIPT_DIR),
        "actions_directory": str(ACTIONS_DIR),
        "images_directory": str(IMAGES_DIR),
        "directories_exist": {
            "scripts": SCRIPT_DIR.exists(),
            "actions": ACTIONS_DIR.exists(),
            "images": IMAGES_DIR.exists(),
            "certs": CERT_DIR.exists()
        },
        "files_exist": {
            "ahk_to_hid_v2.py": (Path.cwd() / "ahk_to_hid_v2.py").exists(),
            "mouse_control.py": (Path.cwd() / "mouse_control.py").exists()
        },
        "hid_devices": {
            "keyboard": Path("/dev/hidg0").exists(),
            "mouse": Path("/dev/hidg1").exists()
        },
        "current_macro": {
            "pid": current_process.pid if current_process else None,
            "script": current_script,
            "paused": macro_paused
        },
        "file_counts": {
            "scripts": len(list(SCRIPT_DIR.glob("*.ahk"))) if SCRIPT_DIR.exists() else 0,
            "actions": len(list(ACTIONS_DIR.glob("*.json"))) if ACTIONS_DIR.exists() else 0,
            "images": len(list(IMAGES_DIR.glob("*"))) if IMAGES_DIR.exists() else 0
        },
        "valid_keys": sorted(VALID_KEYS)
    }

# === STARTUP/SHUTDOWN ===

@app.on_event("startup")
async def startup_event():
    """Initialize server on startup"""
    print("🚀 Enhanced HID Server v2.6.0 starting up...")
    print(f"📁 Script directory: {SCRIPT_DIR}")
    print(f"⚡ Actions directory: {ACTIONS_DIR}")
    print(f"🖼️  Images directory: {IMAGES_DIR}")
    print(f"🔒 Certificate directory: {CERT_DIR}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on server shutdown"""
    global current_process
    if current_process and current_process.poll() is None:
        print("🛑 Stopping running macro...")
        await stop_current_macro()
    print("👋 Enhanced server shutdown complete")

def main():
    """Main function to run server"""
    print("Starting Enhanced HID Keyboard + Mouse Control Server v2.6.0...")
    print("New features: Single key press endpoint + File-based action system")
    
    cert_file, key_file = generate_self_signed_cert()
    
    if cert_file and key_file:
        print(f"🔐 Starting HTTPS server on port 8444...")
        print(f"📚 API Documentation: https://localhost:8444/docs")
        print(f"🔑 New key endpoint: /key/press")
        print(f"⚡ New action endpoints: /actions, /action/{'{action_name}'}")
        
        uvicorn.run(
            "enhanced_server:app",
            host="0.0.0.0",
            port=8444,
            ssl_keyfile=key_file,
            ssl_certfile=cert_file,
            reload=False,
            log_level="info"
        )
    else:
        print(f"🌐 Starting HTTP server on port 8334...")
        print(f"📚 API Documentation: http://localhost:8334/docs")
        print(f"🔑 New key endpoint: /key/press")
        print(f"⚡ New action endpoints: /actions, /action/{'{action_name}'}")
        
        uvicorn.run(
            "enhanced_server:app",
            host="0.0.0.0",
            port=8334,
            reload=True,
            log_level="info"
        )

if __name__ == "__main__":
    main()
