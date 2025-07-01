# === app/services/script_service.py ===
"""
Script management service
"""

import datetime
from pathlib import Path
from typing import List
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ScriptManagementError
from app.models.script import ScriptInfo, ClassMapCombination
from app.utils.script_parser import parse_script_metadata, get_class_display_name, get_map_display_name

class ScriptService:
    """Handles script listing, uploading, deletion, and image management"""
    
    async def list_farming_scripts(self) -> List[ScriptInfo]:
        """List only farming scripts (excludes action scripts and old directory)"""
        scripts = []
        
        for filepath in settings.SCRIPT_DIR.glob("*.ahk"):
            # Skip if it's in old/ subdirectory or any nested directory
            if "old" in str(filepath) or filepath.parent != settings.SCRIPT_DIR:
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
        return scripts
    
    async def get_class_map_combinations(self) -> List[ClassMapCombination]:
        """Get all available class+map combinations"""
        combinations = []
        
        for script_file in settings.SCRIPT_DIR.glob("*.ahk"):
            # Skip old directory and nested files
            if "old" in str(script_file) or script_file.parent != settings.SCRIPT_DIR:
                continue
                
            class_code, map_code = parse_script_metadata(script_file.name)
            if class_code and map_code:
                # Check if image exists
                image_exists = False
                script_base = script_file.stem  # filename without .ahk
                for ext in settings.SUPPORTED_IMAGE_EXTENSIONS:
                    if (settings.IMAGES_DIR / f"{script_base}{ext}").exists():
                        image_exists = True
                        break
                
                combinations.append(ClassMapCombination(
                    id=f"{class_code}_{map_code}",
                    class_name=get_class_display_name(class_code),
                    map_name=get_map_display_name(map_code),
                    script_name=script_file.name,
                    has_image=image_exists
                ))
        
        return combinations
    
    async def upload_script(self, file: UploadFile) -> dict:
        """Upload an AHK script file"""
        if not file.filename:
            raise ScriptManagementError("No file selected")
        
        if not file.filename.endswith('.ahk'):
            raise ScriptManagementError("Invalid file type. Only .ahk files allowed")
        
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise ScriptManagementError(
                f"File too large. Maximum size is {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        try:
            # Secure the filename
            safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-")
            if not safe_filename.endswith('.ahk'):
                safe_filename += '.ahk'
                
            filepath = settings.SCRIPT_DIR / safe_filename
            
            with open(filepath, 'wb') as f:
                f.write(content)
            
            return {
                "success": True,
                "message": "Script uploaded successfully",
                "filename": safe_filename,
                "path": str(filepath)
            }
            
        except Exception as e:
            raise ScriptManagementError(f"Failed to save file: {str(e)}")
    
    async def delete_script(self, script_name: str) -> dict:
        """Delete a script file"""
        script_path = settings.SCRIPT_DIR / script_name
        
        if not script_path.exists():
            raise ScriptManagementError("Script not found")
        
        # TODO: Check if script is currently running (need macro service integration)
        
        try:
            script_path.unlink()
            return {
                "success": True,
                "message": f"Script {script_name} deleted successfully"
            }
        except Exception as e:
            raise ScriptManagementError(f"Failed to delete script: {str(e)}")
    
    async def get_script_image(self, script_name: str) -> Path:
        """Get image path for a script"""
        # Remove .ahk extension if present
        if script_name.endswith('.ahk'):
            script_name = script_name[:-4]
        
        safe_script_name = "".join(c for c in script_name if c.isalnum() or c in "._-")
        
        for extension in settings.SUPPORTED_IMAGE_EXTENSIONS:
            image_path = settings.IMAGES_DIR / f"{safe_script_name}{extension}"
            
            if image_path.exists() and image_path.is_file():
                file_size = image_path.stat().st_size
                if file_size > 50 * 1024 * 1024:  # 50MB limit
                    raise ScriptManagementError("Image file too large")
                
                return image_path
        
        raise ScriptManagementError(f"No image found for script '{script_name}'")
    
    def get_media_type(self, extension: str) -> str:
        """Get media type for image extension"""
        extension = extension.lower()
        media_types = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
            '.gif': 'image/gif', '.webp': 'image/webp', '.bmp': 'image/bmp'
        }
        return media_types.get(extension, 'image/jpeg')
