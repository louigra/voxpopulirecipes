#import the packages i need
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.template import loader
from django.utils import timezone


# import the models i need
from .models import Recipe, Ingredient, Instruction

def index(request):
    lastest_recipe_list = Recipe.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]
    all_recipes = Recipe.objects.all().order_by("id")
    all_unique_ingredients = Ingredient.objects.values_list("ingredient_text", flat=True).distinct().order_by("ingredient_text")
    template = loader.get_template("voxpopulirecipes/index.html")
    context = {
        "latest_recipe_list": lastest_recipe_list,
        "all_recipes": all_recipes,
        "all_unique_ingredients": all_unique_ingredients
    }
    return HttpResponse(template.render(context, request))

def detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    return render(request, "voxpopulirecipes/recipe.html", {"recipe": recipe})

def submit_recipe(request):
    if request.method == 'POST':
        recipe_title = request.POST.get('title')

        if recipe_title:
            recipe = Recipe.objects.create(title=recipe_title, pub_date=timezone.now())
            ingredient_text_1 = request.POST.get('ingredient_text_1')
            instruction_text_1 = request.POST.get('instruction_text_1')
                
            if not ingredient_text_1:
                return render(request, 'voxpopulirecipes/submit_recipe.html', {'error_message': 'Recipe must have at least one ingredient.'})
                    
            if not instruction_text_1:
                return render(request, 'voxpopulirecipes/submit_recipe.html', {'error_message': 'Recipe must have at least one instruction.'})

            # Process the ingredients one at a time
            ingredient_count = 1
            while True:
                ingredient_text = request.POST.get(f'ingredient_text_{ingredient_count}')
                ingredient_amount = request.POST.get(f'ingredient_amount_{ingredient_count}','')
                ingredient_unit = request.POST.get(f'ingredient_unit_{ingredient_count}','')

 
                # must have at least an ingredient text, otherwise break the loop
                if ingredient_text:
                    # Create and save the Ingredient object
                    Ingredient.objects.create(
                        recipe=recipe,
                        ingredient_text=ingredient_text,
                        ingredient_amount=ingredient_amount or None, # allow empty values
                        ingredient_unit=ingredient_unit or None # allow empty values
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
            return render(request, 'voxpopulirecipes/submit_recipe.html', {'error_message': 'Recipe name is required.'})

    # If it's a GET request, render the form
    return render(request, 'voxpopulirecipes/submit_recipe.html')

def random_recipe(request):
    random_recipe = Recipe.objects.order_by("?").first()
    if random_recipe:
        return redirect('voxpopulirecipes:detail', recipe_id=random_recipe.id)
    else:
        return redirect('voxpopulirecipes:index')