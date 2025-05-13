from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator, RegexValidator, MinLengthValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class ClothingCategory(models.Model):
    """Predefined clothing categories."""
    CATEGORY_CHOICES = [
        ('tops', 'Tops'),
        ('bottoms', 'Bottoms'),
        ('dresses', 'Dresses'),
        ('outerwear', 'Outerwear'),
        ('shoes', 'Shoes'),
        ('accessories', 'Accessories'),
        ('underwear', 'Underwear'),
        ('swimwear', 'Swimwear'),
        ('activewear', 'Activewear'),
        ('formalwear', 'Formal Wear'),
        ('sleepwear', 'Sleepwear'),
        ('bags', 'Bags'),
        ('jewelry', 'Jewelry'),
        ('hats', 'Hats'),
        ('gloves', 'Gloves'),
        ('scarves', 'Scarves'),
        ('belts', 'Belts'),
        ('socks', 'Socks'),
        ('ties', 'Ties'),
        ('other', 'Other'),
    ]

    name = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        unique=True,
        validators=[MinLengthValidator(3, message="Category name must be at least 3 characters long.")]
    )
    description = models.TextField(blank=True, max_length=500)

    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name_plural = "Clothing Categories"

class UserProfile(models.Model):
    """
    Extends the User model to store user-specific preferences.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    preferred_colors = models.CharField(max_length=255, blank=True)
    preferred_occasions = models.CharField(max_length=255, blank=True)
    # Add other preference fields as needed

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class ClothingItem(models.Model):
    """Represents a single clothing item in the wardrobe."""
    SEASON_CHOICES = [
        ('all', 'All Seasons'),
        ('summer', 'Summer'),
        ('winter', 'Winter'),
        ('spring', 'Spring'),
        ('autumn', 'Autumn'),
    ]

    FIT_CHOICES = [
        ('loose', 'Loose'),
        ('slim', 'Slim'),
        ('regular', 'Regular'),
        ('oversized', 'Oversized'),
        ('fitted', 'Fitted'),
        ('relaxed', 'Relaxed'),
        ('tapered', 'Tapered'),
        ('straight', 'Straight'),
    ]

    OCCASION_CHOICES = [
        ('casual', 'Casual'),
        ('work', 'Work'),
        ('formal', 'Formal'),
        ('sports', 'Sports'),
        ('party', 'Party'),
        ('wedding', 'Wedding'),
        ('interview', 'Interview'),
        ('date', 'Date Night'),
        ('travel', 'Travel'),
        ('beach', 'Beach'),
        ('gym', 'Gym'),
        ('hiking', 'Hiking'),
        ('running', 'Running'),
        ('swimming', 'Swimming'),
        ('business', 'Business'),
        ('cocktail', 'Cocktail'),
        ('evening', 'Evening'),
        ('brunch', 'Brunch'),
        ('picnic', 'Picnic'),
        ('concert', 'Concert'),
        ('festival', 'Festival'),
        ('graduation', 'Graduation'),
        ('prom', 'Prom'),
        ('religious', 'Religious'),
        ('other', 'Other'),
    ]

    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='clothing_items',
        db_index=True
    )
    name = models.CharField(
        max_length=100, 
        validators=[
            MinLengthValidator(1, message="Name cannot be empty."),
            RegexValidator(
                regex=r'^[\w\s\-\']+$',
                message="Name can only contain letters, numbers, spaces, hyphens, and apostrophes.",
                code='invalid_name'
            )
        ]
    )
    category = models.ForeignKey(
        ClothingCategory,
        on_delete=models.SET_NULL,
        null=True,
        db_index=True
    )
    color = models.CharField(
        max_length=50,
        validators=[
            MinLengthValidator(2, message="Color must be at least 2 characters long.")
        ]
    )
    season = models.CharField(
        max_length=10, 
        choices=SEASON_CHOICES, 
        default='all'
    )
    fit = models.CharField(
        max_length=10,
        choices=FIT_CHOICES,
        default='regular'
    )
    fabric_type = models.CharField(max_length=50, blank=True)
    occasions = models.JSONField(default=list)

    # Image upload with validation
    image = models.ImageField(
        upload_to='wardrobe_items/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif'],
                message="Only .jpg, .jpeg, .png, and .gif files are allowed."
            )
        ]
    )

    # AI Features
    style = models.CharField(max_length=100, blank=True, null=True)
    color_palette = models.JSONField(default=list, blank=True, null=True)
    style_embedding = models.JSONField(default=dict, blank=True, null=True)
    trend_score = models.FloatField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(0.0, message="Trend score cannot be negative."),
            MaxValueValidator(10.0, message="Trend score cannot exceed 10.")
        ]
    )
    features = models.JSONField(default=dict, blank=True, null=True)  # Store extracted features

    # Processing status
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default='pending'
    )
    processing_error = models.TextField(blank=True)

    # Metadata fields
    purchase_date = models.DateField(
        null=True, 
        blank=True,
        validators=[
            MaxValueValidator(
                limit_value=timezone.now().date,
                message="Purchase date cannot be in the future."
            )
        ]
    )
    brand = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True, max_length=1000)

    # Tracking fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.category})"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Clothing Items"
        
    # def clean(self):
    #     from django.core.exceptions import ValidationError
    #     # Check if image is provided
    #     if not self.image:
    #         # We allow items without images, but show a warning message
    #         # Don't raise validation error here, just log a warning
    #         pass
    #     # Additional validation on JSONField
    #     if self.occasions and not isinstance(self.occasions, list):
    #         raise ValidationError({'occasions': 'Occasions must be stored as a list.'})
    #     # Validate color_palette is properly formatted
    #     if self.color_palette and not isinstance(self.color_palette, list):
    #         raise ValidationError({'color_palette': 'Color palette must be stored as a list.'})
    #     # Validate style_embedding is a dictionary
    #     if self.style_embedding and not isinstance(self.style_embedding, dict):
    #         raise ValidationError({'style_embedding': 'Style embedding must be stored as a dictionary.'})

class Outfit(models.Model):
    """Represents a combination of clothing items."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='outfits',
        db_index=True
    )
    name = models.CharField(
        max_length=100,
        validators=[
            MinLengthValidator(1, message="Name cannot be empty."),
            RegexValidator(
                regex=r'^[\w\s\-\']+$',
                message="Name can only contain letters, numbers, spaces, hyphens, and apostrophes.",
                code='invalid_name'
            )
        ]
    )
    items = models.ManyToManyField(ClothingItem)
    
    # Weather association
    suggested_temperature_min = models.FloatField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(-50, message="Temperature cannot be below -50°C."),
            MaxValueValidator(50, message="Temperature cannot be above 50°C.")
        ]
    )
    suggested_temperature_max = models.FloatField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(-50, message="Temperature cannot be below -50°C."),
            MaxValueValidator(50, message="Temperature cannot be above 50°C.")
        ]
    )
    
    # Compatibility score
    compatibility_score = models.FloatField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(0, message="Score cannot be negative."),
            MaxValueValidator(100, message="Score cannot exceed 100.")
        ]
    )

    # Template and sharing features
    is_template = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(
        User,
        related_name='shared_outfits',
        blank=True
    )
    favorited_by = models.ManyToManyField(
        User,
        related_name='favorite_outfits',
        blank=True
    )
    description = models.TextField(blank=True, max_length=1000)
    tags = models.JSONField(default=list, blank=True)
    template_category = models.CharField(
        max_length=50,
        choices=[
            ('casual', 'Casual'),
            ('formal', 'Formal'),
            ('work', 'Work'),
            ('sports', 'Sports'),
            ('party', 'Party'),
            ('special', 'Special Occasion'),
        ],
        blank=True,
        null=True
    )

    # Metadata fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_worn = models.DateField(
        null=True, 
        blank=True,
        validators=[
            MaxValueValidator(
                limit_value=timezone.now().date,
                message="Last worn date cannot be in the future."
            )
        ]
    )
    wear_count = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0, message="Wear count cannot be negative.")
        ]
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
        
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Check if temperature range is valid
        if (self.suggested_temperature_min is not None and 
            self.suggested_temperature_max is not None and 
            self.suggested_temperature_min > self.suggested_temperature_max):
            raise ValidationError({
                'suggested_temperature_min': 'Minimum temperature cannot be greater than maximum temperature.',
                'suggested_temperature_max': 'Maximum temperature cannot be less than minimum temperature.'
            })
            
        # Validate tags
        if self.tags:
            if not isinstance(self.tags, list):
                raise ValidationError({'tags': 'Tags must be stored as a list.'})
            if len(self.tags) > 20:
                raise ValidationError({'tags': 'Maximum of 20 tags allowed.'})
            for tag in self.tags:
                if not isinstance(tag, str):
                    raise ValidationError({'tags': 'Tags must be strings.'})
                if len(tag) > 50:
                    raise ValidationError({'tags': f"Tag '{tag}' is too long (maximum 50 characters)."})

    def increment_wear_count(self):
        """Increment the wear count and update the last worn date."""
        self.wear_count += 1
        self.last_worn = timezone.now().date()
        self.save()

    def share_with_user(self, user):
        """Share the outfit with another user."""
        if user != self.user:  # Don't share with the owner
            self.shared_with.add(user)

    def unshare_with_user(self, user):
        """Unshare the outfit with a user."""
        self.shared_with.remove(user)

    def toggle_favorite(self, user):
        """Toggle favorite status for a user."""
        if user in self.favorited_by.all():
            self.favorited_by.remove(user)
            return False  # Not favorited
        else:
            self.favorited_by.add(user)
            return True  # Favorited 