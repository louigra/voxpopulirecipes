#import the packages i need

from openai import OpenAI

client = OpenAI()


import json

import boto3

import requests


from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.template import loader
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from collections import defaultdict
from firecrawl import FirecrawlApp

from django.core.files.storage import default_storage

from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional


from django.conf import settings

from django.utils.timezone import now


from PIL import Image

import io



# import pagination stuff
from django.core.paginator import Paginator
from django.db.models import F

# import the models i need
from .models import Recipe, Ingredient, Instruction, User, RecipeNote, Rating, CookedInstance, MealType, Cuisine, SavedRecipe, StarredRecipe, MealTypeMap, CuisineMap

def main(request):
    lastest_recipe_list = Recipe.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:4]
    all_recipes = Recipe.objects.all().order_by("id")
    all_unique_ingredients = Ingredient.objects.values_list("ingredient_text", flat=True).distinct().order_by("ingredient_text")
    template = loader.get_template("voxpopulirecipes/main.html")
    context = {
        "latest_recipe_list": lastest_recipe_list,
        "all_recipes": all_recipes,
        "all_unique_ingredients": all_unique_ingredients
    }
    return HttpResponse(template.render(context, request))

def detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
        # Calculate the mean rating
    mean_rating = Rating.objects.filter(recipe=recipe).aggregate(Avg('rating'))['rating__avg'] or 0

    # Calculate the average cook time
    average_cook_time = CookedInstance.objects.filter(recipe=recipe).aggregate(Avg('cook_time'))['cook_time__avg'] or 0

    # Check if the user has saved the recipe
    saved = False
    if request.user.is_authenticated:
        saved = SavedRecipe.objects.filter(user=request.user, recipe=recipe).exists()

    # Check if the user has starred the recipe
    starred = False
    if request.user.is_authenticated:
        starred = StarredRecipe.objects.filter(user=request.user, recipe=recipe).exists()
        
    mealTypes = MealTypeMap.objects.filter(recipe = recipe)
    cuisines = CuisineMap.objects.filter(recipe = recipe)

    return render(request, "voxpopulirecipes/recipe.html", {
        "recipe": recipe,
        "mean_rating": mean_rating,
        "average_cook_time": average_cook_time,
        "saved": saved,
        "starred": starred,
        "mealTypes": mealTypes,
        "cuisines": cuisines
        })

def submit_recipe(request, recipe_id=None):
    mealtypes = MealType.objects.all().order_by('name')
    cuisines = Cuisine.objects.all().order_by('name')
    

    # If editing, fetch the recipe object
    if recipe_id:
        recipe = get_object_or_404(Recipe, id=recipe_id)
    else:
        recipe = None

    if request.method == 'POST':
        recipe_title = request.POST.get('title')
        recipe_image = request.FILES.get('image')  # Get the uploaded image file
        # Get the selected meal types and cuisines (can be multiple)
        selected_mealtypes = request.POST.getlist('mealtypes')  # Get a list of selected meal type IDs
        selected_cuisines = request.POST.getlist('cuisines')    # Get a list of selected cuisine IDs

        # Check if the title is provided
        if recipe_title:
            if recipe:
                # Update existing mappings
                MealTypeMap.objects.filter(recipe=recipe).delete()
                CuisineMap.objects.filter(recipe=recipe).delete()
                # If editing, update the existing recipe
                recipe.title = recipe_title
                if recipe_image:
                    recipe.image = recipe_image  # Update the image if a new one is uploaded
                for mealtype_id in selected_mealtypes:
                    MealTypeMap.objects.create(recipe=recipe, mealType_id=mealtype_id)
                for cuisine_id in selected_cuisines:
                    CuisineMap.objects.create(recipe=recipe, cuisine_id=cuisine_id)
                recipe.save()

                # Handle deleted ingredients and instructions
                deleted_ingredients = request.POST.get('deleted_ingredients', '').split(',')
                deleted_ingredients = [ingredient_id for ingredient_id in deleted_ingredients if ingredient_id]
                if deleted_ingredients:
                    Ingredient.objects.filter(id__in=deleted_ingredients, recipe=recipe).delete()

                deleted_instructions = request.POST.get('deleted_instructions', '').split(',')
                deleted_instructions = [instruction_id for instruction_id in deleted_instructions if instruction_id]
                if deleted_instructions:
                    Instruction.objects.filter(id__in=deleted_instructions, recipe=recipe).delete()
            else:
                # If creating a new recipe
                recipe = Recipe.objects.create(
                    title=recipe_title,
                    image=recipe_image,  # Set the uploaded image
                    pub_date=timezone.now(),
                    creator=request.user,
                )
                for mealtype_id in selected_mealtypes:
                    MealTypeMap.objects.create(recipe=recipe, mealType_id=mealtype_id)
                for cuisine_id in selected_cuisines:
                    CuisineMap.objects.create(recipe=recipe, cuisine_id=cuisine_id)
                

            # Handle ingredients and instructions (same as your original logic)
            posted_ingredient_ids = [key.split('_')[-1] for key in request.POST if key.startswith('ingredient_text_')]
            if not posted_ingredient_ids:
                return render(request, 'voxpopulirecipes/submit_recipe.html', {
                    'error_message': 'Recipe must have at least one ingredient.',
                    'recipe': recipe,
                    'mealtypes': mealtypes,
                    'cuisines': cuisines
                })

            for ingredient_id in posted_ingredient_ids:
                ingredient_text = request.POST.get(f'ingredient_text_{ingredient_id}')
                ingredient_amount = request.POST.get(f'ingredient_amount_{ingredient_id}', '')
                ingredient_unit = request.POST.get(f'ingredient_unit_{ingredient_id}', '')

                if ingredient_text:
                    if ingredient_id.isdigit():
                        ingredient = Ingredient.objects.filter(recipe=recipe, id=ingredient_id).first()
                        if ingredient:
                            ingredient.ingredient_text = ingredient_text
                            ingredient.ingredient_amount = ingredient_amount
                            ingredient.ingredient_unit = ingredient_unit
                            ingredient.save()
                        else:
                            Ingredient.objects.create(
                                recipe=recipe,
                                ingredient_text=ingredient_text,
                                ingredient_amount=ingredient_amount,
                                ingredient_unit=ingredient_unit
                            )
                    else:
                        Ingredient.objects.create(
                            recipe=recipe,
                            ingredient_text=ingredient_text,
                            ingredient_amount=ingredient_amount,
                            ingredient_unit=ingredient_unit
                        )

            posted_instruction_ids = [key.split('_')[-1] for key in request.POST if key.startswith('instruction_text_')]
            if not posted_instruction_ids:
                return render(request, 'voxpopulirecipes/submit_recipe.html', {
                    'error_message': 'Recipe must have at least one instruction.',
                    'recipe': recipe,
                    'mealtypes': mealtypes,
                    'cuisines': cuisines
                })

            for instruction_id in posted_instruction_ids:
                instruction_text = request.POST.get(f'instruction_text_{instruction_id}')

                if instruction_text:
                    if instruction_id.isdigit():
                        instruction = Instruction.objects.filter(recipe=recipe, id=instruction_id).first()
                        if instruction:
                            instruction.instruction_text = instruction_text
                            instruction.save()
                        else:
                            Instruction.objects.create(
                                recipe=recipe,
                                instruction_text=instruction_text,
                                instruction_order=instruction_id
                            )
                    else:
                        Instruction.objects.create(
                            recipe=recipe,
                            instruction_text=instruction_text,
                            instruction_order=instruction_id
                        )

            # Redirect to the recipe detail page or success page
            return redirect('voxpopulirecipes:detail', recipe_id=recipe.id)
        else:
            return render(request, 'voxpopulirecipes/submit_recipe.html', {
                'error_message': 'Recipe name is required.',
                'recipe': recipe,
                'mealtypes': mealtypes,
                'cuisines': cuisines
            })

    # If it's a GET request, render the form

    return render(request, 'voxpopulirecipes/submit_recipe.html', {
        'recipe': recipe,
        'mealtypes': mealtypes,
        'cuisines': cuisines
        })

def random_recipe(request):
    random_recipe = Recipe.objects.order_by("?").first()
    if random_recipe:
        return redirect('voxpopulirecipes:detail', recipe_id=random_recipe.id)
    else:
        return redirect('voxpopulirecipes:main')

def edit_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    mealtypes = MealType.objects.all().order_by('name')
    cuisines = Cuisine.objects.all().order_by('name')

    # Get the IDs of meal types and cuisines mapped to the recipe
    mapped_mealtypes = MealTypeMap.objects.filter(recipe=recipe).values_list('mealType_id', flat=True)
    mapped_cuisines = CuisineMap.objects.filter(recipe=recipe).values_list('cuisine_id', flat=True)

    return render(request, 'voxpopulirecipes/submit_recipe.html', {
        'recipe': recipe,
        'mealtypes': mealtypes,
        'cuisines': cuisines,
        'mapped_mealtypes': mapped_mealtypes,
        'mapped_cuisines': mapped_cuisines,
    })

def delete_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    recipe.delete()
    return redirect('voxpopulirecipes:main')

def search_recipe(request):
    search_text = ""
    if request.method == "POST":
        search_text = request.POST.get("search_text")
    all_recipes = Recipe.objects.all().order_by("id")
    all_unique_ingredients = Ingredient.objects.values_list("ingredient_text", flat=True).distinct().order_by("ingredient_text")
    template = loader.get_template("voxpopulirecipes/search.html")
    context = {
        "all_recipes": all_recipes,
        "all_unique_ingredients": all_unique_ingredients,
        "search_text": search_text,
    }
    return HttpResponse(template.render(context, request))

def all_recipes(request):
    template = loader.get_template("voxpopulirecipes/all_recipes.html")

    # set up pagination
    p = Paginator(Recipe.objects.all(), 20)
    page = request.GET.get('page')
    recipes = p.get_page(page)

    context = {
        "recipes": recipes
    }
    return HttpResponse(template.render(context, request))




from collections import defaultdict

from itertools import chain

def my_recipes(request):
    # Get the recipes created by the user
    recipes = Recipe.objects.filter(creator=request.user).order_by("pub_date")
    
    # Get saved recipes for the user
    saved_recipe_ids = SavedRecipe.objects.filter(user=request.user).values_list("recipe", flat=True)
    saved_recipes = Recipe.objects.filter(id__in=saved_recipe_ids).order_by("pub_date")

    # Get starred recipes for the user
    starred_recipes = list(
        Recipe.objects.filter(
            id__in=StarredRecipe.objects.filter(user=request.user).values_list("recipe", flat=True)
        )
    )
    starred_recipe_ids = list(
        StarredRecipe.objects.filter(user=request.user).order_by("-date_starred").values_list("recipe_id", flat=True)
    )

    # Sort starred recipes by the order of `starred_recipe_ids`
    starred_recipes.sort(key=lambda recipe: starred_recipe_ids.index(recipe.id))

    # Combine all recipes (user's recipes and starred recipes)
    all_recipes = list(set(chain(recipes, starred_recipes)))

    # MealType and Cuisine mapping for user's and starred recipes
    flattened_mealtypes = [
        {"recipe_id": recipe.id, "mealtypes": MealTypeMap.objects.filter(recipe=recipe).select_related("mealType")}
        for recipe in all_recipes
    ]
    
    flattened_cuisines = [
        {"recipe_id": recipe.id, "cuisines": CuisineMap.objects.filter(recipe=recipe).select_related("cuisine")}
        for recipe in all_recipes
    ]
    
    # MealType and Cuisine mapping for user's recipes only
    mealtype_cuisine_map = defaultdict(lambda: defaultdict(list))
    for recipe in recipes:
        mealtypes = MealType.objects.filter(id__in=MealTypeMap.objects.filter(recipe=recipe).values_list("mealType_id", flat=True))
        cuisines = Cuisine.objects.filter(id__in=CuisineMap.objects.filter(recipe=recipe).values_list("cuisine_id", flat=True))
        
        for mealtype in mealtypes:
            for cuisine in cuisines:
                mealtype_cuisine_map[mealtype][cuisine].append(recipe)

    mealtype_cuisine_map = {
        mealtype: {
            cuisine: sorted(recipe_list, key=lambda r: r.pub_date)
            for cuisine, recipe_list in sorted(cuisines.items(), key=lambda c: c[0].name)
        }
        for mealtype, cuisines in sorted(mealtype_cuisine_map.items(), key=lambda mt: mt[0].name)
    }

    # MealType and Cuisine mapping for saved recipes
    saved_mealtype_cuisine_map = defaultdict(lambda: defaultdict(list))
    for recipe in saved_recipes:
        mealtypes = MealType.objects.filter(id__in=MealTypeMap.objects.filter(recipe=recipe).values_list("mealType_id", flat=True))
        cuisines = Cuisine.objects.filter(id__in=CuisineMap.objects.filter(recipe=recipe).values_list("cuisine_id", flat=True))
        
        for mealtype in mealtypes:
            for cuisine in cuisines:
                saved_mealtype_cuisine_map[mealtype][cuisine].append(recipe)

    saved_mealtype_cuisine_map = {
        mealtype: {
            cuisine: sorted(recipe_list, key=lambda r: r.pub_date)
            for cuisine, recipe_list in sorted(cuisines.items(), key=lambda c: c[0].name)
        }
        for mealtype, cuisines in sorted(saved_mealtype_cuisine_map.items(), key=lambda mt: mt[0].name)
    }

    context = {
        "recipes": recipes,
        "mealtype_cuisine_map": mealtype_cuisine_map,
        "saved_mealtype_cuisine_map": saved_mealtype_cuisine_map,
        "starred_recipes": starred_recipes,
        "recipe_mealtypes": flattened_mealtypes,
        "recipe_cuisines": flattened_cuisines,
    }
    return render(request, "voxpopulirecipes/my_recipes.html", context)

def about(request):
    return render(request, "voxpopulirecipes/about.html")

@login_required
@csrf_exempt
def add_note(request, recipe_id):
    if request.method == "POST":
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            note_data = json.loads(request.body)
            note_text = note_data.get("noteText", "").strip()
            note_order = note_data.get("noteOrder", 1)

            if not note_text:
                return JsonResponse(
                    {"success": False, "error": "Note text cannot be empty."}, status=400
                )

            # Create the note
            RecipeNote.objects.create(
                recipe=recipe,
                creator=request.user,  # Assumes request.user is available
                note_text=note_text,
                note_order=note_order,
                note_date=timezone.now(),
            )
            return JsonResponse({"success": True})

        except Recipe.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Recipe not found."}, status=404
            )
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON format."}, status=400
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"An unexpected error occurred: {str(e)}"},
                status=500,
            )

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

def delete_note(request, note_id):
    note = get_object_or_404(RecipeNote, pk=note_id)
    recipe_id = note.recipe.id
    note.delete()
    return redirect('voxpopulirecipes:detail', recipe_id=recipe_id)



def check_review_status(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    has_reviewed = Rating.objects.filter(recipe=recipe, rater=request.user).exists()
    return JsonResponse({"has_reviewed": has_reviewed})

def submit_review(request, recipe_id):
    if request.method == "POST":
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        user = request.user
        cook_time = request.POST.get('cook_time', 0)
        rating = request.POST.get('rating', None)

        # Record cook time
        CookedInstance.objects.create(
            recipe=recipe, 
            creator=user, 
            date_cooked=timezone.now(), 
            cook_time=cook_time)

        # Record rating (if provided)
        if rating:
            Rating.objects.update_or_create(
                recipe=recipe,
                rater=user,
                defaults={
                    'rating': int(rating),
                    'rating_date': timezone.now()
                }
            )
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

def save_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    user = request.user
    exists = SavedRecipe.objects.filter(user=user, recipe=recipe).exists()
    if not exists:
        SavedRecipe.objects.create(user=user, recipe=recipe, date_saved=timezone.now())
        return JsonResponse({'success': True})
    else:
        SavedRecipe.objects.filter(user=user, recipe=recipe).delete()
        return JsonResponse({'success': True})

def star_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    user = request.user
    exists = StarredRecipe.objects.filter(user=user, recipe=recipe).exists()
    if not exists:
        StarredRecipe.objects.create(user=user, recipe=recipe, date_starred=timezone.now())
        return JsonResponse({'success': True})
    else:
        StarredRecipe.objects.filter(user=user, recipe=recipe).delete()
        return JsonResponse({'success': True})

def view_user_book(request, user_id):
    if user_id == request.user.id:
        return redirect("voxpopulirecipes:my_recipes")
    user_to_view = get_object_or_404(User, pk=user_id)

    recipes = Recipe.objects.filter(creator=user_to_view).order_by("pub_date")


    starred_recipes = list(
        Recipe.objects.filter(
            id__in=StarredRecipe.objects.filter(user=request.user).values_list("recipe", flat=True)
        )
    )
    starred_recipe_ids = list(
        StarredRecipe.objects.filter(user=request.user).order_by("-date_starred").values_list("recipe_id", flat=True)
    )

    # Sort the recipes in Python based on the reversed order of IDs
    starred_recipes.sort(key=lambda recipe: starred_recipe_ids.index(recipe.id))

    all_recipes = list(set(chain(recipes, starred_recipes)))
    
    
    
    saved_recipes = Recipe.objects.filter(id__in=SavedRecipe.objects.filter(user=request.user).values_list("recipe", flat=True)).order_by("pub_date")
    saved_recipe_ids = list(SavedRecipe.objects.filter(user=request.user).order_by("-date_saved").values_list("recipe_id", flat=True))

    
    
    flattened_mealtypes = [
        {"recipe_id": recipe.id, "mealtypes": MealTypeMap.objects.filter(recipe=recipe).select_related("mealType")}
        for recipe in all_recipes
    ]
    
    flattened_cuisines = [
        {"recipe_id": recipe.id, "cuisines": CuisineMap.objects.filter(recipe=recipe).select_related("cuisine")}
        for recipe in all_recipes
    ]
    # MealType and Cuisine mapping for user's recipes only
    mealtype_cuisine_map = defaultdict(lambda: defaultdict(list))
    for recipe in recipes:
        mealtypes = MealType.objects.filter(id__in=MealTypeMap.objects.filter(recipe=recipe).values_list("mealType_id", flat=True))
        cuisines = Cuisine.objects.filter(id__in=CuisineMap.objects.filter(recipe=recipe).values_list("cuisine_id", flat=True))
        
        for mealtype in mealtypes:
            for cuisine in cuisines:
                mealtype_cuisine_map[mealtype][cuisine].append(recipe)

    mealtype_cuisine_map = {
        mealtype: {
            cuisine: sorted(recipe_list, key=lambda r: r.pub_date)
            for cuisine, recipe_list in sorted(cuisines.items(), key=lambda c: c[0].name)
        }
        for mealtype, cuisines in sorted(mealtype_cuisine_map.items(), key=lambda mt: mt[0].name)
    }


    context = {
        "recipes": recipes,
        "mealtype_cuisine_map": mealtype_cuisine_map,
        "user_to_view": user_to_view,
        "saved_recipe_ids": saved_recipe_ids,
        "starred_recipe_ids": starred_recipe_ids,
        "recipe_mealtypes": flattened_mealtypes,
        "recipe_cuisines": flattened_cuisines,
    }

    return render(request, "voxpopulirecipes/view_user_book.html", context)

def submit_recipe_selector(request):
    return render(request, "voxpopulirecipes/submit_recipe_selector.html")

def submit_recipe_from_text(request):
    return render(request , "voxpopulirecipes/submit_recipe_from_text.html")

def submit_recipe_from_image(request):
    return render(request, "voxpopulirecipes/submit_recipe_from_image.html")

def submit_recipe_from_url(request):
    return render(request, "voxpopulirecipes/submit_recipe_from_url.html")

from openai import OpenAI

# Initialize S3 client
s3_client = boto3.client('s3')

def extract_text(request):
    """Handles OCR separately from OpenAI processing."""
    if request.method == "POST" and request.FILES.get("recipe_image"):
        try:
            recipe_image = request.FILES["recipe_image"]

            # Generate S3 path and save image
            timestamp = now().strftime("%Y%m%d%H%M%S")
            image_filename = f"recipes/{timestamp}_{recipe_image.name}"
            s3_path = f"media/{image_filename}"
            default_storage.save(s3_path, recipe_image)
            image_url = f"{settings.MEDIA_URL}{image_filename}"

            print("✅ Image successfully uploaded to S3:", image_url)

            # Extract text from image using OCR
            extracted_text = extract_text_from_s3(image_url)

            return JsonResponse({"extracted_text": extracted_text})

        except Exception as e:
            print("❌ Error during image upload or text extraction:", e)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "No image provided"}, status=400)


# Initialize FirecrawlApp with your API key
app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)

# Define schema to match Django models
class IngredientSchema(BaseModel):
    ingredient_text: str
    ingredient_amount: Optional[str] = ""
    ingredient_unit: Optional[str] = ""

class InstructionSchema(BaseModel):
    instruction_text: str
    instruction_order: int = Field(default=0)

class RecipeSchema(BaseModel):
    title: str
    created_by: Optional[str] = None
    mealType: Optional[str] = None
    cuisine: Optional[str] = None
    baking: bool = False
    ingredients: List[IngredientSchema]
    instructions: List[InstructionSchema]
    
def extract_recipe_from_url(request):
    if request.method == "POST":
        try:
            api_key = settings.FIRECRAWL_API_KEY  # Get API key from Django settings
            if not api_key:
                return JsonResponse({"error": "API key is missing"}, status=500)

            app = FirecrawlApp(api_key=api_key)
            website_url = request.POST.get("recipe_url", "").strip()

            if website_url:
                # Request structured JSON data from Firecrawl
                response = app.scrape_url(website_url, {
                    "formats": ["json"],
                    "jsonOptions": {
                        "schema": RecipeSchema.model_json_schema(),
                    }
                })

                if "json" not in response:
                    return JsonResponse({"error": "Invalid Firecrawl response format"}, status=500)

                recipe_data = response["json"]

                # Validate JSON data against Pydantic schema
                try:
                    parsed_recipe = RecipeSchema(**recipe_data)
                except ValidationError as e:
                    return JsonResponse({"error": f"Data validation failed: {str(e)}"}, status=400)

                # Save Recipe
                recipe = Recipe.objects.create(
                    title=parsed_recipe.title,
                    pub_date=now(),
                    created_by=request.user.username if request.user.is_authenticated else None,
                    creator=request.user if request.user.is_authenticated else None,
                    mealType=None,
                    cuisine=None,
                    baking=parsed_recipe.baking,
                )

                # Save Ingredients
                for ing in parsed_recipe.ingredients:
                    Ingredient.objects.create(
                        recipe=recipe,
                        ingredient_text=ing.ingredient_text,
                        ingredient_amount="" if ing.ingredient_amount and ing.ingredient_amount.lower() == "none" else ing.ingredient_amount,
                        ingredient_unit="" if ing.ingredient_unit and ing.ingredient_unit.lower() == "none" else ing.ingredient_unit,
                    )

                # Save Instructions
                for instr in parsed_recipe.instructions:
                    Instruction.objects.create(
                        recipe=recipe,
                        instruction_text=instr.instruction_text,
                        instruction_order=instr.instruction_order,
                    )

                print("✅ Recipe successfully created, sending JSON response...")

                # Instead of redirecting, return JSON with recipe ID
                return JsonResponse({"message": "Recipe successfully created!", "recipe_id": recipe.id}, status=200)

            return JsonResponse({"error": "No URL provided"}, status=400)
        
        except Exception as e:
            return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def parse_recipe(request):
    """Handles OpenAI recipe parsing after OCR is complete."""
    if request.method == "POST":
        recipe_text = request.POST.get("recipe_text", "").strip()

        print("📌 Recipe text received:", recipe_text)

        if not recipe_text:
            return render(request, "voxpopulirecipes/parse_recipe.html", {"error": "No text received"})

        try:
            print("📌 Sending text to OpenAI for parsing...")
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a recipe parser."},
                    {
                        "role": "user",
                        "content": (
                            "Extract the following recipe details and format them as JSON "
                            "with title, ingredients (name, amount, unit), and instructions (text, order).  If instruction text will be more than 500 characters, make 2 separate instructions.:\n\n"
                            + recipe_text
                        )
                    }
                ]
            )
            recipe_data = response.choices[0].message.content
            print("✅ OpenAI Response Received:", recipe_data)

            # Parse API response
            data = json.loads(recipe_data)

            # Create Recipe object
            recipe = Recipe.objects.create(
                title=data["title"],
                pub_date=now(),
                created_by=request.user.username if request.user.is_authenticated else None,
                creator=request.user if request.user.is_authenticated else None
            )

            # Create Ingredient objects
            for ingredient in data.get("ingredients", []):
                Ingredient.objects.create(
                    recipe=recipe,
                    ingredient_text=ingredient["name"],
                    ingredient_amount=ingredient.get("amount"),
                    ingredient_unit=ingredient.get("unit")
                )

            # Create Instruction objects
            for instruction in sorted(data.get("instructions", []), key=lambda x: x["order"]):
                Instruction.objects.create(
                    recipe=recipe,
                    instruction_text=instruction["text"],
                    instruction_order=instruction["order"]
                )

            print("✅ Recipe successfully created, redirecting...")
            return redirect("voxpopulirecipes:edit_recipe", recipe_id=recipe.id)

        except Exception as e:
            print("❌ Error during OpenAI processing:", e)
            return render(request, "voxpopulirecipes/error.html", {"error": str(e)})

    return render(request, "voxpopulirecipes/parse_recipe.html")



def resize_image(image_url, max_size=(1000, 1000), quality=70):
    """Resize and compress image to reduce file size under 1MB."""
    response = requests.get(image_url)
    image = Image.open(io.BytesIO(response.content))

    # Convert to grayscale for better OCR readability
    image = image.convert("L")
    image.thumbnail(max_size, Image.LANCZOS)

    # Save to bytes with compression
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="JPEG", quality=quality)
    img_byte_arr.seek(0)

    # Check file size
    file_size_kb = len(img_byte_arr.getvalue()) / 1024
    print(f"📌 Resized image size: {file_size_kb:.2f} KB")  # Debugging info

    return img_byte_arr

def extract_text_from_s3(image_url):
    """Extract text using OCR.Space with resized image and explicit file type."""
    try:
        api_key = "K84625900288957"
        resized_image = resize_image(image_url)

        # Ensure file is under 1024KB
        if len(resized_image.getvalue()) > 1024 * 1024:
            return "Error: Resized image is still too large."

        payload = {
            "apikey": api_key,
            "language": "eng",
            "filetype": "jpg",
            "OCREngine": "2",  # 🔹 Use better OCR engine
        }
        files = {
            "image": ("image.jpg", resized_image, "image/jpeg")  # 🔹 Force correct filename & MIME type
        }

        response = requests.post("https://api.ocr.space/parse/image", data=payload, files=files)
        result = response.json()

        print("📌 OCR.Space API Response:", result)  # Debugging

        if result.get("IsErroredOnProcessing", False):
            return f"Error: {result.get('ErrorMessage', 'OCR processing failed')}"

        parsed_results = result.get("ParsedResults", [])
        if not parsed_results:
            return "Error: No text extracted"

        parsed_text = parsed_results[0].get("ParsedText", "").strip()
        return parsed_text if parsed_text else "Error: No text found in OCR response"

    except Exception as e:
        return f"Error extracting text with OCR.Space: {str(e)}"


def add_cuisine(request):
    if request.method == "POST":
        cuisine_name = request.POST.get("cuisine_name", "").strip()
        if cuisine_name:
            # Check for duplicate cuisines
            if Cuisine.objects.filter(name__iexact=cuisine_name).exists():
                return JsonResponse({
                    "success": False,
                    "message": "Cuisine already exists."
                })
            
            # Create the new cuisine
            cuisine = Cuisine.objects.create(name=cuisine_name)
            return JsonResponse({
                "success": True,
                "message": "Cuisine added successfully!",
                "cuisine_id": cuisine.id  # Return the new cuisine ID
            })
        return JsonResponse({"success": False, "message": "Cuisine name is required."})
    return JsonResponse({"success": False, "message": "Invalid request method."})
    
def add_mealtype(request):
    if request.method == "POST":
        mealtype_name = request.POST.get("mealtype_name", "").strip()
        mealtype_baking = request.POST.get("mealtype_baking") == "on"  # Convert to boolean
        print(mealtype_baking)
        if mealtype_name:
            if MealType.objects.filter(name__iexact=mealtype_name).exists():
                return JsonResponse({
                    "success": False,
                    "message": "Meal type already exists."
                })
                
            # Create the new meal type
            mealType = MealType.objects.create(name=mealtype_name, baking=mealtype_baking)
            return JsonResponse({
                "success": True,
                "message": "Meal type added successfully!",
                "mealtype_id": mealType.id  # Return the new meal type ID
            })
            
        return JsonResponse({"success": False, "message": "Meal type name is required."})
    return JsonResponse({"success": False, "message": "Invalid request method."})