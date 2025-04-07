from django.contrib import admin
from .models import ClothingCategory, ClothingItem, Outfit

@admin.register(ClothingCategory)
class ClothingCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(ClothingItem)
class ClothingItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category', 'color', 'season', 'created_at')
    list_filter = ('category', 'season', 'user')
    search_fields = ('name', 'brand', 'notes')
    date_hierarchy = 'created_at'

@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    list_filter = ('user',)
    search_fields = ('name',)
    filter_horizontal = ('items',)
