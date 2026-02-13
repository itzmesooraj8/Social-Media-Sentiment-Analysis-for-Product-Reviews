from fastapi import APIRouter, HTTPException
from typing import List, Optional
from services.trading_service import trading_service

router = APIRouter(prefix="/api/trading", tags=["Trading"])

@router.get("/trades")
async def get_trades(limit: int = 50):
    try:
        data = trading_service.get_trades(limit)
        # Format keys for frontend (snake_case to camelCase if needed, but the current tradingAPI seems flexible)
        # Actually our frontend expects Trade[] interface
        formatted = []
        for t in data:
            formatted.append({
                "id": t['id'],
                "symbol": t['symbol'],
                "entryDate": t['entry_date'].isoformat() if hasattr(t['entry_date'], 'isoformat') else str(t['entry_date']),
                "exitDate": t['exit_date'].isoformat() if hasattr(t['exit_date'], 'isoformat') else str(t['exit_date']),
                "entryPrice": t['entry_price'],
                "exitPrice": t['exit_price'],
                "pnl": t['pnl'],
                "pnlPercent": t['pnl_percent'],
                "isProfit": bool(t['is_profit']),
                "duration": int(t['duration']),
                "journalTag": t['journal_tag']
            })
        return formatted
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_analytics():
    try:
        return trading_service.get_analytics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/equity-curve")
async def get_equity_curve():
    try:
        return trading_service.get_equity_curve()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/behavioral-analytics")
async def get_behavioral_analytics():
    try:
        analytics = trading_service.get_analytics()
        return analytics.get("behavioralTags", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
