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
from .forms import UserRegistrationForm, AdminRegistrationForm, UserLoginForm, AdminLoginForm

from .models import ClothingCategory, ClothingItem, Outfit
from .forms import ClothingItemForm, OutfitForm, CategoryForm

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
            return redirect('wardrobe:wardrobe_view')
    else:
        form = UserRegistrationForm()
    return render(request, 'wardrobe_app/register.html', {'form': form})

def register_admin(request):
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

def login_admin(request):
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
    return redirect('home')

# Clothing Item views
@login_required
def item_list(request):
    items = ClothingItem.objects.filter(user=request.user)
    categories = ClothingCategory.objects.all()

    # Filter by category if provided
    category_id = request.GET.get('category')
    if category_id:
        items = items.filter(category_id=category_id)

    # Filter by season if provided
    season = request.GET.get('season')
    if season:
        items = items.filter(season=season)

    context = {
        'items': items,
        'categories': categories,
        'seasons': ClothingItem.SEASON_CHOICES,
    }
    return render(request, 'wardrobe_app/item_list.html', context)

@login_required
def item_detail(request, pk):
    item = get_object_or_404(ClothingItem, pk=pk, user=request.user)
    outfits = item.outfit_set.all()
    context = {
        'item': item,
        'outfits': outfits,
    }
    return render(request, 'wardrobe_app/item_detail.html', context)

@login_required
def item_create(request):
    if request.method == 'POST':
        form = ClothingItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, 'Item added successfully!')
            return redirect('wardrobe:item_detail', pk=item.pk)
    else:
        form = ClothingItemForm()

    context = {
        'form': form,
        'title': 'Add New Item',
    }
    return render(request, 'wardrobe_app/item_create.html', context)

@login_required
def item_update(request, pk):
    item = get_object_or_404(ClothingItem, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ClothingItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item updated successfully!')
            return redirect('wardrobe:item_detail', pk=item.pk)
    else:
        form = ClothingItemForm(instance=item)

    context = {
        'form': form,
        'item': item,
        'title': 'Edit Item',
    }
    return render(request, 'wardrobe_app/item_update.html', context)

@login_required
def item_delete(request, pk):
    item = get_object_or_404(ClothingItem, pk=pk, user=request.user)

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted successfully!')
        return redirect('wardrobe:item_list')

    context = {
        'item': item,
    }
    return render(request, 'wardrobe_app/item_delete.html', context)

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

# Outfit views
@login_required
def outfit_list(request):
    outfits = Outfit.objects.filter(user=request.user)
    context = {
        'outfits': outfits,
    }
    return render(request, 'wardrobe_app/outfit_list.html', context)

@login_required
def outfit_detail(request, pk):
    outfit = get_object_or_404(Outfit, pk=pk, user=request.user)
    context = {
        'outfit': outfit,
    }
    return render(request, 'wardrobe_app/outfit_detail.html', context)

@login_required
def outfit_create(request):
    if request.method == 'POST':
        form = OutfitForm(request.POST, user=request.user)
        if form.is_valid():
            outfit = form.save(commit=False)
            outfit.user = request.user
            outfit.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Outfit created successfully!')
            return redirect('wardrobe:outfit_detail', pk=outfit.pk)
    else:
        form = OutfitForm(user=request.user)

    context = {
        'form': form,
        'title': 'Create New Outfit',
    }
    return render(request, 'wardrobe_app/outfit_create.html', context)

@login_required
def outfit_update(request, pk):
    outfit = get_object_or_404(Outfit, pk=pk, user=request.user)

    if request.method == 'POST':
        form = OutfitForm(request.POST, instance=outfit, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Outfit updated successfully!')
            return redirect('wardrobe:outfit_detail', pk=outfit.pk)
    else:
        form = OutfitForm(instance=outfit, user=request.user)

    context = {
        'form': form,
        'outfit': outfit,
        'title': 'Edit Outfit',
    }
    return render(request, 'wardrobe_app/outfit_update.html', context)

@login_required
def outfit_delete(request, pk):
    outfit = get_object_or_404(Outfit, pk=pk, user=request.user)

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
    # Get counts
    item_count = ClothingItem.objects.filter(user=request.user).count()
    outfit_count = Outfit.objects.filter(user=request.user).count()
    category_count = ClothingCategory.objects.count()
    
    # Get recent items
    recent_items = ClothingItem.objects.filter(user=request.user).order_by('-created_at')[:6]
    
    # Get weather data
    city = request.GET.get('city', 'Kuala Lumpur')  # Default to Kuala Lumpur
    weather_data = get_weather_data(city)
    
    # Get outfits suitable for the current temperature
    suggested_outfits = []
    if weather_data and 'main' in weather_data and 'temp' in weather_data['main']:
        current_temp = weather_data['main']['temp']
        suggested_outfits = Outfit.objects.filter(
            user=request.user,
            suggested_temperature_min__lte=current_temp,
            suggested_temperature_max__gte=current_temp
        )
    
    context = {
        'item_count': item_count,
        'outfit_count': outfit_count,
        'category_count': category_count,
        'recent_items': recent_items,
        'weather_data': weather_data,
        'suggested_outfits': suggested_outfits,
    }
    return render(request, 'wardrobe_app/wardrobe.html', context)

# Weather integration
@login_required
def weather_dashboard(request):
    city = request.GET.get('city', 'Kuala Lumpur')  # Default to Kuala Lumpur
    weather_data = get_weather_data(city)

    # Get outfits suitable for the current temperature
    suggested_outfits = []
    if weather_data and 'main' in weather_data and 'temp' in weather_data['main']:
        current_temp = weather_data['main']['temp']
        suggested_outfits = Outfit.objects.filter(
            user=request.user,
            suggested_temperature_min__lte=current_temp,
            suggested_temperature_max__gte=current_temp
        )

    context = {
        'weather_data': weather_data,
        'city': city,
        'suggested_outfits': suggested_outfits,
    }
    return render(request, 'wardrobe_app/weather_dashboard.html', context)

# API views
@api_view(['GET'])
@login_required
def api_item_list(request):
    items = ClothingItem.objects.filter(user=request.user)
    data = [{
        'id': item.id,
        'name': item.name,
        'category': item.category.name if item.category else None,
        'color': item.color,
        'season': item.season,
        'image_url': request.build_absolute_uri(item.image.url) if item.image else None,
    } for item in items]
    return Response(data)

@api_view(['GET'])
@login_required
def api_outfit_list(request):
    items = Outfit.objects.filter(user=request.user)
    data = [{
        'id': item.id,
        'name': item.name,
        'items': [item.id for item in outfit.items.all()],
        'suggested_temperature_min': outfit.suggested_temperature_min,
        'suggested_temperature_max': outfit.suggested_temperature_max,
    } for item in items]
    return Response(data)

@api_view(['GET'])
@login_required
def api_weather(request):
    city = request.GET.get('city', 'Kuala Lumpur')
    weather_data = get_weather_data(city)
    return Response(data)

# Helper functions
def get_weather_data(city):
    api_key = settings.OPENWEATHERMAP_API_KEY
    if not api_key:
        logger.error("OpenWeatherMap API key not configured")
        return None

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {e}")
        return None
