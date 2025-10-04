from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()


@router.post("/{run_id}")
async def export_report(run_id: str, format: str = "md", db: Session = Depends(get_db)):
    """Export report as .md or .pdf"""
    # TODO: Implement export logic
    # 1. Generate markdown
    # 2. If PDF, convert with WeasyPrint
    # 3. Upload to S3/R2
    # 4. Return signed URL
    
    raise HTTPException(status_code=501, detail="Not implemented")
