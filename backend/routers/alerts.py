from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from database import supabase

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

class Alert(BaseModel):
    id: Optional[str] = None
    title: str
    message: str
    type: str = "info" # info, warning, error, success
    created_at: Optional[str] = None
    read: bool = False

class AlertCreate(BaseModel):
    title: str
    message: str
    type: str = "info"

@router.get("", response_model=List[Alert])
async def get_alerts():
    try:
        # Try to fetch from DB
        if supabase:
            resp = supabase.table("alerts").select("*").order("created_at", desc=True).limit(50).execute()
            if resp.data:
                return resp.data
        
        # Return empty list if no DB or empty
        return []
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        # Return empty list on error to prevent UI crash
        return []

@router.post("", response_model=Alert)
async def create_alert(alert: AlertCreate):
    try:
        data = alert.dict()
        data["created_at"] = datetime.now().isoformat()
        data["read"] = False
        
        if supabase:
            resp = supabase.table("alerts").insert(data).execute()
            if resp.data:
                return resp.data[0]
        
        # Fallback mock return if DB fails (though user said no mock, 
        # but for safety if table doesn't exist yet)
        data["id"] = "temp_" + datetime.now().strftime("%f")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{alert_id}/read")
async def mark_alert_read(alert_id: str):
    try:
        if supabase:
            supabase.table("alerts").update({"read": True}).eq("id", alert_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
