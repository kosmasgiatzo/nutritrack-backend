import uuid
from datetime import date, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, WeightLog, UserProfile
from app.schemas.weight import WeightCreate, WeightResponse, WeightStatsResponse

router = APIRouter()


@router.post("/", response_model=WeightResponse, status_code=status.HTTP_200_OK)
def log_weight(
    weight_in: WeightCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Έλεγχος αν υπάρχει ήδη καταγραφή για αυτή την ημέρα (Upsert)
    existing_log = (
        db.query(WeightLog)
        .filter(
            WeightLog.user_id == current_user.id,
            WeightLog.log_date == weight_in.log_date,
        )
        .first()
    )

    if existing_log:
        existing_log.weight_kg = weight_in.weight_kg
        db.commit()
        db.refresh(existing_log)
        return existing_log

    # 2. Αν όχι, δημιουργία νέας καταγραφής
    new_log = WeightLog(
        user_id=current_user.id,
        log_date=weight_in.log_date,
        weight_kg=weight_in.weight_kg,
    )
    db.add(new_log)

    # Προαιρετικά: Ενημέρωση και του τρέχοντος βάρους στο προφίλ αν η μέτρηση είναι σημερινή
    if weight_in.log_date == date.today() and current_user.profile:
        current_user.profile.current_weight_kg = weight_in.weight_kg

    db.commit()
    db.refresh(new_log)
    return new_log


@router.get("/stats", response_model=WeightStatsResponse)
def get_weight_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Ιστορικό βάρους (ταξινομημένο από το πιο πρόσφατο)
    history = (
        db.query(WeightLog)
        .filter(WeightLog.user_id == current_user.id)
        .order_by(WeightLog.log_date.desc())
        .limit(30)
        .all()
    )

    current_weight = float(history[0].weight_kg) if history else None
    target_weight = (
        float(current_user.profile.target_weight_kg)
        if current_user.profile and current_user.profile.target_weight_kg
        else None
    )

    # 2. Εβδομαδιαίος Μέσος Όρος (τελευταίες 7 ημέρες)
    seven_days_ago = date.today() - timedelta(days=7)
    recent_logs = [log for log in history if log.log_date >= seven_days_ago]
    
    weekly_avg = None
    if recent_logs:
        weekly_avg = round(sum(float(log.weight_kg) for log in recent_logs) / len(recent_logs), 2)

    return WeightStatsResponse(
        current_weight=current_weight,
        target_weight=target_weight,
        weekly_average=weekly_avg,
        history=history,
    )