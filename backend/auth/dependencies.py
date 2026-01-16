
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
        # print(f"DEBUG: Verifying token: {token[:10]}...")
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
            
        return user_response.user
        
    except Exception as e:
        print(f"Auth Verification Error: {e}")
        import traceback
        traceback.print_exc()
        # For Local Dev Debugging: Allow "dev-token" if backend logic fails? No, better to see why it fails.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Alias for verify_user to provide a standard dependency name across the app."""
    return await verify_user(authorization)
