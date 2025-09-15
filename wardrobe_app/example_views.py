"""
Example Django views showing how to integrate the recommendation engine.
This file demonstrates different ways to use the recommendation engine in your views.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages

# Import the recommendation engine
from .recommendation_engine import get_rule_based_recommendations, RecommendationEngine

@login_required
def outfit_recommendations_view(request):
    """
    View to display outfit recommendations for the logged-in user.
    """
    try:
        # Get recommendations using the convenience function
        recommendations = get_rule_based_recommendations(
            user_id=request.user.id,
            max_outfits=10
        )
        
        context = {
            'recommendations': recommendations,
            'user': request.user,
        }
        
        return render(request, 'wardrobe_app/outfit_recommendations.html', context)
        
    except Exception as e:
        messages.error(request, f"Error generating recommendations: {str(e)}")
        return render(request, 'wardrobe_app/outfit_recommendations.html', {
            'recommendations': [],
            'error': str(e)
        })

@login_required
def api_recommendations(request):
    """
    API endpoint to get outfit recommendations as JSON.
    Useful for AJAX requests or mobile apps.
    """
    try:
        max_outfits = int(request.GET.get('max_outfits', 10))
        max_outfits = min(max_outfits, 20)  # Limit to prevent abuse
        
        recommendations = get_rule_based_recommendations(
            user_id=request.user.id,
            max_outfits=max_outfits
        )
        
        return JsonResponse({
            'success': True,
            'recommendations': recommendations,
            'total_generated': len(recommendations)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def save_outfit_from_recommendation(request):
    """
    Save a recommended outfit combination to the user's saved outfits.
    """
    try:
        outfit_data = request.POST.get('outfit_data')
        outfit_name = request.POST.get('outfit_name', 'Recommended Outfit')
        
        if not outfit_data:
            return JsonResponse({
                'success': False,
                'error': 'No outfit data provided'
            }, status=400)
        
        # Parse outfit data and create Outfit object
        # This would depend on how you want to structure the data
        
        return JsonResponse({
            'success': True,
            'message': 'Outfit saved successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def personalized_recommendations_view(request):
    """
    View showing personalized recommendations with filtering options.
    """
    try:
        # Get filter parameters
        season = request.GET.get('season')
        occasion = request.GET.get('occasion')
        max_outfits = int(request.GET.get('max_outfits', 15))
        
        # Use the class-based approach for more control
        engine = RecommendationEngine()
        
        # Get base recommendations
        recommendations = engine.get_rule_based_recommendations(
            user_id=request.user.id,
            max_outfits=max_outfits
        )
        
        # Apply additional filtering if needed
        if season or occasion:
            filtered_recommendations = []
            for outfit in recommendations:
                # Filter by season
                if season:
                    season_match = any(
                        item.get('season') == season or item.get('season') == 'all'
                        for item in outfit['items']
                    )
                    if not season_match:
                        continue
                
                # Filter by occasion
                if occasion:
                    # This would require additional logic to check occasions
                    # For now, we'll include all outfits
                    pass
                
                filtered_recommendations.append(outfit)
            
            recommendations = filtered_recommendations
        
        context = {
            'recommendations': recommendations,
            'user': request.user,
            'filters': {
                'season': season,
                'occasion': occasion,
                'max_outfits': max_outfits
            }
        }
        
        return render(request, 'wardrobe_app/personalized_recommendations.html', context)
        
    except Exception as e:
        messages.error(request, f"Error generating personalized recommendations: {str(e)}")
        return render(request, 'wardrobe_app/personalized_recommendations.html', {
            'recommendations': [],
            'error': str(e)
        })

@login_required
def recommendation_stats_view(request):
    """
    View showing statistics about the user's wardrobe and recommendations.
    """
    try:
        from .models import ClothingItem
        
        # Get wardrobe statistics
        total_items = ClothingItem.objects.filter(user=request.user).count()
        items_by_category = {}
        
        for item in ClothingItem.objects.filter(user=request.user).select_related('category'):
            cat_name = item.category.name if item.category else 'uncategorized'
            if cat_name not in items_by_category:
                items_by_category[cat_name] = 0
            items_by_category[cat_name] += 1
        
        # Get some sample recommendations
        sample_recommendations = get_rule_based_recommendations(
            user_id=request.user.id,
            max_outfits=5
        )
        
        context = {
            'total_items': total_items,
            'items_by_category': items_by_category,
            'sample_recommendations': sample_recommendations,
            'can_generate_outfits': 'tops' in items_by_category and 'bottoms' in items_by_category
        }
        
        return render(request, 'wardrobe_app/recommendation_stats.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading recommendation statistics: {str(e)}")
        return render(request, 'wardrobe_app/recommendation_stats.html', {
            'error': str(e)
        })

# Example of how to use in a template context processor
def recommendation_context_processor(request):
    """
    Context processor to add recommendation data to all templates.
    Use this if you want to show recommendations in your base template.
    """
    if request.user.is_authenticated:
        try:
            # Get a few quick recommendations for the header/navbar
            quick_recommendations = get_rule_based_recommendations(
                user_id=request.user.id,
                max_outfits=3
            )
            
            return {
                'quick_recommendations': quick_recommendations,
                'has_recommendations': len(quick_recommendations) > 0
            }
        except:
            return {
                'quick_recommendations': [],
                'has_recommendations': False
            }
    
    return {
        'quick_recommendations': [],
        'has_recommendations': False
    } 