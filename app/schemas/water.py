from pydantic import BaseModel, Field
from datetime import date

class WaterUpdate(BaseModel):
    log_date: date
    amount_ml: int = Field(ge=0, description="Ποσότητα νερού σε ml")

class WaterResponse(BaseModel):
    log_date: date
    amount_ml: int

    class Config:
        from_attributes = True