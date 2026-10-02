from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.weight_log import WeightLog
from app.schemas.weight import WeightCreate, WeightResponse, WeightStatsResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=WeightResponse)
def log_weight(
    payload: WeightCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Έλεγχος αν υπάρχει ήδη καταγραφή για αυτή την ημέρα -> Update, αλλιώς Insert
    existing = db.query(WeightLog).filter(
        WeightLog.user_id == current_user.id,
        WeightLog.log_date == payload.log_date
    ).first()

    if existing:
        existing.weight_kg = payload.weight_kg
        db.commit()
        db.refresh(existing)
        return existing

    new_log = WeightLog(
        user_id=current_user.id,
        weight_kg=payload.weight_kg,
        log_date=payload.log_date
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@router.get("/stats", response_model=WeightStatsResponse)
def get_weight_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Λήψη όλων των καταγραφών ταξινομημένων χρονολογικά
    logs = db.query(WeightLog).filter(
        WeightLog.user_id == current_user.id
    ).order_by(WeightLog.log_date.desc()).all()

    current_weight = logs[0].weight_kg if logs else getattr(current_user, 'current_weight_kg', None)
    target_weight = getattr(current_user, 'target_weight_kg', None)

    # Υπολογισμός εβδομαδιαίου μέσου όρου (τελευταίες 7 ημέρες)
    today = date.today()
    week_ago = today - timedelta(days=7)
    recent_logs = [log.weight_kg for log in logs if log.log_date >= week_ago]

    weekly_avg = round(sum(recent_logs) / len(recent_logs), 2) if recent_logs else current_weight

    return WeightStatsResponse(
        current_weight=current_weight,
        target_weight=target_weight,
        weekly_average=weekly_avg,
        history=logs[:14] # Επιστροφή των τελευταίων 14 ημερών για γράφημα/λίστα
    )