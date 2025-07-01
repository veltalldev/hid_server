# === app/utils/file_utils.py ===
"""
File operation utilities
"""

from pathlib import Path
from typing import List

def ensure_directory_exists(directory: Path) -> None:
    """Ensure a directory exists, create if it doesn't"""
    directory.mkdir(parents=True, exist_ok=True)

def get_files_by_extension(directory: Path, extension: str) -> List[Path]:
    """Get all files with a specific extension in a directory"""
    if not directory.exists():
        return []
    
    return list(directory.glob(f"*{extension}"))

def safe_filename(filename: str) -> str:
    """Create a safe filename by removing dangerous characters"""
    return "".join(c for c in filename if c.isalnum() or c in "._-")
