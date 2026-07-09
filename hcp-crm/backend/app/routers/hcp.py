from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import HCP

router = APIRouter(prefix="/api/hcps", tags=["hcps"])


class HCPOut(BaseModel):
    id: int
    name: str
    hospital: Optional[str] = None
    specialty: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[HCPOut])
def list_hcps(q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(HCP)
    if q:
        like = f"%{q}%"
        query = query.filter((HCP.name.ilike(like)) | (HCP.hospital.ilike(like)))
    return query.limit(20).all()
