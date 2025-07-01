# === app/api/v1/scripts.py ===
"""
Script management endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status
from fastapi.responses import FileResponse
from app.models.script import ScriptsResponse, UploadResponse
from app.services.script_service import ScriptService
from app.core.exceptions import ScriptManagementError

router = APIRouter()

def get_script_service() -> ScriptService:
    return ScriptService()

@router.get("/scripts", response_model=ScriptsResponse)
async def list_scripts(
    script_service: ScriptService = Depends(get_script_service)
):
    """List available farming scripts (excludes action scripts)"""
    try:
        scripts = await script_service.list_farming_scripts()
        return ScriptsResponse(success=True, scripts=scripts)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scripts: {str(e)}"
        )

@router.post("/upload_script", response_model=UploadResponse)
async def upload_script(
    file: UploadFile = File(...),
    script_service: ScriptService = Depends(get_script_service)
):
    """Upload an AHK script file"""
    try:
        result = await script_service.upload_script(file)
        return UploadResponse(**result)
    except ScriptManagementError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/delete_script/{script_name}")
async def delete_script(
    script_name: str,
    script_service: ScriptService = Depends(get_script_service)
):
    """Delete a script file"""
    try:
        result = await script_service.delete_script(script_name)
        return result
    except ScriptManagementError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/image/{script_name}")
async def get_script_image(
    script_name: str,
    script_service: ScriptService = Depends(get_script_service)
):
    """Get background image for a script"""
    try:
        image_path = await script_service.get_script_image(script_name)
        return FileResponse(
            path=str(image_path),
            media_type=script_service.get_media_type(image_path.suffix),
            filename=image_path.name
        )
    except ScriptManagementError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
