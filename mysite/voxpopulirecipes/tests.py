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
        self.assertInHTML(f'<a href="#" data-id="{recipe1.id}">{recipe1.title}</a>', response.content.decode())
        self.assertInHTML(f'<a href="#" data-id="{recipe2.id}">{recipe2.title}</a>', response.content.decode())
        
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
        
    def test_edit_recipe_click(self):
        """
        This should test that clicking on the edit recipe button redirects to the correct recipe form for editing
        """
        # Create a test recipe
        recipe1 = create_recipe(recipe_title='Test Recipe 1', days=-2)
        ingredient1 = Ingredient.objects.create(recipe=recipe1, ingredient_text='Test Ingredient 1')
        instruction1 = Instruction.objects.create(recipe=recipe1, instruction_text='Test Instruction 1')
        
        # Make a GET request to the edit_recipe view
        response = self.client.get(reverse("voxpopulirecipes:edit_recipe", args=(recipe1.id,)))
        
        # Assert that the correct template is used for the edit recipe form
        self.assertTemplateUsed(response, 'voxpopulirecipes/submit_recipe.html')

        # Assert that the form is pre-filled with the recipe data (e.g., the title)
        self.assertContains(response, recipe1.title)
        self.assertContains(response, ingredient1.ingredient_text)
        self.assertContains(response, instruction1.instruction_text)
        
        
        
    
class RecipeFilterTest(TestCase):
    
    def setUp(self):
        """
        this should test to make sure that when an ingredient filter has been applied, 
        only the correct recipes are shown in the dropdown
        """
        self.recipe1 = create_recipe(recipe_title='Test Recipe 1', days=-2)
        self.recipe2 = create_recipe(recipe_title='Test Recipe 2', days=-3)
        
        self.ingredient1 = Ingredient.objects.create(recipe=self.recipe1, ingredient_text='Test Ingredient 1')
        self.ingredient2 = Ingredient.objects.create(recipe=self.recipe2, ingredient_text='Test Ingredient 2')
        
    def test_filter_recipes(self):
        """
        this should test that the correct recipes are returned when the filter is applied
        """
        seleted_ingredient = 'Test Ingredient 1'
        filtered_recipes = Recipe.objects.filter(ingredient__ingredient_text=seleted_ingredient).distinct()
        
        self.assertEqual(filtered_recipes.count(), 1)
        self.assertEqual(filtered_recipes.first(), self.recipe1)
        self.assertNotIn(self.recipe2, filtered_recipes)
        
        
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
        
class SubmitRecipeViewNewRecipeTest(TestCase):
    
    def test_submit_new_recipe_with_no_name(self):
        """
        test if no name is submitted
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe"))
        self.assertContains(response, "Recipe name is required.")
        
    def test_submit_new_recipe_with_no_ingredients_no_instructions(self):
        """
        because of the ordering of the check, it should return the ingredients error first
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe"), {'title': 'Test Recipe'})
        self.assertContains(response, "Recipe must have at least one ingredient.")
        
    def test_submit_new_recipe_with_ingredients_no_instructions(self):
        """
        this should show the instructions error
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe"), {
            'title': 'Test Recipe', 
            'ingredient_text_1': 'Test Ingredient'
            })
        self.assertContains(response, "Recipe must have at least one instruction.")
        
    def test_submit_new_recipe_with_instructions_no_ingredients(self):
        """
        this should show the ingredients error
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe"), {
            'title': 'Test Recipe', 
            'instruction_text_1': 'Test Instruction'
            })
        self.assertContains(response, "Recipe must have at least one ingredient.")
        
    def test_submit_new_recipe_with_complete_ingredient_and_instruction(self):
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
        
        #check the recipe title
        recipe_test = Recipe.objects.get(title='Test Recipe')
        self.assertEqual(recipe_test.title, 'Test Recipe')
        
        self.assertRedirects(response, reverse("voxpopulirecipes:detail", args=[recipe_test.id]))
        
        #check the ingredient
        ingredient = Ingredient.objects.get(recipe=recipe_test)
        self.assertEqual(ingredient.ingredient_text, 'Test Ingredient')
        
        #check the instruction
        instruction = Instruction.objects.get(recipe=recipe_test)
        self.assertEqual(instruction.instruction_text, 'Test Instruction')
        
    def test_submit_new_recipe_with_incomplete_ingredient_and_instruction(self):
        """
        testing that ingredient with blank optional values is saved correctly
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe"), {
            'title': 'Test Recipe',
            'ingredient_text_1': 'Test Ingredient',
            'instruction_text_1': 'Test Instruction'
        })
        
        recipe = Recipe.objects.get(title='Test Recipe')
        self.assertEqual(recipe.title, 'Test Recipe')
        
        self.assertRedirects(response, reverse("voxpopulirecipes:detail", args=[recipe.id]))
        
        ingredient = Ingredient.objects.get(recipe=recipe)
        self.assertEqual(ingredient.ingredient_text, 'Test Ingredient')
        
        instruction = Instruction.objects.get(recipe=recipe)
        self.assertEqual(instruction.instruction_text, 'Test Instruction')
        
class SubmitRecipeViewEditRecipeTest(TestCase):
    
    def setUp(self):
        self.recipe1 = Recipe.objects.create(title='Test Recipe', pub_date=timezone.now()+datetime.timedelta(days=-5))
        self.ingredient1 = Ingredient.objects.create(recipe=self.recipe1, ingredient_text='Test Ingredient 1')
        self.ingredient2 = Ingredient.objects.create(recipe=self.recipe1, ingredient_text='Test Ingredient 2')
        self.instruction1 = Instruction.objects.create(recipe=self.recipe1, instruction_text='Test Instruction 1')
        self.instruction2 = Instruction.objects.create(recipe=self.recipe1, instruction_text='Test Instruction 2')
        
    def test_ingredients_and_instructions_load_in_order(self):
        """
        this should test that all of the ingredients and instructions are loaded in, and in the correct order
        """
        response = self.client.get(reverse("voxpopulirecipes:edit_recipe", args=[self.recipe1.id]))
        self.assertTemplateUsed(response, 'voxpopulirecipes/submit_recipe.html')
        
        # tests that there is an element for each of the ingredients and instructions
        self.assertContains(response, f'value="{self.ingredient1.ingredient_text}"')
        self.assertContains(response, f'value="{self.ingredient2.ingredient_text}"')
        self.assertContains(response, self.instruction1.instruction_text)
        self.assertContains(response, self.instruction2.instruction_text)
        
        # tests that there aren't any extra elements
        self.assertNotContains(response, 'ingredient_text_3')
        self.assertNotContains(response, 'instruction_text_3')
        
    def test_edited_recipe_with_no_additions(self):
        """
        This should test that an edited recipe with no additions is saved correctly
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe", args=[self.recipe1.id]), {
            'title': 'Edited Test Recipe',
            'ingredient_text_1': 'Edited Test Ingredient 1',
            'ingredient_text_2': 'Test Ingredient 2',
            'instruction_text_1': 'Edited Test Instruction 1',
            'instruction_text_2': 'Test Instruction 2'
        })
        
        # Check the updated recipe title
        recipe_test = Recipe.objects.get(title='Edited Test Recipe')
        self.assertEqual(recipe_test.title, 'Edited Test Recipe')
        
        # Check the updated ingredients
        ingredient1 = Ingredient.objects.get(recipe=recipe_test, ingredient_text='Edited Test Ingredient 1')
        self.assertEqual(ingredient1.ingredient_text, 'Edited Test Ingredient 1')
        ingredient2 = Ingredient.objects.get(recipe=recipe_test, ingredient_text='Test Ingredient 2')
        self.assertEqual(ingredient2.ingredient_text, 'Test Ingredient 2')
        
        # Check the updated instructions
        instruction1 = Instruction.objects.get(recipe=recipe_test, instruction_text='Edited Test Instruction 1')
        self.assertEqual(instruction1.instruction_text, 'Edited Test Instruction 1')
        instruction2 = Instruction.objects.get(recipe=recipe_test, instruction_text='Test Instruction 2')
        self.assertEqual(instruction2.instruction_text, 'Test Instruction 2')

        # Ensure no new ingredients or instructions were added
        self.assertEqual(Ingredient.objects.filter(recipe=recipe_test).count(), 2)
        self.assertEqual(Instruction.objects.filter(recipe=recipe_test).count(), 2)
        
        # ensure no new recipes were added
        self.assertEqual(Recipe.objects.count(), 1)
        
    def test_edited_recipe_with_additions(self):
        """
        This should test that adding an instruciton and an ingredient are saved properly
        """
        response = self.client.post(reverse("voxpopulirecipes:submit_recipe", args=[self.recipe1.id]), {
            'title': 'Edited Test Recipe',
            'ingredient_text_1': 'Edited Test Ingredient 1',
            'ingredient_text_2': 'Test Ingredient 2',
            'ingredient_text_3': 'New Ingredient',
            'instruction_text_1': 'Edited Test Instruction 1',
            'instruction_text_2': 'Test Instruction 2',
            'instruction_text_3': 'New Instruction'
        })
        
        
        # Check the updated recipe title
        recipe_test = Recipe.objects.get(title='Edited Test Recipe')
        self.assertEqual(recipe_test.title, 'Edited Test Recipe')
        
        # Check the updated ingredients
        ingredient1 = Ingredient.objects.get(recipe=recipe_test, ingredient_text='Edited Test Ingredient 1')
        self.assertEqual(ingredient1.ingredient_text, 'Edited Test Ingredient 1')
        ingredient2 = Ingredient.objects.get(recipe=recipe_test, ingredient_text='Test Ingredient 2')
        self.assertEqual(ingredient2.ingredient_text, 'Test Ingredient 2')
        ingredient3 = Ingredient.objects.get(recipe=recipe_test, ingredient_text='New Ingredient')
        self.assertEqual(ingredient3.ingredient_text, 'New Ingredient')
        
        # Check the updated instructions
        instruction1 = Instruction.objects.get(recipe=recipe_test, instruction_text='Edited Test Instruction 1')
        self.assertEqual(instruction1.instruction_text, 'Edited Test Instruction 1')
        instruction2 = Instruction.objects.get(recipe=recipe_test, instruction_text='Test Instruction 2')
        self.assertEqual(instruction2.instruction_text, 'Test Instruction 2')
        instruction3 = Instruction.objects.get(recipe=recipe_test, instruction_text='New Instruction')
        self.assertEqual(instruction3.instruction_text, 'New Instruction')

        # Ensure no new ingredients or instructions were added
        self.assertEqual(Ingredient.objects.filter(recipe=recipe_test).count(), 3)
        self.assertEqual(Instruction.objects.filter(recipe=recipe_test).count(), 3)
        
        # ensure no new recipes were added
        self.assertEqual(Recipe.objects.count(), 1)    
        
        
        