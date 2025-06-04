# upcycling_requests/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UpcyclingRequestForm, UserRegisterForm, OfferForm, MessageForm
from .models import UpcyclingRequest, ArtisanProfile, Offer, Conversation, Message
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt # For API endpoint that JavaScript calls
from django.conf import settings # To access GOOGLE_APPLICATION_CREDENTIALS
import os
import json # Ensure json is imported for loading the file

# For dashboard and fake AI
import random
import time # Add this for fake AI delay
from datetime import date, timedelta, datetime

# --- LOAD FAKE AI DATA ---
# Construct the full path to the JSON file
# Assumes fake_ai_data.json is in the same directory as views.py
FAKE_AI_DATA_PATH = os.path.join(os.path.dirname(__file__), 'fake_ai_data.json')
FAKE_AI_RESPONSES = []
try:
    with open(FAKE_AI_DATA_PATH, 'r', encoding='utf-8') as f:
        FAKE_AI_RESPONSES = json.load(f)
    print(f"Loaded {len(FAKE_AI_RESPONSES)} fake AI responses from {FAKE_AI_DATA_PATH}")
except FileNotFoundError:
    print(f"ERROR: fake_ai_data.json not found at {FAKE_AI_DATA_PATH}. Fake AI will use fallback only.")
except json.JSONDecodeError:
    print(f"ERROR: Could not decode fake_ai_data.json. Check JSON format.")
# --- END LOAD FAKE AI DATA ---

# --- Helper function for AI analysis (THIS IS NOW A BYPASSED PLACEHOLDER FOR DEMO) ---
def analyze_image_with_vision_api(image_bytes):
    """
    This function is now a placeholder for the demo.
    It will NOT be called by api_scan_image in demo mode.
    """
    print("DEMO MODE: analyze_image_with_vision_api is being bypassed.")
    return {
        'product_type': '',
        'material_details': '',
        'raw_labels': []
    }


# A simple home page view (optional, but good to have)
def home_page(request):
    # Fetch up to 3 latest requests that are 'Request Received' (pending)
    latest_requests = UpcyclingRequest.objects.filter(status='Request Received').order_by('-created_at')[:3]
    context = {
        'latest_requests': latest_requests,
    }
    return render(request, 'upcycling_requests/home_page.html', context)

def is_active_artisan(user):
    return user.is_authenticated and hasattr(user, 'artisan_profile') and user.artisan_profile.is_active_artisan

# View to handle creating an upcycling request
@login_required
def create_upcycling_request(request):
    if request.method == 'POST':
        form = UpcyclingRequestForm(request.POST, request.FILES)
        if form.is_valid():
            upcycling_request = form.save(commit=False)
            upcycling_request.user = request.user

            # --- FOR DEMO MODE: AI labels for the final submission will be empty ---
            # This ensures no real AI calls or errors when submitting the form
            upcycling_request.ai_labels = []
            # --- END IMPORTANT ---

            upcycling_request.save()
            messages.success(request, 'Your upcycling request has been submitted successfully!')
            return redirect('upcycling_requests:my_requests')
        else:
            messages.error(request, 'Please correct the errors below.')
            pass # Form will be rendered again with errors if invalid
    else:
        form = UpcyclingRequestForm()

    context = {
        'form': form
    }
    return render(request, 'upcycling_requests/create_upcycling_request.html', context)

# A simple success page view (this is currently not used by create_upcycling_request, can be removed if not needed elsewhere)
def request_success(request):
    return render(request, 'upcycling_requests/request_success.html')


@login_required
def request_detail(request, request_id):
    upcycling_request = get_object_or_404(UpcyclingRequest, id=request_id)

    offer_form = None
    has_made_offer = False # Flag to track if the current artisan has an offer

    if request.user.is_authenticated:
        # Check if the logged-in user is an active artisan AND not the owner of the request
        if hasattr(request.user, 'artisan_profile') and \
           request.user.artisan_profile.is_active_artisan and \
           request.user != upcycling_request.user:

            # Check if this artisan has already made an offer for this request
            if Offer.objects.filter(request=upcycling_request, artisan=request.user.artisan_profile).exists():
                has_made_offer = True
            else:
                # Only initialize the form if no offer has been made by this artisan
                offer_form = OfferForm()

    context = {
        'request': upcycling_request,
        'offer_form': offer_form, # This will be None if offer already made or not artisan
        'has_made_offer': has_made_offer, # Pass the flag to the template
    }
    return render(request, 'upcycling_requests/request_detail.html', context)

@login_required
def my_requests(request):
    user_requests = UpcyclingRequest.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'requests': user_requests
    }
    return render(request, 'upcycling_requests/my_requests.html', context)

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()

    context = {
        'form': form
    }
    return render(request, 'upcycling_requests/register.html', context)

@login_required
@user_passes_test(is_active_artisan, login_url='/accounts/login/')
def artisan_available_requests(request):
    available_requests = UpcyclingRequest.objects.filter(
        status='Request Received',
        accepted_artisan__isnull=True
    ).order_by('-created_at')

    context = {
        'available_requests': available_requests
    }
    return render(request, 'upcycling_requests/artisan_available_requests.html', context)

@login_required
@user_passes_test(is_active_artisan, login_url='/accounts/login/') # Only active artisans can make offers
def make_offer(request, request_id):
    upcycling_request = get_object_or_404(UpcyclingRequest, id=request_id)

    # Prevent request owner from making an offer on their own request
    if request.user == upcycling_request.user:
        messages.error(request, "You cannot make an offer on your own upcycling request.")
        return redirect('upcycling_requests:request_detail', request_id=upcycling_request.id)

    if request.method == 'POST':
        form = OfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.request = upcycling_request
            offer.artisan = request.user.artisan_profile # Link to the artisan profile
            offer.status = 'Pending' # Default status for new offers
            offer.save()
            messages.success(request, "Your offer has been submitted successfully!")
            return redirect('request_detail', request_id=upcycling_request.id)
        else:
            # If form is invalid, re-render the detail page with the form and errors
            offer_form = form # Pass the form with errors
            context = {
                'request': upcycling_request,
                'offer_form': offer_form,
            }
            messages.error(request, "There was an error with your offer submission. Please check the details.")
            return render(request, 'upcycling_requests/request_detail.html', context)
    # If it's not a POST request to make an offer, it shouldn't hit this view directly
    # It's intended for form submission from request_detail.html
    return redirect('request_detail', request_id=upcycling_request.id)


@login_required
def accept_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    upcycling_request = offer.request

    # Ensure the logged-in user is the owner of the request
    if request.user != upcycling_request.user:
        messages.error(request, "You are not authorized to accept this offer.")
        return redirect('request_detail', request_id=upcycling_request.id)

    # Prevent accepting offers if the request is already accepted/completed
    if upcycling_request.status not in ['Request Received', 'Offer Made', 'Open']: # Added 'Open' to allowed statuses
        messages.error(request, f"This request (status: {upcycling_request.status}) can no longer accept offers.")
        return redirect('upcycling_requests:request_detail', request_id=upcycling_request.id)

    # Check if the offer is still pending
    if offer.status != 'Pending':
        messages.error(request, "This offer is not pending and cannot be rejected.")
        return redirect('request_detail', request_id=upcycling_request.id)

    # Start a database transaction for atomicity
    with transaction.atomic():
        # 1. Mark the accepted offer as 'Accepted'
        offer.status = 'Accepted'
        offer.save()

        # 2. Update the UpcyclingRequest status and assign the artisan
        upcycling_request.status = 'Offer Accepted'
        upcycling_request.accepted_artisan = offer.artisan.user
        upcycling_request.save()

        # 3. Reject all other pending offers for this request
        Offer.objects.filter(request=upcycling_request, status='Pending').exclude(id=offer.id).update(status='Rejected')

        # Robustly create or get conversation: enforce participant order
        participant1_user, participant2_user = sorted(
            [upcycling_request.user, offer.artisan.user],
            key=lambda u: u.pk # Sort by primary key to ensure consistent order
        )

        conversation, created = Conversation.objects.get_or_create(
            upcycling_request=upcycling_request,
            participant1=participant1_user,
            participant2=participant2_user,
            defaults={} # No extra defaults needed if all fields are part of the lookup
        )

        # Add an initial message to the conversation
        initial_message_content = f"Your offer for '{upcycling_request.product_type}' has been accepted! Let's discuss details."
        try:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=initial_message_content
            )
        except Exception as e:
            # Log the error, but don't prevent the offer acceptance
            print(f"ERROR: Failed to create initial message: {e}")

    messages.success(request, f"Offer from {offer.artisan.user.username} has been accepted! Request status updated.")
    return redirect('upcycling_requests:request_detail', request_id=upcycling_request.id)


@login_required
def reject_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    upcycling_request = offer.request

    # Ensure the logged-in user is the owner of the request
    if request.user != upcycling_request.user:
        messages.error(request, "You are not authorized to reject this offer.")
        return redirect('request_detail', request_id=upcycling_request.id)

    # Only allow rejection of pending offers
    if offer.status != 'Pending':
        messages.error(request, "This offer is not pending and cannot be rejected.")
        return redirect('request_detail', request_id=upcycling_request.id)

    # Mark the offer as 'Rejected'
    offer.status = 'Rejected'
    offer.save()
    messages.info(request, f"Offer from {offer.artisan.user.username} has been rejected.")
    return redirect('request_detail', request_id=upcycling_request.id)

# NEW: View to list all conversations for the logged-in user
@login_required
def conversation_list(request):
    # Fetch conversations where the current user is either participant1 or participant2
    conversations = Conversation.objects.filter(
        Q(participant1=request.user) | Q(participant2=request.user)
    ).order_by('-updated_at')

    context = {
        'conversations': conversations
    }
    return render(request, 'upcycling_requests/conversation_list.html', context)

# NEW: View to display a specific conversation and allow sending messages
@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    # Ensure the logged-in user is a participant in this conversation
    if request.user not in [conversation.participant1, conversation.participant2]:
        messages.error(request, "You are not authorized to view this conversation.")
        # If it's an AJAX request trying to send a message but unauthorized
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Unauthorized access'}, status=403)
        return redirect('upcycling_requests:conversation_list')

    # Mark all messages in this conversation sent by the *other* participant as read
    Message.objects.filter(conversation=conversation, is_read=False).exclude(sender=request.user).update(is_read=True)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            # Update conversation's 'updated_at' timestamp
            conversation.save()

            # Check if the request is an AJAX request
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Return a JSON response for AJAX requests
                return JsonResponse({
                    'success': True,
                    'message_content': message.content,
                    'timestamp': message.timestamp.strftime("%b %d, %H:%M") # Format timestamp to match template
                })
            else:
                # This block serves as a fallback for non-AJAX POST requests
                # (which should not happen with the JavaScript changes in place)
                messages.success(request, "Message sent!")
                return redirect('upcycling_requests:conversation_detail', conversation_id=conversation.id)
        else:
            # If the form is not valid, return JSON errors for AJAX requests
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)
            else:
                # For non-AJAX requests, add error message and re-render the page
                messages.error(request, "Failed to send message. Please check your input.")
                # Fall through to render the template with form errors
    else:
        # For GET requests, initialize an empty form
        form = MessageForm()

    # Fetch and order messages for GET requests or if form is invalid (non-AJAX)
    messages_in_conversation = conversation.messages.all().order_by('timestamp')

    context = {
        'conversation': conversation,
        'messages_in_conversation': messages_in_conversation,
        'form': form,
        'other_participant': conversation.participant1 if request.user == conversation.participant2 else conversation.participant2
    }
    return render(request, 'upcycling_requests/conversation_detail.html', context)

# --- NEW DASHBOARD VIEWS START HERE ---

# Helper function to generate dummy data for the dashboard charts
def generate_dummy_data():
    today = date.today()
    data = {
        'requests_per_month': [],
        'offers_per_month': [],
        'top_product_types': [],
        'waste_diverted_kg': 0,
    }

    # Data for past 6 months
    for i in range(6, 0, -1): # Iterate backwards to get correct chronological order
        month_date = today - timedelta(days=30 * i)
        month = month_date.strftime('%b %Y')
        data['requests_per_month'].append({
            'month': month,
            'count': random.randint(10, 50)
        })
        data['offers_per_month'].append({
            'month': month,
            'count': random.randint(5, 40)
        })

    # Top product types (dummy logic improved for better distribution)
    product_types_list = ['Furniture', 'Textiles', 'Electronics', 'Decor', 'Other', 'Clothing', 'Accessory']
    type_counts_sum = 0
    temp_product_types_data = []
    for p_type in product_types_list:
        count = random.randint(15, 60)
        temp_product_types_data.append({'label': p_type, 'value': count})
        type_counts_sum += count

    # Sort and take top 5, or all if less than 5
    sorted_types = sorted(temp_product_types_data, key=lambda x: x['value'], reverse=True)
    data['top_product_types'] = sorted_types[:min(5, len(sorted_types))]


    # Dummy waste diverted data (example: kilograms)
    data['waste_diverted_kg'] = random.randint(500, 2000)

    return data

@login_required
def dashboard_view(request):
    # Using the helper function to get dummy data
    dashboard_data = generate_dummy_data()

    # Pass the data to the template
    return render(request, 'upcycling_requests/dashboard.html', {'dashboard_data': dashboard_data})


# Optional: JSON endpoint for dashboard data (if you want to fetch dynamically later)
@login_required
def get_dashboard_data_json(request):
    # This function can return the same dummy data or real data
    dashboard_data = generate_dummy_data() # Use the helper function here too
    return JsonResponse(dashboard_data)

# --- MODIFIED: AI Image Scan API View (Contextual Fake for Demo using JSON) ---
@csrf_exempt
@login_required
def api_scan_image(request):
    if request.method == 'POST':
        if 'image' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No image provided for demo scan.'}, status=400)

        uploaded_image = request.FILES['image']
        image_name_lower = uploaded_image.name.lower() # Get the filename in lowercase

        # --- Find a matching response based on filename keywords from the loaded JSON data ---
        chosen_response = None
        for item_data in FAKE_AI_RESPONSES:
            if item_data["keyword"] in image_name_lower:
                chosen_response = item_data
                break # Use the first match found

        # --- Fallback if no specific keyword is found ---
        if chosen_response is None:
            # Provide a sensible, but general, upcyclable item
            fallback_options = [
                {"product_type": "Mixed Household Waste", "material_details": "Assorted Plastics, Paper, Metal", "raw_labels": ["Waste", "Mixed Materials", "Recyclable"]},
                {"product_type": "Random Discarded Item", "material_details": "Unknown Composite Materials", "raw_labels": ["Discarded", "Object", "Various Materials"]},
                {"product_type": "Upcycling Candidate", "material_details": "Potentially Repurposable Goods", "raw_labels": ["Upcycle", "Item", "Re-use"]}
            ]
            chosen_response = random.choice(fallback_options)


        # --- Optional: Simulate a realistic processing delay ---
        time.sleep(4) # Wait for 4 second (adjust as needed for demo pace)

        return JsonResponse({
            'success': True,
            'product_type': chosen_response['product_type'],
            'material_details': chosen_response['material_details'],
            'raw_labels': chosen_response['raw_labels']
        })
        # --- END DEMO MODE MODIFICATION ---

    return JsonResponse({'success': False, 'error': 'Invalid request method for demo scan.'}, status=405)