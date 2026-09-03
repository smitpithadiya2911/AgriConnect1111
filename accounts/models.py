from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='buyer')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    def is_farmer(self):
        return self.role == 'farmer'

    def is_buyer(self):
        return self.role == 'buyer'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Farmer(models.Model):
    CERTIFICATION_CHOICES = (
        ('verified', 'Verified'),
        ('pending', 'Pending'),
        ('none', 'None'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer_profile')
    farm_name = models.CharField(max_length=100, blank=True, null=True)
    farm_location = models.CharField(max_length=255, blank=True, null=True)
    farm_size = models.CharField(max_length=50, blank=True, null=True)  # e.g., "5 Acres"
    certification_status = models.CharField(max_length=50, choices=CERTIFICATION_CHOICES, default='pending')
    experience = models.CharField(max_length=50, default='5 Years')
    orders_completed = models.IntegerField(default=50)
    store_rating = models.FloatField(default=4.5)
    specialization = models.CharField(max_length=100, default='General Farming')
    about = models.TextField(blank=True, null=True)
    cover_banner = models.ImageField(upload_to='covers/', blank=True, null=True)
    certifications = models.TextField(blank=True, null=True)
    awards = models.TextField(blank=True, null=True)
    repeat_customers = models.IntegerField(default=45)
    ontime_delivery = models.IntegerField(default=98)
    satisfaction_rate = models.IntegerField(default=97)

    village = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    organic_certificate = models.FileField(upload_to='farmer_docs/', blank=True, null=True)

    # Verification workflow fields
    verification_status = models.CharField(
        max_length=20, 
        choices=(
            ('pending', 'Pending Submission'), 
            ('review', 'Under Review'), 
            ('approved', 'Approved'), 
            ('rejected', 'Rejected'), 
            ('resubmit', 'Resubmission Required')
        ), 
        default='pending'
    )
    aadhaar_document = models.FileField(upload_to='farmer_docs/', blank=True, null=True)
    farm_certificate = models.FileField(upload_to='farmer_docs/', blank=True, null=True)
    trust_score = models.IntegerField(default=85)
    verification_date = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='verified_farmers')
    admin_notes = models.TextField(blank=True, null=True)
    approval_history = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Farmer Profile: {self.user.username} - {self.farm_name or 'N/A'}"


class Buyer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer_profile')
    delivery_address = models.TextField(blank=True, null=True)
    contact_name = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"Buyer Profile: {self.user.username}"
