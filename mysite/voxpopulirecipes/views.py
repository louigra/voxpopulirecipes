#import the packages i need
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.template import loader
from django.utils import timezone


# import the models i need
from .models import Recipe, Ingredient, Instruction

def index(request):
    lastest_recipe_list = Recipe.objects.order_by("-pub_date")[:5]
    template = loader.get_template("voxpopulirecipes/index.html")
    context = {
        "latest_recipe_list": lastest_recipe_list,
    }
    return HttpResponse(template.render(context, request))

def detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    return render(request, "voxpopulirecipes/recipe.html", {"recipe": recipe})

def submit_recipe(request):
    if request.method == 'POST':
        # Get the recipe title
        recipe_title = request.POST.get('title')

        # Validate that the recipe title is present
        if recipe_title:
            # Create and save the Recipe object
            recipe = Recipe.objects.create(title=recipe_title, pub_date=timezone.now())

            # Process the ingredients one at a time
            ingredient_count = 1
            while True:
                ingredient_text = request.POST.get(f'ingredient_text_{ingredient_count}')
                ingredient_amount = request.POST.get(f'ingredient_amount_{ingredient_count}')
                ingredient_unit = request.POST.get(f'ingredient_unit_{ingredient_count}')

                # Check if all fields for this ingredient exist; if not, break the loop
                if ingredient_text and ingredient_amount and ingredient_unit:
                    # Create and save the Ingredient object
                    Ingredient.objects.create(
                        recipe=recipe,
                        ingredient_text=ingredient_text,
                        ingredient_amount=ingredient_amount,
                        ingredient_unit=ingredient_unit
                    )
                    ingredient_count += 1
                else:
                    break
            
            instruction_count = 1
            while True:
                instruction_text = request.POST.get(f'instruction_text_{instruction_count}')

                # Check if the instruction exists; if not, break the loop
                if instruction_text:
                    # Create and save the Instruction object
                    Instruction.objects.create(
                        recipe=recipe,
                        instruction_text=instruction_text,
                        instruction_order=instruction_count
                    )
                    instruction_count += 1
                else:
                    break
            
            # Redirect to a success page or recipe list view after form submission
            return redirect('voxpopulirecipes:index')  # Change to the appropriate view
        else:
            # Handle the case where the title is missing
            return render(request, 'voxpopulirecipes/submit_recipe.html', {'error': 'Recipe name is required.'})

    # If it's a GET request, render the form
    return render(request, 'voxpopulirecipes/submit_recipe.html')