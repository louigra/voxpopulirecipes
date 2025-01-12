#import the packages i need
import json
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.template import loader
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from collections import defaultdict

# import pagination stuff
from django.core.paginator import Paginator


# import the models i need
from .models import Recipe, Ingredient, Instruction, User, RecipeNote, Rating, CookedInstance, MealType, Cuisine

def main(request):
    lastest_recipe_list = Recipe.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]
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
    
    return render(request, "voxpopulirecipes/recipe.html", {
        "recipe": recipe,
        "mean_rating": mean_rating,
        "average_cook_time": average_cook_time
        })

def submit_recipe(request, recipe_id=None):
    mealtypes = MealType.objects.all()
    cuisines = Cuisine.objects.all()
    # If editing, fetch the recipe object
    if recipe_id:
        recipe = get_object_or_404(Recipe, id=recipe_id)
    else:
        recipe = None

    if request.method == 'POST':
        recipe_title = request.POST.get('title')
        recipe_image = request.FILES.get('image')  # Get the uploaded image file
        recipe_mealtype = request.POST.get('mealtype')
        recipe_cuisine = request.POST.get('cuisine')

        # Check if the title is provided
        if recipe_title:
            if recipe:
                # If editing, update the existing recipe
                recipe.title = recipe_title
                if recipe_image:
                    recipe.image = recipe_image  # Update the image if a new one is uploaded
                if recipe_mealtype:
                    recipe.mealType = MealType.objects.get(id=recipe_mealtype)
                if recipe_cuisine:
                    recipe.cuisine = Cuisine.objects.get(id=recipe_cuisine)
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
                    mealType=MealType.objects.get(id=recipe_mealtype),
                    cuisine=Cuisine.objects.get(id=recipe_cuisine)
                )

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
    mealtypes = MealType.objects.all()
    cuisines = Cuisine.objects.all()
    return render(request, 'voxpopulirecipes/submit_recipe.html', {
        'recipe': recipe,
        'mealtypes': mealtypes,
        'cuisines': cuisines
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




@login_required
def my_recipes(request):
    recipes = Recipe.objects.filter(creator=request.user).order_by("pub_date")
    mealtype_cuisine_map = defaultdict(lambda: defaultdict(list))

    for recipe in recipes:
        if recipe.mealType and recipe.cuisine:
            mealtype_cuisine_map[recipe.mealType][recipe.cuisine].append(recipe)

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