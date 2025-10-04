from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.schemas.run import RunCreate, RunResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=RunResponse)
async def create_run(run_data: RunCreate, db: Session = Depends(get_db)):
    """Create a new analysis run"""
    logger.info(f"Creating run with topics: {run_data.topics}")
    
    # TODO: Implement run creation logic
    # 1. Create run record
    # 2. Enqueue job in Redis
    # 3. Return run_id
    
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, db: Session = Depends(get_db)):
    """Get run status and basic info"""
    # TODO: Fetch run from DB
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{run_id}/report")
async def get_run_report(run_id: str, db: Session = Depends(get_db)):
    """Get full report with signals, clusters, and briefs"""
    # TODO: Fetch all related data
    raise HTTPException(status_code=501, detail="Not implemented")
