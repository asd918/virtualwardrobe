import requests
import logging
from django.conf import settings
from datetime import datetime
import re
from typing import Dict

logger = logging.getLogger(__name__)

def get_weather_data(city: str, units: str = 'metric'):
	"""
	Fetch current weather data for a given city using Visual Crossing Weather API.
	
	Args:
		city (str): City name to get weather for
		units (str): 'metric' (°C, km/h) or 'imperial' (°F, mph). Defaults to 'metric'.
	
	Returns:
		dict: Weather data including temperature, conditions, humidity, wind speed, city, coordinates
		      or dict with 'error' key if API call fails.
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
	
	# API key
	api_key = getattr(settings, 'VISUAL_CROSSING_API_KEY', None)
	if not api_key:
		logger.error("Visual Crossing API key not configured")
		return {"error": "Weather API key not configured"}
	
	# Units mapping for Visual Crossing
	unit_group = 'metric' if units == 'metric' else 'us'
	
	try:
		# Build request URL
		encoded_city = requests.utils.quote(city)
		url = (
			f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
			f"{encoded_city}?unitGroup={unit_group}&key={api_key}&contentType=json"
		)
		logger.info(f"Visual Crossing request: {url[:-len(api_key)] + 'API_KEY'}")
		response = requests.get(url, timeout=10)
		if response.status_code != 200:
			logger.error(f"Visual Crossing API error {response.status_code}: {response.text}")
			return {"error": f"Weather service error (status {response.status_code})"}
		data = response.json()
		
		# Extract current conditions
		current = data.get('currentConditions') or {}
		if not current:
			logger.error("Missing currentConditions in Visual Crossing response")
			return {"error": "Invalid weather data format"}
		
		# Map fields
		try:
			temperature = float(current.get('temp')) if current.get('temp') is not None else None
			feels_like = float(current.get('feelslike')) if current.get('feelslike') is not None else None
			humidity = int(current.get('humidity')) if current.get('humidity') is not None else None
			wind_speed = float(current.get('windspeed')) if current.get('windspeed') is not None else None
			description = str(current.get('conditions', '')).strip()
			icon = str(current.get('icon', '')).strip() if current.get('icon') is not None else ''
			resolved_address = data.get('resolvedAddress') or city
			latitude = data.get('latitude')
			longitude = data.get('longitude')
		except (TypeError, ValueError) as e:
			logger.error(f"Error parsing Visual Crossing fields: {e}")
			return {"error": "Unable to process weather data"}
		
		weather_data = {
			'temperature': temperature,
			'feels_like': feels_like,
			'humidity': humidity,
			'wind_speed': wind_speed,
			'description': description,
			'icon': icon,
			'city': resolved_address,
			'coordinates': {'lat': latitude, 'lon': longitude},
			'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		}
		return weather_data
	except requests.exceptions.Timeout:
		logger.error(f"Timeout connecting to Visual Crossing for city: {city}")
		return {"error": "Weather service timeout"}
	except requests.exceptions.RequestException as e:
		logger.exception(f"Request error fetching weather data: {e}")
		return {"error": f"Connection error: {str(e)}"}
	except Exception as e:
		logger.exception(f"Unexpected error fetching weather data: {e}")
		return {"error": f"An unexpected error occurred: {str(e)}"}


def get_clothing_recommendations_based_on_weather(weather_data):
	"""
	Generate clothing recommendations based on temperature buckets and rain.
	
	Buckets:
	- Hot (> 30°C): light clothing (t-shirt, shorts)
	- Warm (23–30°C): casual clothing
	- Cool (16–22°C): jackets or sweaters
	- Cold (< 16°C): coats, long pants
	- Rain in conditions: suggest umbrella/raincoat
	"""
	# Validate input
	if not weather_data or not isinstance(weather_data, dict):
		logger.error("Invalid weather_data provided to recommendation function")
		return {
			'message': 'Invalid weather data. Unable to provide recommendations.',
			'recommendations': {},
			'error': True
		}
	
	if 'error' in weather_data:
		return {
			'message': f"Weather data unavailable: {weather_data['error']}",
			'recommendations': {},
			'error': True
		}
	
	temp = weather_data.get('temperature')
	desc = (weather_data.get('description') or '').lower()
	if temp is None:
		return {
			'message': 'Incomplete weather data. Unable to provide accurate recommendations.',
			'recommendations': {},
			'error': True
		}
	
	recommendations: Dict[str, list] = {
		'tops': [],
		'bottoms': [],
		'outerwear': [],
		'accessories': [],
		'general_advice': []
	}
	
	try:
		if temp > 30:
			recommendations['tops'] = ['Light T-shirt', 'Tank top']
			recommendations['bottoms'] = ['Shorts', 'Light skirt']
			recommendations['accessories'] = ['Sunglasses', 'Cap', 'Sunscreen']
			recommendations['general_advice'].append('Choose very light, breathable clothing.')
		elif 23 <= temp <= 30:
			recommendations['tops'] = ['T-shirt', 'Short-sleeve shirt']
			recommendations['bottoms'] = ['Shorts', 'Light pants']
			recommendations['general_advice'].append('Casual clothing is ideal in warm weather.')
		elif 16 <= temp <= 22:
			recommendations['tops'] = ['Long-sleeve shirt', 'Light sweater']
			recommendations['outerwear'] = ['Light jacket', 'Cardigan']
			recommendations['bottoms'] = ['Jeans', 'Chinos']
			recommendations['general_advice'].append('Add a jacket or sweater for comfort.')
		else:  # temp < 16
			recommendations['tops'] = ['Warm sweater', 'Thermal shirt']
			recommendations['outerwear'] = ['Coat', 'Insulated jacket']
			recommendations['bottoms'] = ['Long pants']
			recommendations['accessories'].append('Scarf (optional)')
			recommendations['general_advice'].append('Dress warmly to stay comfortable.')
		
		if 'rain' in desc:
			recommendations['outerwear'].append('Raincoat')
			recommendations['accessories'].append('Umbrella')
			recommendations['general_advice'].append('Rain expected. Bring rain protection.')
		
		city_name = weather_data.get('city', 'your location')
		message = f"Recommendations for {city_name}: {round(temp)}°C, {weather_data.get('description', '')}"
		return {
			'message': message,
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