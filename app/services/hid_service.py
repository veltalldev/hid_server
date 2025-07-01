# === app/services/hid_service.py ===
"""
Low-level HID operations service
"""

import asyncio
import subprocess
from pathlib import Path
from app.core.config import settings
from app.core.exceptions import ActionExecutionError

class HIDService:
    """Handles low-level HID keyboard and mouse operations"""
    
    async def send_key(self, key: str, hold_ms: int = 100):
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
            
            await asyncio.wait_for(process.communicate(), timeout=settings.ACTION_TIMEOUT)
            temp_file.unlink(missing_ok=True)
            
        except Exception as e:
            raise ActionExecutionError(f"Key press failed: {str(e)}")
    
    async def send_key_combo(self, key1: str, key2: str, hold_ms: int = 50):
        """Send a key combination (key1 held while key2 is pressed)"""
        try:
            ahk_content = f"""
Send, {{{key1} Down}}
Sleep, 10
Send, {{{key2} Down}}
Sleep, {hold_ms}
Send, {{{key2} Up}}
Sleep, 10
Send, {{{key1} Up}}
Sleep, 100
"""
            temp_file = Path("/tmp/temp_combo.ahk")
            temp_file.write_text(ahk_content)
            
            process = await asyncio.create_subprocess_exec(
                'python3', 'ahk_to_hid_v2.py', str(temp_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await asyncio.wait_for(process.communicate(), timeout=settings.ACTION_TIMEOUT)
            temp_file.unlink(missing_ok=True)
            
        except Exception as e:
            raise ActionExecutionError(f"Key combination failed: {str(e)}")


    async def click_coordinates(self, x: int, y: int):
        """Click at specific coordinates via mouse control"""
        try:
            process = await asyncio.create_subprocess_exec(
                'python3', 'mouse_control.py', 'click', str(x), str(y),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=settings.ACTION_TIMEOUT
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else stdout.decode()
                raise Exception(f"Mouse click failed: {error_msg}")
                
        except Exception as e:
            raise ActionExecutionError(f"Click failed: {str(e)}")
