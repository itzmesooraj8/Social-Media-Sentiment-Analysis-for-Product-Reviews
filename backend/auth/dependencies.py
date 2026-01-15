
from fastapi import Header, HTTPException, status
from typing import Optional
from database import supabase

async def verify_user(authorization: Optional[str] = Header(None)):
    """
    Dependency to verify user session via JWT.
    Extracts the Bearer token and checks with Supabase Auth.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    try:
        # Expected format: "Bearer <token>"
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        
        # Verify with Supabase
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
            
        return user_response.user
        
    except Exception as e:
        print(f"Auth Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Alias for verify_user to provide a standard dependency name across the app."""
    return await verify_user(authorization)
