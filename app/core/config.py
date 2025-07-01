# === app/core/config.py ===
"""
Application configuration
"""

from pathlib import Path
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings

class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8444
    DEBUG: bool = True
    
    # Directories
    BASE_DIR: Path = Path.cwd()
    SCRIPT_DIR: Path = BASE_DIR / "scripts"
    ACTIONS_DIR: Path = BASE_DIR / "actions"
    IMAGES_DIR: Path = BASE_DIR / "images"
    CERT_DIR: Path = BASE_DIR / "certs"
    
    # File limits
    MAX_FILE_SIZE: int = 16 * 1024 * 1024  # 16MB
    SUPPORTED_IMAGE_EXTENSIONS: list = ['.webp', '.png', '.jpg', '.jpeg', '.gif']
    
    # HID settings
    KEYBOARD_DEVICE: str = "/dev/hidg0"
    MOUSE_DEVICE: str = "/dev/hidg1"
    
    # Action timeout
    ACTION_TIMEOUT: float = 10.0
    
    class Config:
        env_file = ".env"

# Create settings instance
settings = Settings()

# Ensure directories exist
settings.SCRIPT_DIR.mkdir(exist_ok=True)
settings.ACTIONS_DIR.mkdir(exist_ok=True)
settings.IMAGES_DIR.mkdir(exist_ok=True)
settings.CERT_DIR.mkdir(exist_ok=True)
