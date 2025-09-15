from rest_framework import serializers
from .models import ClothingItem, Outfit

class ClothingItemSerializer(serializers.ModelSerializer):
    image_front_url = serializers.SerializerMethodField()
    image_back_url = serializers.SerializerMethodField()

    class Meta:
        model = ClothingItem
        fields = ['id', 'name', 'category', 'color', 'season', 'image_front_url', 'image_back_url']

    def get_image_front_url(self, obj):
        try:
            return obj.image_front.url if obj.image_front else None
        except Exception:
            return None

    def get_image_back_url(self, obj):
        try:
            return obj.image_back.url if obj.image_back else None
        except Exception:
            return None

class OutfitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outfit
        fields = ['id', 'name', 'items', 'suggested_temperature_min', 'suggested_temperature_max']
