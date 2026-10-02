from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import date, timedelta

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, UserProfile, WeightLog
from app.schemas.weight import WeightCreate, WeightResponse, WeightStatsResponse

router = APIRouter()


@router.post("/", response_model=WeightResponse)
async def log_weight(
    payload: WeightCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(WeightLog).where(
        WeightLog.user_id == current_user.id,
        WeightLog.log_date == payload.log_date,
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        existing.weight_kg = payload.weight_kg
        await db.commit()
        await db.refresh(existing)
        return existing

    new_log = WeightLog(
        user_id=current_user.id,
        weight_kg=payload.weight_kg,
        log_date=payload.log_date,
    )
    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)
    return new_log


@router.get("/stats", response_model=WeightStatsResponse)
async def get_weight_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Ανάκτηση όλων των καταγραφών βάρους του χρήστη (πιο πρόσφατες πρώτες)
    query = select(WeightLog).where(
        WeightLog.user_id == current_user.id
    ).order_by(desc(WeightLog.log_date))

    result = await db.execute(query)
    logs = result.scalars().all()

    # 2. Ανάκτηση UserProfile για current και target weight
    profile_query = select(UserProfile).where(UserProfile.user_id == current_user.id)
    profile_res = await db.execute(profile_query)
    profile = profile_res.scalar_one_or_none()

    current_weight = (
        float(logs[0].weight_kg)
        if logs
        else (float(profile.current_weight_kg) if profile else None)
    )
    target_weight = float(profile.target_weight_kg) if profile else None

    # 3. Υπολογισμός εβδομαδιαίου μέσου όρου (τελευταίες 7 ημέρες)
    today = date.today()
    week_ago = today - timedelta(days=7)
    recent_logs = [float(log.weight_kg) for log in logs if log.log_date >= week_ago]

    weekly_avg = (
        round(sum(recent_logs) / len(recent_logs), 2)
        if recent_logs
        else current_weight
    )

    return WeightStatsResponse(
        current_weight=current_weight,
        target_weight=target_weight,
        weekly_average=weekly_avg,
        history=logs[:14],
    )