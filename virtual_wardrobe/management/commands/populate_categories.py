from django.core.management.base import BaseCommand
from wardrobe_app.models import ClothingCategory

class Command(BaseCommand):
    help = 'Populates the clothing categories'

    def handle(self, *args, **kwargs):
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
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created category "{category_id}"')
            ) 