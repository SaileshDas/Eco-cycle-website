# upcycling_requests/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import JSONField # Import JSONField

class UpcyclingRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upcycling_requests')
    product_type = models.CharField(max_length=100)
    material_details = models.TextField()
    style_preference = models.CharField(max_length=200, blank=True, null=True)
    pickup_location = models.CharField(max_length=255)
    budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=50, default='Request Received')
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_artisan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_upcycling_requests')
    item_image = models.ImageField(upload_to='request_images/', blank=True, null=True)
    # NEW FIELD FOR AI LABELS
    ai_labels = JSONField(default=list, blank=True, null=True) # Stores list of AI detected labels

    def __str__(self):
        return f"Request for {self.product_type} by {self.user.username if self.user else 'Guest'}"

# --- NEW ARTISAN PROFILE MODEL ---
class ArtisanProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='artisan_profile')
    bio = models.TextField(blank=True, null=True)
    skills = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated skills (e.g., 'Sewing, Woodworking, Painting')")
    portfolio_link = models.URLField(max_length=200, blank=True, null=True)
    is_active_artisan = models.BooleanField(default=False)

    # Added property to check if user is an artisan for easier template logic (as discussed with base.html)
    @property
    def is_artisan(self):
        return self.is_active_artisan

    def __str__(self):
        return f"{self.user.username}'s Artisan Profile"

class Offer(models.Model):
    request = models.ForeignKey(UpcyclingRequest, on_delete=models.CASCADE, related_name='offers')
    artisan = models.ForeignKey(ArtisanProfile, on_delete=models.CASCADE, related_name='made_offers')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_completion_days = models.IntegerField(help_text="Estimated days to complete the upcycling project")
    message = models.TextField(blank=True, null=True, help_text="Message from the artisan to the requester")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('Pending', 'Pending'),
            ('Accepted', 'Accepted'),
            ('Rejected', 'Rejected'),
        ],
        default='Pending'
    )

    class Meta:
        unique_together = ('request', 'artisan')
        ordering = ['price']

    def __str__(self):
        return f"Offer by {self.artisan.user.username} for Request {self.request.id} - Status: {self.status}"

# --- SIGNAL TO CREATE ARTISAN PROFILE WHEN A NEW USER IS CREATED ---
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        ArtisanProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'artisan_profile'):
        instance.artisan_profile.save()

# NEW: Conversation Model
class Conversation(models.Model):
    upcycling_request = models.ForeignKey(
        'UpcyclingRequest',
        on_delete=models.CASCADE,
        related_name='conversations',
        null=True, blank=True
    )
    participant1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_p1'
    )
    participant2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_p2'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('upcycling_request', 'participant1', 'participant2')
        ordering = ['-updated_at']

    def __str__(self):
        request_info = f" (Request: {self.upcycling_request.id})" if self.upcycling_request else ""
        return f"Conversation between {self.participant1.username} and {self.participant2.username}{request_info}"

# NEW: Message Model
class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender.username} in Conversation {self.conversation.id} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"