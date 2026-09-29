from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User
from app.services.food_service import fetch_food_by_barcode, search_foods_by_query

router = APIRouter()

@router.get("/search")
async def search_foods(
    q: str = Query(..., min_length=2, description="Όρος αναζήτησης τροφίμου"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    results = await search_foods_by_query(query=q, db=db, limit=limit)
    return results

@router.get("/barcode/{barcode}")
async def get_by_barcode(
    barcode: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    food_data = await fetch_food_by_barcode(barcode, db)
    if not food_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food product not found"
        )
    return food_data