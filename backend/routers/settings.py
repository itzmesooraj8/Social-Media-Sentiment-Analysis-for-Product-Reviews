from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel
import os
from dotenv import set_key, load_dotenv
from pathlib import Path

router = APIRouter(prefix="/api/settings", tags=["settings"])

class Settings(BaseModel):
    theme: str = "light"
    email_notifications: bool = True
    scraping_interval: int = 24
    notifications_email: Optional[str] = None

@router.get("", response_model=Dict[str, Any])
async def get_settings():
    # Load from env or DB. for now simple env/defaults
    return {
        "success": True,
        "data": {
            "theme": "dark", # Default to dark as per 'advanced' design request
            "email_notifications": os.getenv("EMAIL_NOTIFICATIONS", "True").lower() == "true",
            "scraping_interval": int(os.getenv("SCRAPING_INTERVAL", "24")),
            "notifications_email": os.getenv("NOTIFICATIONS_EMAIL", "")
        }
    }

@router.post("")
async def update_settings(settings: Settings):
    try:
        env_path = Path(__file__).parent.parent / ".env"
        
        set_key(env_path, "EMAIL_NOTIFICATIONS", str(settings.email_notifications))
        set_key(env_path, "SCRAPING_INTERVAL", str(settings.scraping_interval))
        if settings.notifications_email:
            set_key(env_path, "NOTIFICATIONS_EMAIL", settings.notifications_email)
            
        return {"success": True, "message": "Settings updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
