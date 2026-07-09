from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Interaction
from app.schemas import InteractionOut, InteractionCreate

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.get("", response_model=List[InteractionOut])
def list_interactions(hcp_name: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(Interaction).order_by(Interaction.created_at.desc())
    if hcp_name:
        q = q.filter(Interaction.hcp_name.ilike(f"%{hcp_name}%"))
    return q.limit(limit).all()


@router.get("/{interaction_id}", response_model=InteractionOut)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    obj = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return obj


@router.put("/{interaction_id}", response_model=InteractionOut)
def update_interaction(interaction_id: int, payload: InteractionCreate, db: Session = Depends(get_db)):
    """Direct edit endpoint - used when the user manually tweaks the form fields
    themselves rather than going through the AI assistant."""
    obj = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Interaction not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("", response_model=InteractionOut)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    obj = Interaction(**payload.model_dump(exclude_unset=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
