from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests
import json
import os
import sys

# Add the parent directory to the path to import Django modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual_wardrobe.settings')
import django
django.setup()

# Import Django models and utilities
from wardrobe_app.models import ClothingItem, ClothingCategory
from wardrobe_app.recommendation_engine import get_rule_based_recommendations
from wardrobe_app.weather_utils import get_weather_data, get_clothing_recommendations_based_on_weather
from django.contrib.auth.models import User
from django.core.cache import cache

def get_current_user_wardrobe():
    """
    Get clothing items for the current Django session user or return sample wardrobe.
    Returns sample items if no user is logged in or no items found.
    """
    try:
        # Try to get user from cache (set by Django view)
        user_id = cache.get('current_chat_user_id')
        
        if user_id:
            # Get user's wardrobe from database
            items = list(ClothingItem.objects.filter(
                user_id=user_id,
                processing_status='completed'
            ).select_related('category'))
            
            if items:
                return items, f"user_{user_id}"
        
        # Fallback to sample wardrobe for demo/guest mode
        sample_items = [
            {
                'name': 'Blue Cotton T-shirt',
                'category': 'tops',
                'color': 'blue',
                'season': 'all',
                'fabric_type': 'cotton',
                'occasions': ['casual', 'work']
            },
            {
                'name': 'White Button-down Shirt',
                'category': 'tops',
                'color': 'white',
                'season': 'all',
                'fabric_type': 'cotton',
                'occasions': ['work', 'formal', 'casual']
            },
            {
                'name': 'Black Jeans',
                'category': 'bottoms',
                'color': 'black',
                'season': 'all',
                'fabric_type': 'denim',
                'occasions': ['casual', 'work']
            },
            {
                'name': 'Khaki Chino Pants',
                'category': 'bottoms',
                'color': 'beige',
                'season': 'all',
                'fabric_type': 'cotton',
                'occasions': ['casual', 'work', 'formal']
            },
            {
                'name': 'White Sneakers',
                'category': 'shoes',
                'color': 'white',
                'season': 'all',
                'fabric_type': 'canvas',
                'occasions': ['casual', 'work']
            },
            {
                'name': 'Black Dress Shoes',
                'category': 'shoes',
                'color': 'black',
                'season': 'all',
                'fabric_type': 'leather',
                'occasions': ['formal', 'work']
            },
            {
                'name': 'Navy Blazer',
                'category': 'outerwear',
                'color': 'navy',
                'season': 'all',
                'fabric_type': 'wool',
                'occasions': ['formal', 'work']
            },
            {
                'name': 'Gray Sweater',
                'category': 'outerwear',
                'color': 'gray',
                'season': 'winter',
                'fabric_type': 'wool',
                'occasions': ['casual', 'work']
            },
            {
                'name': 'Red Polo Shirt',
                'category': 'tops',
                'color': 'red',
                'season': 'summer',
                'fabric_type': 'cotton',
                'occasions': ['casual', 'work']
            },
            {
                'name': 'Brown Leather Belt',
                'category': 'accessories',
                'color': 'brown',
                'season': 'all',
                'fabric_type': 'leather',
                'occasions': ['casual', 'work', 'formal']
            }
        ]
        
        return sample_items, "sample_wardrobe"
        
    except Exception as e:
        print(f"Error getting wardrobe: {e}")
        # Return sample items as fallback
        return [
            {
                'name': 'Blue T-shirt',
                'category': 'tops',
                'color': 'blue',
                'season': 'all',
                'fabric_type': 'cotton',
                'occasions': ['casual']
            },
            {
                'name': 'Black Jeans',
                'category': 'bottoms',
                'color': 'black',
                'season': 'all',
                'fabric_type': 'denim',
                'occasions': ['casual']
            }
        ], "fallback"

def get_current_weather(city="Kuala Lumpur"):
    """
    Get current weather data for outfit suggestions.
    """
    try:
        weather_data = get_weather_data(city)
        if 'error' not in weather_data:
            return weather_data
        return None
    except Exception as e:
        print(f"Error getting weather: {e}")
        return None

class ActionOutfitSuggestion(Action):
    def name(self) -> Text:
        return "action_outfit_suggestion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Get user's wardrobe
            wardrobe_items, user_type = get_current_user_wardrobe()
            
            # Get current weather for context
            weather_data = get_current_weather()
            
            response = "Here are some great outfit suggestions for you:\n\n"
            
            if user_type != "guest" and wardrobe_items:
                # Try to get personalized recommendations
                try:
                    user_id = cache.get('current_chat_user_id')
                    if user_id:
                        outfits = get_rule_based_recommendations(user_id, max_outfits=3)
                        if outfits:
                            response += "**Personalized from your wardrobe:**\n"
                            for i, outfit in enumerate(outfits[:3], 1):
                                items_text = ", ".join([item['name'] for item in outfit['items']])
                                response += f"• **Outfit {i}**: {items_text}\n"
                            response += "\n"
                except Exception as e:
                    print(f"Error getting personalized recommendations: {e}")
            elif user_type == "sample_wardrobe":
                response += "**Sample wardrobe suggestions:**\n"
                # Create outfit combinations from sample items
                tops = [item for item in wardrobe_items if item['category'] == 'tops']
                bottoms = [item for item in wardrobe_items if item['category'] == 'bottoms']
                shoes = [item for item in wardrobe_items if item['category'] == 'shoes']
                outerwear = [item for item in wardrobe_items if item['category'] == 'outerwear']
                
                # Generate outfit combinations
                outfit_count = 0
                for top in tops[:2]:
                    for bottom in bottoms[:2]:
                        if outfit_count >= 3:
                            break
                        outfit_items = [top['name'], bottom['name']]
                        
                        # Add shoes if available
                        if shoes:
                            outfit_items.append(shoes[0]['name'])
                        
                        # Add outerwear if available and weather-appropriate
                        if outerwear and weather_data:
                            temp = weather_data.get('temperature')
                            if temp and temp < 20:  # Cool weather
                                outfit_items.append(outerwear[0]['name'])
                        
                        response += f"• **Outfit {outfit_count + 1}**: {' + '.join(outfit_items)}\n"
                        outfit_count += 1
                
                response += "\n"
            elif user_type == "fallback":
                response += "**Basic outfit suggestions:**\n"
                response += "• **Casual Look**: Blue T-shirt + Black Jeans + Sneakers\n"
                response += "• **Smart Casual**: White Button-down + Khaki Pants + Loafers\n"
                response += "• **Professional**: White Shirt + Black Pants + Dress Shoes\n\n"
            
            # Add weather-aware suggestions
            if weather_data:
                temp = weather_data.get('temperature')
                desc = weather_data.get('description', '')
                city = weather_data.get('city', 'your location')
                
                response += f"**Weather-aware suggestions for {city} ({round(temp)}°C, {desc}):**\n"
                
                if temp > 30:
                    response += "• **Hot Weather**: Light cotton t-shirt + breathable shorts + sandals\n"
                    response += "• **Stay Cool**: Tank top + flowy skirt + comfortable shoes\n"
                elif 23 <= temp <= 30:
                    response += "• **Warm Weather**: T-shirt + light pants + sneakers\n"
                    response += "• **Casual Comfort**: Polo shirt + chinos + loafers\n"
                elif 16 <= temp <= 22:
                    response += "• **Cool Weather**: Long-sleeve shirt + jeans + light jacket\n"
                    response += "• **Layered Look**: Sweater + collared shirt + comfortable pants\n"
                else:  # temp < 16
                    response += "• **Cold Weather**: Warm sweater + insulated jacket + long pants\n"
                    response += "• **Winter Ready**: Thermal shirt + coat + warm accessories\n"
                
                if 'rain' in desc.lower():
                    response += "• **Rain Protection**: Add waterproof jacket and umbrella\n"
                
                response += "\n"
            
            # Add general suggestions
            response += "**Classic Combinations:**\n"
            response += "• **Casual Day**: T-shirt + jeans + sneakers\n"
            response += "• **Smart Casual**: Button-down + chinos + loafers\n"
            response += "• **Professional**: Blazer + dress shirt + dress pants\n"
            response += "• **Weekend Style**: Graphic tee + denim jacket + comfortable pants\n\n"
            
            response += "**Styling Tips:**\n"
            response += "• Mix and match your existing pieces\n"
            response += "• Consider the occasion and weather\n"
            response += "• Don't forget comfortable shoes\n"
            response += "• Accessorize to complete your look!"
            
            dispatcher.utter_message(text=response)
            
        except Exception as e:
            dispatcher.utter_message(text="I'm having trouble generating outfit suggestions right now. Try asking for style tips instead!")
        
        return []

class ActionWeatherOutfit(Action):
    def name(self) -> Text:
        return "action_weather_outfit"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Get weather condition from entities or use current weather
            weather_entities = [entity['value'] for entity in tracker.latest_message['entities'] 
                               if entity['entity'] == 'weather_condition']
            
            if weather_entities:
                weather = weather_entities[0].lower()
                response = self._get_weather_specific_advice(weather)
            else:
                # Get current weather data
                weather_data = get_current_weather()
                if weather_data and 'error' not in weather_data:
                    temp = weather_data.get('temperature')
                    desc = weather_data.get('description', '')
                    city = weather_data.get('city', 'your location')
                    
                    response = f"**Current weather in {city}: {round(temp)}°C, {desc}**\n\n"
                    
                    if temp > 30:
                        response += "**Hot Weather Recommendations:**\n"
                        response += "• Light, breathable fabrics (cotton, linen)\n"
                        response += "• Loose, comfortable fits\n"
                        response += "• Light colors that reflect heat\n"
                        response += "• Sun protection accessories\n\n"
                        response += "**Outfit Ideas:**\n"
                        response += "• Light cotton t-shirt + breathable shorts + sandals\n"
                        response += "• Tank top + flowy skirt + comfortable shoes\n"
                        response += "• Linen shirt + loose pants + breathable footwear\n"
                        
                    elif 23 <= temp <= 30:
                        response += "**Warm Weather Recommendations:**\n"
                        response += "• Comfortable, casual clothing\n"
                        response += "• Breathable fabrics\n"
                        response += "• Versatile pieces for temperature changes\n\n"
                        response += "**Outfit Ideas:**\n"
                        response += "• T-shirt + light pants + sneakers\n"
                        response += "• Polo shirt + chinos + loafers\n"
                        response += "• Short-sleeve shirt + comfortable pants + casual shoes\n"
                        
                    elif 16 <= temp <= 22:
                        response += "**Cool Weather Recommendations:**\n"
                        response += "• Light layers for comfort\n"
                        response += "• Medium-weight fabrics\n"
                        response += "• Versatile pieces for layering\n\n"
                        response += "**Outfit Ideas:**\n"
                        response += "• Long-sleeve shirt + jeans + light jacket\n"
                        response += "• Sweater + collared shirt + comfortable pants\n"
                        response += "• Button-down + chinos + cardigan\n"
                        
                    else:  # temp < 16
                        response += "**Cold Weather Recommendations:**\n"
                        response += "• Warm, insulating layers\n"
                        response += "• Heavy fabrics (wool, fleece)\n"
                        response += "• Warm accessories\n\n"
                        response += "**Outfit Ideas:**\n"
                        response += "• Thermal shirt + warm sweater + insulated jacket\n"
                        response += "• Fleece-lined pants + insulated boots + scarf\n"
                        response += "• Layered tops + winter coat + warm accessories\n"
                    
                    if 'rain' in desc.lower():
                        response += "\n**Rain Protection:**\n"
                        response += "• Waterproof or water-resistant outerwear\n"
                        response += "• Closed-toe shoes or boots\n"
                        response += "• Umbrella or hood for extra protection\n"
                        response += "• Darker colors that won't show water spots\n"
                        
                else:
                    response = "I'd love to help you with weather-appropriate fashion advice! Here are some general tips:\n\n"
                    response += "**Always Consider:**\n"
                    response += "• Temperature and humidity levels\n"
                    response += "• Wind and precipitation conditions\n"
                    response += "• Indoor vs. outdoor activities\n"
                    response += "• Duration of time spent outside\n\n"
                    response += "**Adaptable Pieces:**\n"
                    response += "• Lightweight jackets that can be layered\n"
                    response += "• Versatile shoes for different conditions\n"
                    response += "• Breathable fabrics that work in various weather"
            
            dispatcher.utter_message(text=response)
            return []
            
        except Exception as e:
            dispatcher.utter_message(text="I'm having trouble getting weather information. Try asking for general outfit suggestions!")
            return []

    def _get_weather_specific_advice(self, weather: str) -> str:
        """Get specific advice for mentioned weather conditions."""
        if 'rain' in weather or 'rainy' in weather:
            response = "For rainy days, I recommend:\n"
            response += "• Waterproof or water-resistant outerwear\n"
            response += "• Closed-toe shoes or boots\n"
            response += "• Darker colors that won't show water spots\n"
            response += "• Umbrellas or hoods for extra protection\n\n"
            response += "**Rainy Day Outfit Ideas:**\n"
            response += "• Rain jacket + waterproof boots + dark jeans\n"
            response += "• Hooded sweater + water-resistant shoes + comfortable pants\n"
            response += "• Trench coat + closed-toe shoes + weather-appropriate bottoms"
            
        elif 'cold' in weather or 'winter' in weather:
            response = "For cold weather, consider:\n"
            response += "• Layering with wool, fleece, or thermal materials\n"
            response += "• Warm accessories like scarves, gloves, and hats\n"
            response += "• Rich, deep colors that complement the season\n"
            response += "• Proper insulation for your core\n\n"
            response += "**Cold Weather Outfit Ideas:**\n"
            response += "• Thermal base layer + sweater + warm jacket\n"
            response += "• Fleece-lined pants + insulated boots + warm accessories\n"
            response += "• Layered tops + winter coat + weatherproof footwear"
            
        elif 'hot' in weather or 'summer' in weather:
            response = "For hot weather, I suggest:\n"
            response += "• Light, breathable fabrics like cotton and linen\n"
            response += "• Loose, comfortable fits\n"
            response += "• Light colors that reflect heat\n"
            response += "• Sun protection accessories\n\n"
            response += "**Hot Weather Outfit Ideas:**\n"
            response += "• Light cotton t-shirt + breathable shorts + sandals\n"
            response += "• Linen shirt + loose pants + comfortable shoes\n"
            response += "• Tank top + flowy skirt + breathable footwear"
            
        else:
            response = "Here are some general weather fashion tips:\n"
            response += "• Check the forecast before choosing your outfit\n"
            response += "• Layer appropriately for temperature changes\n"
            response += "• Consider humidity and wind conditions\n"
            response += "• Choose fabrics that work with the weather\n\n"
            response += "**Versatile Weather Outfits:**\n"
            response += "• Light layers that can be added or removed\n"
            response += "• Breathable fabrics for comfort\n"
            response += "• Weather-appropriate footwear"
        
        return response

class ActionCasualOutfit(Action):
    def name(self) -> Text:
        return "action_casual_outfit"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Get user's wardrobe for personalized suggestions
            wardrobe_items, user_type = get_current_user_wardrobe()
            
            response = "Here are some fantastic casual outfit ideas:\n\n"
            
            if user_type != "guest" and wardrobe_items:
                response += "**From your wardrobe, try these casual combinations:**\n"
                # Add personalized suggestions based on available items
                tops = [item for item in wardrobe_items if hasattr(item, 'category') and item.category and 'top' in item.category.name.lower()]
                bottoms = [item for item in wardrobe_items if hasattr(item, 'category') and item.category and 'bottom' in item.category.name.lower()]
                
                if tops and bottoms:
                    for i, top in enumerate(tops[:2], 1):
                        for bottom in bottoms[:2]:
                            response += f"• {top.name} + {bottom.name}\n"
                    response += "\n"
            elif user_type == "sample_wardrobe":
                response += "**Sample wardrobe casual combinations:**\n"
                tops = [item for item in wardrobe_items if item['category'] == 'tops']
                bottoms = [item for item in wardrobe_items if item['category'] == 'bottoms']
                shoes = [item for item in wardrobe_items if item['category'] == 'shoes']
                
                if tops and bottoms:
                    for top in tops[:2]:
                        for bottom in bottoms[:2]:
                            outfit = f"{top['name']} + {bottom['name']}"
                            if shoes:
                                outfit += f" + {shoes[0]['name']}"
                            response += f"• {outfit}\n"
                    response += "\n"
            elif user_type == "fallback":
                response += "**Basic casual combinations:**\n"
                response += "• Blue T-shirt + Black Jeans + White Sneakers\n"
                response += "• Red Polo Shirt + Khaki Pants + Casual Shoes\n\n"
            
            response += "**Everyday Casual:**\n"
            response += "• **Comfortable Classic**: Cotton t-shirt + well-fitted jeans + sneakers\n"
            response += "• **Relaxed Style**: Henley shirt + chino pants + casual shoes\n"
            response += "• **Weekend Vibes**: Graphic tee + denim jacket + comfortable pants\n\n"
            
            response += "**Smart Casual:**\n"
            response += "• **Elevated Basic**: Polo shirt + dark jeans + loafers\n"
            response += "• **Casual Professional**: Button-down shirt + chinos + casual dress shoes\n"
            response += "• **Weekend Refined**: Sweater + collared shirt + comfortable pants\n\n"
            
            response += "**Casual Styling Tips:**\n"
            response += "• Layer with comfortable cardigans or hoodies\n"
            response += "• Choose relaxed, breathable fabrics\n"
            response += "• Opt for neutral colors that mix and match\n"
            response += "• Complete with comfortable shoes\n"
            response += "• Add accessories like watches or bracelets for personality"
            
            dispatcher.utter_message(text=response)
            return []
            
        except Exception as e:
            dispatcher.utter_message(text="I'm having trouble with casual outfit suggestions. Try asking for general style tips!")
            return []

class ActionFormalOutfit(Action):
    def name(self) -> Text:
        return "action_formal_outfit"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Get user's wardrobe for personalized suggestions
            wardrobe_items, user_type = get_current_user_wardrobe()
            
            response = "Here are some sophisticated formal outfit suggestions:\n\n"
            
            if user_type != "guest" and wardrobe_items:
                response += "**From your wardrobe, consider these formal pieces:**\n"
                # Add personalized suggestions based on available items
                formal_items = [item for item in wardrobe_items if hasattr(item, 'category') and item.category and 
                              any(word in item.category.name.lower() for word in ['dress', 'suit', 'blazer', 'formal'])]
                
                if formal_items:
                    for item in formal_items[:3]:
                        response += f"• {item.name} - perfect for formal occasions\n"
                    response += "\n"
            elif user_type == "sample_wardrobe":
                response += "**Sample wardrobe formal pieces:**\n"
                formal_items = [item for item in wardrobe_items if item['category'] in ['outerwear', 'shoes'] or 
                              any(word in item['name'].lower() for word in ['dress', 'blazer', 'formal'])]
                
                if formal_items:
                    for item in formal_items[:3]:
                        response += f"• {item['name']} - great for formal occasions\n"
                    response += "\n"
            elif user_type == "fallback":
                response += "**Basic formal pieces:**\n"
                response += "• White Button-down Shirt - versatile for formal occasions\n"
                response += "• Black Dress Shoes - essential for formal wear\n"
                response += "• Navy Blazer - perfect for business and formal events\n\n"
            
            response += "**Business Professional:**\n"
            response += "• **Classic Suit**: Well-fitted suit in navy or charcoal + dress shirt + tie\n"
            response += "• **Business Casual**: Blazer + dress shirt + tailored pants + dress shoes\n"
            response += "• **Meeting Ready**: Sweater + collared shirt + dress pants + loafers\n\n"
            
            response += "**Special Occasions:**\n"
            response += "• **Wedding Guest**: Suit or blazer + dress shirt + tie + dress shoes\n"
            response += "• **Interview**: Conservative suit + white/blue shirt + conservative tie\n"
            response += "• **Evening Event**: Dark suit + dress shirt + pocket square + dress shoes\n\n"
            
            response += "**Formal Styling Tips:**\n"
            response += "• Choose classic, well-fitted pieces\n"
            response += "• Stick to neutral colors (black, navy, gray)\n"
            response += "• Quality accessories elevate your look\n"
            response += "• Ensure everything is clean and pressed\n"
            response += "• Pay attention to fit - well-fitted clothes look more expensive"
            
            dispatcher.utter_message(text=response)
            return []
            
        except Exception as e:
            dispatcher.utter_message(text="I'm having trouble with formal outfit suggestions. Try asking for general style tips!")
            return []

class ActionColorMatching(Action):
    def name(self) -> Text:
        return "action_color_matching"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Get user's wardrobe for color examples
            wardrobe_items, user_type = get_current_user_wardrobe()
            
            response = "Here are some expert color coordination tips:\n\n"
            
            if user_type != "guest" and wardrobe_items:
                response += "**Colors in your wardrobe:**\n"
                colors = set()
                for item in wardrobe_items:
                    if hasattr(item, 'color') and item.color:
                        colors.add(item.color.lower())
                
                if colors:
                    color_list = ", ".join(list(colors)[:5])  # Show first 5 colors
                    response += f"• You have: {color_list}\n"
                    response += "• These colors work well together in various combinations\n\n"
            elif user_type == "sample_wardrobe":
                response += "**Colors in the sample wardrobe:**\n"
                colors = set()
                for item in wardrobe_items:
                    if item.get('color'):
                        colors.add(item['color'].lower())
                
                if colors:
                    color_list = ", ".join(list(colors)[:5])  # Show first 5 colors
                    response += f"• Sample colors: {color_list}\n"
                    response += "• These colors create versatile combinations\n\n"
            elif user_type == "fallback":
                response += "**Basic color palette:**\n"
                response += "• Blue, White, Black, Beige, Gray\n"
                response += "• These neutral colors work well together\n\n"
            
            response += "**Complementary Colors:**\n"
            response += "• Red pairs beautifully with green or teal\n"
            response += "• Blue looks great with orange or peach\n"
            response += "• Yellow complements purple or violet perfectly\n"
            response += "• Green works well with red or pink tones\n\n"
            
            response += "**Analogous Colors:**\n"
            response += "• Warm colors (red, orange, yellow) work well together\n"
            response += "• Cool colors (blue, green, purple) create harmony\n"
            response += "• Neutral colors (black, white, gray) go with everything\n\n"
            
            response += "**Color Combinations by Occasion:**\n"
            response += "• **Professional**: Navy + white + gray accents\n"
            response += "• **Casual**: Denim + white + earth tones\n"
            response += "• **Evening**: Black + white + metallic accents\n"
            response += "• **Summer**: Light blues + whites + pastels\n\n"
            
            response += "**Pro Tips:**\n"
            response += "• Start with neutral colors and add one pop of color\n"
            response += "• Use the 60-30-10 rule: 60% dominant color, 30% secondary, 10% accent\n"
            response += "• Consider your skin tone when choosing colors\n"
            response += "• Don't be afraid to experiment with color combinations!\n"
            response += "• Remember: confidence makes any color combination work"
            
            dispatcher.utter_message(text=response)
            return []
            
        except Exception as e:
            dispatcher.utter_message(text="I'm having trouble with color matching advice. Try asking for general style tips!")
            return []

class ActionStyleTips(Action):
    def name(self) -> Text:
        return "action_style_tips"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Get user's wardrobe for personalized tips
            wardrobe_items, user_type = get_current_user_wardrobe()
            
            response = "Here are some timeless fashion tips that will transform your style:\n\n"
            
            if user_type != "guest" and wardrobe_items:
                response += "**Based on your wardrobe:**\n"
                categories = set()
                for item in wardrobe_items:
                    if hasattr(item, 'category') and item.category:
                        categories.add(item.category.name)
                
                if categories:
                    response += f"• You have items in: {', '.join(list(categories)[:3])}\n"
                    response += "• Mix and match these categories for versatile looks\n"
                    response += "• Consider adding pieces in missing categories\n\n"
            elif user_type == "sample_wardrobe":
                response += "**Based on the sample wardrobe:**\n"
                categories = set()
                for item in wardrobe_items:
                    if item.get('category'):
                        categories.add(item['category'])
                
                if categories:
                    response += f"• Sample categories: {', '.join(list(categories)[:3])}\n"
                    response += "• These categories provide a good foundation\n"
                    response += "• Consider adding more variety to your collection\n\n"
            elif user_type == "fallback":
                response += "**Basic wardrobe foundation:**\n"
                response += "• Tops, Bottoms, Shoes, Outerwear, Accessories\n"
                response += "• Start with these essential categories\n"
                response += "• Build your collection gradually\n\n"
            
            response += "**Building Your Wardrobe:**\n"
            response += "• Invest in quality basics that mix and match\n"
            response += "• Choose colors that complement your skin tone\n"
            response += "• Focus on fit - well-fitted clothes look more expensive\n"
            response += "• Build around a neutral color palette\n\n"
            
            response += "**Accessorizing Like a Pro:**\n"
            response += "• Less is often more - don't over-accessorize\n"
            response += "• Choose accessories that complement your outfit\n"
            response += "• Consider the occasion when selecting jewelry\n"
            response += "• A good watch can elevate any outfit\n\n"
            
            response += "**Seasonal Dressing:**\n"
            response += "• Layer appropriately for temperature changes\n"
            response += "• Choose fabrics that work with the weather\n"
            response += "• Don't forget seasonal accessories\n"
            response += "• Transitional pieces are worth the investment\n\n"
            
            response += "**Style Confidence:**\n"
            response += "• Wear what makes you feel confident\n"
            response += "• Don't be afraid to experiment with new styles\n"
            response += "• Your personal style should reflect your personality\n"
            response += "• Remember: the best accessory is confidence!\n\n"
            
            response += "**Quick Style Hacks:**\n"
            response += "• Roll up sleeves for a more casual look\n"
            response += "• Tuck in shirts to look more polished\n"
            response += "• Use belts to define your waist\n"
            response += "• Mix high and low-end pieces for balance"
            
            dispatcher.utter_message(text=response)
            return []
            
        except Exception as e:
            dispatcher.utter_message(text="I'm having trouble with style tips. Try asking for general outfit suggestions!")
            return []

class ActionOccasionOutfit(Action):
    def name(self) -> Text:
        return "action_occasion_outfit"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Get occasion from entities
            occasion_entities = [entity['value'] for entity in tracker.latest_message['entities'] 
                               if entity['entity'] == 'occasion']
            
            # Get user's wardrobe for personalized suggestions
            wardrobe_items, user_type = get_current_user_wardrobe()
            
            if occasion_entities:
                occasion = occasion_entities[0].lower()
                response = self._get_occasion_specific_advice(occasion, wardrobe_items, user_type)
            else:
                response = "I'd love to help you choose the perfect outfit for your occasion! Here are some general guidelines:\n\n"
                response += "**Occasion-Based Dressing:**\n"
                response += "• **Work/Professional**: Focus on polished, well-fitted pieces\n"
                response += "• **Social Events**: Choose comfortable yet stylish options\n"
                response += "• **Special Occasions**: Opt for elevated, sophisticated looks\n"
                response += "• **Casual Outings**: Prioritize comfort and personal style\n\n"
                response += "**What type of event are you attending?** I can give you more specific recommendations!"
            
            dispatcher.utter_message(text=response)
            return []
            
        except Exception as e:
            dispatcher.utter_message(text="I'm having trouble with occasion-specific advice. Try asking for general outfit suggestions!")
            return []

    def _get_occasion_specific_advice(self, occasion: str, wardrobe_items: list, user_type: str) -> str:
        """Get specific advice for mentioned occasions."""
        response = ""
        
        if 'party' in occasion or 'celebration' in occasion:
            response = "For parties and celebrations, you want to look festive and confident:\n\n"
            
            if user_type != "guest" and wardrobe_items:
                response += "**From your wardrobe for parties:**\n"
                party_items = [item for item in wardrobe_items if hasattr(item, 'category') and item.category and 
                             any(word in item.category.name.lower() for word in ['dress', 'formal', 'blazer'])]
                if party_items:
                    for item in party_items[:2]:
                        response += f"• {item.name} - perfect for parties!\n"
                    response += "\n"
            elif user_type == "sample_wardrobe":
                response += "**From the sample wardrobe for parties:**\n"
                party_items = [item for item in wardrobe_items if item['category'] in ['outerwear', 'shoes'] or 
                             any(word in item['name'].lower() for word in ['blazer', 'dress', 'formal'])]
                if party_items:
                    for item in party_items[:2]:
                        response += f"• {item['name']} - perfect for parties!\n"
                    response += "\n"
            elif user_type == "fallback":
                response += "**Basic party pieces:**\n"
                response += "• Navy Blazer - elevates any outfit\n"
                response += "• Black Dress Shoes - essential for formal events\n\n"
            
            response += "**Party Outfit Ideas:**\n"
            response += "• **Bold Statement**: Bright colored shirt + dark pants + statement shoes\n"
            response += "• **Classic Party**: Dark shirt + fitted pants + dress shoes\n"
            response += "• **Trendy Look**: Patterned shirt + solid pants + fashionable footwear\n\n"
            response += "**Styling Tips:**\n"
            response += "• Choose bold colors or statement pieces\n"
            response += "• Add sparkle with jewelry or metallic accents\n"
            response += "• Consider the venue's dress code\n"
            response += "• Don't forget comfortable shoes for dancing!"
            
        elif 'work' in occasion or 'office' in occasion or 'business' in occasion:
            response = "For work and business settings, focus on professionalism:\n\n"
            
            if user_type != "guest" and wardrobe_items:
                response += "**From your wardrobe for work:**\n"
                work_items = [item for item in wardrobe_items if hasattr(item, 'category') and item.category and 
                            any(word in item.category.name.lower() for word in ['dress', 'formal', 'blazer', 'shirt'])]
                if work_items:
                    for item in work_items[:2]:
                        response += f"• {item.name} - great for the office!\n"
                    response += "\n"
            elif user_type == "sample_wardrobe":
                response += "**From the sample wardrobe for work:**\n"
                work_items = [item for item in wardrobe_items if item['category'] in ['tops', 'bottoms', 'outerwear', 'shoes'] or 
                            any(word in item['name'].lower() for word in ['button-down', 'blazer', 'dress'])]
                if work_items:
                    for item in work_items[:2]:
                        response += f"• {item['name']} - great for the office!\n"
                    response += "\n"
            elif user_type == "fallback":
                response += "**Basic work pieces:**\n"
                response += "• White Button-down Shirt - professional staple\n"
                response += "• Khaki Chino Pants - business casual essential\n\n"
            
            response += "**Work Outfit Ideas:**\n"
            response += "• **Business Professional**: Suit + dress shirt + tie + dress shoes\n"
            response += "• **Smart Casual**: Blazer + collared shirt + chinos + loafers\n"
            response += "• **Creative Office**: Button-down shirt + dark jeans + casual shoes\n\n"
            response += "**Styling Tips:**\n"
            response += "• Stick to classic cuts and neutral colors\n"
            response += "• Well-fitted pieces look more professional\n"
            response += "• Quality accessories like a watch or belt\n"
            response += "• Ensure everything is clean and pressed"
            
        elif 'date' in occasion or 'dinner' in occasion:
            response = "For dates and dinners, aim for romantic and sophisticated:\n\n"
            
            if user_type != "guest" and wardrobe_items:
                response += "**From your wardrobe for dates:**\n"
                date_items = [item for item in wardrobe_items if hasattr(item, 'category') and item.category and 
                            any(word in item.category.name.lower() for word in ['dress', 'formal', 'blazer'])]
                if date_items:
                    for item in date_items[:2]:
                        response += f"• {item.name} - perfect for a date!\n"
                    response += "\n"
            elif user_type == "sample_wardrobe":
                response += "**From the sample wardrobe for dates:**\n"
                date_items = [item for item in wardrobe_items if item['category'] in ['tops', 'bottoms', 'outerwear', 'shoes'] or 
                            any(word in item['name'].lower() for word in ['button-down', 'blazer', 'dress'])]
                if date_items:
                    for item in date_items[:2]:
                        response += f"• {item['name']} - perfect for a date!\n"
                    response += "\n"
            elif user_type == "fallback":
                response += "**Basic date pieces:**\n"
                response += "• White Button-down Shirt - classic and sophisticated\n"
                response += "• Navy Blazer - adds polish to any outfit\n\n"
            
            response += "**Date Night Outfit Ideas:**\n"
            response += "• **Romantic Dinner**: Dark shirt + fitted pants + dress shoes\n"
            response += "• **Casual Date**: Collared shirt + dark jeans + stylish shoes\n"
            response += "• **Special Evening**: Blazer + dress shirt + tailored pants\n\n"
            response += "**Styling Tips:**\n"
            response += "• Choose darker colors and richer fabrics\n"
            response += "• Add romantic touches like lace or silk\n"
            response += "• Consider the venue's atmosphere\n"
            response += "• Don't forget to accessorize elegantly"
            
        else:
            response = f"For {occasion}, consider the formality level and venue:\n\n"
            response += "**General Guidelines:**\n"
            response += "• **Formal Events**: Suit or blazer + dress shirt + dress shoes\n"
            response += "• **Semi-Formal**: Collared shirt + dress pants + loafers\n"
            response += "• **Casual Events**: T-shirt + jeans + comfortable shoes\n\n"
            response += "**Always Consider:**\n"
            response += "• The venue's dress code\n"
            response += "• Time of day and season\n"
            response += "• Your comfort and confidence\n"
            response += "• Weather conditions"
        
        return response

class ActionFallback(Action):
    def name(self) -> Text:
        return "action_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        response = "I'm your AI Stylist, ready to help you look fabulous! Try asking me about:\n\n"
        response += "• **Outfit suggestions** (\"Suggest an outfit\")\n"
        response += "• **Style tips** (\"How do I match colors?\")\n"
        response += "• **Weather-appropriate clothing** (\"What to wear in the rain?\")\n"
        response += "• **Casual or formal advice** (\"Help me dress casually\")\n"
        response += "• **Occasion-specific outfits** (\"What to wear to a party?\")\n\n"
        response += "**Popular Questions:**\n"
        response += "• \"What should I wear today?\"\n"
        response += "• \"How do I match colors?\"\n"
        response += "• \"Give me style tips\"\n"
        response += "• \"What to wear to work?\"\n"
        response += "• \"Suggest an outfit for hot weather\"\n\n"
        response += "I can also check your wardrobe and current weather to give you personalized suggestions! 👗✨"
        
        dispatcher.utter_message(text=response)
        return [] 