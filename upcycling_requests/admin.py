# requests/admin.py
from django.contrib import admin
from .models import UpcyclingRequest, ArtisanProfile, Offer # Import your model

admin.site.register(UpcyclingRequest) # Register it with the admin
admin.site.register(ArtisanProfile) # <--- REGISTER ARTISANPROFILE
admin.site.register(Offer) # <--- REGISTER OFFER