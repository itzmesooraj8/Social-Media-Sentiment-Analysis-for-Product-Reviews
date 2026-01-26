
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from auth.utils import create_access_token, get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta

router = APIRouter()

# Demo User Database
# Demo User Database removed - using Supabase Auth
from database import supabase

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/api/login")
async def login_for_access_token(form_data: LoginRequest):
    """
    Login using Supabase Auth.
    Expects 'username' to be the email for Supabase.
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        # Authenticate with Supabase Auth
        # Note: form_data.username is used as email
        res = supabase.auth.sign_in_with_password({
            "email": form_data.username, 
            "password": form_data.password
        })
        
        if res.session:
            return {
                "token": res.session.access_token, 
                "user": {
                    "email": res.user.email,
                    "id": res.user.id
                }
            }
        else:
             raise HTTPException(status_code=401, detail="Login failed")
             
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
