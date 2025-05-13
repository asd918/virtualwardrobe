"""
WSGI config for virtual_wardrobe project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from dotenv import load_dotenv # Added for .env support

from django.core.wsgi import get_wsgi_application

load_dotenv() # Added for .env support
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual_wardrobe.settings')

application = get_wsgi_application()
