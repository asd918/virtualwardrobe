import requests
from django.conf import settings
import logging
import urllib.parse

logger = logging.getLogger(__name__)

def get_weather_data(city):
    api_key = settings.OPENWEATHERMAP_API_KEY
    if not api_key:
        logger.error("OpenWeatherMap API key not configured")
        return {'error': 'API key not configured'}

    # Ensure city is properly encoded
    encoded_city = urllib.parse.quote(city)
    url = f"https://api.openweathermap.org/data/2.5/weather?q={encoded_city}&units=metric&appid={api_key}"
    
    logger.debug(f"Querying OpenWeatherMap API for city: {city}")
    
    try:
        response = requests.get(url, timeout=10)  # Set a timeout
        
        # Log the status for debugging
        logger.debug(f"OpenWeatherMap API response status: {response.status_code}")
        
        # First check the response status code
        if response.status_code != 200:
            error_message = f"API returned status code {response.status_code}"
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_message = f"API error: {error_data['message']}"
            except:
                pass
            
            logger.error(f"OpenWeatherMap API error for {city}: {error_message}")
            return {'error': error_message}
        
        # Try to parse the JSON response
        try:
            data = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {'error': 'Invalid response from weather service'}
        
        # Check for API errors in the response
        if data.get('cod') != 200:
            error_msg = data.get('message', 'City not found or invalid data')
            logger.error(f"City not found or invalid data for {city}: {error_msg}")
            return {'error': error_msg}
        
        # Log success and return data
        logger.debug(f"Successfully retrieved weather data for {city}")
        return data
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error fetching weather data for {city}")
        return {'error': 'Connection to weather service timed out'}
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error fetching weather data for {city}")
        return {'error': 'Could not connect to weather service'}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {e}")
        return {'error': 'Failed to fetch weather data'}
    except Exception as e:
        logger.error(f"Unexpected error fetching weather data: {e}")
        return {'error': 'An unexpected error occurred'}

def get_clothing_recommendations_based_on_weather(weather_data):
    if weather_data and 'main' in weather_data and 'temp' in weather_data['main']:
        temperature = weather_data['main']['temp']
        description = weather_data['weather'][0]['description']

        if temperature < 10:
            return "Recommend a heavy coat, gloves, and a scarf."
        elif temperature < 20:
            return "Recommend a light jacket or sweater."
        else:
            return "Recommend light clothing such as t-shirts and shorts."
    else:
        return "Unable to provide weather-based recommendations."
