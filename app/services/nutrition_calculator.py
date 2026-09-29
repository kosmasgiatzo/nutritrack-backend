from datetime import date

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,        # Καθιστική ζωή / γραφείο
    "light": 1.375,          # 1-3 φορές άσκηση/εβδομάδα
    "moderate": 1.55,        # 3-5 φορές άσκηση/εβδομάδα
    "active": 1.725,         # 6-7 φορές έντονη άσκηση
    "very_active": 1.9       # Διπλές προπονήσεις / χειρωνακτική εργασία
}

def calculate_age(birth_date: date) -> int:
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def calculate_targets(
    gender: str,
    birth_date: date,
    height_cm: float,
    weight_kg: float,
    activity_level: str,
    goal: str
) -> dict:
    age = calculate_age(birth_date)
    
    # 1. BMR (Mifflin-St Jeor)
    if gender.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

    # 2. TDEE
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    tdee = bmr * multiplier

    # 3. Προσαρμογή βάσει στόχου
    if goal == "lose_weight":
        calorie_target = round(tdee - 500)
    elif goal == "gain_muscle":
        calorie_target = round(tdee + 300)
    else:  # maintain
        calorie_target = round(tdee)

    # 4. Κατανομή Macros
    # Πρωτεΐνη: 2.0g ανά κιλό βάρους (4 kcal / g)
    protein_g = round(weight_kg * 2.0)
    protein_cals = protein_g * 4

    # Λιπαρά: 25% των συνολικών θερμίδων (9 kcal / g)
    fat_cals = calorie_target * 0.25
    fat_g = round(fat_cals / 9)

    # Υδατάνθρακες: Οι υπόλοιπες θερμίδες (4 kcal / g)
    carb_cals = max(0, calorie_target - (protein_cals + fat_cals))
    carbs_g = round(carb_cals / 4)

    return {
        "daily_calorie_target": calorie_target,
        "protein_target_g": protein_g,
        "carbs_target_g": carbs_g,
        "fat_target_g": fat_g
    }