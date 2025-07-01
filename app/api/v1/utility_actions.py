"""
Extended utility action endpoints
"""

from fastapi import APIRouter, HTTPException, status
from app.models.macro import MacroResponse
from app.services.action_service import ActionService
from app.core.exceptions import ActionExecutionError

router = APIRouter()

def get_action_service() -> ActionService:
    return ActionService()

@router.post("/action/utility/change_channel", response_model=MacroResponse)
async def change_channel():
    """Change game channel sequence"""
    try:
        action_service = get_action_service()
        result = await action_service.change_channel()
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/action/utility/quick_travel_setup", response_model=MacroResponse)
async def quick_travel_setup():
    """Open quick travel menu for manual selection"""
    try:
        action_service = get_action_service()
        result = await action_service.quick_travel_setup()
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/action/utility/inventory_management", response_model=MacroResponse)
async def inventory_management():
    """Extended inventory management - organize and use items"""
    try:
        action_service = get_action_service()
        result = await action_service.inventory_management()
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
