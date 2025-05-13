import logging
import requests
import random
from collections import Counter
from django.utils import timezone
from datetime import timedelta
from .models import ClothingItem
from .ai_utils import calculate_trend_score

logger = logging.getLogger(__name__)

class TrendAnalysisService:
    """Service for analyzing fashion trends and making recommendations"""
    
    def __init__(self):
        self.trend_data = {}
        self.last_updated = None
    
    def get_trends(self, force_refresh=False):
        """
        Get current fashion trends.
        
        Args:
            force_refresh (bool): Whether to force refresh trend data
            
        Returns:
            dict: Current trend data
        """
        # Check if we need to refresh trend data
        if (force_refresh or 
            not self.trend_data or 
            not self.last_updated or 
            timezone.now() - self.last_updated > timedelta(days=7)):
            
            self.refresh_trend_data()
        
        return self.trend_data
    
    def refresh_trend_data(self):
        """
        Refresh trend data by fetching from external sources.
        In a real application, this would call fashion APIs or scrape trend sites.
        """
        try:
            # This is a mock implementation with hardcoded trends
            # In a real application, this would fetch from external sources
            
            self.trend_data = {
                'colors': [
                    # RGB values of trending colors
                    [34, 87, 122],  # Deep blue
                    [227, 181, 164],  # Blush
                    [163, 201, 163],  # Sage green
                    [230, 155, 3],  # Mustard
                    [122, 51, 77]   # Burgundy
                ],
                'styles': [
                    # Trending styles with weights (0-1)
                    ('Minimalist', 0.9),
                    ('Streetwear', 0.85),
                    ('Vintage', 0.8),
                    ('Business Casual', 0.75),
                    ('Bohemian', 0.7)
                ],
                'patterns': [
                    # Trending patterns with weights (0-1)
                    ('Floral', 0.85),
                    ('Stripes', 0.8),
                    ('Geometric', 0.75),
                    ('Animal Print', 0.7),
                    ('Plaid', 0.65)
                ],
                'fabric_types': [
                    # Trending fabrics with weights (0-1)
                    ('Linen', 0.9),
                    ('Organic Cotton', 0.85),
                    ('Recycled Polyester', 0.8),
                    ('Tencel', 0.75),
                    ('Hemp', 0.7)
                ],
                'categories': [
                    # Trending categories with weights (0-1)
                    ('Oversized Blazer', 0.9),
                    ('Wide-Leg Pants', 0.85),
                    ('Crop Top', 0.8),
                    ('Statement Coat', 0.75),
                    ('Chunky Boots', 0.7)
                ]
            }
            
            # Update last updated timestamp
            self.last_updated = timezone.now()
            
            logger.info("Fashion trend data refreshed successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Error refreshing trend data: {e}")
            return False

def get_current_trends():
    """
    Get current fashion trends.
    
    Returns:
        dict: Current trend data
    """
    service = TrendAnalysisService()
    return service.get_trends()

def calculate_trend_compatibility_score(items):
    """
    Calculate how well a set of items matches current trends.
    
    Args:
        items (list): List of ClothingItem objects
        
    Returns:
        float: Trend compatibility score between 0 and 1
    """
    try:
        if not items:
            return 0
        
        # Get current trends
        trends = get_current_trends()
        if not trends:
            return 0.5  # Neutral if no trend data
        
        # Calculate score for each item
        item_scores = []
        for item in items:
            # Extract item features
            item_features = {
                'avg_color': item.color,
                'style': item.style,
                'pattern': getattr(item, 'pattern', None),
                'fabric_type': getattr(item, 'fabric_type', None)
            }
            
            # Calculate individual item score
            item_score = calculate_trend_score(item_features, trends)
            item_scores.append(item_score)
        
        # Average of all item scores
        return sum(item_scores) / len(item_scores) if item_scores else 0
    
    except Exception as e:
        logger.exception(f"Error calculating trend compatibility: {e}")
        return 0.5

def identify_missing_trendy_items(user):
    """
    Identify trending item categories missing from user's wardrobe.
    
    Args:
        user: User object
        
    Returns:
        list: List of missing trend categories
    """
    try:
        # Get user's clothing items
        user_items = ClothingItem.objects.filter(user=user)
        
        # Get current trends
        trends = get_current_trends()
        if not trends or 'categories' not in trends:
            return []
        
        # Get user's item categories
        user_categories = [item.category.name for item in user_items if item.category]
        
        # Find trending categories not in user's wardrobe
        missing_categories = []
        for trend_category, weight in trends['categories']:
            # Check if user has any items in this category
            if not any(trend_category.lower() in category.lower() for category in user_categories):
                missing_categories.append((trend_category, weight))
        
        # Sort by trend weight
        missing_categories.sort(key=lambda x: x[1], reverse=True)
        
        return missing_categories
    
    except Exception as e:
        logger.exception(f"Error identifying missing trends: {e}")
        return []

def recommend_trendy_additions(user, limit=5):
    """
    Recommend trendy items to add to user's wardrobe.
    
    Args:
        user: User object
        limit (int): Maximum number of recommendations
        
    Returns:
        list: List of trend recommendations
    """
    try:
        # Get missing trend categories
        missing_trends = identify_missing_trendy_items(user)
        
        # Limit recommendations
        missing_trends = missing_trends[:limit]
        
        # Generate detailed recommendations
        recommendations = []
        trends = get_current_trends()
        
        for category, weight in missing_trends:
            # Get random trending color
            color = random.choice(trends['colors']) if trends.get('colors') else None
            color_name = _get_color_name(color) if color else "trending color"
            
            # Get random trending style
            style = random.choice(trends['styles'])[0] if trends.get('styles') else None
            
            # Create recommendation
            recommendation = {
                'category': category,
                'description': f"Add a {color_name} {style if style else ''} {category} to your wardrobe.",
                'trend_score': weight,
                'color': color,
                'style': style
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    except Exception as e:
        logger.exception(f"Error generating trend recommendations: {e}")
        return []

def _get_color_name(rgb):
    """
    Get a human-readable name for an RGB color.
    
    Args:
        rgb (list): RGB color value
        
    Returns:
        str: Color name
    """
    # This is a simplified implementation with basic color names
    if not rgb:
        return "unknown"
    
    r, g, b = rgb
    
    # Define color ranges (simplified)
    if max(r, g, b) < 50:
        return "black"
    if min(r, g, b) > 200:
        return "white"
    if r > 200 and g < 100 and b < 100:
        return "red"
    if r < 100 and g > 200 and b < 100:
        return "green"
    if r < 100 and g < 100 and b > 200:
        return "blue"
    if r > 200 and g > 200 and b < 100:
        return "yellow"
    if r > 200 and g < 100 and b > 200:
        return "magenta"
    if r < 100 and g > 200 and b > 200:
        return "cyan"
    if r > 200 and g > 100 and b < 100:
        return "orange"
    if r > 100 and g < 100 and b > 100:
        return "purple"
    if r > 100 and g > 100 and b < 100:
        return "brown"
    
    return "trendy" 