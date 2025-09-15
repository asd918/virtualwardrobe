"""
Google Dialogflow client for AI Stylist Chatbot
"""

import os
from google.cloud import dialogflow_v2 as dialogflow
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Dialogflow project configuration
DIALOGFLOW_PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID", "virtualwardrobe-eqqa")
DIALOGFLOW_LANGUAGE_CODE = os.getenv("DIALOGFLOW_LANGUAGE_CODE", "en")

def get_dialogflow_response(session_id, text, language_code=DIALOGFLOW_LANGUAGE_CODE):
    """
    Get response from Dialogflow for the given text.
    
    Args:
        session_id (str): Unique session identifier
        text (str): User input text
        language_code (str): Language code for the request
        
    Returns:
        str: Bot response text
    """
    try:
        # Ensure credentials are set for Google Cloud client
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set or file not found. See README for setup.")

        # Initialize Dialogflow client
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)
        
        # Create text input
        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        
        # Detect intent and get response
        response = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )
        
        # Return the fulfillment text
        return response.query_result.fulfillment_text
        
    except Exception as e:
        logger.error(f"Dialogflow error: {e}")
        # Fallback response
        return "I'm sorry, I'm having trouble connecting right now. Please try again later."

def get_dialogflow_response_with_confidence(session_id, text, language_code=DIALOGFLOW_LANGUAGE_CODE):
    """
    Get response from Dialogflow with confidence score.
    
    Args:
        session_id (str): Unique session identifier
        text (str): User input text
        language_code (str): Language code for the request
        
    Returns:
        dict: Response with text and confidence score
    """
    try:
        # Ensure credentials are set for Google Cloud client
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set or file not found. See README for setup.")

        # Initialize Dialogflow client
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)
        
        # Create text input
        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        
        # Detect intent and get response
        response = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )
        
        result = response.query_result
        
        return {
            "text": result.fulfillment_text,
            "confidence": result.intent_detection_confidence,
            "intent": result.intent.display_name,
            "parameters": dict(result.parameters)
        }
        
    except Exception as e:
        logger.error(f"Dialogflow error: {e}")
        # Fallback response
        return {
            "text": "I'm sorry, I'm having trouble connecting right now. Please try again later.",
            "confidence": 0.0,
            "intent": "fallback",
            "parameters": {}
        }

def test_dialogflow_connection():
    """
    Test the Dialogflow connection.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        test_response = get_dialogflow_response("test_session", "hello")
        return test_response is not None
    except Exception as e:
        logger.error(f"Dialogflow connection test failed: {e}")
        return False
