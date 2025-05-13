import logging
import random
from django.db.models import Q
from .models import ClothingItem, Outfit
from .color_utils import is_color_similar

logger = logging.getLogger(__name__)

def calculate_compatibility_score(outfit):
    """
    Calculate compatibility score for an outfit.
    
    Args:
        outfit (Outfit): Outfit to calculate score for
        
    Returns:
        float: Compatibility score between 0 and 1
    """
    try:
        if not outfit or not outfit.items.exists():
            return 0
            
        items = list(outfit.items.all())
        
        # Calculate various compatibility factors
        color_score = _calculate_color_compatibility(items)
        style_score = _calculate_style_compatibility(items)
        season_score = _calculate_season_compatibility(items)
        category_score = _calculate_category_completeness(items)
        
        # Weighted average of scores
        weights = {
            'color': 0.35,
            'style': 0.25,
            'season': 0.2,
            'category': 0.2
        }
        
        total_score = (
            color_score * weights['color'] +
            style_score * weights['style'] +
            season_score * weights['season'] +
            category_score * weights['category']
        )
        
        return round(total_score, 2)
    
    except Exception as e:
        logger.exception(f"Error calculating compatibility score: {e}")
        return 0

def _calculate_color_compatibility(items):
    """
    Calculate color compatibility among items.
    
    Args:
        items (list): List of ClothingItem objects
        
    Returns:
        float: Color compatibility score between 0 and 1
    """
    if not items:
        return 0
    
    try:
        # Count items with color information
        items_with_color = [item for item in items if item.color]
        if not items_with_color:
            return 0.5  # Neutral if no color info
            
        # Check for monochromatic (all same color)
        if len(set(item.color for item in items_with_color)) == 1:
            return 0.9
            
        # Check for complementary colors
        # This is a simplified implementation
        # In a real application, would use color theory
        
        # For now, we'll give a higher score if colors are different enough
        color_pairs = []
        for i, item1 in enumerate(items_with_color):
            for item2 in items_with_color[i+1:]:
                if not is_color_similar(item1.color, item2.color, threshold=50):
                    color_pairs.append(1.0)  # Different colors
                else:
                    color_pairs.append(0.7)  # Similar colors
        
        return sum(color_pairs) / len(color_pairs) if color_pairs else 0.5
    
    except Exception as e:
        logger.exception(f"Error calculating color compatibility: {e}")
        return 0.5

def _calculate_style_compatibility(items):
    """
    Calculate style compatibility among items.
    
    Args:
        items (list): List of ClothingItem objects
        
    Returns:
        float: Style compatibility score between 0 and 1
    """
    if not items:
        return 0
    
    try:
        # Count items with style information
        items_with_style = [item for item in items if item.style]
        if not items_with_style:
            return 0.5  # Neutral if no style info
            
        # Check if all items have the same style
        styles = set(item.style for item in items_with_style)
        if len(styles) == 1:
            return 1.0  # Perfect match
            
        # Check for complementary styles
        # This is a simplified implementation
        complementary_styles = {
            'Casual': ['Sporty', 'Streetwear'],
            'Formal': ['Business Casual', 'Minimalist'],
            'Business Casual': ['Formal', 'Minimalist'],
            'Sporty': ['Casual', 'Streetwear'],
            'Bohemian': ['Vintage', 'Casual'],
            'Vintage': ['Bohemian', 'Minimalist'],
            'Minimalist': ['Formal', 'Business Casual'],
            'Streetwear': ['Casual', 'Sporty']
        }
        
        # Calculate score based on style compatibility
        score = 0
        for style in styles:
            compatible = complementary_styles.get(style, [])
            other_styles = styles - {style}
            
            # Check how many styles are compatible
            overlap = len([s for s in other_styles if s in compatible])
            if overlap:
                score += overlap / len(other_styles)
            else:
                score += 0.3  # Some penalty for non-compatible styles
        
        return score / len(styles) if styles else 0.5
    
    except Exception as e:
        logger.exception(f"Error calculating style compatibility: {e}")
        return 0.5

def _calculate_season_compatibility(items):
    """
    Calculate season compatibility among items.
    
    Args:
        items (list): List of ClothingItem objects
        
    Returns:
        float: Season compatibility score between 0 and 1
    """
    if not items:
        return 0
    
    try:
        # Get seasons for all items
        seasons = [item.season for item in items if item.season]
        if not seasons:
            return 0.5  # Neutral if no season info
            
        # If all items are for the same season, perfect score
        if len(set(seasons)) == 1:
            return 1.0
            
        # Check for adjacent seasons (more compatible)
        adjacent_seasons = {
            'Winter': ['Fall', 'Spring'],
            'Spring': ['Winter', 'Summer'],
            'Summer': ['Spring', 'Fall'],
            'Fall': ['Summer', 'Winter']
        }
        
        # Calculate score based on season adjacency
        score = 0
        for i, season1 in enumerate(seasons):
            for season2 in seasons[i+1:]:
                if season1 == season2:
                    score += 1.0
                elif season2 in adjacent_seasons.get(season1, []):
                    score += 0.7
                else:
                    score += 0.3  # Opposite seasons
        
        # Normalize score
        pairs = len(seasons) * (len(seasons) - 1) / 2
        return score / pairs if pairs else 0.5
    
    except Exception as e:
        logger.exception(f"Error calculating season compatibility: {e}")
        return 0.5

def _calculate_category_completeness(items):
    """
    Calculate how complete the outfit is in terms of categories.
    
    Args:
        items (list): List of ClothingItem objects
        
    Returns:
        float: Category completeness score between 0 and 1
    """
    if not items:
        return 0
    
    try:
        # Get categories for all items
        categories = [item.category.name for item in items if item.category]
        
        # Define essential categories for a complete outfit
        essential_categories = ['Top', 'Bottom', 'Footwear']
        optional_categories = ['Outerwear', 'Accessory']
        
        # Calculate score based on category presence
        essentials_present = sum(1 for cat in essential_categories if any(cat in c for c in categories))
        optional_present = sum(1 for cat in optional_categories if any(cat in c for c in categories))
        
        # Prioritize essential categories
        score = (essentials_present / len(essential_categories)) * 0.8
        score += (optional_present / len(optional_categories)) * 0.2
        
        return score
    
    except Exception as e:
        logger.exception(f"Error calculating category completeness: {e}")
        return 0.5

def generate_outfit_combinations(user, occasion=None, temperature=None):
    """
    Generate outfit combinations based on various criteria.
    
    Args:
        user: User to generate outfits for
        occasion (str, optional): Occasion to match
        temperature (float, optional): Temperature to match
        
    Returns:
        Outfit: Generated outfit or None
    """
    try:
        # Get user's clothing items
        items = ClothingItem.objects.filter(user=user)
        
        if not items.exists():
            return None
            
        # Filter by occasion if specified
        if occasion:
            occasion_items = items.filter(occasions__icontains=occasion)
            if occasion_items.exists():
                items = occasion_items
        
        # Filter by temperature if specified
        if temperature is not None:
            # This is a simplified implementation
            # Ideally, this would use a more sophisticated temperature mapping
            if temperature < 5:  # Very cold
                season_items = items.filter(Q(season='Winter') | Q(fabric_type__icontains='Wool'))
            elif temperature < 15:  # Cold
                season_items = items.filter(Q(season='Winter') | Q(season='Fall'))
            elif temperature < 25:  # Moderate
                season_items = items.filter(Q(season='Spring') | Q(season='Fall'))
            else:  # Warm
                season_items = items.filter(Q(season='Summer') | Q(season='Spring'))
                
            if season_items.exists():
                items = season_items
        
        # Get category breakdown
        tops = items.filter(category__name__icontains='Top')
        bottoms = items.filter(category__name__icontains='Bottom')
        outerwear = items.filter(category__name__icontains='Outerwear')
        footwear = items.filter(category__name__icontains='Footwear')
        accessories = items.filter(category__name__icontains='Accessory')
        
        # Ensure we have at least tops and bottoms
        if not tops.exists() or not bottoms.exists():
            return None
            
        # Randomly select items from each category
        selected_items = []
        
        if tops.exists():
            selected_items.append(random.choice(list(tops)))
            
        if bottoms.exists():
            selected_items.append(random.choice(list(bottoms)))
            
        if outerwear.exists() and random.random() > 0.3:  # 70% chance to include outerwear
            selected_items.append(random.choice(list(outerwear)))
            
        if footwear.exists():
            selected_items.append(random.choice(list(footwear)))
            
        if accessories.exists() and random.random() > 0.5:  # 50% chance to include accessory
            selected_items.append(random.choice(list(accessories)))
        
        # Create outfit
        outfit_name = f"Suggested Outfit for {occasion}" if occasion else "Suggested Outfit"
        outfit = Outfit.objects.create(
            user=user,
            name=outfit_name,
            suggested_temperature_min=temperature - 5 if temperature else None,
            suggested_temperature_max=temperature + 5 if temperature else None
        )
        outfit.items.set(selected_items)
        
        # Calculate compatibility score
        outfit.compatibility_score = calculate_compatibility_score(outfit)
        outfit.save()
        
        return outfit
    
    except Exception as e:
        logger.exception(f"Error generating outfit combinations: {e}")
        return None

def personalize_recommendations(user, outfits):
    """
    Personalize outfit recommendations based on user preferences.
    
    Args:
        user: User to personalize for
        outfits (list): List of Outfit objects
        
    Returns:
        list: Personalized outfit recommendations
    """
    try:
        if not outfits:
            return []
            
        # Get user's frequently worn items and favorite outfits
        favorite_items = set(ClothingItem.objects.filter(
            user=user, wear_count__gt=0).order_by('-wear_count')[:10])
        
        # Sort outfits by compatibility score and presence of favorite items
        for outfit in outfits:
            # Boost score if outfit includes favorite items
            outfit_items = set(outfit.items.all())
            favorite_overlap = len(outfit_items.intersection(favorite_items))
            
            # Apply a small boost based on favorites (up to 0.1)
            boost = min(0.1, 0.02 * favorite_overlap)
            outfit.adjusted_score = (outfit.compatibility_score or 0) + boost
        
        # Sort by adjusted score
        return sorted(outfits, key=lambda o: o.adjusted_score if hasattr(o, 'adjusted_score') else 0, reverse=True)
    
    except Exception as e:
        logger.exception(f"Error personalizing recommendations: {e}")
        return outfits

def match_occasion(outfits, occasion):
    """
    Match outfits to a specific occasion.
    
    Args:
        outfits (list): List of Outfit objects
        occasion (str): Occasion to match
        
    Returns:
        list: Outfits that match the occasion
    """
    try:
        if not outfits or not occasion:
            return outfits
            
        matched_outfits = []
        
        for outfit in outfits:
            # Get occasion tags of all items in the outfit
            items = outfit.items.all()
            occasion_tags = []
            for item in items:
                if item.occasions:
                    occasion_tags.extend(item.occasions.split(','))
            
            # Check if the outfit matches the occasion
            if occasion.lower() in [tag.strip().lower() for tag in occasion_tags]:
                matched_outfits.append(outfit)
        
        return matched_outfits
    
    except Exception as e:
        logger.exception(f"Error matching occasion: {e}")
        return outfits

def get_similar_items_for_item(item, limit=5):
    """
    Get similar items for a given clothing item.
    
    Args:
        item (ClothingItem): Item to find similar items for
        limit (int): Maximum number of similar items to return
        
    Returns:
        list: List of similar ClothingItem objects
    """
    try:
        if not item:
            return []
            
        # Find items with similar properties
        similar_items = ClothingItem.objects.filter(
            user=item.user,
            category=item.category
        ).exclude(id=item.id)
        
        # Further filter by style, color, or season if available
        if item.style:
            similar_items = similar_items.filter(style=item.style)
            
        if item.color:
            # This would ideally use color similarity calculation
            similar_items = similar_items.filter(color=item.color)
            
        if item.season:
            similar_items = similar_items.filter(season=item.season)
        
        # Return limited results
        return list(similar_items[:limit])
    
    except Exception as e:
        logger.exception(f"Error getting similar items: {e}")
        return [] 