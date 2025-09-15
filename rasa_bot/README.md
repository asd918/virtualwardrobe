# Rasa AI Stylist Chatbot (Developer Edition with CALM)

This is an AI-powered fashion stylist chatbot built with Rasa Developer Edition using CALM (Conversational AI with Language Models) that provides personalized outfit suggestions, style tips, and fashion advice with enhanced features.

## Features

### Core Features
- **Outfit Suggestions**: Get personalized outfit recommendations based on your wardrobe
- **Weather-Aware Fashion**: Receive weather-appropriate clothing advice
- **Style Tips**: Learn about color matching, fashion rules, and styling techniques
- **Occasion-Based Dressing**: Get outfit suggestions for specific events
- **Casual & Formal Advice**: Tailored recommendations for different dress codes

### CALM (Conversational AI with Language Models) Features
- **LLM-Powered Responses**: Uses OpenAI GPT models for natural language generation
- **Flow-Based Conversations**: Modern flow-based conversation management
- **Contextual Response Rephraser**: Automatically rephrases responses for variety
- **Advanced Intent Recognition**: Better understanding through LLM processing
- **Enhanced Entity Extraction**: More accurate extraction using language models

### Developer Edition Enhancements
- **Advanced Conversation Management**: Improved context handling and memory
- **Better Response Quality**: More natural and contextual responses
- **Advanced Analytics**: Detailed conversation analytics and insights
- **Silence Handling**: Automatic timeout handling for voice interactions

## Quick Start

### Option 1: Using the Batch Script (Windows) - Recommended
```bash
# Double-click or run (includes license key):
start_chatbot.bat
```

### Option 2: Manual Startup with CALM Configuration
```bash
# Set license key and OpenAI API key (PowerShell)
$env:RASA_LICENSE_KEY="your_license_key_here"
$env:OPENAI_API_KEY="your_openai_api_key_here"

# Terminal 1: Start Rasa Server
rasa run --enable-api --cors "*" --port 5005

# Terminal 2: Start Action Server (optional, for custom actions)
rasa run actions --port 5055
```

### Option 3: Using Python Script
```bash
python start_servers.py
```

## Testing the Chatbot

### Test with Developer Edition Features
```bash
python test_licensed_chatbot.py
```

### Basic Functionality Test
```bash
python test_chatbot.py
```

### Test with Direct API Calls
```bash
# Test status
curl http://localhost:5005/status

# Test chat
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test", "message": "hello"}'
```

## Integration with Django

The chatbot is integrated with the Django virtual wardrobe application:

1. **Django View**: `stylist_chatbot/views.py` handles the chat interface
2. **Template**: `stylist_chatbot/templates/stylist_chatbot/chat_interface.html`
3. **URL**: Access at `http://localhost:8000/stylist-chat/`

## License Configuration

The chatbot is configured with a Rasa Developer Edition License Key that provides enhanced features:

- **License Key**: Already configured in startup scripts
- **Environment File**: `rasa_license.env` contains the license key
- **Enhanced Features**: Advanced conversation management, better intent recognition, improved entity extraction

### Setting the License Key Manually

**PowerShell:**
```powershell
$env:RASA_LICENSE_KEY="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Command Prompt:**
```cmd
set RASA_LICENSE_KEY=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Linux/Mac:**
```bash
export RASA_LICENSE_KEY="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Configuration Files

- `config.yml`: Rasa pipeline and policy configuration
- `domain.yml`: Intents, entities, slots, and responses
- `data/nlu.yml`: Training examples for natural language understanding
- `data/stories.yml`: Conversation flows
- `data/rules.yml`: Simple conversation rules
- `actions.py`: Custom actions for personalized responses
- `credentials.yml`: API credentials and webhook configuration
- `rasa_license.env`: Developer Edition license key

## Custom Actions

The chatbot includes custom actions that:
- Access the user's wardrobe from Django database
- Provide weather-aware outfit suggestions
- Generate personalized recommendations
- Handle fallback scenarios

## Troubleshooting

### Common Issues

1. **Server not starting**: Check if ports 5005 and 5055 are available
2. **Model not loading**: Run `rasa train` to retrain the model
3. **Actions not working**: Ensure action server is running on port 5055
4. **Django integration issues**: Check if Django server is running on port 8000

### Debug Mode
```bash
# Start with debug logging
rasa run --enable-api --cors "*" --port 5005 --debug
```

### Validate Configuration
```bash
# Validate data and configuration
rasa data validate
```

## Development

### Retraining the Model
```bash
# After making changes to data or configuration
rasa train
```

### Interactive Learning
```bash
# Train interactively
rasa interactive
```

### Testing Stories
```bash
# Test conversation flows
rasa test
```

## API Endpoints

- `GET /status`: Server status
- `POST /webhooks/rest/webhook`: Send messages to chatbot
- `GET /domain`: Get domain information
- `POST /model/parse`: Parse text for intents and entities

## Example Conversations

**User**: "Suggest an outfit for today"
**Bot**: "Here are some great outfit suggestions for you..."

**User**: "What to wear in the rain?"
**Bot**: "For rainy days, I recommend waterproof outerwear..."

**User**: "Give me style tips"
**Bot**: "Here are some timeless fashion tips that will transform your style..."

## Requirements

- Python 3.8+
- Rasa 3.6.15
- Django (for integration)
- TensorFlow (for ML models)

## Installation

```bash
# Install Rasa
pip install rasa==3.6.15

# Install additional dependencies
pip install -r requirements.txt
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Rasa documentation: https://rasa.com/docs/
3. Check Django integration in `stylist_chatbot/` directory