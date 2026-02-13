from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from services.research_service import research_service

router = APIRouter(prefix="/api/research", tags=["Research Lab"])

class CreateExperimentRequest(BaseModel):
    name: str
    strategy_type: str
    description: Optional[str] = ""

class LogRunRequest(BaseModel):
    experiment_id: str
    run_name: str
    symbol: str
    timeframe: str
    parameters: Dict[str, Any]
    metrics: Dict[str, Any]
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@router.get("/templates")
async def get_strategy_templates():
    """Get all strategy templates (Momentum, Mean-Reversion, Seasonality)."""
    try:
        return research_service.get_strategy_templates()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/experiments")
async def create_experiment(req: CreateExperimentRequest):
    """Create a new research experiment."""
    try:
        return research_service.create_experiment(
            req.name, req.strategy_type, req.description
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiments")
async def get_experiments():
    """Get all experiments."""
    try:
        return research_service.get_experiments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiments/{experiment_id}/runs")
async def get_experiment_runs(experiment_id: str):
    """Get all runs for a specific experiment."""
    try:
        return research_service.get_experiment_runs(experiment_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/runs")
async def log_run(req: LogRunRequest):
    """Log a new backtest run to an experiment."""
    try:
        return research_service.log_run(
            req.experiment_id,
            req.run_name,
            req.symbol,
            req.timeframe,
            req.parameters,
            req.metrics,
            req.start_date,
            req.end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_runs(run_ids: List[str]):
    """Compare multiple runs side-by-side."""
    try:
        return research_service.compare_runs(run_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
