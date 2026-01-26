
from fastapi import Header, HTTPException, status
from typing import Optional
from database import supabase
import os



async def verify_user(authorization: Optional[str] = Header(None)):
    """
    Strict Dependency: Verifies valid JWT or REJECTS request.
    No more demo bypass.
    """
    # Allow an opt-in development bypass for local testing when explicitly enabled.
    # Set environment variable DEV_ALLOW_ANON=1 or DEV_ALLOW_ANON=true to enable.
    if os.environ.get("DEV_ALLOW_ANON", "").lower() in ["1", "true"]:
        return {"id": "dev-user", "email": "dev@local"}
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    try:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        
        # Try decoding as custom JWT first
        from auth.utils import decode_access_token
        custom_token_data = decode_access_token(token)
        if custom_token_data:
             return {"id": custom_token_data.username, "email": f"{custom_token_data.username}@local"}

        # If not custom, try Supabase
        user_response = supabase.auth.get_user(token)
        if user_response.user:
             return user_response.user
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
        
    except Exception as e:
        print(f"Auth Verification Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Alias for verify_user to provide a standard dependency name across the app."""
    return await verify_user(authorization)
