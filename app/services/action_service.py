"""
Action execution service - Final corrected version with confirmed sequences
"""

import asyncio
from app.services.hid_service import HIDService
from app.core.exceptions import ActionExecutionError

class ActionService:
    """Handles execution of movement, utility, class, and map actions"""
    
    def __init__(self):
        self.hid_service = HIDService()
        
    # === CONTEXT-AWARE CLASS ACTIONS ===
    
    async def init_class_for_combination(self, combination_id: str) -> dict:
        """Initialize class based on combination ID"""
        if combination_id.startswith('drk_'):
            return await self.init_dark_knight()
        elif combination_id.startswith('nw_'):
            return await self.init_night_walker()
        else:
            raise ActionExecutionError(f"Unknown class in combination: {combination_id}")
    
    async def nav_map_for_combination(self, combination_id: str) -> dict:
        """Navigate to map based on combination ID"""
        if 'bottom_deck_passage_3' in combination_id:
            return await self.nav_bottom_deck_passage_3()
        elif 'laboratory_behind_closed_door_3' in combination_id:
            return await self.nav_laboratory_behind_closed_door_3()
        else:
            raise ActionExecutionError(f"Unknown map in combination: {combination_id}")
    
    async def pos_map_for_combination(self, combination_id: str) -> dict:
        """Position for farming based on combination ID"""
        if 'bottom_deck_passage_3' in combination_id:
            return await self.pos_bottom_deck_passage_3()
        elif 'laboratory_behind_closed_door_3' in combination_id:
            return await self.pos_laboratory_behind_closed_door_3()
        else:
            raise ActionExecutionError(f"Unknown map positioning for: {combination_id}")
    
    # === ENHANCED MOVEMENT WITH STEP SIZE ===
    
    async def movement_with_step_size(self, direction: str, step_size_multiplier: float = 1.0) -> dict:
        """Execute directional movement with step size multiplier"""
        valid_directions = ["up", "down", "left", "right"]
        if direction not in valid_directions:
            raise ActionExecutionError(
                f"Invalid direction. Must be one of: {valid_directions}"
            )
        
        # Base durations from your research
        base_durations = {
            "up": 300,
            "down": 300, 
            "left": 1200,
            "right": 1200
        }
        
        # Apply step size multiplier (0.1 to 3.0 from slider)
        duration = int(base_durations[direction] * step_size_multiplier)
        
        try:
            await self.hid_service.send_key(direction.title(), duration)
            await asyncio.sleep(0.1)  # Buffer
            
            step_description = self._get_step_description(step_size_multiplier)
            return {
                "success": True,
                "message": f"{step_description} {direction} movement executed ({duration}ms)"
            }
        except Exception as e:
            raise ActionExecutionError(f"Movement failed: {str(e)}")
    
    def _get_step_description(self, multiplier: float) -> str:
        """Get human-readable step size description"""
        if multiplier < 0.5:
            return "Tiny"
        elif multiplier < 1.0:
            return "Small" 
        elif multiplier == 1.0:
            return "Medium"
        elif multiplier < 2.0:
            return "Large"
        else:
            return "Huge"
    
    # === MOVEMENT ACTIONS (Based on research documentation) ===
    
    async def double_jump(self) -> dict:
        """Execute double jump action - Based on double_jump.ahk"""
        try:
            # From double_jump.ahk: Space Down -> 50ms -> Space Up -> 100ms -> Space Down -> 50ms -> Space Up -> 300ms
            await self.hid_service.send_key("Space", 50)
            await asyncio.sleep(0.1)
            await self.hid_service.send_key("Space", 50)
            await asyncio.sleep(0.3)
            
            return {"success": True, "message": "Double jump executed"}
        except Exception as e:
            raise ActionExecutionError(f"Double jump failed: {str(e)}")
    
    async def jump_down(self) -> dict:
        """Execute jump down action - CORRECTED with key combination"""
        try:
            # CORRECTED: Down held while Space is pressed (Down Down -> Space Down -> Space Up -> Down Up)
            await self.hid_service.send_key_combo("Down", "Space", 50)
            await asyncio.sleep(1.0)  # Landing buffer
            
            return {"success": True, "message": "Jump down executed"}
        except Exception as e:
            raise ActionExecutionError(f"Jump down failed: {str(e)}")
    
    async def rope_up(self) -> dict:
        """Execute rope/platform ascent - Based on end_up.ahk"""
        try:
            # From end_up.ahk: End Down -> 200ms -> End Up -> 2000ms
            await self.hid_service.send_key("End", 200)
            await asyncio.sleep(2.0)
            
            return {"success": True, "message": "Rope up executed"}
        except Exception as e:
            raise ActionExecutionError(f"Rope up failed: {str(e)}")
    
    async def interact(self) -> dict:
        """Execute interact (Y key) - Based on press_y.ahk"""
        try:
            # From press_y.ahk: y Down -> 100ms -> y Up -> 100ms
            await self.hid_service.send_key("y", 100)
            await asyncio.sleep(0.1)
            
            return {"success": True, "message": "Interact executed"}
        except Exception as e:
            raise ActionExecutionError(f"Interact failed: {str(e)}")
    
    async def movement(self, direction: str, step_size: str = "medium") -> dict:
        """Execute directional movement - CORRECTED step durations"""
        valid_directions = ["up", "down", "left", "right"]
        if direction not in valid_directions:
            raise ActionExecutionError(
                f"Invalid direction. Must be one of: {valid_directions}"
            )
        
        # CORRECTED step durations: xs=100, s=300, m=1200, l=2000
        step_durations = {
            "xs": 100,      # Extra small
            "small": 300,   # Small  
            "medium": 1200, # Medium
            "large": 2000   # Large
        }
        
        # Accept both 's' and 'small' format
        if step_size == "s":
            step_size = "small"
        elif step_size == "m":
            step_size = "medium"
        elif step_size == "l":
            step_size = "large"
        
        if step_size not in step_durations:
            raise ActionExecutionError(
                f"Invalid step size. Must be one of: {list(step_durations.keys())}"
            )
        
        try:
            hold_duration = step_durations[step_size]
            await self.hid_service.send_key(direction.title(), hold_duration)
            await asyncio.sleep(0.1)  # Buffer from research doc
            
            return {
                "success": True,
                "message": f"{step_size.title()} {direction} movement executed"
            }
        except Exception as e:
            raise ActionExecutionError(f"Movement failed: {str(e)}")
    
    # === UTILITY ACTIONS (Based on research documentation) ===
    
    async def go_to_town(self) -> dict:
        """Go to town sequence - From Enhanced Server Use Cases document"""
        try:
            # From research: send `=`, click 1150 642 (town button), wait 5000ms, send `Esc`
            await self.hid_service.send_key("=", 100)
            await asyncio.sleep(0.5)
            await self.hid_service.click_coordinates(1150, 642)  # Documented coordinates
            await asyncio.sleep(5.0)  # Documented loading time
            await self.hid_service.send_key("Escape", 100)
            
            return {"success": True, "message": "Go to town executed"}
        except Exception as e:
            raise ActionExecutionError(f"Go to town failed: {str(e)}")
    
    async def use_consumables(self) -> dict:
        """Use all consumable items - From Enhanced Server Use Cases document"""
        try:
            
            await self.hid_service.send_key("f7", 100)
            await asyncio.sleep(0.3)
            await self.hid_service.send_key("f8", 100)
            await asyncio.sleep(0.3)
            await self.hid_service.send_key("f9", 100)
            await asyncio.sleep(0.3)
            await self.hid_service.send_key("f10", 100)
            await asyncio.sleep(0.3)
            await self.hid_service.send_key("f11", 100)
            await asyncio.sleep(0.3)
            await self.hid_service.send_key("f12", 100)
            await asyncio.sleep(0.3)
            
            return {"success": True, "message": "Use consumables executed"}
        except Exception as e:
            raise ActionExecutionError(f"Use consumables failed: {str(e)}")
    
    # === CLASS INITIALIZATION ACTIONS ===
    
    async def init_dark_knight(self) -> dict:
        """Initialize Dark Knight class - CONFIRMED sequence"""
        try:
            # CONFIRMED: DRK init sequence is correct
            await self.hid_service.send_key("0", 100)
            await asyncio.sleep(1)
            await self.hid_service.send_key("g", 100)
            await asyncio.sleep(1)
            await self.hid_service.send_key("pgdn", 100)
            await asyncio.sleep(0.5)
            await self.hid_service.send_key("right", 100)
            await asyncio.sleep(0.5)
            
            return {"success": True, "message": "Dark Knight class initialized"}
        except Exception as e:
            raise ActionExecutionError(f"Dark Knight init failed: {str(e)}")
    
    async def init_night_walker(self) -> dict:
        """Initialize Night Walker class - CONFIRMED sequence"""
        try:
            # CONFIRMED: NW init is send 0, send 9
            await self.hid_service.send_key("0", 100)
            await asyncio.sleep(0.5)
            await self.hid_service.send_key("9", 100)
            await asyncio.sleep(0.5)
            await self.hid_service.send_key("g", 100)
            await asyncio.sleep(0.5)
            
            return {"success": True, "message": "Night Walker class initialized"}
        except Exception as e:
            raise ActionExecutionError(f"Night Walker init failed: {str(e)}")
    
    # === MAP NAVIGATION ACTIONS ===
    
    async def nav_bottom_deck_passage_3(self) -> dict:
        """Navigate to Bottom Deck Passage 3 - CONFIRMED sequence"""
        try:
            # CONFIRMED: BDP3 nav is correct, was original go_to_hunting map
            await self.hid_service.send_key("=", 100)
            await asyncio.sleep(0.2)
            await self.hid_service.send_key("=", 100)
            await asyncio.sleep(0.5)
            await self.hid_service.click_coordinates(725, 1075)  # Confirmed coordinates
            await asyncio.sleep(1.0)
            await self.hid_service.click_coordinates(1180, 986)  # Documented confirm
            await asyncio.sleep(5.0)  # Documented loading time
            await self.hid_service.send_key("Escape", 100)
            
            return {"success": True, "message": "Navigated to Bottom Deck Passage 3"}
        except Exception as e:
            raise ActionExecutionError(f"BDP3 navigation failed: {str(e)}")
    
    async def nav_laboratory_behind_closed_door_3(self) -> dict:
        """Navigate to Laboratory Behind Closed Door 3 - PLACEHOLDER"""
        try:
            # PLACEHOLDER: Lab nav coordinates to be filled in later
            return {"success": True, "message": "Lab navigation not implemented yet - coordinates needed"}
        except Exception as e:
            raise ActionExecutionError(f"LBLD3 navigation failed: {str(e)}")
    
    # === MAP POSITIONING ACTIONS ===
    
    async def pos_bottom_deck_passage_3(self) -> dict:
        """Position for farming in Bottom Deck Passage 3 - CONFIRMED sequence"""
        try:
            # CONFIRMED: pos bottom deck is left 1200
            await self.hid_service.send_key("left", 1200)
            await asyncio.sleep(0.5)
            
            return {"success": True, "message": "Positioned for BDP3 farming"}
        except Exception as e:
            raise ActionExecutionError(f"BDP3 positioning failed: {str(e)}")
    
    async def pos_laboratory_behind_closed_door_3(self) -> dict:
        """Position for farming in Laboratory Behind Closed Door 3 - PLACEHOLDER"""
        try:
            # PLACEHOLDER: Lab positioning to be defined
            return {"success": True, "message": "Lab positioning not implemented yet"}
        except Exception as e:
            raise ActionExecutionError(f"LBLD3 positioning failed: {str(e)}")
    
    # === EXTENDED UTILITY ACTIONS ===
    
    async def change_channel(self) -> dict:
        """Change game channel - CONFIRMED sequence"""
        try:
            # CONFIRMED: esc enter right enter wait
            await self.hid_service.send_key("Escape", 100)
            await asyncio.sleep(0.2)
            await self.hid_service.send_key("Enter", 100)
            await asyncio.sleep(0.2)
            await self.hid_service.send_key("Right", 100)
            await asyncio.sleep(0.2)
            await self.hid_service.send_key("Enter", 100)
            await asyncio.sleep(5.0)  # Wait for channel change
            
            return {"success": True, "message": "Channel changed successfully"}
        except Exception as e:
            raise ActionExecutionError(f"Channel change failed: {str(e)}")
    
    async def quick_travel_setup(self) -> dict:
        """Open quick travel menu for manual selection"""
        try:
            # Based on documented pattern - just open menu
            await self.hid_service.send_key("=", 100)
            await asyncio.sleep(0.5)
            
            # Leave menu open for manual selection
            return {"success": True, "message": "Quick travel menu opened - manual selection ready"}
        except Exception as e:
            raise ActionExecutionError(f"Quick travel setup failed: {str(e)}")
    
    async def inventory_management(self) -> dict:
        """Extended inventory management - Same as use_consumables"""
        try:
            # Same as use_consumables but with extended message
            await self.hid_service.send_key("i", 100)
            await asyncio.sleep(0.5)
            
            # Use documented item slot coordinates (2x3 grid)
            documented_slots = [
                (1538, 600),  # Slot 1 (documented)
                (1435, 600),  # Slot 2 (documented)
                (1360, 600),  # Slot 3 (documented)
                (1360, 525),  # Slot 4 (documented)
                (1435, 525),  # Slot 5 (documented)
                (1538, 525)   # Slot 6 (documented)
            ]
            
            for x, y in documented_slots:
                # Double-click each documented slot
                await self.hid_service.click_coordinates(x, y)
                await asyncio.sleep(0.1)
                await self.hid_service.click_coordinates(x, y)
                await asyncio.sleep(0.2)
            
            # Close inventory
            await self.hid_service.send_key("i", 100)
            
            return {"success": True, "message": "Extended inventory management completed"}
        except Exception as e:
            raise ActionExecutionError(f"Inventory management failed: {str(e)}")
