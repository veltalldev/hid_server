# === app/core/ssl_manager.py ===
"""
SSL certificate management
"""

import subprocess
from pathlib import Path
from typing import Tuple, Optional

from app.core.config import settings

class SSLManager:
    """Manages SSL certificate generation and retrieval"""
    
    def __init__(self):
        self.cert_file = settings.CERT_DIR / "cert.pem"
        self.key_file = settings.CERT_DIR / "key.pem"
    
    def get_or_create_certificates(self) -> Tuple[Optional[Path], Optional[Path]]:
        """Get existing certificates or create new ones"""
        
        if self.cert_file.exists() and self.key_file.exists():
            print("📜 Using existing SSL certificates")
            return self.cert_file, self.key_file
        
        print("🔐 Generating self-signed SSL certificate...")
        
        if self._generate_certificates():
            return self.cert_file, self.key_file
        
        return None, None
    
    def _generate_certificates(self) -> bool:
        """Generate self-signed certificates using OpenSSL"""
        try:
            subprocess.run([
                "openssl", "req", "-x509", "-newkey", "rsa:4096",
                "-keyout", str(self.key_file),
                "-out", str(self.cert_file),
                "-days", "365", "-nodes", "-subj",
                "/C=US/ST=State/L=City/O=HIDServer/CN=localhost"
            ], check=True, capture_output=True)
            
            print(f"✅ SSL certificate generated: {self.cert_file}")
            print(f"✅ SSL private key generated: {self.key_file}")
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ OpenSSL not found or certificate generation failed")
            print("Install with: sudo apt-get install openssl")
            return False
