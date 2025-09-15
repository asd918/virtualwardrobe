from django.urls import path
from . import views

app_name = 'stylist_chatbot'

urlpatterns = [
    # Main chat interface
    path('', views.stylist_chat_view, name='chat_interface'),
    
    # API endpoints
    path('api/message/', views.chat_message_api, name='chat_message_api'),
    path('api/clear-history/', views.clear_chat_history, name='clear_chat_history'),
    path('api/history/', views.get_chat_history, name='get_chat_history'),
    
    # Dialogflow chatbot endpoint
    path('chatbot-response/', views.chatbot_response, name='chatbot_response'),
] 