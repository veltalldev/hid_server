#!/usr/bin/env python3
"""
Robust Mouse Control Program with Coordinate Discovery
FIXED VERSION - Resolves coordinate tracking and step size issues
"""

import time
import sys

# Screen and HID coordinate constants
SCREEN_WIDTH = 2560
SCREEN_HEIGHT = 1600
HID_MAX_X = 692
HID_MAX_Y = 433

def send_mouse_report(buttons=0, x_rel=0, y_rel=0):
    """Send HID mouse report with bounds checking"""
    x_rel = max(-127, min(127, x_rel))
    y_rel = max(-127, min(127, y_rel))
    
    report = bytes([buttons & 0xFF, x_rel & 0xFF, y_rel & 0xFF, 0])
    
    try:
        with open('/dev/hidg1', 'wb') as f:
            f.write(report)
        return True
    except Exception as e:
        print(f"❌ HID Error: {e}")
        return False

def screen_to_hid_coords(screen_x, screen_y):
    """Convert screen pixel coordinates to HID coordinates"""
    hid_x = int((screen_x / SCREEN_WIDTH) * HID_MAX_X)
    hid_y = int((screen_y / SCREEN_HEIGHT) * HID_MAX_Y)
    return hid_x, hid_y

def hid_to_screen_coords(hid_x, hid_y):
    """Convert HID coordinates to screen pixel coordinates"""
    screen_x = int((hid_x / HID_MAX_X) * SCREEN_WIDTH)
    screen_y = int((hid_y / HID_MAX_Y) * SCREEN_HEIGHT)
    return screen_x, screen_y

def reset_to_origin():
    """Reset mouse to absolute (0,0)"""
    print("🔄 Resetting to origin...")
    overshoot_x, overshoot_y = -3000, -3000
    
    while abs(overshoot_x) > 0 or abs(overshoot_y) > 0:
        chunk_x = max(-127, overshoot_x)
        chunk_y = max(-127, overshoot_y)
        if not send_mouse_report(x_rel=chunk_x, y_rel=chunk_y):
            print("❌ Failed during reset to origin")
            return False
        overshoot_x -= chunk_x
        overshoot_y -= chunk_y
        time.sleep(0.001)
    return True

def move_to_hid_coordinates(hid_x, hid_y):
    """Move to absolute HID coordinates"""
    if not reset_to_origin():
        return False
    
    time.sleep(0.05)
    
    rel_x, rel_y = hid_x, hid_y
    
    # Move in chunks to handle large distances
    while abs(rel_x) > 100 or abs(rel_y) > 100:
        chunk_x = min(100, max(-100, rel_x))
        chunk_y = min(100, max(-100, rel_y))
        if not send_mouse_report(x_rel=chunk_x, y_rel=chunk_y):
            print("❌ Failed during large movement")
            return False
        rel_x -= chunk_x
        rel_y -= chunk_y
        time.sleep(0.005)
    
    # Final movement
    if rel_x != 0 or rel_y != 0:
        if not send_mouse_report(x_rel=rel_x, y_rel=rel_y):
            print("❌ Failed during final movement")
            return False
    
    return True

def click_at_screen_coordinates(screen_x, screen_y):
    """Click at screen pixel coordinates"""
    hid_x, hid_y = screen_to_hid_coords(screen_x, screen_y)
    print(f"🎯 Clicking at screen ({screen_x}, {screen_y}) -> HID ({hid_x}, {hid_y})")
    
    if not move_to_hid_coordinates(hid_x, hid_y):
        print("❌ Failed to move to target coordinates")
        return False
    
    time.sleep(0.1)
    
    # Click: button down, wait, button up
    if not send_mouse_report(buttons=1):
        print("❌ Failed to press mouse button")
        return False
    
    time.sleep(0.05)
    
    if not send_mouse_report(buttons=0):
        print("❌ Failed to release mouse button")
        return False
    
    print(f"✅ Clicked successfully!")
    return True

def get_user_input():
    """Get user input - works reliably over SSH"""
    try:
        return input("> ").strip().lower()
    except KeyboardInterrupt:
        return 'q'
    except EOFError:
        return 'q'

def coordinate_discovery_mode():
    """Interactive coordinate discovery mode - Fixed with absolute positioning."""
    print("\n" + "="*60)
    print("🎯 COORDINATE DISCOVERY MODE")
    print("="*60)
    print("Starting at screen center...")

    # Start at center of screen using absolute positioning
    center_screen_x = SCREEN_WIDTH // 2
    center_screen_y = SCREEN_HEIGHT // 2
    current_hid_x, current_hid_y = screen_to_hid_coords(center_screen_x, center_screen_y)

    print(f"Center: screen({center_screen_x}, {center_screen_y}) -> HID({current_hid_x}, {current_hid_y})")

    move_to_hid_coordinates(current_hid_x, current_hid_y)

    print("\nCommands (type and press Enter):")
    print("  w/up    = Move up     | s/down  = Move down")
    print("  a/left  = Move left   | d/right = Move right")
    print("  c/click = Click here  | q/quit  = Get coordinates")
    print("  big     = Large steps | small   = Small steps | tiny = 1 HID unit")
    print("  reset   = Go back to center | help = Show help")
    print("-" * 60)

    step_hid_units = 7  # Start with medium steps, changed from 3
    step_names = {1: "tiny", 3: "small", 7: "medium", 15: "big", 30: "huge"}

    while True:
        try:
            current_screen_x, current_screen_y = hid_to_screen_coords(current_hid_x, current_hid_y)
            step_name = step_names.get(step_hid_units, f"{step_hid_units}HID")

            approx_x_pixels = int((step_hid_units / HID_MAX_X) * SCREEN_WIDTH)
            approx_y_pixels = int((step_hid_units / HID_MAX_Y) * SCREEN_HEIGHT)

            print(f"\nHID: ({current_hid_x}, {current_hid_y}) -> Screen: ({current_screen_x}, {current_screen_y})")
            print(f"Step: {step_hid_units} HID units ({step_name}) ≈ {approx_x_pixels}x, {approx_y_pixels}y pixels")

            command = get_user_input()

            if command in ['q', 'quit', 'exit']:
                final_screen_x, final_screen_y = hid_to_screen_coords(current_hid_x, current_hid_y)
                print(f"\n🎯 TARGET COORDINATES:")
                print(f"Screen: ({final_screen_x}, {final_screen_y})")
                print(f"HID: ({current_hid_x}, {current_hid_y})")
                print(f"\nTo click this later:")
                print(f"  sudo python3 mouse_control.py click {final_screen_x} {final_screen_y}")
                break

            # --- MODIFIED LOGIC: Use absolute positioning for consistent movement ---
            new_hid_x, new_hid_y = current_hid_x, current_hid_y
            moved = False

            if command in ['w', 'up']:
                new_hid_y = max(0, current_hid_y - step_hid_units)
                if new_hid_y != current_hid_y:
                    print(f"↑ Moving up...")
                    moved = True
            elif command in ['s', 'down']:
                new_hid_y = min(HID_MAX_Y, current_hid_y + step_hid_units)
                if new_hid_y != current_hid_y:
                    print(f"↓ Moving down...")
                    moved = True
            elif command in ['a', 'left']:
                new_hid_x = max(0, current_hid_x - step_hid_units)
                if new_hid_x != current_hid_x:
                    print(f"← Moving left...")
                    moved = True
            elif command in ['d', 'right']:
                new_hid_x = min(HID_MAX_X, current_hid_x + step_hid_units)
                if new_hid_x != current_hid_x:
                    print(f"→ Moving right...")
                    moved = True
            
            if moved:
                # Use the reliable absolute move function for every adjustment
                move_to_hid_coordinates(new_hid_x, new_hid_y)
                current_hid_x, current_hid_y = new_hid_x, new_hid_y
                print("✓ Moved!")
                continue # Skip to next prompt
            # --- END OF MODIFIED LOGIC ---

            elif command in ['c', 'click']:
                send_mouse_report(buttons=1)
                time.sleep(0.05)
                send_mouse_report(buttons=0)
                current_screen_x, current_screen_y = hid_to_screen_coords(current_hid_x, current_hid_y)
                print(f"🖱️  Clicked at HID({current_hid_x}, {current_hid_y}) = Screen({current_screen_x}, {current_screen_y})")

            elif command == 'reset':
                current_hid_x, current_hid_y = screen_to_hid_coords(center_screen_x, center_screen_y)
                move_to_hid_coordinates(current_hid_x, current_hid_y)
                print("🎯 Reset to center")

            elif command == 'tiny':
                step_hid_units = 1
                print(f"📏 Step: {step_hid_units} HID unit (precise)")
            # ... (rest of the step size and help commands remain the same) ...
            
            # (Keep the rest of your elif commands for step sizes, help, etc. as they are)
            elif command == 'small':
                step_hid_units = 3
                print(f"📏 Step: {step_hid_units} HID units (small)")
            elif command in ['medium', 'med']:
                step_hid_units = 7
                print(f"📏 Step: {step_hid_units} HID units (medium)")
            elif command == 'big':
                step_hid_units = 15
                print(f"📏 Step: {step_hid_units} HID units (big)")
            elif command == 'huge':
                step_hid_units = 30
                print(f"📏 Step: {step_hid_units} HID units (huge)")
            elif command in ['help', '?']:
                print("\nCommands:")
                print("  Movement: w/up s/down a/left d/right")
                print("  Actions: c/click q/quit reset")
                print("  Step sizes: tiny(1) small(3) medium(7) big(15) huge(30)")
            elif command == '':
                continue
            else:
                print(f"❓ Unknown: '{command}' (try 'help')")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

def debug_coordinates(screen_x, screen_y):
    """Debug coordinate conversion"""
    hid_x, hid_y = screen_to_hid_coords(screen_x, screen_y)
    back_screen_x, back_screen_y = hid_to_screen_coords(hid_x, hid_y)
    
    print(f"🔍 COORDINATE DEBUG:")
    print(f"  Input screen: ({screen_x}, {screen_y})")
    print(f"  Converted HID: ({hid_x}, {hid_y})")
    print(f"  Back to screen: ({back_screen_x}, {back_screen_y})")
    print(f"  Error: ({screen_x - back_screen_x}, {screen_y - back_screen_y})")
    print(f"  Scale factors: X={SCREEN_WIDTH/HID_MAX_X:.2f}, Y={SCREEN_HEIGHT/HID_MAX_Y:.2f}")

def test_corners():
    """Test all four corners"""
    print("🏁 Testing corners (watch cursor movement)...")
    
    corners = [
        (0, 0, "Top-left"),
        (SCREEN_WIDTH-1, 0, "Top-right"), 
        (0, SCREEN_HEIGHT-1, "Bottom-left"),
        (SCREEN_WIDTH-1, SCREEN_HEIGHT-1, "Bottom-right"),
        (SCREEN_WIDTH//2, SCREEN_HEIGHT//2, "Center")
    ]
    
    for screen_x, screen_y, name in corners:
        hid_x, hid_y = screen_to_hid_coords(screen_x, screen_y)
        print(f"\n{name}: screen({screen_x}, {screen_y}) -> HID({hid_x}, {hid_y})")
        if move_to_hid_coordinates(hid_x, hid_y):
            print(f"✅ Moved to {name}")
        else:
            print(f"❌ Failed to move to {name}")
        time.sleep(2)

def main():
    print("🖱️  Robust Mouse Control Program - FIXED VERSION")
    print(f"📺 For {SCREEN_WIDTH}x{SCREEN_HEIGHT} screen resolution")
    print(f"🎛️  HID coordinate space: {HID_MAX_X}x{HID_MAX_Y}")
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python3 mouse_control.py click X Y     - Click at screen coordinates")
        print("  python3 mouse_control.py move X Y      - Move to screen coordinates")
        print("  python3 mouse_control.py discover      - Interactive coordinate finder")
        print("  python3 mouse_control.py center        - Move to screen center")
        print("  python3 mouse_control.py debug X Y     - Debug coordinate conversion")
        print("  python3 mouse_control.py test_corners  - Test all corners")
        print("\nExamples:")
        print("  python3 mouse_control.py click 1280 800    # Click center")
        print("  python3 mouse_control.py discover          # Find coordinates")
        print("  python3 mouse_control.py debug 1280 800    # Debug center")
        return
    
    command = sys.argv[1].lower()
    
    if command == "click":
        if len(sys.argv) != 4:
            print("Usage: python3 mouse_control.py click X Y")
            return
        try:
            x, y = int(sys.argv[2]), int(sys.argv[3])
            click_at_screen_coordinates(x, y)
        except ValueError:
            print("Error: X and Y must be integers")
        
    elif command == "move":
        if len(sys.argv) != 4:
            print("Usage: python3 mouse_control.py move X Y")
            return
        try:
            x, y = int(sys.argv[2]), int(sys.argv[3])
            hid_x, hid_y = screen_to_hid_coords(x, y)
            print(f"Moving to screen ({x}, {y}) -> HID ({hid_x}, {hid_y})")
            if move_to_hid_coordinates(hid_x, hid_y):
                print("✅ Moved successfully!")
            else:
                print("❌ Move failed!")
        except ValueError:
            print("Error: X and Y must be integers")
        
    elif command == "discover":
        coordinate_discovery_mode()
        
    elif command == "center":
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        hid_x, hid_y = screen_to_hid_coords(center_x, center_y)
        print(f"Moving to center ({center_x}, {center_y}) -> HID ({hid_x}, {hid_y})")
        if move_to_hid_coordinates(hid_x, hid_y):
            print("✅ Centered successfully!")
        else:
            print("❌ Center move failed!")
        
    elif command == "debug":
        if len(sys.argv) != 4:
            print("Usage: python3 mouse_control.py debug X Y")
            return
        try:
            x, y = int(sys.argv[2]), int(sys.argv[3])
            debug_coordinates(x, y)
        except ValueError:
            print("Error: X and Y must be integers")
        
    elif command == "test_corners":
        test_corners()
        
    else:
        print(f"Unknown command: {command}")
        print("Available: click, move, discover, center, debug, test_corners")

if __name__ == "__main__":
    main()
