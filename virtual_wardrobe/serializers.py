from rest_framework import serializers
from .models import ClothingItem, Outfit

class ClothingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClothingItem
        fields = ['id', 'name', 'category', 'color', 'season', 'image_url']

class OutfitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outfit
        fields = ['id', 'name', 'items', 'suggested_temperature_min', 'suggested_temperature_max']
