import uuid
from datetime import date, datetime
from typing import Literal, List
from pydantic import BaseModel, Field

class MealLogCreate(BaseModel):
    food_id: uuid.UUID
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    log_date: date
    amount_grams: float = Field(gt=0, description="Ποσότητα σε γραμμάρια")

class MealLogUpdate(BaseModel):
    amount_grams: float | None = Field(default=None, gt=0)
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] | None = None

class MealLogItemResponse(BaseModel):
    id: uuid.UUID
    food_id: uuid.UUID
    food_name: str
    meal_type: str
    log_date: date
    amount_grams: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    created_at: datetime

    class Config:
        from_attributes = True

class DailySummaryResponse(BaseModel):
    date: date
    calorie_target: int
    calories_consumed: float
    calories_remaining: float
    protein_target_g: int
    protein_consumed: float
    carbs_target_g: int
    carbs_consumed: float
    fat_target_g: int
    fat_consumed: float
    meals: List[MealLogItemResponse]