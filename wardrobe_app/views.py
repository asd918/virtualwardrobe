import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
import logging
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, AdminRegistrationForm, UserLoginForm, AdminLoginForm, UserProfileForm

from .models import ClothingCategory, ClothingItem, Outfit, UserProfile
from .forms import ClothingItemForm, OutfitForm, CategoryForm
from .weather_utils import get_weather_data, get_clothing_recommendations_based_on_weather
from .serializers import ClothingItemSerializer, OutfitSerializer
from .image_processing import preprocess_image, extract_features, classify_style
from .color_utils import generate_color_palette
from .style_profile import StyleProfileGenerator
# Added get_similar_items_for_item to import
from .recommendation_utils import calculate_compatibility_score, generate_outfit_combinations, personalize_recommendations, match_occasion, get_similar_items_for_item
from .trend_analysis import get_current_trends, calculate_trend_compatibility_score, identify_missing_trendy_items, recommend_trendy_additions, TrendAnalysisService
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from . import tasks
from .ai_utils import calculate_trend_score, get_style_embedding
from collections import Counter
from datetime import datetime
from .recommendation_engine import get_rule_based_recommendations

logger = logging.getLogger(__name__)

# Home view
def home(request):
    if request.user.is_authenticated:
        return redirect('wardrobe:wardrobe_view')
    return render(request, 'home.html')

def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Virtual Wardrobe.')
            return redirect('wardrobe:wardrobe_view')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    return render(request, 'wardrobe_app/register.html', {'form': form})

@login_required
def register_admin(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to register an admin.")
        return redirect('wardrobe:home')
    
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_staff = True
            user.is_superuser = True
            user.save()
            login(request, user)
            return redirect('admin:index')
    else:
        form = AdminRegistrationForm()
    return render(request, 'wardrobe_app/admin_register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('wardrobe:wardrobe_view')
            else:
                messages.error(request, "Invalid username or password")
        else:
            messages.error(request, "Invalid username or password")
    else:
        form = UserLoginForm()
    return render(request, 'wardrobe_app/login.html', {'form': form})

@login_required
def login_admin(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('wardrobe:home')
    
    if request.method == 'POST':
        form = AdminLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None and user.is_staff and user.is_superuser:
                login(request, user)
                return redirect('admin:index')
            else:
                messages.error(request, "Invalid username or password")
        else:
            messages.error(request, "Invalid username or password")
    else:
        form = AdminLoginForm()
    return render(request, 'wardrobe_app/admin_login.html', {'form': form})

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect('wardrobe:home')

@login_required
def user_profile(request):
    """View and update user profile information."""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # This shouldn't happen due to the signal, but just in case
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            try:
                profile = form.save(commit=False)
                # Run full validation on the model
                profile.full_clean()
                profile.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('wardrobe:user_profile')
            except Exception as e:
                messages.error(request, f"Error updating profile: {str(e)}")
        else:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserProfileForm(instance=profile)
    
    # Get style profile information
    try:
        style_profile = StyleProfileGenerator(request.user).generate_profile()
    except Exception as e:
        logger.error(f"Error generating style profile: {e}")
        style_profile = None
    
    # Get preferred colors and occasions for display
    preferred_colors = profile.preferred_colors.split(',') if profile.preferred_colors else []
    preferred_occasions = profile.preferred_occasions.split(',') if profile.preferred_occasions else []
    
    context = {
        'form': form,
        'profile': profile,
        'style_profile': style_profile,
        'preferred_colors': preferred_colors,
        'preferred_occasions': preferred_occasions,
    }
    return render(request, 'wardrobe_app/user_profile.html', context)

# Clothing Item views
@login_required
def item_list(request):
    # Get filter parameters
    category_id = request.GET.get('category')
    season = request.GET.get('season')
    style = request.GET.get('style')
    
    # Start with base queryset
    items = ClothingItem.objects.filter(user=request.user)
    
    # Apply filters
    if category_id:
        items = items.filter(category_id=category_id)
    if season:
        items = items.filter(season=season)
    if style:
        items = items.filter(style=style)
    
    # Get available categories for filter dropdown
    categories = ClothingCategory.objects.all()
    
    # Get available seasons and styles for filter dropdowns
    seasons = ClothingItem.SEASON_CHOICES
    styles = ClothingItem.objects.filter(user=request.user).exclude(style__isnull=True).values_list('style', flat=True).distinct()
    
    # Pagination
    paginator = Paginator(items, 12)  # Show 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'items': page_obj,
        'categories': categories,
        'seasons': seasons,
        'styles': styles,
        'selected_category': int(category_id) if category_id else None,
        'selected_season': season,
        'selected_style': style,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'wardrobe_app/item_list.html', context)

@login_required
def item_detail(request, item_id):
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    return render(request, 'wardrobe_app/item_detail.html', {'item': item})

@login_required
def add_item(request):
    if request.method == 'POST':
        form = ClothingItemForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                item = form.save(commit=False)
                item.user = request.user
                
                # Run full validation on the model
                item.full_clean()
                item.save()
                
                try:
                    # Process image synchronously instead of using Celery
                    if item.image_front:
                        # Extract features and classify style
                        img = preprocess_image(item.image_front.path)
                        features = extract_features(img)
                        style = classify_style(features)
                        
                        # Generate color palette
                        color_palette = generate_color_palette(img)
                        
                        # Update item with extracted information
                        item.style = style
                        item.color_palette = color_palette
                        item.features = features
                        item.processing_status = 'completed'
                        item.save()
                    
                    messages.success(request, 'Item added successfully!')
                except Exception as e:
                    item.processing_status = 'failed'
                    item.processing_error = str(e)
                    item.save()
                    messages.warning(request, f'Item added but image processing failed: {str(e)}. You can try updating the item later.')
            except Exception as e:
                messages.error(request, f'Error saving item: {str(e)}')
                return render(request, 'wardrobe_app/item_form.html', {'form': form, 'title': 'Add New Item'})
                
            return redirect('wardrobe:item_list')
        else:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ClothingItemForm()
    
    return render(request, 'wardrobe_app/item_form.html', {'form': form, 'title': 'Add New Item'})

@login_required
def edit_item(request, item_id):
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    
    if request.method == 'POST':
        form = ClothingItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item = form.save()
            
            # If front image was changed, trigger reprocessing
            if 'image_front' in form.changed_data:
                try:
                    if item.image_front:
                        # Process image synchronously
                        img = preprocess_image(item.image_front.path)
                        features = extract_features(img)
                        style = classify_style(features)
                        color_palette = generate_color_palette(img)
                        
                        item.style = style
                        item.color_palette = color_palette
                        item.features = features
                        item.processing_status = 'completed'
                        item.save()
                        messages.info(request, 'Image updated and processed successfully.')
                    else:
                        # Image was removed
                        item.style = None
                        item.color_palette = []
                        item.features = {}
                        item.processing_status = 'pending'
                        item.save()
                except Exception as e:
                    # Handle image processing error but still save the item
                    item.processing_status = 'failed'
                    item.processing_error = str(e)
                    item.save()
                    messages.warning(request, f'Item updated but image processing failed: {str(e)}.')
            
            messages.success(request, 'Item updated successfully!')
            return redirect('wardrobe:item_detail', item_id=item.id)
    else:
        form = ClothingItemForm(instance=item)
    
    return render(request, 'wardrobe_app/item_form.html', {'form': form, 'title': 'Edit Item'})

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted successfully!')
        return redirect('wardrobe:item_list')
    
    return render(request, 'wardrobe_app/item_delete.html', {'item': item})

# Category views
@login_required
def category_list(request):
    categories = ClothingCategory.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'wardrobe_app/category_list.html', context)

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!')
            return redirect('wardrobe:category_list')
    else:
        form = CategoryForm()

    context = {
        'form': form,
        'title': 'Add New Category',
    }
    return render(request, 'wardrobe_app/category_create.html', context)

@login_required
def category_update(request, category_id):
    category = get_object_or_404(ClothingCategory, pk=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('wardrobe:category_list')
    else:
        form = CategoryForm(instance=category)

    context = {
        'form': form,
        'category': category,
        'title': 'Edit Category',
    }
    return render(request, 'wardrobe_app/category_update.html', context)

@login_required
def category_delete(request, category_id):
    category = get_object_or_404(ClothingCategory, pk=category_id)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('wardrobe:category_list')

    context = {
        'category': category,
    }
    return render(request, 'wardrobe_app/category_delete.html', context)

# Outfit views
@login_required
def outfit_list(request):
    outfits = Outfit.objects.filter(user=request.user)
    context = {
        'outfits': outfits,
    }
    return render(request, 'wardrobe_app/outfit_list.html', context)

@login_required
def outfit_detail(request, outfit_id):
    outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
    context = {
        'outfit': outfit,
    }
    return render(request, 'wardrobe_app/outfit_detail.html', context)

@login_required
def outfit_create(request):
    if request.method == 'POST':
        form = OutfitForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                outfit = form.save(commit=False)
                outfit.user = request.user
                
                # Run full validation on the model
                outfit.full_clean()
                outfit.save()
                form.save_m2m()  # Save many-to-many relationships
                
                # Generate outfit recommendations
                occasion = form.cleaned_data.get('occasion', '')
                
                # Calculate compatibility score if not already set
                if not outfit.compatibility_score:
                    outfit_items = list(outfit.items.all())
                    if outfit_items:
                        compatibility_score = calculate_compatibility_score(outfit_items)
                        outfit.compatibility_score = compatibility_score
                        outfit.save()
                
                messages.success(request, 'Outfit created successfully!')
                return redirect('wardrobe:outfit_detail', outfit_id=outfit.id)
            except Exception as e:
                messages.error(request, f'Error saving outfit: {str(e)}')
        else:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = OutfitForm(user=request.user)
        
        # Add image URLs as data attributes to select options
        if form.fields['items'].queryset:
            item_choices = []
            for item in form.fields['items'].queryset:
                image_url = item.image_front.url if getattr(item, 'image_front', None) else ''
                item_choices.append((item.id, item.name, image_url))
            
            # Update widget choices with the same item data
            form.fields['items'].widget.choices = [(id, name) for id, name, _ in item_choices]
            # Add all item data as JSON
            form.fields['items'].widget.attrs['data-choices'] = json.dumps(
                [{'id': str(id), 'name': name, 'image_url': url} for id, name, url in item_choices]
            )
            
            # Log sample data for debugging
            if item_choices:
                logger.info(f"Sample item choice: {item_choices[0]}")

    # Get filter options
    categories = ClothingCategory.objects.all()
    seasons = ClothingItem.SEASON_CHOICES
    styles = ClothingItem.objects.filter(user=request.user).exclude(style__isnull=True).values_list('style', flat=True).distinct()

    context = {
        'form': form,
        'title': 'Create New Outfit',
        'categories': categories,
        'seasons': seasons,
        'styles': styles,
    }
    return render(request, 'wardrobe_app/outfit_create.html', context)

@login_required
def edit_outfit(request, outfit_id):
    outfit = get_object_or_404(Outfit, pk=outfit_id, user=request.user)

    if request.method == 'POST':
        form = OutfitForm(request.POST, instance=outfit, user=request.user)
        if form.is_valid():
            try:
                outfit = form.save(commit=False)
                
                # Run full validation on the model
                outfit.full_clean()
                outfit.save()
                form.save_m2m()  # Save many-to-many relationships
                
                # Recalculate compatibility score if items changed
                if 'items' in form.changed_data:
                    outfit_items = list(outfit.items.all())
                    if outfit_items:
                        compatibility_score = calculate_compatibility_score(outfit_items)
                        outfit.compatibility_score = compatibility_score
                        outfit.save()
                
                messages.success(request, 'Outfit updated successfully!')
                return redirect('wardrobe:outfit_detail', outfit_id=outfit.id)
            except Exception as e:
                messages.error(request, f'Error saving outfit: {str(e)}')
        else:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = OutfitForm(instance=outfit, user=request.user)

    context = {
        'form': form,
        'outfit': outfit,
        'title': 'Edit Outfit',
    }
    return render(request, 'wardrobe_app/outfit_edit.html', context)

@login_required
def delete_outfit(request, outfit_id):
    outfit = get_object_or_404(Outfit, pk=outfit_id, user=request.user)

    if request.method == 'POST':
        outfit.delete()
        messages.success(request, 'Outfit deleted successfully!')
        return redirect('wardrobe:outfit_list')

    context = {
        'outfit': outfit,
    }
    return render(request, 'wardrobe_app/outfit_delete.html', context)

# Wardrobe view - shown after login
@login_required
def wardrobe_view(request):
    cache_key = f'user_{request.user.id}_wardrobe'
    wardrobe_data = cache.get(cache_key)
    
    if wardrobe_data is None:
        items = ClothingItem.objects.filter(user=request.user).select_related('category')
        outfits = Outfit.objects.filter(user=request.user).prefetch_related(
            Prefetch('items', queryset=ClothingItem.objects.select_related('category'))
        )
        
        # Get weather data
        try:
            weather_data = get_weather_data(request.user.userprofile.location)
            recommendations = get_clothing_recommendations_based_on_weather(weather_data)
        except Exception as e:
            logger.error(f"Error getting weather data: {e}")
            weather_data = None
            recommendations = None
        
        # Get style profile
        try:
            style_profile = StyleProfileGenerator(request.user).generate_profile()
        except Exception as e:
            logger.error(f"Error generating style profile: {e}")
            style_profile = None
        
        wardrobe_data = {
            'items': items,
            'outfits': outfits,
            'weather_data': weather_data,
            'recommendations': recommendations,
            'style_profile': style_profile,
        }
        cache.set(cache_key, wardrobe_data, 300)  # Cache for 5 minutes
    else:
        items = wardrobe_data['items']
        outfits = wardrobe_data['outfits']
        weather_data = wardrobe_data['weather_data']
        recommendations = wardrobe_data['recommendations']
        style_profile = wardrobe_data['style_profile']
    
    context = {
        'items': items,
        'outfits': outfits,
        'weather_data': weather_data,
        'recommendations': recommendations,
        'style_profile': style_profile,
    }
    return render(request, 'wardrobe_app/wardrobe.html', context)

# Weather integration
def get_geocode(city):
	"""
	Deprecated: Geocoding not required for Visual Crossing timeline endpoint.
	Return None to indicate no geocode step.
	"""
	return None

def get_weather_data(city_input, units='metric'):
	"""
	Wrapper for Visual Crossing util function.
	"""
	from .weather_utils import get_weather_data as vc_get_weather
	return vc_get_weather(city_input, units=units)

@login_required
def weather_dashboard(request):
	city = request.GET.get('city', 'Kuala Lumpur')
	units = request.GET.get('units', 'metric')
	
	weather_data = get_weather_data(city, units=units)
	
	context = {
		'city': city,
		'units': units,
	}
	
	if weather_data is None or (isinstance(weather_data, dict) and 'error' in weather_data):
		error_msg = weather_data.get('error') if isinstance(weather_data, dict) else 'Unable to fetch weather data.'
		messages.error(request, error_msg)
		return render(request, 'wardrobe_app/weather_dashboard.html', context)
	
	recommendations = get_clothing_recommendations_based_on_weather(weather_data)
	
	# Suggested outfits by temperature (convert to Celsius if imperial requested)
	suggested_outfits = []
	if weather_data and weather_data.get('temperature') is not None:
		current_temp_c = weather_data['temperature']
		if units == 'imperial':
			current_temp_c = (current_temp_c - 32) * 5/9
		
		suggested_outfits = Outfit.objects.filter(
			user=request.user,
			suggested_temperature_min__lte=current_temp_c,
			suggested_temperature_max__gte=current_temp_c
		).prefetch_related('items')
	
	if not suggested_outfits:
		suggested_outfits = Outfit.objects.filter(user=request.user).order_by('-created_at')[:3]
	
	context.update({
		'weather_data': weather_data,
		'coordinates': weather_data.get('coordinates', {}),
		'suggested_outfits': suggested_outfits,
		'recommendations': recommendations,
	})
	
	return render(request, 'wardrobe_app/weather_dashboard.html', context)

# API views
@api_view(['GET'])
@login_required
def api_item_list(request):
    """API endpoint to get all clothing items for the authenticated user."""
    try:
        # Filter by user for security
        items = ClothingItem.objects.filter(user=request.user)
        
        # Apply optional filters from query parameters
        category = request.query_params.get('category')
        if category:
            items = items.filter(category__name=category)
            
        season = request.query_params.get('season')
        if season:
            items = items.filter(season=season)
            
        style = request.query_params.get('style')
        if style:
            items = items.filter(style=style)
        
        serializer = ClothingItemSerializer(items, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error in api_item_list: {str(e)}")
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@login_required
def api_outfit_list(request):
    """API endpoint to get all outfits for the authenticated user."""
    try:
        # Filter by user for security
        outfits = Outfit.objects.filter(user=request.user)
        
        # Apply optional filters from query parameters
        template_category = request.query_params.get('template_category')
        if template_category:
            outfits = outfits.filter(template_category=template_category)
            
        is_template = request.query_params.get('is_template')
        if is_template is not None:
            is_template_bool = str(is_template).lower() in ('true', '1', 't', 'y', 'yes')
            outfits = outfits.filter(is_template=is_template_bool)
        
        serializer = OutfitSerializer(outfits, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error in api_outfit_list: {str(e)}")
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
def api_weather(request):
	"""API endpoint to fetch weather data for a given city."""
	city = request.query_params.get('city', 'Kuala Lumpur')
	units = request.query_params.get('units', 'metric')
	
	if not city or len(str(city).strip()) == 0:
		return Response({"error": "City parameter is required"}, status=400)
	
	logger.info(f"Weather API request for: {city}, units: {units}")
	try:
		weather_data = get_weather_data(city, units=units)
		if weather_data is None:
			logger.warning(f"Unable to fetch weather data for {city}")
			return Response({
				"error": f"Unable to fetch weather data for {city}. Please check the city name and try again.",
				"weather": None,
				"recommendations": {},
				"message": ""
			}, status=200)
		
		if isinstance(weather_data, dict) and 'error' in weather_data:
			logger.warning(f"Weather API error for {city}: {weather_data['error']}")
			return Response({
				"error": weather_data['error'],
				"weather": None,
				"recommendations": {},
				"message": ""
			}, status=200)
		
		recommendations = get_clothing_recommendations_based_on_weather(weather_data)
		response_data = {
			'weather': weather_data,
			'recommendations': recommendations.get('recommendations', {}),
			'message': f"Weather data retrieved for {weather_data.get('city', city)}."
		}
		return Response(response_data, status=200)
	except Exception as e:
		logger.error(f"Error in weather API: {e}")
		return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@login_required
def get_outfit_suggestions(request):
    """
    API endpoint for getting smart suggestions based on selected items.
    """
    try:
        # Validate input parameters
        if not request.data:
            return Response({'error': 'No data provided'}, status=400)
            
        item_ids = request.data.get('item_ids', [])
        occasion = request.data.get('occasion')
        
        # Validate item_ids
        if not isinstance(item_ids, list):
            return Response({'error': 'item_ids must be a list'}, status=400)
            
        # Validate occasion if provided
        if occasion and not isinstance(occasion, str):
            return Response({'error': 'occasion must be a string'}, status=400)
            
        if occasion and len(occasion) > 50:
            return Response({'error': 'occasion string is too long'}, status=400)
        
        # Get the selected items and ensure they belong to the current user
        items = ClothingItem.objects.filter(id__in=item_ids, user=request.user)
        
        # Check if any items were found
        if not items:
            return Response({'error': 'No valid items found'}, status=400)
            
        # Check if all requested items were found
        if len(items) != len(item_ids):
            valid_ids = set(items.values_list('id', flat=True))
            invalid_ids = [id for id in item_ids if id not in valid_ids]
            logger.warning(f"User {request.user.id} requested suggestions for invalid item IDs: {invalid_ids}")
            # Continue with valid items instead of returning error
        
        # Calculate suggestions
        suggestions = {
            'color_coordination': calculate_color_coordination(items),
            'style_compatibility': calculate_style_compatibility(items),
            'weather_suitability': calculate_weather_suitability(items),
            'occasion_appropriateness': calculate_occasion_appropriateness(items, occasion)
        }
        
        # Add overall score
        scores = list(suggestions.values())
        suggestions['overall_score'] = sum(scores) / len(scores) if scores else 0
        
        return Response(suggestions)
        
    except Exception as e:
        logger.error(f"Error in get_outfit_suggestions: {str(e)}")
        return Response({'error': str(e)}, status=500)

def calculate_color_coordination(items):
    """
    Calculate color coordination score based on item color palettes.
    """
    if not items:
        return 0
    
    color_scores = []
    for item in items:
        if item.color_palette:
            # Compare with other items' color palettes
            for other_item in items:
                if other_item != item and other_item.color_palette:
                    # Simple color harmony calculation
                    # This could be enhanced with more sophisticated color theory
                    common_colors = set(item.color_palette) & set(other_item.color_palette)
                    if common_colors:
                        color_scores.append(1.0)
                    else:
                        # Check for complementary colors
                        color_scores.append(0.5)
    
    return sum(color_scores) / len(color_scores) if color_scores else 0

def calculate_style_compatibility(items):
    """
    Calculate style compatibility score based on item styles.
    """
    if not items:
        return 0
    
    style_scores = []
    for item in items:
        if item.style:
            for other_item in items:
                if other_item != item and other_item.style:
                    if item.style == other_item.style:
                        style_scores.append(1.0)
                    else:
                        style_scores.append(0.5)
    
    return sum(style_scores) / len(style_scores) if style_scores else 0

def calculate_weather_suitability(items):
    """
    Calculate weather suitability score based on item properties.
    """
    if not items:
        return 0
    
    # This is a simplified calculation
    # Could be enhanced with actual weather data and more sophisticated analysis
    scores = []
    for item in items:
        if item.fabric_type:
            # Example scoring based on fabric type
            if 'wool' in item.fabric_type.lower():
                scores.append(0.8)  # Good for cold weather
            elif 'cotton' in item.fabric_type.lower():
                scores.append(0.6)  # Good for moderate weather
            else:
                scores.append(0.4)  # Default score
    
    return sum(scores) / len(scores) if scores else 0

def calculate_occasion_appropriateness(items, occasion):
    """
    Calculate occasion appropriateness score.
    """
    if not items or not occasion:
        return 0
    
    scores = []
    for item in items:
        if item.occasions:
            if occasion in item.occasions:
                scores.append(1.0)
            else:
                scores.append(0.3)
    
    return sum(scores) / len(scores) if scores else 0

# Helper functions
def populate_categories(request):
    """Populate initial clothing categories."""
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('wardrobe:home')
    
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
    
    messages.success(request, f"Successfully created {len(categories)} categories!")
    return redirect('wardrobe:item_list')

@login_required
def trend_report(request):
    # Get user's clothing items
    user_items = ClothingItem.objects.filter(user=request.user)
    
    # Initialize trend data
    trend_data = {
        'overall_score': 0,
        'current_trends': {
            'styles': [],
            'colors': [],
            'categories': []
        },
        'style_analysis': {
            'preferred_styles': [],
            'color_preferences': [],
            'most_worn_categories': []
        },
        'trendy_items': [],
        'recommendations': {
            'suggested_additions': [],
            'missing_trends': []
        }
    }
    
    if user_items.exists():
        # Calculate overall trend score
        total_score = 0
        style_counts = Counter()
        color_counts = Counter()
        category_counts = Counter()
        
        trendy_items = []
        
        for item in user_items:
            # Get style embedding and calculate trend score
            if item.style_embedding:
                score = calculate_trend_score(item.style_embedding)
                total_score += score
                
                # Track item if it's trendy (score > 0.7)
                if score > 0.7:
                    trendy_items.append({
                        'item': item,
                        'score': score
                    })
            
            # Count styles, colors, and categories
            if item.style:
                style_counts[item.style] += 1
            if item.color:
                color_counts[item.color] += 1
            if item.category:
                category_counts[item.category.name] += 1
        
        # Calculate average trend score
        trend_data['overall_score'] = int((total_score / len(user_items)) * 100)
        
        # Get top styles, colors, and categories
        trend_data['style_analysis']['preferred_styles'] = style_counts.most_common(5)
        trend_data['style_analysis']['color_preferences'] = color_counts.most_common(5)
        trend_data['style_analysis']['most_worn_categories'] = category_counts.most_common(5)
        
        # Sort trendy items by score and get top 5
        trendy_items.sort(key=lambda x: x['score'], reverse=True)
        trend_data['trendy_items'] = trendy_items[:5]
        
        # Generate recommendations based on missing trends
        current_trends = [
            ('Sustainable Fashion', 'Eco-friendly and sustainable clothing options'),
            ('Oversized Fits', 'Comfortable and stylish oversized pieces'),
            ('Vintage Revival', 'Classic pieces with a modern twist'),
            ('Minimalist Basics', 'High-quality essential items'),
            ('Statement Accessories', 'Bold accessories to elevate outfits')
        ]
        
        # Check which trends the user is missing
        user_styles = set(style_counts.keys())
        missing_trends = [
            {'name': trend[0], 'description': trend[1]}
            for trend in current_trends
            if trend[0] not in user_styles
        ]
        trend_data['recommendations']['missing_trends'] = missing_trends
        
        # Generate suggested additions based on gaps in the wardrobe
        if 'Casual' not in style_counts:
            trend_data['recommendations']['suggested_additions'].append({
                'category': 'Casual Wear',
                'reason': 'Add versatile casual pieces for everyday styling'
            })
        if 'Formal' not in style_counts:
            trend_data['recommendations']['suggested_additions'].append({
                'category': 'Formal Wear',
                'reason': 'Include some formal options for special occasions'
            })
    
    return render(request, 'wardrobe_app/trend_report.html', {
        'trend_data': trend_data
    })

@login_required
def smart_recommender(request):
    # Get weather data
    try:
        # Try to get user's location from profile, default to Kuala Lumpur
        user_location = getattr(request.user.userprofile, 'location', 'Kuala Lumpur') if hasattr(request.user, 'userprofile') else 'Kuala Lumpur'
        weather_data = get_weather_data(user_location)
    except Exception as e:
        logger.error(f"Error getting weather data: {e}")
        weather_data = None

    # Get user's clothing items
    user_items = ClothingItem.objects.filter(
        user=request.user,
        processing_status='completed'  # Only use processed items
    ).select_related('category')
    
    # Initialize data structures
    recommended_outfits = []
    current_trends = []
    style_stats = {
        'preferred_styles': [],
        'color_preferences': []
    }
    suggestions = []
    weather_condition = None

    if user_items.exists():
        # Get outfit recommendations using the recommendation engine
        try:
            outfits = get_rule_based_recommendations(
                user_id=request.user.id, 
                max_outfits=12,
                weather_data=weather_data
            )
            recommended_outfits = outfits
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            recommended_outfits = []

        # Analyze current weather conditions
        weather_appropriate_items = []
        if weather_data and 'main' in weather_data and 'weather' in weather_data and weather_data['weather']:
            temp = weather_data['main'].get('temp')
            weather_condition = weather_data['weather'][0].get('main', '').lower()
            
            # Filter items based on weather
            if temp is not None:
                if temp < 15:  # Cold
                    weather_appropriate_items.extend(user_items.filter(
                        Q(category__name__in=['outerwear', 'sweaters']) |
                        Q(fabric_type__in=['wool', 'fleece', 'thermal'])
                    ))
                elif temp > 25:  # Hot
                    weather_appropriate_items.extend(user_items.filter(
                        Q(fabric_type__in=['cotton', 'linen']) |
                        Q(category__name__in=['tops', 'shorts', 'dresses'])
                    ))
                else:  # Moderate
                    weather_appropriate_items.extend(user_items.filter(
                        Q(season='all') | Q(fabric_type__in=['cotton', 'denim'])
                    ))

            # Additional weather-specific filters
            if weather_condition and 'rain' in weather_condition:
                weather_appropriate_items.extend(user_items.filter(
                    category__name__in=['outerwear', 'boots']
                ))
        else:
            # If no weather data, use all items
            weather_appropriate_items = list(user_items)

        # Get style statistics
        style_counts = Counter()
        color_counts = Counter()
        
        for item in user_items:
            if item.style:
                style_counts[item.style] += 1
            if item.color:
                color_counts[item.color] += 1

        style_stats['preferred_styles'] = [
            {'name': style, 'count': count}
            for style, count in style_counts.most_common(5)
        ]
        
        style_stats['color_preferences'] = [
            {'hex': color, 'count': count}
            for color, count in color_counts.most_common(5)
        ]

        # Current fashion trends (example trends - replace with actual API data)
        current_trends = [
            {
                'name': 'Sustainable Fashion',
                'description': 'Eco-friendly and sustainable clothing options'
            },
            {
                'name': 'Oversized Fits',
                'description': 'Comfortable and stylish oversized pieces'
            },
            {
                'name': 'Vintage Revival',
                'description': 'Classic pieces with a modern twist'
            }
        ]

        # Generate personalized suggestions
        suggestions = [
            {
                'title': 'Style Enhancement',
                'description': 'Try incorporating some trending styles into your current wardrobe.'
            },
            {
                'title': 'Color Coordination',
                'description': 'Add items that complement your most-worn color palette.'
            }
        ]

        # Add weather-specific suggestion only if weather data is available
        if weather_condition:
            suggestions.insert(0, {
                'title': 'Weather-Appropriate Items',
                'description': f"Consider adding more {weather_condition} appropriate items to your wardrobe."
            })

    context = {
        'weather_data': weather_data,
        'recommended_outfits': recommended_outfits,
        'current_trends': current_trends,
        'style_stats': style_stats,
        'suggestions': suggestions
    }
    
    return render(request, 'wardrobe_app/smart_recommender.html', context)

@login_required
def get_recommendations_api(request):
    """
    API endpoint to get outfit recommendations as JSON.
    Used for AJAX requests to refresh recommendations dynamically.
    """
    try:
        max_outfits = int(request.GET.get('max_outfits', 12))
        max_outfits = min(max_outfits, 20)  # Limit to prevent abuse
        
        # Get weather data for filtering
        weather_data = None
        try:
            user_location = getattr(request.user.userprofile, 'location', 'Kuala Lumpur') if hasattr(request.user, 'userprofile') else 'Kuala Lumpur'
            weather_data = get_weather_data(user_location)
        except Exception as e:
            logger.error(f"Error getting weather data for API: {e}")
        
        recommendations = get_rule_based_recommendations(
            user_id=request.user.id,
            max_outfits=max_outfits,
            weather_data=weather_data
        )
        
        return JsonResponse({
            'success': True,
            'recommendations': recommendations,
            'total_generated': len(recommendations)
        })
        
    except Exception as e:
        logger.error(f"Error getting recommendations for user {request.user.id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
