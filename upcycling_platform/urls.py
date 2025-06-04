# upcycling_platform/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView # NEW IMPORT

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # NEW: Redirect the root path '/' to the namespaced home page
    path('', RedirectView.as_view(pattern_name='upcycling_requests:home', permanent=False)),
    
    # Your app's URLs are now prefixed
    path('upcycling_requests/', include('upcycling_requests.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)