from difflib import get_close_matches
from .models import MetaIngredient, Ingredient

def map_ingredients_to_meta():
    meta_ingredients = [meta.name for meta in MetaIngredient.objects.all()]

    # If no meta ingredients exist, populate with a default list
    if not meta_ingredients:
        default_meta = ["pepper", "salt", "sugar", "garlic"]
        MetaIngredient.objects.bulk_create([MetaIngredient(name=name) for name in default_meta])
        meta_ingredients = default_meta

    ingredients = Ingredient.objects.all()

    for ingredient in ingredients:
        normalized_text = ingredient.ingredient_text.strip().lower()

        # Match with meta ingredients
        match = get_close_matches(normalized_text, meta_ingredients, n=1, cutoff=0.8)

        if match:
            matched_meta = match[0]
        else:
            # If no close match is found, add the normalized ingredient to meta
            matched_meta = normalized_text
            MetaIngredient.objects.get_or_create(name=matched_meta)

        # Update Ingredient with matched meta ingredient (if needed)
        print(f"Mapping {ingredient.ingredient_text} to {matched_meta}")