import requests
import logging
from django.conf import settings
from datetime import datetime
import re

logger = logging.getLogger(__name__)

def get_weather_data(city):
    """
    Fetch current weather data for a given city using OpenWeatherMap API.
    Uses geocoding first to get precise coordinates, then requests weather.
    
    Args:
        city (str): City name to get weather for
        
    Returns:
        dict: Weather data including temperature, conditions, etc.
              Returns dict with 'error' key if API call fails
    """
    # Validate input
    if not city or not isinstance(city, str):
        logger.error("Invalid city parameter provided")
        return {"error": "Invalid city parameter"}
    
    # Sanitize input - remove any special characters except spaces, hyphens and periods
    sanitized_city = re.sub(r'[^\w\s\-\.]', '', city)
    if sanitized_city != city:
        logger.warning(f"City name was sanitized from '{city}' to '{sanitized_city}'")
        city = sanitized_city
    
    # Check for API key
    api_key = settings.OPENWEATHERMAP_API_KEY
    if not api_key:
        logger.error("OpenWeatherMap API key not set. Unable to fetch weather data.")
        return {"error": "Weather API key not configured"}
    
    try:
        # Step 1: Get coordinates using geocoding API
        geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct?q={requests.utils.quote(city)}&limit=1&appid={api_key}"
        
        # Set timeout to prevent hanging requests
        geo_response = requests.get(geocoding_url, timeout=10)
        
        if geo_response.status_code != 200:
            logger.error(f"Geocoding API error. Status code: {geo_response.status_code}")
            return {"error": f"Geocoding service error (status {geo_response.status_code})"}
            
        geo_data = geo_response.json()
        
        # Check if geocoding returned any results
        if not geo_data or not isinstance(geo_data, list) or len(geo_data) == 0:
            logger.warning(f"City not found in geocoding: {city}")
            return {"error": f"City '{city}' not found"}
            
        # Extract coordinates
        try:
            location = geo_data[0]
            lat = float(location.get('lat'))
            lon = float(location.get('lon'))
            city_name = location.get('name', city)
            country = location.get('country', '')
            state = location.get('state', '')
            
            # Log the coordinates found
            logger.info(f"Found coordinates for {city}: lat={lat}, lon={lon}")
            
        except (KeyError, ValueError, IndexError) as e:
            logger.error(f"Error extracting geocoding data: {e}")
            return {"error": f"Invalid geocoding data format: {str(e)}"}
            
        # Step 2: Get weather data using coordinates
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        
        weather_response = requests.get(weather_url, timeout=10)
        
        if weather_response.status_code == 200:
            data = weather_response.json()
            
            # Validate response data structure
            required_fields = [
                ('main', dict), 
                ('weather', list), 
                ('wind', dict),
                ('sys', dict)
            ]
            
            for field, expected_type in required_fields:
                if field not in data or not isinstance(data[field], expected_type):
                    logger.error(f"Missing or invalid field in weather data: {field}")
                    return {"error": f"Invalid weather data format: missing {field}"}
            
            if not data['weather'] or not isinstance(data['weather'][0], dict):
                logger.error("Invalid weather array in response")
                return {"error": "Invalid weather data format"}
            
            # Extract relevant weather information with proper validation
            try:
                formatted_location = city_name
                if state:
                    formatted_location += f", {state}"
                if country:
                    formatted_location += f", {country}"
                
                weather_data = {
                    'temperature': float(data['main']['temp']),
                    'feels_like': float(data['main']['feels_like']),
                    'humidity': int(data['main']['humidity']),
                    'wind_speed': float(data['wind']['speed']),
                    'description': str(data['weather'][0]['description']),
                    'icon': str(data['weather'][0]['icon']),
                    'city': formatted_location,
                    'coordinates': {'lat': lat, 'lon': lon},
                    'country': country,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                return weather_data
            except (KeyError, ValueError, TypeError) as e:
                logger.error(f"Error extracting weather data fields: {e}")
                return {"error": f"Unable to process weather data: {str(e)}"}
        
        elif weather_response.status_code == 401:
            logger.error("Unauthorized weather API request - check API key")
            return {"error": "Invalid weather API key"}
        
        else:
            logger.error(f"Failed to get weather data. Status code: {weather_response.status_code}")
            return {"error": f"Weather service error (status {weather_response.status_code})"}
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout connecting to weather API for city: {city}")
        return {"error": "Weather service timeout"}
    
    except requests.exceptions.RequestException as e:
        logger.exception(f"Request error fetching weather data: {e}")
        return {"error": f"Connection error: {str(e)}"}
        
    except Exception as e:
        logger.exception(f"Unexpected error fetching weather data: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

def get_clothing_recommendations_based_on_weather(weather_data):
    """
    Generate clothing item recommendations based on weather conditions.
    
    Args:
        weather_data (dict): Weather data returned from get_weather_data()
        
    Returns:
        dict: Clothing recommendations by category
    """
    # Validate input
    if not weather_data or not isinstance(weather_data, dict):
        logger.error("Invalid weather_data provided to recommendation function")
        return {
            'message': 'Invalid weather data. Unable to provide recommendations.',
            'recommendations': {},
            'error': True
        }
    
    # Check for error in weather data
    if 'error' in weather_data:
        logger.warning(f"Weather data contains error: {weather_data['error']}")
        return {
            'message': f"Weather data unavailable: {weather_data['error']}",
            'recommendations': {},
            'error': True
        }
    
    # Validate required fields
    required_fields = ['temperature', 'description']
    missing_fields = [field for field in required_fields if field not in weather_data]
    
    if missing_fields:
        logger.error(f"Weather data missing required fields: {missing_fields}")
        return {
            'message': 'Incomplete weather data. Unable to provide accurate recommendations.',
            'recommendations': {},
            'error': True
        }
    
    try:
        temperature = float(weather_data.get('temperature', 0))
        description = str(weather_data.get('description', '')).lower()
        wind_speed = float(weather_data.get('wind_speed', 0))
        
        recommendations = {
            'tops': [],
            'bottoms': [],
            'outerwear': [],
            'accessories': [],
            'general_advice': []
        }
        
        # Very cold (below 5°C)
        if temperature < 5:
            recommendations['tops'] = ['Thermal undershirt', 'Heavy sweater', 'Long-sleeve shirt']
            recommendations['bottoms'] = ['Thermal underwear', 'Heavy pants', 'Jeans']
            recommendations['outerwear'] = ['Winter coat', 'Heavy jacket', 'Parka']
            recommendations['accessories'] = ['Scarf', 'Gloves', 'Winter hat', 'Thick socks']
            recommendations['general_advice'].append('Layer your clothing for maximum warmth.')
        
        # Cold (5-10°C)
        elif temperature < 10:
            recommendations['tops'] = ['Long-sleeve shirt', 'Light sweater', 'Turtleneck']
            recommendations['bottoms'] = ['Jeans', 'Trousers', 'Thick leggings']
            recommendations['outerwear'] = ['Medium jacket', 'Light coat', 'Blazer']
            recommendations['accessories'] = ['Light scarf', 'Gloves', 'Beanie']
            recommendations['general_advice'].append('Light layering is recommended.')
            
        # Cool (10-15°C)
        elif temperature < 15:
            recommendations['tops'] = ['Light sweater', 'Long-sleeve shirt', 'Button-up shirt']
            recommendations['bottoms'] = ['Jeans', 'Casual pants', 'Chinos']
            recommendations['outerwear'] = ['Light jacket', 'Cardigan', 'Blazer']
            recommendations['accessories'] = ['Light scarf']
            recommendations['general_advice'].append('A light jacket or sweater should be sufficient.')
            
        # Mild (15-20°C)
        elif temperature < 20:
            recommendations['tops'] = ['T-shirt', 'Light long-sleeve', 'Button-up shirt']
            recommendations['bottoms'] = ['Jeans', 'Light pants', 'Skirt with leggings']
            recommendations['outerwear'] = ['Light cardigan', 'Light jacket']
            recommendations['general_advice'].append('Comfortable temperature for light clothing.')
            
        # Warm (20-25°C)
        elif temperature < 25:
            recommendations['tops'] = ['T-shirt', 'Short-sleeve shirt', 'Blouse']
            recommendations['bottoms'] = ['Light pants', 'Shorts', 'Skirt']
            recommendations['outerwear'] = ['Very light cardigan (optional)']
            recommendations['accessories'] = ['Sunglasses', 'Hat']
            recommendations['general_advice'].append('Comfortable temperature for most clothing.')
            
        # Hot (25-30°C)
        elif temperature < 30:
            recommendations['tops'] = ['T-shirt', 'Tank top', 'Short-sleeve shirt']
            recommendations['bottoms'] = ['Shorts', 'Skirt', 'Light pants']
            recommendations['accessories'] = ['Sunglasses', 'Sun hat', 'Sunscreen']
            recommendations['general_advice'].append('Choose light, breathable fabrics.')
            
        # Very hot (30°C+)
        else:
            recommendations['tops'] = ['Light T-shirt', 'Tank top', 'Breathable shirt']
            recommendations['bottoms'] = ['Light shorts', 'Light skirt']
            recommendations['accessories'] = ['Sunglasses', 'Wide-brim hat', 'Sunscreen']
            recommendations['general_advice'].append('Choose very light, loose-fitting clothing.')
            recommendations['general_advice'].append('Stay hydrated and avoid direct sun exposure during peak hours.')
        
        # Adjust for rain
        if 'rain' in description or 'drizzle' in description or 'shower' in description:
            recommendations['outerwear'].append('Rain jacket')
            recommendations['accessories'].append('Umbrella')
            recommendations['general_advice'].append('Waterproof clothing recommended.')
            
        # Adjust for snow
        if 'snow' in description:
            recommendations['outerwear'].append('Waterproof jacket')
            recommendations['bottoms'].append('Waterproof pants')
            recommendations['accessories'].extend(['Waterproof boots', 'Thick gloves'])
            recommendations['general_advice'].append('Waterproof and insulated clothing recommended.')
            
        # Adjust for wind
        if wind_speed > 10:
            recommendations['general_advice'].append('Windy conditions. Choose clothing that won\'t be affected by wind.')
            if temperature < 15:
                recommendations['accessories'].append('Windbreaker')
        
        city_name = weather_data.get("city", "Unknown")
        return {
            'message': f'Recommendations for {city_name}: {temperature}°C, {description}',
            'recommendations': recommendations,
            'error': False
        } 
    
    except Exception as e:
        logger.exception(f"Error generating clothing recommendations: {e}")
        return {
            'message': f'Error generating recommendations: {str(e)}',
            'recommendations': {},
            'error': True
        } 