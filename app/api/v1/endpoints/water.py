from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, WaterIntake
from app.schemas.water import WaterUpdate, WaterResponse

router = APIRouter()

@router.get("/{log_date}", response_model=WaterResponse)
async def get_water_intake(
    log_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(WaterIntake).where(
        WaterIntake.user_id == current_user.id,
        WaterIntake.log_date == log_date
    )
    result = await db.execute(query)
    record = result.scalars().first()

    if not record:
        return WaterResponse(log_date=log_date, amount_ml=0)

    return record


@router.post("/", response_model=WaterResponse)
async def set_or_update_water(
    water_in: WaterUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(WaterIntake).where(
        WaterIntake.user_id == current_user.id,
        WaterIntake.log_date == water_in.log_date
    )
    result = await db.execute(query)
    record = result.scalars().first()

    if record:
        record.amount_ml = water_in.amount_ml
    else:
        record = WaterIntake(
            user_id=current_user.id,
            log_date=water_in.log_date,
            amount_ml=water_in.amount_ml
        )
        db.add(record)

    await db.commit()
    await db.refresh(record)
    return record