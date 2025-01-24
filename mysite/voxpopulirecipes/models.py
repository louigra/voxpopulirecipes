from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class VPUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    bio = models.TextField(blank=True, null=True)
    ingredients_at_home = models.ManyToManyField("Ingredient", blank=True)
    def __str__(self):
        return f"{self.user.username}'s VPUser"    

class Recipe(models.Model):
    title = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    created_by = models.CharField(max_length=200, blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    mealType = models.ForeignKey("MealType", on_delete=models.SET_NULL, blank=True, null=True)
    cuisine = models.ForeignKey("Cuisine", on_delete=models.SET_NULL, blank=True, null=True)
    image = models.ImageField(upload_to='uploads/recipe/', blank=True, null=True)
    baking = models.BooleanField(default=False)
    def __str__(self):
        return self.title

class Ingredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient_text = models.CharField(max_length=200) #required
    ingredient_amount = models.CharField(max_length=200, blank=True, null=True) #optional
    ingredient_unit = models.CharField(max_length=200, blank=True, null=True) #optional
    def __str__(self):
        return self.ingredient_text
    
class Instruction(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    instruction_text = models.CharField(max_length=500)
    instruction_order = models.IntegerField(default=0)
    def __str__(self):
        return self.instruction_text
    
class RecipeNote(models.Model):
    recipe = models.ForeignKey(Recipe, related_name="notes", on_delete=models.CASCADE)
    note_text = models.CharField(max_length=2000)
    note_order = models.IntegerField(default=0)
    note_date = models.DateTimeField("date created")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self):
        return self.note_text
    
class MealType(models.Model):
    name = models.CharField(max_length=200)
    baking = models.BooleanField(default=False)
    def __str__(self):
        return self.name

class Cuisine(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name

class Rating(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)
    rater = models.ForeignKey(User, on_delete=models.CASCADE)
    rating_date = models.DateTimeField("date rated", null=True, blank=True)
    def __str__(self):
        return f"{self.rater} rated {self.recipe} {self.rating}"
    
class CookedInstance(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    date_cooked = models.DateTimeField("date cooked")
    cook_time = models.IntegerField(default=0)  # Optional: Track how long it took to cook the recipe
    def __str__(self):
        return f"{self.user} cooked {self.recipe} on {self.date_cooked}"
 
class CookingPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipes = models.ManyToManyField(Recipe, related_name="cooking_plans")
    title = models.CharField(max_length=200, default="My Cooking Plan", blank=True, null=True)  # Optional: Add a title for the plan
    created_at = models.DateTimeField(auto_now_add=True)  # Optional: Track when the plan was created
    def __str__(self):
        return f"{self.user}'s Cooking Plan: {self.title}"
    
class StarredRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    date_starred = models.DateTimeField("date starred")
    def __str__(self):
        return f"{self.user} starred {self.recipe} on {self.date_starred}"
    
class SavedRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    date_saved = models.DateTimeField("date saved")
    def __str__(self):
        return f"{self.user} saved {self.recipe} on {self.date_saved}"
    
class MealTypeMap(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    mealType = models.ForeignKey(MealType, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.recipe} is a {self.mealType}"
    
class CuisineMap(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    cuisine = models.ForeignKey(Cuisine, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.recipe} is {self.cuisine}"
    