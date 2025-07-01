# === app/api/v1/macros.py ===
"""
Macro execution endpoints
"""

from fastapi import APIRouter, HTTPException, status
from app.models.macro import MacroRequest, MacroResponse, StatusResponse
from app.services.macro_service import MacroService
from app.core.exceptions import MacroExecutionError

router = APIRouter()

# Global macro service instance to maintain state
_macro_service = MacroService()

def get_macro_service() -> MacroService:
    """Get the global macro service instance"""
    return _macro_service

@router.post("/start_macro", response_model=MacroResponse)
async def start_macro(request: MacroRequest):
    """Start macro execution"""
    try:
        macro_service = get_macro_service()
        result = await macro_service.start_macro(request.script_name)
        return MacroResponse(**result)
    except MacroExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/pause_macro", response_model=MacroResponse)
async def pause_macro():
    """Pause current macro execution"""
    try:
        macro_service = get_macro_service()
        result = await macro_service.pause_macro()
        return MacroResponse(**result)
    except MacroExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/resume_macro", response_model=MacroResponse)
async def resume_macro():
    """Resume paused macro execution"""
    try:
        macro_service = get_macro_service()
        result = await macro_service.resume_macro()
        return MacroResponse(**result)
    except MacroExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/stop_macro", response_model=MacroResponse)
async def stop_macro():
    """Stop current macro execution"""
    try:
        macro_service = get_macro_service()
        result = await macro_service.stop_macro()
        return MacroResponse(**result)
    except MacroExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current macro execution status"""
    macro_service = get_macro_service()
    result = macro_service.get_status()
    return StatusResponse(**result)
