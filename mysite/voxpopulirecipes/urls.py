from django.urls import path
from . import views

app_name = "voxpopulirecipes"
urlpatterns = [
    # ex: /voxpopulirecipes/
    path("", views.index, name="index"),
    
    # ex: /voxpopulirecipes/recipedetail/1/
    path("recipedetail/<int:recipe_id>/", views.detail, name="detail"),
    
    path("submit_recipe/", views.submit_recipe, name="submit_recipe"),
    
    path("random_recipe/", views.random_recipe, name="random_recipe"),
]