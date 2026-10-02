from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class WeightCreate(BaseModel):
    weight_kg: float
    log_date: date

class WeightResponse(BaseModel):
    id: int
    weight_kg: float
    log_date: date

    class Config:
        from_attributes = True

class WeightStatsResponse(BaseModel):
    current_weight: Optional[float] = None
    target_weight: Optional[float] = None
    weekly_average: Optional[float] = None
    history: List[WeightResponse] = []