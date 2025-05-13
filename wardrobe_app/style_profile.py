import logging
from collections import Counter
from django.db.models import Count
from .models import ClothingItem, Outfit

logger = logging.getLogger(__name__)

class StyleProfileGenerator:
    """
    Generates a style profile for a user based on their wardrobe.
    """
    
    def __init__(self, user):
        """
        Initialize the StyleProfileGenerator.
        
        Args:
            user: User object to generate style profile for
        """
        self.user = user
        self.items = ClothingItem.objects.filter(user=user)
        self.outfits = Outfit.objects.filter(user=user)
    
    def generate_profile(self):
        """
        Generate a style profile for the user.
        
        Returns:
            dict: Style profile information
        """
        try:
            # Count items by category
            category_counts = self.items.values('category__name').annotate(
                count=Count('category')).order_by('-count')
            
            # Count items by color
            colors = [item.color for item in self.items if item.color]
            color_counts = Counter(colors).most_common(5)
            
            # Count items by style
            styles = [item.style for item in self.items if item.style]
            style_counts = Counter(styles).most_common(3)
            
            # Count items by season
            season_counts = self.items.values('season').annotate(
                count=Count('season')).order_by('-count')
            
            # Find favorite outfits (most worn)
            favorite_outfits = self.outfits.order_by('-wear_count')[:3]
            
            # Calculate average compatibility score
            avg_compat_score = 0
            if self.outfits.exists():
                avg_compat_score = sum(outfit.compatibility_score or 0 for outfit in self.outfits) / self.outfits.count()
            
            # Determine style preferences
            style_preferences = self._determine_style_preferences(style_counts)
            
            # Generate recommendations based on profile
            recommendations = self._generate_recommendations(
                category_counts, color_counts, style_counts, season_counts)
            
            return {
                'category_distribution': list(category_counts),
                'color_preferences': color_counts,
                'style_preferences': style_counts,
                'season_distribution': list(season_counts),
                'favorite_outfits': favorite_outfits,
                'avg_compatibility_score': avg_compat_score,
                'style_profile': style_preferences,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.exception(f"Error generating style profile: {e}")
            return {}
    
    def _determine_style_preferences(self, style_counts):
        """
        Determine overall style preferences based on item styles.
        
        Args:
            style_counts (list): List of (style, count) tuples
            
        Returns:
            dict: Style preferences information
        """
        # This is a simplified implementation
        # In a real application, this would be more sophisticated
        
        if not style_counts:
            return {
                'primary_style': 'Unknown',
                'description': 'Not enough data to determine style preferences.'
            }
        
        primary_style = style_counts[0][0]
        
        # Map style to description
        style_descriptions = {
            'Casual': 'You prefer comfortable, relaxed clothing for everyday wear.',
            'Formal': 'You value polished, sophisticated attire for a professional appearance.',
            'Business Casual': 'You balance professionalism with comfort in your wardrobe choices.',
            'Sporty': 'You prioritize athletic, functional clothing with a focus on performance.',
            'Bohemian': 'You favor artistic, unconventional clothing with natural fabrics and patterns.',
            'Vintage': 'You appreciate classic styles from past eras with timeless appeal.',
            'Minimalist': 'You prefer simple, clean lines with a focus on quality over quantity.',
            'Streetwear': 'You embrace urban, trendy elements with bold graphics and statement pieces.'
        }
        
        description = style_descriptions.get(
            primary_style, 
            'Your style is unique and personalized to your preferences.'
        )
        
        return {
            'primary_style': primary_style,
            'description': description
        }
    
    def _generate_recommendations(self, category_counts, color_counts, style_counts, season_counts):
        """
        Generate wardrobe recommendations based on the user's profile.
        
        Args:
            category_counts (list): Category distribution
            color_counts (list): Color preferences
            style_counts (list): Style preferences
            season_counts (list): Season distribution
            
        Returns:
            list: Recommendations
        """
        recommendations = []
        
        # Check for category imbalances
        if category_counts:
            top_category = category_counts[0]['category__name']
            if category_counts[0]['count'] > sum(c['count'] for c in category_counts[1:]):
                recommendations.append(
                    f"Your wardrobe is heavily focused on {top_category}. Consider adding more variety."
                )
        
        # Check for color variety
        if len(color_counts) <= 2 and sum(count for _, count in color_counts) >= 5:
            recommendations.append(
                "Your wardrobe has limited color variety. Consider introducing new colors."
            )
        
        # Check for seasonal gaps
        seasons = [s['season'] for s in season_counts]
        for season in ['Winter', 'Spring', 'Summer', 'Fall']:
            if season not in seasons:
                recommendations.append(
                    f"You have few or no items for {season}. Consider adding {season} appropriate clothing."
                )
        
        # Check for style consistency
        if style_counts and len(style_counts) >= 3:
            if style_counts[0][1] < 2 * style_counts[2][1]:
                recommendations.append(
                    "Your style preferences are quite varied. For a more cohesive wardrobe, consider focusing on fewer styles."
                )
        
        # Default recommendation if none generated
        if not recommendations:
            recommendations.append(
                "Your wardrobe appears well-balanced. Continue building your collection with pieces that complement your style."
            )
        
        return recommendations 