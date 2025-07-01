# === app/services/macro_service.py ===
"""
Macro execution service
"""

import subprocess
import signal
import asyncio
from typing import Optional
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import MacroExecutionError

class MacroService:
    """Handles macro execution, pausing, resuming, and stopping"""
    
    def __init__(self):
        self.current_process: Optional[subprocess.Popen] = None
        self.current_script: Optional[str] = None
        self.is_paused: bool = False
    
    async def start_macro(self, script_name: str) -> dict:
        """Start macro execution"""
        script_path = settings.SCRIPT_DIR / script_name
        
        if not script_path.exists():
            raise MacroExecutionError(f"Script file not found: {script_name}")
        
        # Stop current macro if running
        if self.is_running():
            await self.stop_macro()
        
        try:
            self.current_process = subprocess.Popen([
                'python3', 'ahk_to_hid_v2.py', str(script_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.current_script = script_name
            self.is_paused = False
            
            return {
                "success": True,
                "message": "Macro started successfully",
                "script": script_name,
                "pid": self.current_process.pid
            }
            
        except Exception as e:
            raise MacroExecutionError(f"Failed to start macro: {str(e)}")
    
    async def pause_macro(self) -> dict:
        """Pause current macro"""
        if not self.is_running():
            raise MacroExecutionError("No macro currently running")
        
        if self.is_paused:
            return {"success": True, "message": "Macro is already paused"}
        
        try:
            self.current_process.send_signal(signal.SIGUSR1)
            self.is_paused = True
            return {"success": True, "message": "Macro paused successfully"}
        except Exception as e:
            raise MacroExecutionError(f"Failed to pause macro: {str(e)}")
    
    async def resume_macro(self) -> dict:
        """Resume paused macro"""
        if not self.is_running():
            raise MacroExecutionError("No macro currently running")
        
        if not self.is_paused:
            return {"success": True, "message": "Macro is not paused"}
        
        try:
            self.current_process.send_signal(signal.SIGUSR2)
            self.is_paused = False
            return {"success": True, "message": "Macro resumed successfully"}
        except Exception as e:
            raise MacroExecutionError(f"Failed to resume macro: {str(e)}")
    
    async def stop_macro(self) -> dict:
        """Stop current macro"""
        if not self.is_running():
            return {"success": True, "message": "No macro currently running"}
        
        try:
            await self._stop_process()
            return {"success": True, "message": "Macro stopped successfully"}
        except Exception as e:
            raise MacroExecutionError(f"Failed to stop macro: {str(e)}")
    
    def get_status(self) -> dict:
        """Get current macro status"""
        if self.current_process:
            if self.current_process.poll() is None:
                status_val = 'paused' if self.is_paused else 'running'
                pid = self.current_process.pid
            else:
                # Process finished
                status_val = 'stopped'
                pid = None
                self._reset_state()
        else:
            status_val = 'idle'
            pid = None
        
        return {
            "status": status_val,
            "current_script": self.current_script,
            "pid": pid
        }
    
    def is_running(self) -> bool:
        """Check if macro is currently running"""
        return (self.current_process is not None and 
                self.current_process.poll() is None)
    
    async def _stop_process(self):
        """Internal method to stop the process"""
        if self.current_process:
            try:
                # Graceful shutdown
                self.current_process.send_signal(signal.SIGTERM)
                
                # Wait for graceful shutdown
                for _ in range(50):  # 5 second timeout
                    if self.current_process.poll() is not None:
                        break
                    await asyncio.sleep(0.1)
                else:
                    # Force kill
                    self.current_process.kill()
                    self.current_process.wait()
                    
            except ProcessLookupError:
                pass  # Process already died
            finally:
                self._reset_state()
    
    def _reset_state(self):
        """Reset internal state"""
        self.current_process = None
        self.current_script = None
        self.is_paused = False
