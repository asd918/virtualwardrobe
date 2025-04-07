from django.urls import path
from . import views

app_name = 'wardrobe'

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    path('dashboard/', views.home, name='dashboard'),
    
    # Authentication
    path('register/', views.register_user, name='register'),
    path('admin-register/', views.register_admin, name='admin_register'),
    path('login/', views.login_user, name='login'),
    path('admin-login/', views.login_admin, name='admin_login'),
    path('logout/', views.logout_user, name='logout'),
    
    # Wardrobe main view (after login)
    path('my-wardrobe/', views.wardrobe_view, name='wardrobe_view'),
    
    # Clothing items
    path('items/', views.item_list, name='item_list'),
    path('items/add/', views.item_create, name='item_create'),
    path('items/<int:pk>/', views.item_detail, name='item_detail'),
    path('items/<int:pk>/edit/', views.item_update, name='item_update'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),
    
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    
    # Outfits
    path('outfits/', views.outfit_list, name='outfit_list'),
    path('outfits/add/', views.outfit_create, name='outfit_create'),
    path('outfits/<int:pk>/', views.outfit_detail, name='outfit_detail'),
    path('outfits/<int:pk>/edit/', views.outfit_update, name='outfit_update'),
    path('outfits/<int:pk>/delete/', views.outfit_delete, name='outfit_delete'),
    
    # Weather integration
    path('weather/', views.weather_dashboard, name='weather_dashboard'),
    
    # API endpoints
    path('api/items/', views.api_item_list, name='api_item_list'),
    path('api/outfits/', views.api_outfit_list, name='api_outfit_list'),
    path('api/weather/', views.api_weather, name='api_weather'),
]
