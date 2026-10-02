import uuid
from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional, List

class WeightCreate(BaseModel):
    weight_kg: float
    log_date: date

class WeightResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    weight_kg: float
    log_date: date

    model_config = ConfigDict(from_attributes=True)

class WeightStatsResponse(BaseModel):
    current_weight: Optional[float] = None
    target_weight: Optional[float] = None
    weekly_average: Optional[float] = None
    history: List[WeightResponse] = []

    model_config = ConfigDict(from_attributes=True)