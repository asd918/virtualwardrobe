from rest_framework import serializers
from .models import ClothingItem, Outfit

class ClothingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClothingItem
        fields = ['id', 'name', 'category', 'image', 'color', 'season', 'style', 'occasions', 'created_at']

class OutfitSerializer(serializers.ModelSerializer):
    items = ClothingItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Outfit
        fields = ['id', 'name', 'items', 'suggested_temperature_min', 'suggested_temperature_max', 'compatibility_score', 'created_at'] 