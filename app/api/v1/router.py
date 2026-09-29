from fastapi import APIRouter
from app.api.v1.endpoints import auth, profile, foods, meals, water

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profile.router, prefix="/profile", tags=["User Profile & Targets"])
api_router.include_router(foods.router, prefix="/foods", tags=["Foods & Barcode"])
api_router.include_router(meals.router, prefix="/meals", tags=["Meal Tracking"])
api_router.include_router(water.router, prefix="/water", tags=["water"])