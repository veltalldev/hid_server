# === app/utils/script_parser.py ===
"""
Script metadata parsing utilities
"""

from typing import Tuple, Optional

def parse_script_metadata(script_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse class and map from semantic script name"""
    # Example: drk_bottom_deck_passage_3.ahk -> ("drk", "bottom_deck_passage_3")
    if not script_name.endswith('.ahk'):
        return None, None
    
    base_name = script_name[:-4]  # Remove .ahk
    parts = base_name.split('_', 1)  # Split on first underscore only
    
    if len(parts) == 2:
        class_name = parts[0]
        map_name = parts[1]
        return class_name, map_name
    
    return None, None

def get_class_display_name(class_code: str) -> str:
    """Convert class code to display name"""
    class_names = {
        'drk': 'Dark Knight',
        'nw': 'Night Walker',
        # Add more as needed
    }
    return class_names.get(class_code, class_code.upper())

def get_map_display_name(map_code: str) -> str:
    """Convert map code to display name"""
    # Convert underscores to spaces and title case
    return map_code.replace('_', ' ').title()
