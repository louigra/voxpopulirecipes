from django import forms
from django.forms import ModelForm
from .models import Recipe, Ingredient

# Create a form for the Ingredient model

class IngredientForm(forms.Form):
    ingredient_amount = forms.CharField(max_length=10, label='Amount')
    ingredient_unit = forms.CharField(max_length=10, label='Unit')
    ingredient_text = forms.CharField(max_length=100, label='Ingredient')

class RecipeForm(forms.Form):
    title = forms.CharField(max_length=100, label='Recipe Name')
    # handle ingredients dynamically with JavaScript in the template.