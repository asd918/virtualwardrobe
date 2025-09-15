# Generated manually to fix database schema mismatch

from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ClothingCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('tops', 'Tops'), ('bottoms', 'Bottoms'), ('dresses', 'Dresses'), ('outerwear', 'Outerwear'), ('shoes', 'Shoes'), ('accessories', 'Accessories'), ('underwear', 'Underwear'), ('swimwear', 'Swimwear'), ('activewear', 'Activewear'), ('formalwear', 'Formal Wear'), ('sleepwear', 'Sleepwear'), ('bags', 'Bags'), ('jewelry', 'Jewelry'), ('hats', 'Hats'), ('gloves', 'Gloves'), ('scarves', 'Scarves'), ('belts', 'Belts'), ('socks', 'Socks'), ('ties', 'Ties'), ('other', 'Other')], max_length=50, unique=True, validators=[django.core.validators.MinLengthValidator(3, message='Category name must be at least 3 characters long.')])),
                ('description', models.TextField(blank=True, max_length=500)),
            ],
            options={
                'verbose_name_plural': 'Clothing Categories',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preferred_colors', models.CharField(blank=True, max_length=255)),
                ('preferred_occasions', models.CharField(blank=True, max_length=255)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ClothingItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, validators=[django.core.validators.MinLengthValidator(1, message='Name cannot be empty.'), django.core.validators.RegexValidator(code='invalid_name', message='Name can only contain letters, numbers, spaces, hyphens, and apostrophes.', regex='^[\\w\\s\\-\\\']+$')])),
                ('color', models.CharField(max_length=50, validators=[django.core.validators.MinLengthValidator(2, message='Color must be at least 2 characters long.')])),
                ('season', models.CharField(choices=[('all', 'All Seasons'), ('summer', 'Summer'), ('winter', 'Winter'), ('spring', 'Spring'), ('autumn', 'Autumn')], default='all', max_length=10)),
                ('fit', models.CharField(choices=[('loose', 'Loose'), ('slim', 'Slim'), ('regular', 'Regular'), ('oversized', 'Oversized'), ('fitted', 'Fitted'), ('relaxed', 'Relaxed'), ('tapered', 'Tapered'), ('straight', 'Straight')], default='regular', max_length=10)),
                ('fabric_type', models.CharField(blank=True, max_length=50)),
                ('occasions', models.JSONField(default=list)),
                ('image_front', models.ImageField(blank=True, null=True, upload_to='wardrobe_items/', validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif'], message='Only .jpg, .jpeg, .png, and .gif files are allowed.')])),
                ('image_back', models.ImageField(blank=True, null=True, upload_to='wardrobe_items/', validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif'], message='Only .jpg, .jpeg, .png, and .gif files are allowed.')])),
                ('style', models.CharField(blank=True, max_length=100, null=True)),
                ('color_palette', models.JSONField(blank=True, default=list, null=True)),
                ('style_embedding', models.JSONField(blank=True, default=dict, null=True)),
                ('trend_score', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0, message='Trend score cannot be negative.'), django.core.validators.MaxValueValidator(10.0, message='Trend score cannot exceed 10.')])),
                ('features', models.JSONField(blank=True, default=dict, null=True)),
                ('processing_status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('processing_error', models.TextField(blank=True)),
                ('purchase_date', models.DateField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(limit_value=django.utils.timezone.now().date, message='Purchase date cannot be in the future.')])),
                ('brand', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True, max_length=1000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(db_index=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='wardrobe_app.clothingcategory')),
                ('user', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='clothing_items', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Clothing Items',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Outfit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, validators=[django.core.validators.MinLengthValidator(1, message='Name cannot be empty.'), django.core.validators.RegexValidator(code='invalid_name', message='Name can only contain letters, numbers, spaces, hyphens, and apostrophes.', regex='^[\\w\\s\\-\\\']+$')])),
                ('suggested_temperature_min', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(-50, message='Temperature cannot be below -50°C.'), django.core.validators.MaxValueValidator(50, message='Temperature cannot be above 50°C.')])),
                ('suggested_temperature_max', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(-50, message='Temperature cannot be below -50°C.'), django.core.validators.MaxValueValidator(50, message='Temperature cannot be above 50°C.')])),
                ('compatibility_score', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0, message='Score cannot be negative.'), django.core.validators.MaxValueValidator(100, message='Score cannot exceed 100.')])),
                ('is_template', models.BooleanField(default=False)),
                ('is_public', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True, max_length=1000)),
                ('tags', models.JSONField(blank=True, default=list)),
                ('template_category', models.CharField(blank=True, choices=[('casual', 'Casual'), ('formal', 'Formal'), ('work', 'Work'), ('sports', 'Sports'), ('party', 'Party'), ('special', 'Special Occasion')], max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_worn', models.DateField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(limit_value=django.utils.timezone.now().date, message='Last worn date cannot be in the future.')])),
                ('wear_count', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0, message='Wear count cannot be negative.')])),
                ('favorited_by', models.ManyToManyField(blank=True, related_name='favorite_outfits', to=settings.AUTH_USER_MODEL)),
                ('items', models.ManyToManyField(to='wardrobe_app.clothingitem')),
                ('shared_with', models.ManyToManyField(blank=True, related_name='shared_outfits', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='outfits', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
