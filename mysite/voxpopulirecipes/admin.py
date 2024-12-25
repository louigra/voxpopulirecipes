from django.contrib import admin

# Register your models here.

from .models import Recipe, Ingredient, Instruction, VPUser

class IngredientInline(admin.TabularInline):
    model = Ingredient
    extra = 0

class InstructionInLine(admin.TabularInline):
    model = Instruction
    extra = 0

class RecipeAdmin(admin.ModelAdmin):
    inlines = [IngredientInline, InstructionInLine]
    list_display = ["title", "pub_date"]
    list_filter = ["pub_date"]
    search_fields = ["title"]

admin.site.register(VPUser)


