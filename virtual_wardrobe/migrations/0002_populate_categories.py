from django.db import migrations

def create_initial_categories(apps, schema_editor):
    ClothingCategory = apps.get_model('virtual_wardrobe', 'ClothingCategory')
    # First, clear existing categories
    ClothingCategory.objects.all().delete()
    
    categories = [
        ('tops', 'Tops - Shirts, T-shirts, Blouses, etc.'),
        ('bottoms', 'Bottoms - Pants, Shorts, Skirts, etc.'),
        ('dresses', 'Dresses - All types of dresses'),
        ('outerwear', 'Outerwear - Jackets, Coats, Sweaters, etc.'),
        ('shoes', 'Shoes - All types of footwear'),
        ('accessories', 'Accessories - Various fashion accessories'),
        ('underwear', 'Underwear - Undergarments'),
        ('swimwear', 'Swimwear - Swimming and beach wear'),
        ('activewear', 'Activewear - Sports and exercise clothing'),
        ('formalwear', 'Formal Wear - Suits, Evening gowns, etc.'),
        ('sleepwear', 'Sleepwear - Pajamas, Nightgowns, etc.'),
        ('bags', 'Bags - Handbags, Backpacks, etc.'),
        ('jewelry', 'Jewelry - Necklaces, Rings, etc.'),
        ('hats', 'Hats - All types of headwear'),
        ('gloves', 'Gloves - Hand protection and fashion'),
        ('scarves', 'Scarves - Neck scarves and wraps'),
        ('belts', 'Belts - Waist belts and accessories'),
        ('socks', 'Socks - All types of socks'),
        ('ties', 'Ties - Neckties and bow ties'),
        ('other', 'Other - Miscellaneous items'),
    ]
    
    for category_id, description in categories:
        ClothingCategory.objects.create(
            name=category_id,
            description=description
        )

def remove_categories(apps, schema_editor):
    ClothingCategory = apps.get_model('virtual_wardrobe', 'ClothingCategory')
    ClothingCategory.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('virtual_wardrobe', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_categories, remove_categories),
    ] 