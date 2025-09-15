# Virtual Wardrobe

A Django-based web application for managing your wardrobe, creating outfits, and getting weather-based clothing recommendations.

## Features

- User authentication (registration, login, password reset)
- Wardrobe management (add, edit, delete clothing items)
- Outfit creation and management
- Weather-based clothing recommendations
- Responsive design with Bootstrap 5

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd virtual_wardrobe
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following variables:
```
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
OPENWEATHERMAP_API_KEY=your-api-key
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

8. Access the application at http://127.0.0.1:8000/

## Dialogflow Chatbot Integration

This project integrates Google Dialogflow (ES) as the chatbot backend for the AI Stylist.

### Prerequisites

- Install dependency (already in requirements.txt):
  - `google-cloud-dialogflow`
- Service account JSON credentials for your Dialogflow project.
- Project ID: `virtualwardrobe-eqqa`

### Environment

Set the Google credentials environment variable before running Django.

- PowerShell (Windows):
```
set GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\dialogflow-key.json"
```

- Bash:
```
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/dialogflow-key.json"
```

### Backend Endpoints

- Chat message API used by the UI:
  - `POST /stylist-chat/api/message/` with JSON `{ "message": "..." }`
- Simple external endpoint:
  - `GET /stylist-chat/chatbot-response?message=hello`

### Where the code lives

- Dialogflow client: `stylist_chatbot/dialogflow_client.py`
- Views and intent mapping: `stylist_chatbot/views.py`
- URLs: `stylist_chatbot/urls.py`
- Chat UI: `stylist_chatbot/templates/stylist_chatbot/chat_interface.html`

### Import ready-made Dialogflow agent

We provide an export you can import directly:

- Folder: `stylist_chatbot/dialogflow_export/`
  - `agent.json`
  - `intents/*.json` (Welcome, Outfit Recommendation, Weather Outfit, Color Matching, Casual Outfit, Formal Outfit, Goodbye)

Steps:
1) Zip the contents of `stylist_chatbot/dialogflow_export/` (include `agent.json` and the `intents` folder).
2) Dialogflow ES Console → your agent → Settings (gear) → Export and Import → Import from ZIP.

### Testing

Run unit tests:
```
python manage.py test stylist_chatbot -v 2
```

Quick endpoint check:
```
http://localhost:8000/stylist-chat/chatbot-response?message=hello
```

## Project Structure

- `wardrobe_app/` - Main application directory
  - `templates/` - HTML templates
  - `static/` - Static files (CSS, JS, images)
  - `models.py` - Database models
  - `views.py` - View functions
  - `urls.py` - URL routing
  - `forms.py` - Form definitions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 