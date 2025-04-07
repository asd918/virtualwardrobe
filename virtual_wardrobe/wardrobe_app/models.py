from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

class ClothingCategory(models.Model):
    """Predefined clothing categories."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Clothing Categories"

class ClothingItem(models.Model):
    """Represents a single clothing item in the wardrobe."""
    SEASON_CHOICES = [
        ('all', 'All Seasons'),
        ('summer', 'Summer'),
        ('winter', 'Winter'),
        ('spring', 'Spring'),
        ('autumn', 'Autumn'),
    ]

    OCCASION_CHOICES = [
        ('casual', 'Casual'),
        ('work', 'Work'),
        ('formal', 'Formal'),
        ('sports', 'Sports'),
        ('party', 'Party'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='clothing_items'
    )
    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        ClothingCategory, 
        on_delete=models.SET_NULL, 
        null=True
    )
    color = models.CharField(max_length=50)
    season = models.CharField(
        max_length=10, 
        choices=SEASON_CHOICES, 
        default='all'
    )
    occasions = models.JSONField(default=list)
    
    # Image upload with validation
    image = models.ImageField(
        upload_to='wardrobe_items/',
        null=True, 
        blank=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif'])
        ]
    )
    
    # Metadata fields
    purchase_date = models.DateField(null=True, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    # Tracking fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.color})"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Clothing Items"

class Outfit(models.Model):
    """Represents a combination of clothing items."""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='outfits'
    )
    name = models.CharField(max_length=100)
    items = models.ManyToManyField(ClothingItem)
    
    # Weather association
    suggested_temperature_min = models.FloatField(null=True, blank=True)
    suggested_temperature_max = models.FloatField(null=True, blank=True)
    
    # Metadata fields
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']