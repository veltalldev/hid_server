# === app/core/exceptions.py ===
"""
Custom exception classes
"""

class HIDServerException(Exception):
    """Base exception for HID server"""
    pass

class MacroExecutionError(HIDServerException):
    """Raised when macro execution fails"""
    pass

class ActionExecutionError(HIDServerException):
    """Raised when action execution fails"""
    pass

class ScriptManagementError(HIDServerException):
    """Raised when script management fails"""
    pass
