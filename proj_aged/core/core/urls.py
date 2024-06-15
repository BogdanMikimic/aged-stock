from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import custom_auth_urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('aged.urls')),
    path('accounts/', include(custom_auth_urls)),  # Use my authentication file
    ]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
