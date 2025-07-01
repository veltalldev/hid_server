# === main.py ===
#!/usr/bin/env python3
"""
HID Server v4.0 - Organized Application
Entry point for the HID keyboard and mouse control server
"""

import uvicorn
from app.core.config import settings
from app.core.ssl_manager import SSLManager
from app import create_app

def main():
    """Main entry point"""
    print("🚀 HID Server v4.0 - Organized Application")
    print(f"📁 Scripts: {settings.SCRIPT_DIR}")
    print(f"🎮 Actions: {settings.ACTIONS_DIR}")
    print(f"🖼️  Images: {settings.IMAGES_DIR}")
    
    # SSL setup
    ssl_manager = SSLManager()
    cert_file, key_file = ssl_manager.get_or_create_certificates()
    
    if cert_file and key_file:
        print(f"🔐 Starting HTTPS server on port {settings.PORT}...")
        print(f"📚 API Documentation: https://localhost:{settings.PORT}/docs")
        print("⚠️  Accept self-signed certificate warnings")
        
        uvicorn.run(
            "main:app",  # ✅ Import string for reload support
            host=settings.HOST,
            port=settings.PORT,
            ssl_keyfile=str(key_file),
            ssl_certfile=str(cert_file),
            reload=settings.DEBUG,
            log_level="info"
        )
    else:
        print("⚠️  SSL setup failed, using HTTP...")
        print(f"🌐 Starting HTTP server on port {settings.PORT}...")
        print(f"📚 API Documentation: http://localhost:{settings.PORT}/docs")
        
        uvicorn.run(
            "main:app",  # ✅ Import string for reload support
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level="info"
        )

# Create app instance at module level for uvicorn import string
app = create_app()

if __name__ == "__main__":
    main()

