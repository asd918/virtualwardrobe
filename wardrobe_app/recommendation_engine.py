import logging
import random
from typing import List, Dict, Optional, Tuple
from django.db.models import Q
from django.contrib.auth.models import User
from .models import ClothingItem, ClothingCategory, Outfit
from .color_utils import is_color_similar
from .weather_utils import get_weather_data

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """
    A rule-based recommendation engine for generating outfit combinations.
    """
    
    def __init__(self):
        # Define core outfit categories that must be present
        self.core_categories = ['tops', 'bottoms']
        self.optional_categories = ['shoes', 'outerwear', 'accessories']
        
        # Color compatibility rules
        self.complementary_colors = {
            'red': ['green', 'teal'],
            'blue': ['orange', 'peach'],
            'yellow': ['purple', 'violet'],
            'green': ['red', 'pink'],
            'orange': ['blue', 'navy'],
            'purple': ['yellow', 'gold'],
            'pink': ['green', 'mint'],
            'navy': ['orange', 'coral'],
            'black': ['white', 'cream', 'beige', 'gray'],
            'white': ['black', 'navy', 'red', 'blue'],
            'gray': ['black', 'white', 'red', 'blue'],
            'brown': ['blue', 'navy', 'white', 'cream'],
            'beige': ['black', 'navy', 'brown', 'olive'],
            'olive': ['beige', 'cream', 'white', 'black']
        }
        
        # Analogous color groups (colors that work well together)
        self.analogous_colors = {
            'warm': ['red', 'orange', 'yellow', 'peach', 'coral', 'pink'],
            'cool': ['blue', 'green', 'teal', 'navy', 'purple', 'violet'],
            'neutral': ['black', 'white', 'gray', 'brown', 'beige', 'cream'],
            'earth': ['brown', 'beige', 'olive', 'tan', 'cream', 'khaki']
        }
        
        # Season compatibility matrix
        self.season_compatibility = {
            'summer': ['spring', 'autumn'],
            'winter': ['autumn', 'spring'],
            'spring': ['summer', 'autumn'],
            'autumn': ['spring', 'winter']
        }

    def get_rule_based_recommendations(self, user_id: int, max_outfits: int = 10, weather_data: Dict = None) -> List[Dict]:
        """
        Generate rule-based outfit recommendations for a user.
        
        Args:
            user_id (int): ID of the user to generate recommendations for
            max_outfits (int): Maximum number of outfits to generate
            weather_data (Dict): Current weather data for filtering
            
        Returns:
            List[Dict]: List of outfit dictionaries with item IDs and names
        """
        try:
            # Get user's clothing items
            user_items = self._get_user_wardrobe(user_id)
            if not user_items:
                logger.warning(f"No clothing items found for user {user_id}")
                return []
            
            # Apply weather-based filtering if weather data is available
            if weather_data:
                user_items = self._filter_items_by_weather(user_items, weather_data)
                if not user_items:
                    logger.warning(f"No weather-appropriate items found for user {user_id}")
                    return []
            
            # Group items by category
            categorized_items = self._categorize_items(user_items)
            
            # Generate outfit combinations
            outfits = self._generate_outfit_combinations(categorized_items, max_outfits)
            
            # Score and rank outfits
            scored_outfits = self._score_outfits(outfits)
            
            # Return top recommendations
            return scored_outfits[:max_outfits]
            
        except Exception as e:
            logger.exception(f"Error generating recommendations for user {user_id}: {e}")
            return []

    def _get_user_wardrobe(self, user_id: int) -> List[ClothingItem]:
        """
        Retrieve all clothing items from a user's wardrobe.
        
        Args:
            user_id (int): User ID
            
        Returns:
            List[ClothingItem]: List of user's clothing items
        """
        try:
            return list(ClothingItem.objects.filter(
                user_id=user_id,
                processing_status='completed'  # Only use processed items
            ).select_related('category'))
        except Exception as e:
            logger.exception(f"Error retrieving wardrobe for user {user_id}: {e}")
            return []

    def _filter_items_by_weather(self, items: List[ClothingItem], weather_data: Dict) -> List[ClothingItem]:
        """
        Filter clothing items based on current weather conditions.
        
        Args:
            items (List[ClothingItem]): List of clothing items
            weather_data (Dict): Current weather data
            
        Returns:
            List[ClothingItem]: Weather-appropriate items
        """
        if not weather_data or 'error' in weather_data:
            return items
        
        temperature = weather_data.get('temperature')
        description = weather_data.get('description', '').lower()
        
        if temperature is None:
            return items
        
        weather_appropriate_items = []
        
        for item in items:
            # Temperature-based filtering
            if temperature > 30:  # Hot weather
                if (item.fabric_type and any(fabric in item.fabric_type.lower() for fabric in ['cotton', 'linen', 'breathable']) or
                    item.category and item.category.name in ['tops', 'shorts', 'dresses'] or
                    item.season in ['summer', 'all']):
                    weather_appropriate_items.append(item)
                    
            elif 23 <= temperature <= 30:  # Warm weather
                if (item.fabric_type and any(fabric in item.fabric_type.lower() for fabric in ['cotton', 'denim', 'light']) or
                    item.season in ['summer', 'spring', 'all'] or
                    item.category and item.category.name in ['tops', 'bottoms', 'dresses']):
                    weather_appropriate_items.append(item)
                    
            elif 16 <= temperature <= 22:  # Cool weather
                if (item.fabric_type and any(fabric in item.fabric_type.lower() for fabric in ['cotton', 'denim', 'medium']) or
                    item.season in ['spring', 'autumn', 'all'] or
                    item.category and item.category.name in ['tops', 'bottoms', 'outerwear']):
                    weather_appropriate_items.append(item)
                    
            else:  # Cold weather (temperature < 16)
                if (item.fabric_type and any(fabric in item.fabric_type.lower() for fabric in ['wool', 'fleece', 'thermal', 'warm']) or
                    item.season in ['winter', 'autumn', 'all'] or
                    item.category and item.category.name in ['outerwear', 'sweaters', 'tops', 'bottoms']):
                    weather_appropriate_items.append(item)
            
            # Rain-specific filtering
            if 'rain' in description:
                if (item.category and item.category.name in ['outerwear', 'shoes'] or
                    item.fabric_type and 'waterproof' in item.fabric_type.lower()):
                    weather_appropriate_items.append(item)
        
        # If no weather-appropriate items found, return all items
        return weather_appropriate_items if weather_appropriate_items else items

    def _categorize_items(self, items: List[ClothingItem]) -> Dict[str, List[ClothingItem]]:
        """
        Group clothing items by their category.
        
        Args:
            items (List[ClothingItem]): List of clothing items
            
        Returns:
            Dict[str, List[ClothingItem]]: Items grouped by category
        """
        categorized = {}
        
        for item in items:
            if item.category:
                category_name = item.category.name
                if category_name not in categorized:
                    categorized[category_name] = []
                categorized[category_name].append(item)
        
        return categorized

    def _generate_outfit_combinations(self, categorized_items: Dict[str, List[ClothingItem]], 
                                   max_outfits: int) -> List[List[ClothingItem]]:
        """
        Generate outfit combinations following fashion rules.
        
        Args:
            categorized_items (Dict): Items grouped by category
            max_outfits (int): Maximum outfits to generate
            
        Returns:
            List[List[ClothingItem]]: List of outfit combinations
        """
        outfits = []
        
        # Get core category items
        tops = categorized_items.get('tops', [])
        bottoms = categorized_items.get('bottoms', [])
        shoes = categorized_items.get('shoes', [])
        outerwear = categorized_items.get('outerwear', [])
        accessories = categorized_items.get('accessories', [])
        
        if not tops or not bottoms:
            logger.warning("Cannot generate outfits without tops and bottoms")
            return outfits
        
        # Generate combinations
        combinations_generated = 0
        max_attempts = max_outfits * 3   # Limit attempts to avoid infinite loops
        
        for top in tops:
            for bottom in bottoms:
                if combinations_generated >= max_outfits:
                    break
                    
                # Check basic compatibility
                if not self._are_items_compatible(top, bottom):
                    continue
                
                # Create base outfit
                outfit = [top, bottom]
                
                # Add optional items
                outfit = self._add_optional_items(outfit, shoes, outerwear, accessories, categorized_items)
                
                # Check if outfit meets minimum requirements
                if self._is_valid_outfit(outfit):
                    outfits.append(outfit)
                    combinations_generated += 1
                
                if combinations_generated >= max_attempts:
                    break
            
            if combinations_generated >= max_outfits:
                break
        
        return outfits

    def _are_items_compatible(self, item1: ClothingItem, item2: ClothingItem) -> bool:
        """
        Check if two clothing items are compatible based on basic rules.
        
        Args:
            item1 (ClothingItem): First clothing item
            item2 (ClothingItem): Second clothing item
            
        Returns:
            bool: True if items are compatible
        """
        # Check color compatibility
        if not self._are_colors_compatible(item1.color, item2.color):
            return False
        
        # Check season compatibility
        if not self._are_seasons_compatible(item1.season, item2.season):
            return False
        
        # Check occasion compatibility
        if not self._are_occasions_compatible(item1.occasions, item2.occasions):
            return False
        
        return True

    def _are_colors_compatible(self, color1: str, color2: str) -> bool:
        """
        Check if two colors are compatible.
        
        Args:
            color1 (str): First color
            color2 (str): Second color
            
        Returns:
            bool: True if colors are compatible
        """
        if not color1 or not color2:
            return True  # Allow if color is not specified
        
        color1_lower = color1.lower()
        color2_lower = color2.lower()
        
        # Check if colors are the same
        if color1_lower == color2_lower:
            return True
        
        # Check complementary colors
        if color1_lower in self.complementary_colors:
            if color2_lower in self.complementary_colors[color1_lower]:
                return True
        
        # Check analogous colors
        for color_group in self.analogous_colors.values():
            if color1_lower in color_group and color2_lower in color_group:
                return True
        
        # Check if one is neutral (neutral colors go with everything)
        neutral_colors = ['black', 'white', 'gray', 'beige', 'cream', 'navy']
        if color1_lower in neutral_colors or color2_lower in neutral_colors:
            return True
        
        return False

    def _are_seasons_compatible(self, season1: str, season2: str) -> bool:
        """
        Check if two seasons are compatible.
        
        Args:
            season1 (str): First season
            season2 (str): Second season
            
        Returns:
            bool: True if seasons are compatible
        """
        if season1 == 'all' or season2 == 'all':
            return True
        
        if season1 == season2:
            return True
        
        if season1 in self.season_compatibility:
            if season2 in self.season_compatibility[season1]:
                return True
        
        return False

    def _are_occasions_compatible(self, occasions1: List[str], occasions2: List[str]) -> bool:
        """
        Check if two sets of occasions are compatible.
        
        Args:
            occasions1 (List[str]): First set of occasions
            occasions2 (List[str]): Second set of occasions
            
        Returns:
            bool: True if occasions are compatible
        """
        if not occasions1 or not occasions2:
            return True  # Allow if occasions are not specified
        
        # Check for overlapping occasions
        common_occasions = set(occasions1) & set(occasions2)
        if common_occasions:
            return True
        
        # Check for compatible occasion pairs
        compatible_pairs = [
            ('casual', 'casual'),
            ('work', 'business'),
            ('formal', 'formal'),
            ('party', 'party'),
            ('date', 'evening'),
            ('casual', 'work'),  # Smart casual
        ]
        
        for occ1 in occasions1:
            for occ2 in occasions2:
                if (occ1, occ2) in compatible_pairs or (occ2, occ1) in compatible_pairs:
                    return True
        
        return False

    def _add_optional_items(self, outfit: List[ClothingItem], shoes: List[ClothingItem], 
                          outerwear: List[ClothingItem], accessories: List[ClothingItem],
                          categorized_items: Dict[str, List[ClothingItem]]) -> List[ClothingItem]:
        """
        Add optional items to complete the outfit.
        
        Args:
            outfit (List[ClothingItem]): Current outfit
            shoes (List[ClothingItem]): Available shoes
            outerwear (List[ClothingItem]): Available outerwear
            accessories (List[ClothingItem]): Available accessories
            categorized_items (Dict): All categorized items
            
        Returns:
            List[ClothingItem]: Outfit with optional items added
        """
        # Add shoes if available and compatible
        if shoes:
            compatible_shoes = [shoe for shoe in shoes if self._is_item_compatible_with_outfit(shoe, outfit)]
            if compatible_shoes:
                outfit.append(random.choice(compatible_shoes))
        
        # Add outerwear if available and compatible
        if outerwear:
            compatible_outerwear = [ow for ow in outerwear if self._is_item_compatible_with_outfit(ow, outfit)]
            if compatible_outerwear:
                outfit.append(random.choice(compatible_outerwear))
        
        # Add accessories if available and compatible
        if accessories:
            compatible_accessories = [acc for acc in accessories if self._is_item_compatible_with_outfit(acc, outfit)]
            if compatible_accessories:
                # Add 1-2 accessories
                num_accessories = min(2, len(compatible_accessories))
                selected_accessories = random.sample(compatible_accessories, num_accessories)
                outfit.extend(selected_accessories)
        
        return outfit

    def _is_item_compatible_with_outfit(self, item: ClothingItem, outfit: List[ClothingItem]) -> bool:
        """
        Check if an item is compatible with the entire outfit.
        
        Args:
            item (ClothingItem): Item to check
            outfit (List[ClothingItem]): Current outfit
            
        Returns:
            bool: True if item is compatible with outfit
        """
        for outfit_item in outfit:
            if not self._are_items_compatible(item, outfit_item):
                return False
        return True

    def _is_valid_outfit(self, outfit: List[ClothingItem]) -> bool:
        """
        Check if an outfit meets minimum requirements.
        
        Args:
            outfit (List[ClothingItem]): Outfit to validate
            
        Returns:
            bool: True if outfit is valid
        """
        if len(outfit) < 2:
            return False
        
        # Must have at least one top and one bottom
        has_top = any(item.category and item.category.name == 'tops' for item in outfit)
        has_bottom = any(item.category and item.category.name == 'bottoms' for item in outfit)
        
        return has_top and has_bottom

    def _score_outfits(self, outfits: List[List[ClothingItem]]) -> List[Dict]:
        """
        Score and format outfits for display.
        
        Args:
            outfits (List[List[ClothingItem]]): List of outfit combinations
            
        Returns:
            List[Dict]: Scored and formatted outfits
        """
        scored_outfits = []
        
        for outfit in outfits:
            # Calculate compatibility score
            score = self._calculate_outfit_score(outfit)
            
            # Format outfit for display
            formatted_outfit = {
                'items': [
                    {
                        'id': item.id,
                        'name': item.name,
                        'category': item.category.name if item.category else 'Unknown',
                        'color': item.color,
                        'image_front_url': item.image_front.url if item.image_front else None,
                        'image_back_url': item.image_back.url if item.image_back else None,
                        'season': item.season,
                        'occasions': item.occasions
                    }
                    for item in outfit
                ],
                'score': score,
                'total_items': len(outfit)
            }
            
            scored_outfits.append(formatted_outfit)
        
        # Sort by score (highest first)
        scored_outfits.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_outfits

    def _calculate_outfit_score(self, outfit: List[ClothingItem]) -> float:
        """
        Calculate a compatibility score for an outfit.
        
        Args:
            outfit (List[ClothingItem]): Outfit to score
            
        Returns:
            float: Compatibility score (0-100)
        """
        if len(outfit) < 2:
            return 0.0
        
        score = 50.0  # Base score
        
        # Color compatibility bonus
        color_compatibility = 0
        for i, item1 in enumerate(outfit):
            for j, item2 in enumerate(outfit):
                if i != j:
                    if self._are_colors_compatible(item1.color, item2.color):
                        color_compatibility += 1
        
        color_score = (color_compatibility / (len(outfit) * (len(outfit) - 1))) * 20
        score += color_score
        
        # Season compatibility bonus
        season_compatibility = 0
        for i, item1 in enumerate(outfit):
            for j, item2 in enumerate(outfit):
                if i != j:
                    if self._are_seasons_compatible(item1.season, item2.season):
                        season_compatibility += 1
        
        season_score = (season_compatibility / (len(outfit) * (len(outfit) - 1))) * 15
        score += season_score
        
        # Occasion compatibility bonus
        occasion_compatibility = 0
        for i, item1 in enumerate(outfit):
            for j, item2 in enumerate(outfit):
                if i != j:
                    if self._are_occasions_compatible(item1.occasions, item2.occasions):
                        occasion_compatibility += 1
        
        occasion_score = (occasion_compatibility / (len(outfit) * (len(outfit) - 1))) * 15
        score += occasion_score
        
        return min(100.0, score)

# Convenience function for easy access
def get_rule_based_recommendations(user_id: int, max_outfits: int = 10, weather_data: Dict = None) -> List[Dict]:
    """
    Get rule-based outfit recommendations for a user.
    
    Args:
        user_id (int): User ID
        max_outfits (int): Maximum number of outfits to generate
        weather_data (Dict): Current weather data for filtering
        
    Returns:
        List[Dict]: List of outfit recommendations
    """
    engine = RecommendationEngine()
    return engine.get_rule_based_recommendations(user_id, max_outfits, weather_data) 