from django.db import models

# Create your models here.

class Recipe(models.Model):
    title = models.CharField(max_length=200)
    # published = models.BooleanField(default=False)
    pub_date = models.DateTimeField("date published")
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
    instruction_text = models.CharField(max_length=200)
    instruction_order = models.IntegerField(default=0)