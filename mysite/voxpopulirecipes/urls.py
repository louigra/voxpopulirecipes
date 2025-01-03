from django.urls import path
from . import views

app_name = "voxpopulirecipes"
urlpatterns = [

    path("", views.main, name="main"),
    
    path("recipedetail/<int:recipe_id>/", views.detail, name="detail"),
    
    path("submit_recipe/", views.submit_recipe, name="submit_recipe"),
    
    path("submit_recipe/<int:recipe_id>/", views.submit_recipe, name="submit_recipe"),
    
    path("random_recipe/", views.random_recipe, name="random_recipe"),
    
    path("<int:recipe_id>/edit", views.edit_recipe, name="edit_recipe"),
    
    path("<int:recipe_id>/delete", views.delete_recipe, name="delete_recipe"),
    
    path("search/", views.search_recipe, name="search_recipe"),
    
    path("all_recipes/", views.all_recipes, name="all_recipes"),
    
    path("my_recipes", views.my_recipes, name="my_recipes"),
    
    path("about/", views.about, name="about"),
]