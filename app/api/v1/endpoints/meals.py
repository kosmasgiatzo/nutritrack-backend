import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas.meal_log import (
    MealLogCreate, 
    MealLogUpdate, 
    MealLogItemResponse, 
    DailySummaryResponse
)

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Food, MealLog, UserProfile
from app.schemas.meal_log import MealLogCreate, MealLogItemResponse, DailySummaryResponse

router = APIRouter()

@router.post("/", response_model=MealLogItemResponse, status_code=status.HTTP_201_CREATED)
async def log_meal(
    meal_in: MealLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    target_food_id = meal_in.food_id if isinstance(meal_in.food_id, uuid.UUID) else uuid.UUID(str(meal_in.food_id))

    result = await db.execute(select(Food).where(Food.id == target_food_id))
    food = result.scalars().first()
    if not food:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food item not found")

    factor = float(meal_in.amount_grams) / 100.0
    calories = round(float(food.calories_100g) * factor, 1)
    protein = round(float(food.protein_100g) * factor, 1)
    carbs = round(float(food.carbs_100g) * factor, 1)
    fat = round(float(food.fat_100g) * factor, 1)
    fiber = round(float(food.fiber_100g or 0.0) * factor, 1)

    meal_log = MealLog(
        user_id=current_user.id,
        food_id=food.id,
        meal_type=meal_in.meal_type,
        log_date=meal_in.log_date,
        total_grams=float(meal_in.amount_grams),
        servings_consumed=round(factor, 2),
        calories=calories,
        protein_g=protein,
        carbs_g=carbs,
        fat_g=fat
    )
    db.add(meal_log)
    await db.commit()
    await db.refresh(meal_log)

    return MealLogItemResponse(
        id=meal_log.id,
        food_id=food.id,
        food_name=food.name,
        meal_type=meal_log.meal_type,
        log_date=meal_log.log_date,
        amount_grams=float(meal_log.total_grams),
        calories=float(meal_log.calories),
        protein_g=float(meal_log.protein_g),
        carbs_g=float(meal_log.carbs_g),
        fat_g=float(meal_log.fat_g),
        fiber_g=fiber,
        created_at=meal_log.created_at
    )

@router.get("/daily/{log_date}", response_model=DailySummaryResponse)
async def get_daily_summary(
    log_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile_res = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = profile_res.scalars().first()
    
    cal_target = profile.daily_calorie_target if profile else 2000
    protein_target = profile.protein_target_g if profile else 150
    carbs_target = profile.carbs_target_g if profile else 200
    fat_target = profile.fat_target_g if profile else 65

    stmt = (
        select(MealLog, Food.name, Food.fiber_100g)
        .join(Food, MealLog.food_id == Food.id)
        .where(MealLog.user_id == current_user.id, MealLog.log_date == log_date)
    )
    result = await db.execute(stmt)
    records = result.all()

    meals_list = []
    total_cals = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0

    for log, food_name, food_fiber_100g in records:
        total_cals += float(log.calories)
        total_protein += float(log.protein_g)
        total_carbs += float(log.carbs_g)
        total_fat += float(log.fat_g)

        factor = float(log.total_grams) / 100.0
        calculated_fiber = round(float(food_fiber_100g or 0.0) * factor, 1)

        meals_list.append(
            MealLogItemResponse(
                id=log.id,
                food_id=log.food_id,
                food_name=food_name,
                meal_type=log.meal_type,
                log_date=log.log_date,
                amount_grams=float(log.total_grams),
                calories=float(log.calories),
                protein_g=float(log.protein_g),
                carbs_g=float(log.carbs_g),
                fat_g=float(log.fat_g),
                fiber_g=calculated_fiber,
                created_at=log.created_at
            )
        )

    return DailySummaryResponse(
        date=log_date,
        calorie_target=cal_target,
        calories_consumed=round(total_cals, 1),
        calories_remaining=round(cal_target - total_cals, 1),
        protein_target_g=protein_target,
        protein_consumed=round(total_protein, 1),
        carbs_target_g=carbs_target,
        carbs_consumed=round(total_carbs, 1),
        fat_target_g=fat_target,
        fat_consumed=round(total_fat, 1),
        meals=meals_list
    )
@router.delete("/{meal_log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_log(
    meal_log_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MealLog).where(
            MealLog.id == meal_log_id,
            MealLog.user_id == current_user.id
        )
    )
    meal_log = result.scalars().first()
    if not meal_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal log entry not found")

    await db.delete(meal_log)
    await db.commit()
    return None

@router.patch("/{meal_log_id}", response_model=MealLogItemResponse)
async def update_meal_log(
    meal_log_id: uuid.UUID,
    update_data: MealLogUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(MealLog, Food)
        .join(Food, MealLog.food_id == Food.id)
        .where(MealLog.id == meal_log_id, MealLog.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal log entry not found")
    
    meal_log, food = row

    if update_data.meal_type:
        meal_log.meal_type = update_data.meal_type

    if update_data.amount_grams is not None:
        factor = float(update_data.amount_grams) / 100.0
        meal_log.total_grams = float(update_data.amount_grams)
        meal_log.servings_consumed = round(factor, 2)
        meal_log.calories = round(float(food.calories_100g) * factor, 1)
        meal_log.protein_g = round(float(food.protein_100g) * factor, 1)
        meal_log.carbs_g = round(float(food.carbs_100g) * factor, 1)
        meal_log.fat_g = round(float(food.fat_100g) * factor, 1)

    await db.commit()
    await db.refresh(meal_log)

    fiber_factor = float(meal_log.total_grams) / 100.0
    calculated_fiber = round(float(food.fiber_100g or 0.0) * fiber_factor, 1)

    return MealLogItemResponse(
        id=meal_log.id,
        food_id=food.id,
        food_name=food.name,
        meal_type=meal_log.meal_type,
        log_date=meal_log.log_date,
        amount_grams=float(meal_log.total_grams),
        calories=float(meal_log.calories),
        protein_g=float(meal_log.protein_g),
        carbs_g=float(meal_log.carbs_g),
        fat_g=float(meal_log.fat_g),
        fiber_g=calculated_fiber,
        created_at=meal_log.created_at
    )