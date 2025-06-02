# requests/urls.py
from django.urls import path
from . import views # Import the views from our app

urlpatterns = [
    path('', views.home_page, name='home'),
    # path('relative_path/', views.your_view_function, name='name_for_url'),
    path('create/', views.create_upcycling_request, name='create_request'),
    path('success/', views.request_success, name='request_success'),
    # NEW URL PATTERN FOR DETAIL VIEW
    path('<int:request_id>/', views.request_detail, name='request_detail'),
    # NEW URL PATTERN FOR LIST VIEW
    path('my-requests/', views.my_requests, name='my_requests'),
    # NEW URL PATTERN FOR REGISTRATION
    path('register/', views.register, name='register'),
    # NEW URL PATTERN FOR ARTISAN VIEW
    path('available-requests/', views.artisan_available_requests, name='artisan_available_requests'),
    # --- NEW URL PATTERNS FOR OFFER ACTIONS ---
    path('offer/<int:offer_id>/accept/', views.accept_offer, name='accept_offer'),
    path('offer/<int:offer_id>/reject/', views.reject_offer, name='reject_offer'),
    # --- ADD THIS NEW URL PATTERN FOR MAKING AN OFFER ---
    path('<int:request_id>/make_offer/', views.make_offer, name='make_offer'), # <-- ADD THIS LINE
    # NEW: Messaging URLs
    path('messages/', views.conversation_list, name='conversation_list'),
    path('messages/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),

    # --- NEW DASHBOARD URLS ---
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/dashboard-data/', views.get_dashboard_data_json, name='dashboard_data_api'), # Optional API endpoint
    # --- END NEW DASHBOARD URLS ---
]