import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from unittest.mock import patch

from .models import Recipe, Ingredient, Instruction

# Create your tests here.

def create_recipe(recipe_title, days):
    """
    Create a recipe with the given `recipe_title` and published the
    given number of `days` offset to now (negative for recipes published
    in the past, positive for recipes that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Recipe.objects.create(title=recipe_title, pub_date=time)


class RecipeIndexViewTests(TestCase):
    def test_no_recipes(self):
        """
        if there are no recipes, the correct message is displayed
        """
        response = self.client.get(reverse("voxpopulirecipes:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No recipes are available.")
        self.assertQuerySetEqual(response.context["latest_recipe_list"], [])
        
    def test_past_recipe(self):
        """
        Recipes with a pub_date in the past are displayed on the index page
        """
        recipe = create_recipe(recipe_title='Test Past Recipe', days=-30)
        response = self.client.get(reverse("voxpopulirecipes:index"))
        self.assertQuerySetEqual(
            response.context["latest_recipe_list"],
            [recipe],
        )
    
    def test_future_recipe(self):
        """
        Recipes with a pub_date in teh future aren't displayed on the index page
        """
        recipe = create_recipe(recipe_title='Test Future Recipe', days=30)
        response = self.client.get(reverse("voxpopulirecipes:index"))
        self.assertContains(response, "No recipes are available.")
        self.assertQuerySetEqual(response.context["latest_recipe_list"], [])
        
    def test_future_recipe_and_past_recipe(self):
        """
        Even if both past and future recipes exist, only past recipes are displayed
        """
        past_recipe = create_recipe(recipe_title='Test Past Recipe', days=-30)
        create_recipe(recipe_title='Test Future Recipe', days=30)
        response = self.client.get(reverse("voxpopulirecipes:index"))
        self.assertQuerySetEqual(
            response.context["latest_recipe_list"],
            [past_recipe],
        )
        
    def test_two_past_recipes(self):
        """
        The recipes index page may display multiple recipes
        """
        recipe1 = create_recipe(recipe_title='Test Past Recipe Newer', days=-5)
        recipe2 = create_recipe(recipe_title='Test Past Recipe Older', days=-30)
        response = self.client.get(reverse("voxpopulirecipes:index"))
        self.assertQuerySetEqual(
            response.context["latest_recipe_list"],
            [recipe1, recipe2],
        )
    
    def test_more_than_five_recipes(self):
        """
        if there are more than five recipes, the five most recent are displayed
        """
        recipe1 = create_recipe(recipe_title='Test Recipe 1', days=-2)
        recipe2 = create_recipe(recipe_title='Test Recipe 2', days=-3)
        recipe3 = create_recipe(recipe_title='Test Recipe 3', days=-4)
        recipe4 = create_recipe(recipe_title='Test Recipe 4', days=-5)
        recipe5 = create_recipe(recipe_title='Test Recipe 5', days=-6)
        create_recipe(recipe_title='Test Recipe 6', days=-7)
        response = self.client.get(reverse("voxpopulirecipes:index"))
        self.assertQuerySetEqual(
            response.context["latest_recipe_list"],
            [recipe1, recipe2, recipe3, recipe4, recipe5],
        )
    
    def test_all_recipes_return(self):
        """
        this is testing that all recipes are returned for the search bar
        """
        recipe1 = create_recipe(recipe_title='Test Recipe 1', days=-2)
        recipe2 = create_recipe(recipe_title='Test Recipe 2', days=-3)
        recipe3 = create_recipe(recipe_title='Test Recipe 3', days=-4)
        recipe4 = create_recipe(recipe_title='Test Recipe 4', days=-5)
        recipe5 = create_recipe(recipe_title='Test Recipe 5', days=-6)
        recipe6 = create_recipe(recipe_title='Test Recipe 6', days=-7)
        
        response = self.client.get(reverse("voxpopulirecipes:index"))
        self.assertQuerySetEqual(
            response.context["all_recipes"],
            [recipe1, recipe2, recipe3, recipe4, recipe5, recipe6],
            transform = lambda x: x #this compares the actual objects instead of the string representations
        )
        
    def test_dropdown_has_all_recipes(self):
        """
        This should test that all the recipes passed into the context are in the dropdown
        """
        recipe1 = create_recipe(recipe_title='Test Recipe 1', days=-2)
        recipe2 = create_recipe(recipe_title='Test Recipe 2', days=-3)
        
        response = self.client.get(reverse("voxpopulirecipes:index"))
        
        # Check if the response contains the recipe titles
        self.assertContains(response, recipe1.title)
        self.assertContains(response, recipe2.title)
        
        # Check if the dropdown list (ul) is present
        self.assertContains(response, '<ul id="recipe-list">')
        
        # Check if the specific list items and links are present in the dropdown (without strict HTML checking)
        self.assertInHTML(f'<li><a href="#" data-id="{recipe1.id}">{recipe1.title}</a></li>', response.content.decode())
        self.assertInHTML(f'<li><a href="#" data-id="{recipe2.id}">{recipe2.title}</a></li>', response.content.decode())
        
    def test_all_unique_ingredients_in_context(self):
        """
        This should test that all the unique ingredients are in the context.
        """
        recipe1 = create_recipe(recipe_title='Test Recipe 1', days=-2)
        recipe2 = create_recipe(recipe_title='Test Recipe 2', days=-3)
        
        ingredient1 = Ingredient.objects.create(recipe=recipe1, ingredient_text='Test Ingredient 1')
        ingredient2 = Ingredient.objects.create(recipe=recipe1, ingredient_text='Test Ingredient 2')
        ingredient11 = Ingredient.objects.create(recipe=recipe2, ingredient_text='Test Ingredient 1')  # Duplicate
        ingredient3 = Ingredient.objects.create(recipe=recipe2, ingredient_text='Test Ingredient 3')
        ingredient4 = Ingredient.objects.create(recipe=recipe2, ingredient_text='Test Ingredient 4')
        
        response = self.client.get(reverse("voxpopulirecipes:index"))
        
        # Check that the context contains the unique ingredients, ignoring duplicates
        self.assertQuerySetEqual(
            response.context["all_unique_ingredients"],
            ['Test Ingredient 1', 'Test Ingredient 2', 'Test Ingredient 3', 'Test Ingredient 4'],
            transform=lambda x: x
        )
    
    def test_dropdown_filter(self):
        """
        this should test to make sure that when an ingredient filter has been applied, 
        only the correct recips are shown in the dropdown
        """
        
        recipe1 = create_recipe(recipe_title='Test Recipe 1', days=-2)
        recipe2 = create_recipe(recipe_title='Test Recipe 2', days=-3)
        
        ingredient1 = Ingredient.objects.create(recipe=recipe1, ingredient_text='Test Ingredient 1')
        ingredient2 = Ingredient.objects.create(recipe=recipe1, ingredient_text='Test Ingredient 2')
        ingretient3 = Ingredient.objects.create(recipe=recipe2, ingredient_text='Test Ingredient 3')
        ingredient4 = Ingredient.objects.create(recipe=recipe2, ingredient_text='Test Ingredient 4')
        
        
        
class RandomRecipeViewTest(TestCase):
    
    def setUp(self):
        # create some mock recipes
        self.recipe1 = Recipe.objects.create(title='Test Recipe 1', pub_date=timezone.now()+datetime.timedelta(days=-5))
        self.recipe2 = Recipe.objects.create(title='Test Recipe 2', pub_date=timezone.now()+datetime.timedelta(days=-5))
        self.recipe3 = Recipe.objects.create(title='Test Recipe 3', pub_date=timezone.now()+datetime.timedelta(days=-5))
    
    # 
    @patch('voxpopulirecipes.views.Recipe.objects.order_by')
    def test_random_recipe_redirects_to_correct_recipe(self, mock_order_by):
        mock_order_by.return_value.first.return_value = self.recipe2
        response = self.client.get(reverse("voxpopulirecipes:random_recipe"))
        self.assertRedirects(response, reverse("voxpopulirecipes:detail", args=(self.recipe2.id,)))
        
    def test_random_recipe_redirects_to_index_if_no_recipes(self):
        Recipe.objects.all().delete()
        response = self.client.get(reverse("voxpopulirecipes:random_recipe"))
        self.assertRedirects(response, reverse("voxpopulirecipes:index"))
        
class SubmitRecipeViewTest(TestCase):
    
    def test_submit_recipe_with_no_name(self):
        """
        test if no name is submitted
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe"))
        self.assertContains(response, "Recipe name is required.")
        
    def test_submit_recipe_name_saved_correctly(self):
        """
        tests that name is set correctly
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe"), {'title': 'Test Recipe'})
        self.assertEqual(Recipe.objects.first().title, 'Test Recipe')
        
    def test_submit_recipe_with_no_ingredients_no_instructions(self):
        """
        because of the ordering of the check, it should return the ingredients error first
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe"), {'title': 'Test Recipe'})
        self.assertContains(response, "Recipe must have at least one ingredient.")
        
    def test_submit_recipe_with_ingredients_no_instructions(self):
        """
        this should show the instructions error
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe"), {'title': 'Test Recipe', 'ingredient_text_1': 'Test Ingredient'})
        self.assertContains(response, "Recipe must have at least one instruction.")
        
    def test_submit_recipe_with_instructions_no_ingredients(self):
        """
        this should show the ingredients error
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe"), {'title': 'Test Recipe', 'instruction_text_1': 'Test Instruction'})
        self.assertContains(response, "Recipe must have at least one ingredient.")
        
    def test_submit_recipe_with_complete_ingredient_and_instruction(self):
        """
        testing that ingredient and instruction are added correctly with a complete ingredient
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe"), {
            'title': 'Test Recipe', 
            'ingredient_text_1': 'Test Ingredient',
            'ingredient_amount_1': '1',
            'ingredient_unit_1': 'cup',
            'instruction_text_1': 'Test Instruction'
        })
        #first assert that the response is a redirect
        self.assertRedirects(response, reverse("voxpopulirecipes:index"))
        
        #check the recipe title
        recipe = Recipe.objects.get(title='Test Recipe')
        self.assertEqual(recipe.title, 'Test Recipe')
        
        #check the ingredient
        ingredient = Ingredient.objects.get(recipe=recipe)
        self.assertEqual(ingredient.ingredient_text, 'Test Ingredient')
        
        #check the instruction
        instruction = Instruction.objects.get(recipe=recipe)
        self.assertEqual(instruction.instruction_text, 'Test Instruction')
        
    def test_submit_recipe_with_incomplete_ingredient_and_instruction(self):
        """
        testing that ingredient with blank optional values is saved correctly
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe"), {
            'title': 'Test Recipe',
            'ingredient_text_1': 'Test Ingredient',
            'instruction_text_1': 'Test Instruction'
        })
        self.assertRedirects(response, reverse("voxpopulirecipes:index"))
        recipe = Recipe.objects.get(title='Test Recipe')
        self.assertEqual(recipe.title, 'Test Recipe')
        
        ingredient = Ingredient.objects.get(recipe=recipe)
        self.assertEqual(ingredient.ingredient_text, 'Test Ingredient')
        
        instruction = Instruction.objects.get(recipe=recipe)
        self.assertEqual(instruction.instruction_text, 'Test Instruction')