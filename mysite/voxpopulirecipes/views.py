#import the packages i need
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.template import loader
from django.utils import timezone


# import the models i need
from .models import Recipe, Ingredient, Instruction

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
    #if editing, fetch the recipe object
    if recipe_id:
        recipe = get_object_or_404(Recipe, id=recipe_id)
    else:
        recipe = None

    if request.method == 'POST':
        recipe_title = request.POST.get('title')
        # if title is missing, render the page back with the error message
        if recipe_title:
            
            if recipe:
                # If editing, update the existing recipe
                recipe.title = recipe_title
                recipe.save()
                
                # Handle deleted ingredients
                deleted_ingredients = request.POST.get('deleted_ingredients', '').split(',')
                # Remove any empty strings from the list
                deleted_ingredients = [ingredient_id for ingredient_id in deleted_ingredients if ingredient_id]
                if deleted_ingredients:
                    Ingredient.objects.filter(id__in=deleted_ingredients, recipe=recipe).delete()

                # Handle deleted instructions
                deleted_instructions = request.POST.get('deleted_instructions', '').split(',')
                # Remove any empty strings from the list
                deleted_instructions = [instruction_id for instruction_id in deleted_instructions if instruction_id]
                if deleted_instructions:
                    Instruction.objects.filter(id__in=deleted_instructions, recipe=recipe).delete()
                    
            else:
                # If creating a new recipe
                recipe = Recipe.objects.create(title=recipe_title, pub_date=timezone.now())

            # Extract the posted ingredient IDs from the form data
            posted_ingredient_ids = [key.split('_')[-1] for key in request.POST if key.startswith('ingredient_text_')]
            
            # if there are no ingredients, render the page back with the error message
            if not posted_ingredient_ids:
                return render(request, 'voxpopulirecipes/submit_recipe.html', {
                    'error_message': 'Recipe must have at least one ingredient.',
                    'recipe': recipe
                })

            # Process the ingredients
            for ingredient_id in posted_ingredient_ids:
                ingredient_text = request.POST.get(f'ingredient_text_{ingredient_id}')
                ingredient_amount = request.POST.get(f'ingredient_amount_{ingredient_id}', '')
                ingredient_unit = request.POST.get(f'ingredient_unit_{ingredient_id}', '')

                if ingredient_text:
                    if ingredient_id.isdigit():  # If it's an existing ingredient
                        ingredient = Ingredient.objects.filter(recipe=recipe, id=ingredient_id).first()
                        if ingredient:
                            # Update the existing ingredient
                            ingredient.ingredient_text = ingredient_text
                            ingredient.ingredient_amount = ingredient_amount
                            ingredient.ingredient_unit = ingredient_unit
                            ingredient.save()
                        else:
                            # Create a new ingredient if the ID does not exist
                            Ingredient.objects.create(
                                recipe=recipe,
                                ingredient_text=ingredient_text,
                                ingredient_amount=ingredient_amount,
                                ingredient_unit=ingredient_unit
                            )
                    else:
                        # Create new ingredients for any dynamically added ones (no ID)
                        Ingredient.objects.create(
                            recipe=recipe,
                            ingredient_text=ingredient_text,
                            ingredient_amount=ingredient_amount,
                            ingredient_unit=ingredient_unit
                        )

            # Process the instructions similarly by extracting posted instruction IDs
            posted_instruction_ids = [key.split('_')[-1] for key in request.POST if key.startswith('instruction_text_')]
            
            # if there are no instructions, render the page back with the error message
            if not posted_instruction_ids:
                return render(request, 'voxpopulirecipes/submit_recipe.html', {
                    'error_message': 'Recipe must have at least one instruction.',
                    'recipe': recipe
                    })

            for instruction_id in posted_instruction_ids:
                instruction_text = request.POST.get(f'instruction_text_{instruction_id}')

                if instruction_text:
                    if instruction_id.isdigit():  # If it's an existing instruction
                        instruction = Instruction.objects.filter(recipe=recipe, id=instruction_id).first()
                        if instruction:
                            # Update the existing instruction
                            instruction.instruction_text = instruction_text
                            instruction.save()
                        else:
                            # Create a new instruction if the ID does not exist
                            Instruction.objects.create(
                                recipe=recipe,
                                instruction_text=instruction_text,
                                instruction_order=instruction_id  # Make sure instruction order is set correctly
                            )
                    else:
                        # Create new instructions for dynamically added ones (no ID)
                        Instruction.objects.create(
                            recipe=recipe,
                            instruction_text=instruction_text,
                            instruction_order=instruction_id
                        )
                


            # Redirect to the recipe detail page or some success page after submission
            return redirect('voxpopulirecipes:detail', recipe_id=recipe.id)

        else:
            # Handle the case where the title is missing
            return render(request, 'voxpopulirecipes/submit_recipe.html', {
                'error_message': 'Recipe name is required.',
                'recipe': recipe
            })

    # If it's a GET request, render the form for editing or creating
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
    all_recipes = Recipe.objects.all().order_by("id")
    all_unique_ingredients = Ingredient.objects.values_list("ingredient_text", flat=True).distinct().order_by("ingredient_text")
    template = loader.get_template("voxpopulirecipes/search.html")
    context = {
        "all_recipes": all_recipes,
        "all_unique_ingredients": all_unique_ingredients
    }
    return HttpResponse(template.render(context, request))

def all_recipes(request):
    all_recipes = Recipe.objects.all().order_by("id")
    template = loader.get_template("voxpopulirecipes/all_recipes.html")
    context = {
        "all_recipes": all_recipes
    }
    return HttpResponse(template.render(context, request))

