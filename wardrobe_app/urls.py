from django.urls import path
from django.contrib.auth import views as auth_views
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
    # User profile
    path('profile/', views.user_profile, name='user_profile'),
    # Password reset
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    # Wardrobe main view (after login)
    path('my-wardrobe/', views.wardrobe_view, name='wardrobe_view'),
    # Clothing items
    path('items/', views.item_list, name='item_list'),
    path('items/add/', views.add_item, name='add_item'),
    path('items/<int:item_id>/', views.item_detail, name='item_detail'),
    path('items/<int:item_id>/edit/', views.edit_item, name='edit_item'),
    path('items/<int:item_id>/delete/', views.delete_item, name='delete_item'),
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/edit/', views.category_update, name='category_update'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    path('categories/populate/', views.populate_categories, name='populate_categories'),
    # Outfits
    path('outfits/', views.outfit_list, name='outfit_list'),
    path('outfits/add/', views.outfit_create, name='outfit_create'),
    path('outfits/<int:outfit_id>/', views.outfit_detail, name='outfit_detail'),
    path('outfits/<int:outfit_id>/edit/', views.edit_outfit, name='edit_outfit'),
    path('outfits/<int:outfit_id>/delete/', views.delete_outfit, name='delete_outfit'),
    # Weather integration
    path('weather/', views.weather_dashboard, name='weather_dashboard'),
    # API endpoints
    path('api/items/', views.api_item_list, name='api_item_list'),
    path('api/outfits/', views.api_outfit_list, name='api_outfit_list'),
    path('api/outfits/suggestions/', views.get_outfit_suggestions, name='api_outfit_suggestions'),
    path('api/weather/', views.api_weather, name='api_weather'),
    # Smart Recommender and Trend Report
    path('recommender/', views.smart_recommender, name='smart_recommender'),
    path('trends/', views.trend_report, name='trend_report'),
] 