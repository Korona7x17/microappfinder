from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()


@router.get("/{run_id}")
async def get_clusters(run_id: str, db: Session = Depends(get_db)):
    """Get all clusters for a run"""
    # TODO: Implement
    return {"clusters": []}
