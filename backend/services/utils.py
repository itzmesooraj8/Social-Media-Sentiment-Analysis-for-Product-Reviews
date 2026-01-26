
import hashlib

def anonymize_user(username: str) -> str:
    """Hash username for privacy using SHA-256"""
    if not username:
        return "anonymous"
    return hashlib.sha256(username.encode()).hexdigest()[:16]
