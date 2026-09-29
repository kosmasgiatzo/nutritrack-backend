from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, UserProfile
from app.schemas.profile import ProfileCreate, ProfileResponse
from app.services.nutrition_calculator import calculate_targets

router = APIRouter()

@router.post("/", response_model=ProfileResponse)
async def setup_or_update_profile(
    profile_in: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Αυτόματος υπολογισμός Macros & Calories
    targets = calculate_targets(
        gender=profile_in.gender,
        birth_date=profile_in.birth_date,
        height_cm=profile_in.height_cm,
        weight_kg=profile_in.current_weight_kg,
        activity_level=profile_in.activity_level,
        goal=profile_in.goal
    )

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.scalars().first()

    if profile:
        # Ενημέρωση υπάρχοντος προφίλ
        for key, value in profile_in.model_dump().items():
            setattr(profile, key, value)
        for key, value in targets.items():
            setattr(profile, key, value)
    else:
        # Δημιουργία νέου προφίλ
        profile = UserProfile(
            user_id=current_user.id,
            **profile_in.model_dump(),
            **targets
        )
        db.add(profile)

    await db.commit()
    await db.refresh(profile)
    return profile

@router.get("/", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please complete onboarding first."
        )
    return profile