from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()


@router.get("/{run_id}")
async def get_briefs(run_id: str, db: Session = Depends(get_db)):
    """Get all briefs for a run"""
    # TODO: Implement
    return {"briefs": []}
