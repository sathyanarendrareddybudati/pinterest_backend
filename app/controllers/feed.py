from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Pin
from app.schemas.schemas import PinResponse
from typing import List, Optional
from uuid import UUID
from app.services.recommendation import recommender
from app.services.trending import get_trending_pins

router = APIRouter()


def _valid_uuid_list(ids):
    valid_ids = []
    for value in ids:
        try:
            UUID(str(value))
            print(f"Valid UUID: {value}")
            valid_ids.append(value)
        except (ValueError, TypeError):
            continue
    return valid_ids


def train_model_task(db: Session):
    recommender.train(db)

@router.post("/train-model")
def trigger_training(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Async trigger for recommendation model training"""
    background_tasks.add_task(train_model_task, db)
    return {"message": "Training started"}

@router.get("/recommendations", response_model=List[PinResponse])
def get_feed(user_id: Optional[UUID] = Query(None), limit: int = Query(10), db: Session = Depends(get_db)):
    """
    Returns personalized recommendation feed using ALS Matrix Factorization.
    """
    recommended_ids = []
    if user_id:
        recommended_ids = recommender.recommend(user_id, num_items=limit)

    if not recommended_ids:
        # Fallback to trending
        recommended_ids = _valid_uuid_list(get_trending_pins(limit))

    if not recommended_ids:
        # Final fallback, recent pins
        return db.query(Pin).order_by(Pin.created_at.desc()).limit(limit).all()

    pins = (
        db.query(Pin)
        .filter(Pin.id.in_(recommended_ids), Pin.created_at.isnot(None))
        .all()
    )
    return pins

@router.get("/trending", response_model=List[PinResponse])
def trending_feed(limit: int = Query(10), db: Session = Depends(get_db)):
    """
    Returns real-time trending pins via Redis sorted sets.
    """
    trending_ids = _valid_uuid_list(get_trending_pins(limit))
    if not trending_ids:
        return db.query(Pin).order_by(Pin.created_at.desc()).limit(limit).all()
    pins = (
        db.query(Pin).filter(Pin.id.in_(trending_ids), Pin.created_at.isnot(None)).all()
    )
    if not pins:
        return db.query(Pin).order_by(Pin.created_at.desc()).limit(limit).all()
    return pins