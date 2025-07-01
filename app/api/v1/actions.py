"""
Context-aware action execution endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from app.models.macro import MacroResponse
from app.services.action_service import ActionService
from app.services.session_service import SessionService
from app.core.exceptions import ActionExecutionError

router = APIRouter()

def get_action_service() -> ActionService:
    return ActionService()

def get_session_service() -> SessionService:
    # Import the same global instance from session endpoints
    from app.api.v1.session import get_session_service
    return get_session_service()

# === CONTEXT-AWARE CLASS/MAP ACTIONS ===

@router.post("/action/class/init", response_model=MacroResponse)
async def init_class_for_current_combination(
    action_service: ActionService = Depends(get_action_service),
    session_service: SessionService = Depends(get_session_service)
):
    """Initialize class for currently selected combination"""
    try:
        session_state = session_service.get_session_state()
        if not session_state.selected_combination_id:
            raise ActionExecutionError("No class+map combination selected")
        
        result = await action_service.init_class_for_combination(
            session_state.selected_combination_id
        )
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/action/map/navigate", response_model=MacroResponse)
async def navigate_to_current_map(
    action_service: ActionService = Depends(get_action_service),
    session_service: SessionService = Depends(get_session_service)
):
    """Navigate to map for currently selected combination"""
    try:
        session_state = session_service.get_session_state()
        if not session_state.selected_combination_id:
            raise ActionExecutionError("No class+map combination selected")
        
        result = await action_service.nav_map_for_combination(
            session_state.selected_combination_id
        )
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/action/map/position", response_model=MacroResponse)
async def position_for_current_map(
    action_service: ActionService = Depends(get_action_service),
    session_service: SessionService = Depends(get_session_service)
):
    """Position for farming in currently selected map"""
    try:
        session_state = session_service.get_session_state()
        if not session_state.selected_combination_id:
            raise ActionExecutionError("No class+map combination selected")
        
        result = await action_service.pos_map_for_combination(
            session_state.selected_combination_id
        )
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# === CONTEXT-AGNOSTIC ACTIONS (no changes needed) ===

@router.post("/action/movement/double_jump", response_model=MacroResponse)
async def action_double_jump(
    action_service: ActionService = Depends(get_action_service)
):
    """Execute double jump action"""
    try:
        result = await action_service.double_jump()
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/action/movement/jump_down", response_model=MacroResponse)
async def action_jump_down(
    action_service: ActionService = Depends(get_action_service)
):
    """Execute jump down action"""
    try:
        result = await action_service.jump_down()
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/action/movement/rope_up", response_model=MacroResponse)
async def action_rope_up(
    action_service: ActionService = Depends(get_action_service)
):
    """Execute rope/platform ascent"""
    try:
        result = await action_service.rope_up()
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/action/movement/interact", response_model=MacroResponse)
async def action_interact(
    action_service: ActionService = Depends(get_action_service)
):
    """Execute interact (Y key)"""
    try:
        result = await action_service.interact()
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/action/movement/{direction}", response_model=MacroResponse)
async def action_movement(
    direction: str,
    step_size: str = "medium",
    action_service: ActionService = Depends(get_action_service)
):
    """Execute directional movement with step size"""
    try:
        result = await action_service.movement(direction, step_size)
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Utility actions
@router.post("/action/utility/go_to_town", response_model=MacroResponse)
async def action_go_to_town(
    action_service: ActionService = Depends(get_action_service)
):
    """Go to town sequence"""
    try:
        result = await action_service.go_to_town()
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/action/utility/go_to_hunting", response_model=MacroResponse)
async def action_go_to_hunting(
    action_service: ActionService = Depends(get_action_service)
):
    """Go to hunting ground sequence"""
    try:
        result = await action_service.go_to_hunting()
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/action/utility/use_consumables", response_model=MacroResponse)
async def action_use_consumables(
    action_service: ActionService = Depends(get_action_service)
):
    """Use all consumable items"""
    try:
        result = await action_service.use_consumables()
        return MacroResponse(**result)
    except ActionExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
