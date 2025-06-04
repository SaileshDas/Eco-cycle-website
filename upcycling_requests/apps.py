from django.apps import AppConfig

class UpcyclingRequestsConfig(AppConfig): # Renamed the class for consistency
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'upcycling_requests'           # <-- CRITICAL: Change this to the new app name