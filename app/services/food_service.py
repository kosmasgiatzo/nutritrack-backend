import json
import httpx
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.models import Food

OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/api/v2/product"

async def get_redis_client() -> Redis:
    return Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

async def fetch_food_by_barcode(barcode: str, db: AsyncSession) -> dict | None:
    redis = await get_redis_client()
    cache_key = f"food:barcode:{barcode}"

    # 1. Έλεγχος στο Redis Cache
    cached_data = await redis.get(cache_key)
    if cached_data:
        await redis.close()
        return json.loads(cached_data)

    # 2. Έλεγχος στην PostgreSQL
    result = await db.execute(select(Food).where(Food.barcode == barcode))
    local_food = result.scalars().first()
    if local_food:
        food_dict = {
            "name": local_food.name,
            "brand": local_food.brand,
            "barcode": local_food.barcode,
            "calories_100g": float(local_food.calories_100g),
            "protein_100g": float(local_food.protein_100g),
            "carbs_100g": float(local_food.carbs_100g),
            "fat_100g": float(local_food.fat_100g),
            "fiber_100g": float(local_food.fiber_100g or 0),
            "source": "local_database"
        }
        await redis.set(cache_key, json.dumps(food_dict), ex=86400)
        await redis.close()
        return food_dict

    # 3. Κλήση στο Open Food Facts API
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{OPEN_FOOD_FACTS_URL}/{barcode}.json")
        if response.status_code != 200:
            await redis.close()
            return None

        data = response.json()
        if data.get("status") != 1:
            await redis.close()
            return None

        product = data.get("product", {})
        nutriments = product.get("nutriments", {})

        food_name = product.get("product_name", "Unknown Product")
        brand = product.get("brands", "Generic")
        calories = nutriments.get("energy-kcal_100g", nutriments.get("energy-kcal", 0.0))
        protein = nutriments.get("proteins_100g", 0.0)
        carbs = nutriments.get("carbohydrates_100g", 0.0)
        fat = nutriments.get("fat_100g", 0.0)
        fiber = nutriments.get("fiber_100g", 0.0)

        new_food = Food(
            name=food_name,
            brand=brand,
            barcode=barcode,
            calories_100g=float(calories or 0.0),
            protein_100g=float(protein or 0.0),
            carbs_100g=float(carbs or 0.0),
            fat_100g=float(fat or 0.0),
            fiber_100g=float(fiber or 0.0),
            is_verified=True
        )
        db.add(new_food)
        await db.commit()
        await db.refresh(new_food)

        food_dict = {
            "id": str(new_food.id),
            "name": new_food.name,
            "brand": new_food.brand,
            "barcode": new_food.barcode,
            "calories_100g": float(new_food.calories_100g),
            "protein_100g": float(new_food.protein_100g),
            "carbs_100g": float(new_food.carbs_100g),
            "fat_100g": float(new_food.fat_100g),
            "fiber_100g": float(new_food.fiber_100g),
            "source": "open_food_facts"
        }

        await redis.set(cache_key, json.dumps(food_dict), ex=86400)
        await redis.close()
        return food_dict

async def search_foods_by_query(query: str, db: AsyncSession, limit: int = 10) -> list[dict]:
    clean_query = query.strip()
    if not clean_query:
        return []

    # 1. Αναζήτηση στην τοπική PostgreSQL
    stmt = (
        select(Food)
        .where(Food.name.ilike(f"%{clean_query}%"))
        .limit(limit)
    )
    res = await db.execute(stmt)
    local_foods = res.scalars().all()

    results = [
        {
            "id": str(food.id),
            "name": food.name,
            "brand": food.brand,
            "barcode": food.barcode,
            "calories_100g": float(food.calories_100g),
            "protein_100g": float(food.protein_100g),
            "carbs_100g": float(food.carbs_100g),
            "fat_100g": float(food.fat_100g),
            "fiber_100g": float(food.fiber_100g or 0.0),
            "source": "local_database"
        }
        for food in local_foods
    ]

    if len(results) >= limit:
        return results

    # 2. Αναζήτηση στο Open Food Facts API αν χρειάζονται κι άλλα αποτελέσματα
    search_url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": clean_query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": limit - len(results)
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(search_url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                products = data.get("products", [])

                for item in products:
                    nutriments = item.get("nutriments", {})
                    name = item.get("product_name")
                    if not name:
                        continue

                    barcode = item.get("code")
                    brand = item.get("brands", "Generic")
                    calories = nutriments.get("energy-kcal_100g", nutriments.get("energy-kcal", 0.0))
                    protein = nutriments.get("proteins_100g", 0.0)
                    carbs = nutriments.get("carbohydrates_100g", 0.0)
                    fat = nutriments.get("fat_100g", 0.0)
                    fiber = nutriments.get("fiber_100g", 0.0)

                    new_food = None
                    if barcode:
                        existing = await db.execute(select(Food).where(Food.barcode == barcode))
                        if not existing.scalars().first():
                            new_food = Food(
                                name=name,
                                brand=brand,
                                barcode=barcode,
                                calories_100g=float(calories or 0.0),
                                protein_100g=float(protein or 0.0),
                                carbs_100g=float(carbs or 0.0),
                                fat_100g=float(fat or 0.0),
                                fiber_100g=float(fiber or 0.0),
                                is_verified=True
                            )
                            db.add(new_food)
                            await db.commit()
                            await db.refresh(new_food)

                    results.append({
                        "id": str(new_food.id) if new_food else None,
                        "name": name,
                        "brand": brand,
                        "barcode": barcode,
                        "calories_100g": float(calories or 0.0),
                        "protein_100g": float(protein or 0.0),
                        "carbs_100g": float(carbs or 0.0),
                        "fat_100g": float(fat or 0.0),
                        "fiber_100g": float(fiber or 0.0),
                        "source": "open_food_facts"
                    })
    except Exception:
        pass

    return results