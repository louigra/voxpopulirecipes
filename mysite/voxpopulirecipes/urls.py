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
    path('add-note/<int:recipe_id>/', views.add_note, name='add_note'),
    path('delete-note/<int:note_id>/', views.delete_note, name='delete_note'),
    path("check_review_status/<int:recipe_id>/", views.check_review_status, name="check_review_status"),
    path("submit_review/<int:recipe_id>/", views.submit_review, name="submit_review"),
    path("save_recipe/<int:recipe_id>/", views.save_recipe, name="save_recipe"),
    path("star_recipe/<int:recipe_id>/", views.star_recipe, name="star_recipe"),
    path("view-user-book/<int:user_id>/", views.view_user_book, name="view_user_book"),
    path("submit_recipe_selector/", views.submit_recipe_selector, name="submit_recipe_selector"),
    path("parse_recipe/", views.parse_recipe, name="parse_recipe"),
    path("submit_recipe_from_text/", views.submit_recipe_from_text, name="submit_recipe_from_text"),
    path("submit_recipe_from_image/", views.submit_recipe_from_image, name="submit_recipe_from_image"),
    path("extract_text", views.extract_text, name="extract_text"),
]