# Recommendation Engine Documentation

## Overview

The `recommendation_engine.py` module provides a rule-based system for generating outfit combinations from a user's wardrobe. It uses fashion theory principles to create compatible outfit combinations based on color harmony, season compatibility, and occasion appropriateness.

## Features

- **Rule-based outfit generation**: Creates outfits following fashion rules
- **Color compatibility**: Implements complementary and analogous color theory
- **Season matching**: Ensures seasonal appropriateness
- **Occasion filtering**: Considers occasion compatibility
- **Scoring system**: Ranks outfits by compatibility score
- **Django integration**: Seamlessly works with Django ORM and models

## Quick Start

### Basic Usage

```python
from wardrobe_app.recommendation_engine import get_rule_based_recommendations

# Get outfit recommendations for a user
recommendations = get_rule_based_recommendations(user_id=123, max_outfits=10)

# Each recommendation contains:
# - items: List of clothing items with IDs, names, categories, colors
# - score: Compatibility score (0.0 to 1.0)
# - total_items: Number of items in the outfit
```

### Class-based Usage

```python
from wardrobe_app.recommendation_engine import RecommendationEngine

# Create engine instance
engine = RecommendationEngine()

# Get recommendations
recommendations = engine.get_rule_based_recommendations(user_id=123, max_outfits=10)
```

## API Reference

### `get_rule_based_recommendations(user_id, max_outfits=10)`

**Parameters:**
- `user_id` (int): ID of the user to generate recommendations for
- `max_outfits` (int): Maximum number of outfits to generate (default: 10)

**Returns:**
- `List[Dict]`: List of outfit dictionaries

**Example Response:**
```python
[
    {
        "items": [
            {
                "id": 1,
                "name": "Blue T-Shirt",
                "category": "tops",
                "color": "blue",
                "image_url": "/media/wardrobe_items/blue_tshirt.jpg"
            },
            {
                "id": 5,
                "name": "Black Jeans",
                "category": "bottoms",
                "color": "black",
                "image_url": "/media/wardrobe_items/black_jeans.jpg"
            }
        ],
        "score": 0.875,
        "total_items": 2
    }
]
```

## Fashion Rules Implemented

### Color Compatibility

#### Complementary Colors
- Red ↔ Green/Teal
- Blue ↔ Orange/Peach
- Yellow ↔ Purple/Violet
- Green ↔ Red/Pink
- Orange ↔ Blue/Navy
- Purple ↔ Yellow/Gold

#### Analogous Color Groups
- **Warm**: Red, Orange, Yellow, Peach, Coral, Pink
- **Cool**: Blue, Green, Teal, Navy, Purple, Violet
- **Neutral**: Black, White, Gray, Brown, Beige, Cream
- **Earth**: Brown, Beige, Olive, Tan, Cream, Khaki

#### Neutral Colors
Neutral colors (Black, White, Gray, Brown, Beige, Cream, Navy) go with everything.

### Season Compatibility
- Summer ↔ Spring, Autumn
- Winter ↔ Autumn, Spring
- Spring ↔ Summer, Autumn
- Autumn ↔ Spring, Winter

### Outfit Structure Rules
- **Required**: At least one top and one bottom
- **Optional**: Shoes, outerwear, accessories
- **Maximum**: Recommended 5 items per outfit

## Integration with Django Views

### Basic View Integration

```python
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .recommendation_engine import get_rule_based_recommendations

@login_required
def outfit_recommendations(request):
    recommendations = get_rule_based_recommendations(
        user_id=request.user.id,
        max_outfits=10
    )
    
    return render(request, 'outfit_recommendations.html', {
        'recommendations': recommendations
    })
```

### API Endpoint

```python
from django.http import JsonResponse

def api_recommendations(request):
    recommendations = get_rule_based_recommendations(
        user_id=request.user.id,
        max_outfits=int(request.GET.get('max_outfits', 10))
    )
    
    return JsonResponse({
        'success': True,
        'recommendations': recommendations
    })
```

### Context Processor

```python
# settings.py
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... other context processors
                'wardrobe_app.example_views.recommendation_context_processor',
            ],
        },
    },
]
```

## Customization

### Extending Color Rules

```python
class CustomRecommendationEngine(RecommendationEngine):
    def __init__(self):
        super().__init__()
        
        # Add custom color rules
        self.complementary_colors.update({
            'teal': ['coral', 'peach'],
            'mint': ['rose', 'pink']
        })
        
        # Add custom analogous groups
        self.analogous_colors['pastel'] = ['mint', 'lavender', 'peach', 'cream']
```

### Custom Scoring

```python
class CustomRecommendationEngine(RecommendationEngine):
    def _calculate_outfit_score(self, outfit):
        # Get base score
        base_score = super()._calculate_outfit_score(outfit)
        
        # Add custom scoring logic
        brand_bonus = self._calculate_brand_bonus(outfit)
        trend_bonus = self._calculate_trend_bonus(outfit)
        
        # Combine scores
        final_score = (base_score * 0.7) + (brand_bonus * 0.2) + (trend_bonus * 0.1)
        return min(final_score, 1.0)
```

## Performance Considerations

### Database Optimization
- The engine uses `select_related('category')` to minimize database queries
- Only processes items with `processing_status='completed'`
- Limits the number of outfit combinations to prevent infinite loops

### Caching Recommendations
```python
from django.core.cache import cache

def get_cached_recommendations(user_id, max_outfits=10):
    cache_key = f"outfit_recommendations_{user_id}_{max_outfits}"
    
    # Try to get from cache first
    recommendations = cache.get(cache_key)
    if recommendations is None:
        # Generate new recommendations
        recommendations = get_rule_based_recommendations(user_id, max_outfits)
        # Cache for 1 hour
        cache.set(cache_key, recommendations, 3600)
    
    return recommendations
```

## Testing

### Run the Test Script

```bash
# From your Django project directory
python manage.py shell < wardrobe_app/test_recommendation_engine.py
```

### Unit Testing

```python
from django.test import TestCase
from django.contrib.auth.models import User
from .recommendation_engine import RecommendationEngine

class RecommendationEngineTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.engine = RecommendationEngine()
    
    def test_basic_recommendations(self):
        recommendations = self.engine.get_rule_based_recommendations(
            user_id=self.user.id,
            max_outfits=5
        )
        self.assertIsInstance(recommendations, list)
```

## Troubleshooting

### Common Issues

1. **No recommendations generated**
   - Check if user has clothing items
   - Ensure items have proper categories (especially 'tops' and 'bottoms')
   - Verify items have `processing_status='completed'`

2. **Performance issues**
   - Reduce `max_outfits` parameter
   - Implement caching
   - Check database indexes on user_id and category fields

3. **Color compatibility not working**
   - Verify color values in database match expected format
   - Check for case sensitivity in color names
   - Ensure colors are properly normalized

### Debug Mode

```python
import logging
logging.getLogger('wardrobe_app.recommendation_engine').setLevel(logging.DEBUG)

# This will show detailed information about the recommendation process
```

## Future Enhancements

- **Machine Learning Integration**: Use user preferences and wear history
- **Weather Integration**: Consider current weather conditions
- **Style Profiles**: Personalized style preferences
- **Social Features**: Share and rate outfit combinations
- **Trend Analysis**: Incorporate current fashion trends

## Support

For issues or questions about the recommendation engine:
1. Check the Django logs for error messages
2. Verify your database schema matches the expected models
3. Test with the provided test script
4. Review the fashion rules implementation for your use case 