import uuid
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field

class ProfileBase(BaseModel):
    gender: Literal["male", "female", "other"]
    birth_date: date
    height_cm: float = Field(gt=50, lt=260, description="Ύψος σε εκατοστά")
    current_weight_kg: float = Field(gt=20, lt=350, description="Τρέχον βάρος σε κιλά")
    target_weight_kg: float = Field(gt=20, lt=350, description="Στόχος βάρους σε κιλά")
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"]
    goal: Literal["lose_weight", "maintain", "gain_muscle"]

class ProfileCreate(ProfileBase):
    pass

class ProfileResponse(ProfileBase):
    user_id: uuid.UUID
    daily_calorie_target: int
    protein_target_g: int
    carbs_target_g: int
    fat_target_g: int
    updated_at: datetime

    class Config:
        from_attributes = True