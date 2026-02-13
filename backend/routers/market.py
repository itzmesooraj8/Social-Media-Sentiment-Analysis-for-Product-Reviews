from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from services.market_service import market_service

router = APIRouter(prefix="/api/market", tags=["Market Data"])

@router.get("/ohlc/{symbol}")
async def get_ohlc(
    symbol: str,
    timeframe: str = "1D",
    start: Optional[str] = None,
    end: Optional[str] = None
):
    try:
        data = market_service.get_ohlc(symbol, timeframe, start, end)
        if not data:
            raise HTTPException(status_code=404, detail="No data found for symbol")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    try:
        data = market_service.get_quote(symbol)
        if not data:
            raise HTTPException(status_code=404, detail="Quote not found")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news/{symbol}")
async def get_news(symbol: str, limit: int = 10):
    try:
        return market_service.get_news(symbol, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/overview")
async def get_overview():
    try:
        return market_service.get_market_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scanner")
async def get_scanner():
    try:
        return market_service.get_scanner_results()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_stocks(q: str):
    # Simplification: use yfinance to search or common tickers
    # For a real implementation, you'd use a stock symbol list or a specific API
    try:
        # yfinance doesn't have a direct "search" that returns names well
        # This is a placeholder
        return [
            {"symbol": q.upper(), "name": f"{q.upper()} Corp", "sector": "Technology", "exchange": "NASDAQ"}
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
