#!/usr/bin/env python3
"""
AHK to HID Keyboard Emulator v2 for Raspberry Pi
Parses AutoHotkey macro syntax and outputs USB HID keyboard reports to /dev/hidg0
VERSION 2: Includes proper state tracking for simultaneous/overlapping key presses
VERSION 2.1: Added pause/resume functionality via signals
"""

import re
import time
import signal
import sys
import threading
from typing import List, Dict, Tuple, Optional, Set

# USB HID Keyboard scan codes
# Complete USB HID Keyboard scan codes for ahk_to_hid_v2.py
# Replace the existing KEY_MAP in your ahk_to_hid_v2.py with this complete version

KEY_MAP = {
    # Letters (a-z)
    'a': 0x04, 'b': 0x05, 'c': 0x06, 'd': 0x07, 'e': 0x08, 'f': 0x09,
    'g': 0x0A, 'h': 0x0B, 'i': 0x0C, 'j': 0x0D, 'k': 0x0E, 'l': 0x0F,
    'm': 0x10, 'n': 0x11, 'o': 0x12, 'p': 0x13, 'q': 0x14, 'r': 0x15,
    's': 0x16, 't': 0x17, 'u': 0x18, 'v': 0x19, 'w': 0x1A, 'x': 0x1B,
    'y': 0x1C, 'z': 0x1D,
    
    # Numbers (1-9, 0)
    '1': 0x1E, '2': 0x1F, '3': 0x20, '4': 0x21, '5': 0x22,
    '6': 0x23, '7': 0x24, '8': 0x25, '9': 0x26, '0': 0x27,
    
    # Special keys
    'enter': 0x28, 'escape': 0x29, 'backspace': 0x2A, 'tab': 0x2B,
    'space': 0x2C, 'minus': 0x2D, 'equal': 0x2E, 'lbracket': 0x2F,
    'rbracket': 0x30, 'backslash': 0x31, 'semicolon': 0x33, 'quote': 0x34,
    'grave': 0x35, 'comma': 0x36, 'period': 0x37, 'slash': 0x38,
    'capslock': 0x39,
    
    # Function keys
    'f1': 0x3A, 'f2': 0x3B, 'f3': 0x3C, 'f4': 0x3D, 'f5': 0x3E, 'f6': 0x3F,
    'f7': 0x40, 'f8': 0x41, 'f9': 0x42, 'f10': 0x43, 'f11': 0x44, 'f12': 0x45,
    
    # Special keys continued
    'printscreen': 0x46, 'scrolllock': 0x47, 'pause': 0x48, 'insert': 0x49,
    'home': 0x4A, 'pgup': 0x4B, 'delete': 0x4C, 'end': 0x4D, 'pgdn': 0x4E,
    
    # Arrow keys  
    'right': 0x4F, 'left': 0x50, 'down': 0x51, 'up': 0x52,
    
    # Numpad
    'numlock': 0x53, 'kp_divide': 0x54, 'kp_multiply': 0x55, 'kp_minus': 0x56,
    'kp_plus': 0x57, 'kp_enter': 0x58, 'kp_1': 0x59, 'kp_2': 0x5A,
    'kp_3': 0x5B, 'kp_4': 0x5C, 'kp_5': 0x5D, 'kp_6': 0x5E,
    'kp_7': 0x5F, 'kp_8': 0x60, 'kp_9': 0x61, 'kp_0': 0x62, 'kp_dot': 0x63,
    
    # Modifier keys (these need special handling in HID reports)
    'lctrl': 0xE0, 'lshift': 0xE1, 'lalt': 0xE2, 'lwin': 0xE3,
    'rctrl': 0xE4, 'rshift': 0xE5, 'ralt': 0xE6, 'rwin': 0xE7,
    
    # Aliases for compatibility with your server
    '-': 0x2D, '=': 0x2E, '[': 0x2F, ']': 0x30, '\\': 0x31,
    ';': 0x33, "'": 0x34, '`': 0x35, ',': 0x36, '.': 0x37, '/': 0x38,
    'ctrl': 0xE0, 'shift': 0xE1, 'alt': 0xE2, 'lwin': 0xE3,
}

# Global flags
running = True
paused = False
pause_event = threading.Event()
pause_event.set()  # Start unpaused

# Global keyboard state tracker
keyboard_state = {
    'pressed_keys': set(),  # Set of currently pressed key names
    'modifiers': 0          # Modifier byte (for future Ctrl/Alt/Shift support)
}

def signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown"""
    global running
    print("\nShutdown signal received, stopping...")
    running = False
    pause_event.set()  # Unblock any waiting threads

def handle_pause(signum, frame):
    """Handle SIGUSR1 - Pause execution"""
    global paused
    paused = True
    pause_event.clear()
    print("⏸️  Macro execution PAUSED")

def handle_resume(signum, frame):
    """Handle SIGUSR2 - Resume execution"""
    global paused
    paused = False
    pause_event.set()
    print("▶️  Macro execution RESUMED")

def parse_ahk_file(filename: str) -> List[dict]:
    """Parse AHK file and return list of commands"""
    with open(filename, 'r') as f:
        content = f.read()
    
    commands = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines and comments
        if not line or line.startswith(';') or line.startswith('#'):
            i += 1
            continue
            
        # Handle Loop commands
        if line.startswith('Loop'):
            loop_match = re.match(r'Loop(?:,\s*(\d+))?', line)
            if loop_match:
                count = int(loop_match.group(1)) if loop_match.group(1) else -1  # -1 for infinite
                loop_body, skip_lines = parse_loop_body(lines, i + 1)
                commands.append({'type': 'loop', 'count': count, 'body': loop_body})
                i += skip_lines + 1
                continue
        
        # Handle Send commands
        send_match = re.match(r'Send,\s*\{(.+?)\}', line)
        if send_match:
            key_command = send_match.group(1)
            commands.append(parse_send_command(key_command))
            
        # Handle Sleep commands
        sleep_match = re.match(r'Sleep,\s*(\d+)', line)
        if sleep_match:
            duration = int(sleep_match.group(1))
            commands.append({'type': 'sleep', 'duration': duration})
            
        i += 1
    
    return commands

def parse_loop_body(lines: List[str], start_idx: int) -> Tuple[List[dict], int]:
    """Parse the body of a loop, handling nested braces"""
    body_commands = []
    brace_count = 0
    i = start_idx
    
    # Find opening brace
    while i < len(lines) and lines[i].strip() != '{':
        i += 1
    
    if i >= len(lines):
        return body_commands, i - start_idx
        
    i += 1  # Skip opening brace
    brace_count = 1
    
    while i < len(lines) and brace_count > 0:
        line = lines[i].strip()
        
        if line == '{':
            brace_count += 1
        elif line == '}':
            brace_count -= 1
            if brace_count == 0:
                break
                
        # Skip empty lines and comments
        if not line or line.startswith(';'):
            i += 1
            continue
            
        # Parse commands within loop body
        if line.startswith('Loop'):
            loop_match = re.match(r'Loop(?:,\s*(\d+))?', line)
            if loop_match:
                count = int(loop_match.group(1)) if loop_match.group(1) else -1
                nested_body, skip_lines = parse_loop_body(lines, i + 1)
                body_commands.append({'type': 'loop', 'count': count, 'body': nested_body})
                i += skip_lines + 1
                continue
                
        send_match = re.match(r'Send,\s*\{(.+?)\}', line)
        if send_match:
            key_command = send_match.group(1)
            body_commands.append(parse_send_command(key_command))
            
        sleep_match = re.match(r'Sleep,\s*(\d+)', line)
        if sleep_match:
            duration = int(sleep_match.group(1))
            body_commands.append({'type': 'sleep', 'duration': duration})
            
        i += 1
    
    return body_commands, i - start_idx

def parse_send_command(key_command: str) -> dict:
    """Parse a Send command like 'r Down' or 'Space Up'"""
    parts = key_command.split()
    if len(parts) == 2:
        key_name = parts[0].lower()
        action = parts[1].lower()  # 'down' or 'up'
        return {'type': 'key', 'key': key_name, 'action': action}
    else:
        # Handle simple key presses without explicit Down/Up
        key_name = key_command.lower()
        return {'type': 'key', 'key': key_name, 'action': 'press'}

def create_hid_report_from_state() -> bytes:
    """Create HID keyboard report from current keyboard state"""
    # HID report format: [modifier, reserved, key1, key2, key3, key4, key5, key6]
    report = [0] * 8
    
    # Set modifier byte (for future use)
    report[0] = keyboard_state['modifiers']
    
    # Fill key slots (up to 6 keys)
    key_slots = []
    for key_name in keyboard_state['pressed_keys']:
        scan_code = KEY_MAP.get(key_name.lower())
        if scan_code:
            key_slots.append(scan_code)
    
    # Fill report with pressed keys (up to 6)
    for i, scan_code in enumerate(key_slots[:6]):
        report[2 + i] = scan_code
    
    return bytes(report)

def get_state_debug_info() -> str:
    """Get debug info about current keyboard state"""
    if keyboard_state['pressed_keys']:
        keys_list = ', '.join(f"'{k}'" for k in sorted(keyboard_state['pressed_keys']))
        return f"[HELD: {keys_list}]"
    else:
        return "[NO KEYS HELD]"

def send_hid_report(report: bytes, debug_info: str = ""):
    """Send HID report to /dev/hidg0 or print to stdout for debugging"""
    try:
        with open('/dev/hidg0', 'wb') as f:
            f.write(report)
    except:
        # Debug mode: print to stdout instead
        hex_bytes = ' '.join(f'{b:02x}' for b in report)
        state_info = get_state_debug_info()
        pause_status = " [PAUSED]" if paused else ""
        print(f"HID: [{hex_bytes}] {debug_info} {state_info}{pause_status}")
        pass

def execute_key_action(key: str, action: str):
    """Execute a key action (down, up, or press) with state tracking"""
    if action == 'down':
        # Add key to pressed set
        keyboard_state['pressed_keys'].add(key)
        report = create_hid_report_from_state()
        send_hid_report(report, f"'{key}' DOWN")
        
    elif action == 'up':
        # Remove key from pressed set
        keyboard_state['pressed_keys'].discard(key)  # discard won't error if key not present
        report = create_hid_report_from_state()
        send_hid_report(report, f"'{key}' UP")
        
    elif action == 'press':
        # Send key down then up with state tracking
        keyboard_state['pressed_keys'].add(key)
        report_down = create_hid_report_from_state()
        send_hid_report(report_down, f"'{key}' DOWN")
        
        time.sleep(0.01)  # Brief delay between down/up
        
        keyboard_state['pressed_keys'].discard(key)
        report_up = create_hid_report_from_state()
        send_hid_report(report_up, f"'{key}' UP")

def wait_for_resume():
    """Wait while paused, checking for resume signal"""
    while paused and running:
        if not pause_event.wait(timeout=0.1):
            continue
        break

def execute_commands(commands: List[dict]):
    """Execute a list of commands with pause/resume support"""
    global running
    
    for command in commands:
        if not running:
            break
            
        # Wait if paused
        wait_for_resume()
        
        if not running:  # Check again after potential pause
            break
            
        if command['type'] == 'key':
            execute_key_action(command['key'], command['action'])
            
        elif command['type'] == 'sleep':
            duration_ms = command['duration']
            if duration_ms >= 100:  # Only show sleep debug for longer delays
                print(f"Sleep: {duration_ms}ms")
            
            # Sleep in small chunks to allow pause detection
            sleep_time = duration_ms / 1000.0
            chunk_size = 0.1  # 100ms chunks
            while sleep_time > 0 and running:
                wait_for_resume()  # Check for pause
                if not running:
                    break
                    
                current_chunk = min(chunk_size, sleep_time)
                time.sleep(current_chunk)
                sleep_time -= current_chunk
            
        elif command['type'] == 'loop':
            count = command['count']
            body = command['body']
            
            if count == -1:  # Infinite loop
                iteration = 0
                while running:
                    wait_for_resume()  # Check for pause
                    if not running:
                        break
                    print(f"Loop iteration {iteration + 1}")
                    execute_commands(body)
                    iteration += 1
            else:  # Fixed count loop
                for i in range(count):
                    if not running:
                        break
                    wait_for_resume()  # Check for pause
                    if not running:
                        break
                    print(f"Loop iteration {i + 1}/{count}")
                    execute_commands(body)

def main():
    global running
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGUSR1, handle_pause)   # Pause signal
    signal.signal(signal.SIGUSR2, handle_resume)  # Resume signal
    
    if len(sys.argv) != 2:
        print("Usage: python3 ahk_to_hid_v2.py <ahk_file>")
        sys.exit(1)
    
    ahk_file = sys.argv[1]
    
    try:
        print(f"AHK to HID Emulator v2.1 - State Tracking + Pause/Resume Edition")
        print(f"Parsing AHK file: {ahk_file}")
        commands = parse_ahk_file(ahk_file)
        print(f"Parsed {len(commands)} top-level commands")
        
        print("Starting macro execution (Ctrl+C to stop)...")
        print("v2.1 Features: Simultaneous key support, state tracking, pause/resume")
        print("Signals: SIGUSR1 = Pause, SIGUSR2 = Resume")
        execute_commands(commands)
        
    except FileNotFoundError:
        print(f"Error: File '{ahk_file}' not found")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # Clear any held keys on exit
        if keyboard_state['pressed_keys']:
            print(f"Clearing held keys: {keyboard_state['pressed_keys']}")
            keyboard_state['pressed_keys'].clear()
            report = create_hid_report_from_state()
            send_hid_report(report, "CLEANUP")
    
    print("Macro execution completed")

if __name__ == "__main__":
    main()
