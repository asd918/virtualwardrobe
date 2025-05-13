import requests
from django.conf import settings
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import numpy as np
from .models import ClothingItem, Outfit
from django.db.models import Count
from django.core.cache import cache

logger = logging.getLogger(__name__)

class TrendAnalysisService:
    """Service for analyzing fashion trends and providing trend-based recommendations."""
    
    def __init__(self):
        self.api_key = settings.FASHION_API_KEY
        self.trend_cache_timeout = 86400  # 24 hours
    
    def get_current_trends(self) -> Dict:
        """
        Fetch current fashion trends from external API.
        Returns cached data if available, otherwise makes new API request.
        """
        cache_key = 'current_fashion_trends'
        cached_trends = cache.get(cache_key)
        
        if cached_trends:
            return cached_trends
        
        try:
            # Example API endpoint - replace with actual fashion trend API
            url = f"https://api.fashiontrends.com/v1/trends"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            trends_data = response.json()
            cache.set(cache_key, trends_data, self.trend_cache_timeout)
            return trends_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching trend data: {e}")
            return {}

    def analyze_user_style_history(self, user) -> Dict:
        """
        Analyze user's style history based on their wardrobe items and outfits.
        """
        items = ClothingItem.objects.filter(user=user)
        
        # Analyze style preferences
        style_counts = items.values('style').annotate(count=Count('style'))
        color_counts = items.values('color').annotate(count=Count('color'))
        category_counts = items.values('category__name').annotate(count=Count('category'))
        
        # Calculate seasonal preferences
        season_counts = items.values('season').annotate(count=Count('season'))
        
        return {
            'style_distribution': {item['style']: item['count'] for item in style_counts if item['style']},
            'color_preferences': {item['color']: item['count'] for item in color_counts if item['color']},
            'category_distribution': {item['category__name']: item['count'] for item in category_counts},
            'seasonal_preferences': {item['season']: item['count'] for item in season_counts if item['season']},
        }

    def calculate_trend_compatibility_score(self, item: ClothingItem) -> float:
        """
        Calculate how well an item aligns with current trends.
        Returns a score between 0 and 1.
        """
        current_trends = self.get_current_trends()
        if not current_trends:
            return 0.5  # Default score if trends unavailable
        
        score = 0.0
        weights = {
            'style': 0.4,
            'color': 0.3,
            'category': 0.2,
            'season': 0.1
        }
        
        # Compare item attributes with trends
        if item.style and item.style.lower() in str(current_trends.get('trending_styles', '')).lower():
            score += weights['style']
            
        if item.color and item.color.lower() in str(current_trends.get('trending_colors', '')).lower():
            score += weights['color']
            
        if item.category and item.category.name.lower() in str(current_trends.get('trending_categories', '')).lower():
            score += weights['category']
            
        current_season = self._get_current_season()
        if item.season == current_season:
            score += weights['season']
        
        return min(score, 1.0)

    def identify_missing_trendy_items(self, user) -> List[Dict]:
        """
        Identify trending items that are missing from user's wardrobe.
        """
        current_trends = self.get_current_trends()
        user_items = ClothingItem.objects.filter(user=user)
        
        missing_trends = []
        if not current_trends:
            return missing_trends
        
        # Compare user's wardrobe with current trends
        trending_categories = current_trends.get('trending_categories', [])
        user_categories = set(user_items.values_list('category__name', flat=True))
        
        for category in trending_categories:
            if category.lower() not in [cat.lower() for cat in user_categories]:
                missing_trends.append({
                    'category': category,
                    'importance': 'high',
                    'reason': 'Currently trending category missing from wardrobe'
                })
        
        return missing_trends

    def recommend_trendy_additions(self, user) -> List[Dict]:
        """
        Recommend trendy items to add to the wardrobe based on current trends
        and user's style history.
        """
        user_history = self.analyze_user_style_history(user)
        current_trends = self.get_current_trends()
        missing_items = self.identify_missing_trendy_items(user)
        
        recommendations = []
        if not current_trends:
            return recommendations
        
        # Generate personalized recommendations
        for missing_item in missing_items:
            category = missing_item['category']
            trending_styles = current_trends.get('trending_styles', [])
            trending_colors = current_trends.get('trending_colors', [])
            
            # Find styles that match user preferences
            preferred_styles = sorted(
                user_history['style_distribution'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            for style, _ in preferred_styles:
                if style in trending_styles:
                    recommendations.append({
                        'category': category,
                        'style': style,
                        'colors': [color for color in trending_colors[:3]],
                        'priority': 'high',
                        'reason': f'Matches your style preferences and current trends'
                    })
        
        return recommendations

    def _get_current_season(self) -> str:
        """
        Determine the current season based on the date.
        """
        month = datetime.now().month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'

def get_current_trends() -> Dict:
    """
    Convenience function to get current trends using the TrendAnalysisService.
    """
    service = TrendAnalysisService()
    return service.get_current_trends()

def calculate_trend_compatibility_score(item: ClothingItem) -> float:
    """
    Convenience function to calculate trend compatibility score for an item.
    """
    service = TrendAnalysisService()
    return service.calculate_trend_compatibility_score(item)

def identify_missing_trendy_items(user) -> List[Dict]:
    """
    Convenience function to identify missing trendy items for a user.
    """
    service = TrendAnalysisService()
    return service.identify_missing_trendy_items(user)

def recommend_trendy_additions(user) -> List[Dict]:
    """
    Convenience function to get trend-based recommendations for a user.
    """
    service = TrendAnalysisService()
    return service.recommend_trendy_additions(user)
