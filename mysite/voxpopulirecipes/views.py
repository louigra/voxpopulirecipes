#import the packages i need
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.template import loader
from django.utils import timezone


# import pagination stuff
from django.core.paginator import Paginator


# import the models i need
from .models import Recipe, Ingredient, Instruction, User, RecipeNote

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
    return render(request, "voxpopulirecipes/recipe.html", {"recipe": recipe})

def submit_recipe(request, recipe_id=None):
    # If editing, fetch the recipe object
    if recipe_id:
        recipe = get_object_or_404(Recipe, id=recipe_id)
    else:
        recipe = None

    if request.method == 'POST':
        recipe_title = request.POST.get('title')
        recipe_image = request.FILES.get('image')  # Get the uploaded image file

        # Check if the title is provided
        if recipe_title:
            if recipe:
                # If editing, update the existing recipe
                recipe.title = recipe_title
                if recipe_image:
                    recipe.image = recipe_image  # Update the image if a new one is uploaded
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
                    creator=request.user
                )

            # Handle ingredients and instructions (same as your original logic)
            posted_ingredient_ids = [key.split('_')[-1] for key in request.POST if key.startswith('ingredient_text_')]
            if not posted_ingredient_ids:
                return render(request, 'voxpopulirecipes/submit_recipe.html', {
                    'error_message': 'Recipe must have at least one ingredient.',
                    'recipe': recipe
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
                    'recipe': recipe
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
                'recipe': recipe
            })

    # If it's a GET request, render the form
    return render(request, 'voxpopulirecipes/submit_recipe.html', {'recipe': recipe})

def random_recipe(request):
    random_recipe = Recipe.objects.order_by("?").first()
    if random_recipe:
        return redirect('voxpopulirecipes:detail', recipe_id=random_recipe.id)
    else:
        return redirect('voxpopulirecipes:main')
    
def edit_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    return render(request, 'voxpopulirecipes/submit_recipe.html', {'recipe': recipe})

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

def my_recipes(request):
    template = loader.get_template("voxpopulirecipes/my_recipes.html")
    recipes = Recipe.objects.all()
    context = {
        "recipes": recipes
    }
    return HttpResponse(template.render(context, request))

def about(request):
    return render(request, "voxpopulirecipes/about.html")