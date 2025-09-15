from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from .dialogflow_client import get_dialogflow_response, get_dialogflow_response_with_confidence
from wardrobe_app.recommendation_engine import get_rule_based_recommendations
from wardrobe_app.weather_utils import (
    get_weather_data,
    get_clothing_recommendations_based_on_weather,
)
from wardrobe_app.models import ClothingItem
from wardrobe_app.recommendation_engine import get_rule_based_recommendations
from wardrobe_app.weather_utils import (
    get_weather_data,
    get_clothing_recommendations_based_on_weather,
)
from wardrobe_app.models import ClothingItem
import json
import logging

logger = logging.getLogger(__name__)

@login_required
def stylist_chat_view(request):
    """
    Main view for the AI Stylist chatbot interface.
    """
    try:
        # Set current user ID in cache for Rasa actions to access
        cache.set('current_chat_user_id', request.user.id, 3600)  # 1 hour
        
        # Get user's chat history from cache
        chat_history = cache.get(f'stylist_chat_history_{request.user.id}', [])
        
        # Add welcome message if this is the first visit
        if not chat_history:
            welcome_message = {
                'message': "👗 Hello! I'm your AI Stylist, ready to help you look fabulous! I can:\n\n"
                          "• Suggest outfits from your wardrobe\n"
                          "• Give weather-appropriate fashion advice\n"
                          "• Share style tips and color coordination\n"
                          "• Help with casual or formal dressing\n\n"
                          "What would you like to know about fashion today? ✨",
                'type': 'welcome',
                'timestamp': 'now',
                'is_bot': True
            }
            chat_history = [welcome_message]
            # Cache the welcome message
            cache.set(f'stylist_chat_history_{request.user.id}', chat_history, 3600)  # 1 hour
        
        context = {
            'user': request.user,
            'chat_history': chat_history
        }
        
        return render(request, 'stylist_chatbot/chat_interface.html', context)
        
    except Exception as e:
        logger.error(f"Error in stylist chat view: {e}")
        return render(request, 'stylist_chatbot/chat_interface.html', {
            'user': request.user,
            'chat_history': [],
            'error': str(e)
        })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def chat_message_api(request):
    """
    API endpoint to handle chat messages and return Rasa bot responses.
    """
    try:
        # Set current user ID in cache for Rasa actions to access
        cache.set('current_chat_user_id', request.user.id, 3600)  # 1 hour
        
        # Parse the request data
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)
        
        # Generate session ID for Dialogflow
        session_id = f"user_{request.user.id}_{request.session.session_key or 'default'}"
        
        # Send message to Dialogflow
        dialogflow_response = send_message_to_dialogflow(message, session_id)
        
        if dialogflow_response.get('success'):
            bot_response = dialogflow_response['response']

            # Optional: override with domain logic based on recognized intent
            intent_override = handle_intent_with_business_logic(
                intent_name=dialogflow_response.get('intent', ''),
                parameters=dialogflow_response.get('parameters', {}),
                user_id=request.user.id,
            )
            if intent_override:
                bot_response = intent_override
            
            # If we overrode with business logic, carry that into the formatted payload
            formatted_response = {
                'message': bot_response,
                'type': 'dialogflow_response',
                'timestamp': 'now',
                'is_bot': True,
                'confidence': dialogflow_response.get('confidence', 0.0),
                'intent': dialogflow_response.get('intent', 'unknown')
            }
            
            # Update chat history in cache
            chat_history = cache.get(f'stylist_chat_history_{request.user.id}', [])
            
            # Add user message
            user_message = {
                'message': message,
                'type': 'user_message',
                'timestamp': 'now',
                'is_bot': False
            }
            chat_history.append(user_message)
            
            # Add bot response
            chat_history.append(formatted_response)
            
            # Keep only last 50 messages to prevent memory issues
            if len(chat_history) > 50:
                chat_history = chat_history[-50:]
            
            # Cache the updated history
            cache.set(f'stylist_chat_history_{request.user.id}', chat_history, 3600)  # 1 hour
            
            return JsonResponse({
                'success': True,
                'response': formatted_response,
                'chat_history': chat_history
            })
        else:
            return JsonResponse({
                'success': False,
                'error': dialogflow_response.get('error', 'Failed to get response from Dialogflow')
            }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error in chat message API: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

def send_message_to_dialogflow(message: str, session_id: str) -> dict:
    """
    Send message to Dialogflow and get response.
    """
    try:
        # Get response from Dialogflow
        dialogflow_response = get_dialogflow_response_with_confidence(session_id, message)
        
        if dialogflow_response and dialogflow_response.get('text'):
            return {
                'success': True,
                'response': dialogflow_response['text'],
                'confidence': dialogflow_response.get('confidence', 0.0),
                'intent': dialogflow_response.get('intent', 'unknown'),
                'parameters': dialogflow_response.get('parameters', {})
            }
        else:
            return {
                'success': False,
                'error': 'No response from Dialogflow'
            }
            
    except Exception as e:
        logger.error(f"Error communicating with Dialogflow: {e}")
        return {
            'success': False,
            'error': f'Error communicating with Dialogflow: {str(e)}'
        }


def handle_intent_with_business_logic(intent_name: str, parameters: dict, user_id: int) -> str:
    """
    Map Dialogflow intents to Django business logic.
    Returns a response string if we override the LLM reply; otherwise returns ''.
    """
    try:
        intent = (intent_name or '').lower()

        if intent in {'outfit recommendation', 'outfit_recommendation'}:
            outfits = get_rule_based_recommendations(user_id, max_outfits=3)
            if outfits:
                lines = ["Here are personalized outfits from your wardrobe:"]
                for i, outfit in enumerate(outfits, 1):
                    items_text = ", ".join([item.get('name') if isinstance(item, dict) else getattr(item, 'name', '') for item in outfit.get('items', [])])
                    lines.append(f"• Outfit {i}: {items_text}")
                return "\n".join(lines)
            return "I couldn't find enough wardrobe items yet. Upload more pieces to get personalized outfits."

        if intent in {'weather outfit', 'weather_outfit'}:
            city = parameters.get('city') if isinstance(parameters, dict) else None
            city = city or 'Kuala Lumpur'
            data = get_weather_data(city)
            if data and 'error' not in data:
                recs = get_clothing_recommendations_based_on_weather(data)
                return f"Weather in {data.get('city', city)} ~{round(data.get('temperature', 0))}°C, {data.get('description','')}. Suggestions: {', '.join(recs)}"
            return "I couldn't fetch the weather right now. Try again shortly."

        if intent in {'casual outfit', 'casual_outfit'}:
            tops = ClothingItem.objects.filter(user_id=user_id, processing_status='completed', category__name__icontains='top')[:2]
            bottoms = ClothingItem.objects.filter(user_id=user_id, processing_status='completed', category__name__icontains='bottom')[:2]
            if tops and bottoms:
                combos = []
                for t in tops:
                    for b in bottoms:
                        combos.append(f"{t.name} + {b.name}")
                return "Casual ideas:\n" + "\n".join([f"• {c}" for c in combos[:3]])
            return "Try pairing a cotton tee with jeans and white sneakers."

        if intent in {'formal outfit', 'formal_outfit'}:
            items = ClothingItem.objects.filter(user_id=user_id, processing_status='completed', category__name__iregex='(blazer|dress|suit|formal)')[:3]
            if items:
                lines = ["Formal pieces from your wardrobe:"] + [f"• {it.name}" for it in items]
                return "\n".join(lines)
            return "Consider a blazer, dress shirt, tailored pants, and dress shoes."

        # Color matching
        if intent in {'color matching', 'color_matching'}:
            color_param = ''
            if isinstance(parameters, dict):
                # Dialogflow may pass color as '@sys.color' or generic 'color'
                color_param = parameters.get('color') or parameters.get('@sys.color') or ''
            base = str(color_param).strip().lower()
            if not base:
                return "Great color question! Neutrals like white, black, gray, navy match most colors. Ask me about a specific color (e.g., what matches with red)."
            suggestions = {
                'red': ['navy', 'white', 'black', 'charcoal', 'denim'],
                'blue': ['khaki', 'white', 'gray', 'camel', 'tan'],
                'green': ['navy', 'white', 'beige', 'brown'],
                'yellow': ['navy', 'gray', 'white', 'denim'],
                'black': ['white', 'beige', 'camel', 'gray'],
                'white': ['denim', 'black', 'tan', 'olive'],
                'navy': ['white', 'khaki', 'gray', 'burgundy'],
                'brown': ['blue', 'white', 'cream', 'olive']
            }
            picks = suggestions.get(base, ['neutrals (white/black/gray)', 'denim'])
            response = f"{base.capitalize()} pairs well with: {', '.join(picks)}."
            # Wardrobe-aware examples if possible
            try:
                qs = ClothingItem.objects.filter(user_id=user_id, processing_status='completed')
                matched_items = []
                for p in picks:
                    item = qs.filter(color__icontains=p).first()
                    if item:
                        matched_items.append(item.name)
                    if len(matched_items) >= 3:
                        break
                if matched_items:
                    response += "\nFrom your wardrobe: " + ", ".join(matched_items)
            except Exception:
                pass
            return response

        # Occasion outfit
        if intent in {'occasion outfit', 'occasion_outfit'}:
            occasion = ''
            if isinstance(parameters, dict):
                occasion = parameters.get('occasion') or ''
            occasion = (occasion or '').lower()
            if 'party' in occasion:
                return "Party idea: statement shirt, dark trousers, and dress shoes or clean sneakers."
            if 'wedding' in occasion:
                return "Wedding guest: dark suit, dress shirt, polished shoes; add a pocket square."
            if 'work' in occasion or 'office' in occasion or 'business' in occasion:
                return "Workwear: blazer, collared shirt, chinos or dress pants, and loafers."
            return "Consider the venue and formality. I can suggest options if you specify the occasion (party, wedding, work)."

        return ''
    except Exception as e:
        logger.error(f"Intent handler error: {e}")
        return ''

@login_required
def clear_chat_history(request):
    """
    Clear the user's chat history.
    """
    try:
        cache_key = f'stylist_chat_history_{request.user.id}'
        cache.delete(cache_key)
        
        return JsonResponse({
            'success': True,
            'message': 'Chat history cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to clear chat history'
        }, status=500)

@login_required
def get_chat_history(request):
    """
    Get the user's chat history.
    """
    try:
        chat_history = cache.get(f'stylist_chat_history_{request.user.id}', [])
        
        return JsonResponse({
            'success': True,
            'chat_history': chat_history
        })
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get chat history'
        }, status=500)

@csrf_exempt
def chatbot_response(request):
    """
    Simple chatbot response endpoint for external use.
    """
    try:
        # Get message from GET parameter
        user_message = request.GET.get("message", "")
        session_id = request.session.session_key or "default"
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message parameter is required'
            }, status=400)
        
        # Get response from Dialogflow
        dialogflow_response = send_message_to_dialogflow(user_message, session_id)
        
        if dialogflow_response.get('success'):
            return JsonResponse({
                'success': True,
                'reply': dialogflow_response['response'],
                'confidence': dialogflow_response.get('confidence', 0.0),
                'intent': dialogflow_response.get('intent', 'unknown')
            })
        else:
            return JsonResponse({
                'success': False,
                'error': dialogflow_response.get('error', 'Failed to get response')
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in chatbot_response: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)
