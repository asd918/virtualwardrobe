from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('wardrobe_app.urls', 'wardrobe'), namespace='wardrobe')),
    path('stylist-chat/', include(('stylist_chatbot.urls', 'stylist_chatbot'), namespace='stylist_chatbot')),
]

# Add media files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
