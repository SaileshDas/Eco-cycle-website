# requests/forms.py
from django import forms
from .models import UpcyclingRequest, Offer, Conversation, Message
from django.contrib.auth.forms import UserCreationForm

class UpcyclingRequestForm(forms.ModelForm):
    class Meta:
        model = UpcyclingRequest
        # Define the fields from your model that you want to include in the form
        fields = [
            'product_type',
            'material_details',
            'style_preference',
            'pickup_location',
            'budget',
            'item_image',
            # 'user' and 'created_at' are handled automatically or in the view
            # 'status' will have a default value
        ]
        # Optional: Customize how fields are displayed (e.g., make text areas bigger)
        widgets = {
            'material_details': forms.Textarea(attrs={'rows': 4}),
        }
        # Optional: Add a label for the image field for better user experience
        labels = {
            'item_image': 'Upload an image of your item',
        }
        
# --- NEW FORM FOR USER REGISTRATION ---
class UserRegisterForm(UserCreationForm):
    # You can add custom fields here if needed later (e.g., email)
    # For now, we'll keep it simple with just username and password
    pass

# --- NEW FORM FOR OFFERS ---
class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        # Artisan should only input price, estimated days, and message.
        # request and artisan fields will be set by the view.
        fields = ['price', 'estimated_completion_days', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'price': 'Your Offer Price ($)',
            'estimated_completion_days': 'Estimated Completion (days)',
            'message': 'Your Message to Requester',
        }

# NEW: Form for sending messages
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content'] # Only need the message content from the user
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message...'}),
        }