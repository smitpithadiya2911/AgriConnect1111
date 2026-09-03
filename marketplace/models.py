from django.db import models
from django.conf import settings
from accounts.models import Farmer
from datetime import date, timedelta

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Crop(models.Model):
    UNIT_CHOICES = (
        ('kg', 'Kilogram (kg)'),
        ('ton', 'Ton'),
        ('piece', 'Piece'),
        ('quintal', 'Quintal (100kg)'),
    )
    AVAILABILITY_CHOICES = (
        ('available', 'Available'),
        ('out_of_stock', 'Out of Stock'),
    )
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='crops')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='crops')
    name = models.CharField(max_length=100)
    description = models.TextField()
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price per Unit")  # matches unit price
    quantity_available = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    image = models.ImageField(upload_to='crops/', blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    harvest_date = models.DateField(default=date.today)
    shelf_life_days = models.IntegerField(default=30)
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def remaining_shelf_life_days(self):
        if not self.harvest_date:
            return 0
        delta = (self.harvest_date + timedelta(days=self.shelf_life_days)) - date.today()
        return max(0, delta.days)

    @property
    def freshness_status(self):
        days = self.remaining_shelf_life_days
        if days <= 0:
            return "Expired"
        elif days <= 2:
            return "Expiring Soon"
        return "Fresh"

    def estimated_delivery_days(self, buyer):
        if not buyer or not buyer.city:
            return 4  # Default national/interstate delivery
        farmer = self.farmer
        if farmer.city and buyer.city and farmer.city.strip().lower() == buyer.city.strip().lower():
            return 1  # Same city
        if farmer.state and buyer.state and farmer.state.strip().lower() == buyer.state.strip().lower():
            return 2  # Same state
        return 4  # Interstate

    def is_eligible_for_delivery(self, buyer):
        return self.remaining_shelf_life_days >= self.estimated_delivery_days(buyer)

    # Let's fix decimal_length to decimal_places for Django fields
    # wait, yes, Django DecimalField takes decimal_places, not decimal_length!
    # Let me ensure I use decimal_places.

    def __str__(self):
        return f"{self.name} - {self.farmer.user.username}"


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.crop.price_per_kg * self.quantity

    def __str__(self):
        return f"{self.user.username} - {self.crop.name} ({self.quantity})"


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Packed', 'Packed'),
        ('Out For Delivery', 'Out For Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Returned', 'Returned'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('COD', 'Cash on Delivery'),
        ('Online', 'Online Payment'),
    )
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='COD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    shipping_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    def total_price(self):
        return self.price_per_unit * self.quantity

    def __str__(self):
        return f"Item: {self.crop.name if self.crop else 'Deleted Crop'} x {self.quantity} in Order #{self.order.id}"


class Payment(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.status}"


class Review(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(default=5)  # 1 to 5
    title = models.CharField(max_length=200, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='reviews/', blank=True, null=True)
    helpful_votes = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='helpful_reviews')
    reply = models.TextField(blank=True, null=True)
    reply_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.crop.name} by {self.buyer.username} - {self.rating} Stars"

    def is_verified_purchase(self):
        from marketplace.models import OrderItem
        return OrderItem.objects.filter(
            order__buyer=self.buyer,
            order__status='Delivered',
            crop=self.crop
        ).exists()


class FarmerRating(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='farmer_ratings')
    farmer = models.ForeignKey('accounts.Farmer', on_delete=models.CASCADE, related_name='farmer_ratings')
    rating = models.PositiveIntegerField(default=5)
    quality_rating = models.PositiveIntegerField(default=5)
    communication_rating = models.PositiveIntegerField(default=5)
    delivery_rating = models.PositiveIntegerField(default=5)
    packaging_rating = models.PositiveIntegerField(default=5)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating for {self.farmer.user.username} by {self.buyer.username} - {self.rating} Stars"


class Notification(models.Model):
    TYPE_CHOICES = (
        ('order', 'Order Update'),
        ('price', 'Price Alert'),
        ('weather', 'Weather Alert'),
        ('system', 'System Announcement'),
        ('message', 'Chat Message'),
        ('review', 'Customer Review'),
        ('product', 'Product Status'),
        ('verification', 'Document Verification'),
    )
    PRIORITY_CHOICES = (
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    link = models.CharField(max_length=200, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username} - {self.notification_type} ({self.priority})"


class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feedbacks')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback: {self.subject} by {self.user.username}"


class PriceTrend(models.Model):
    crop_name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    avg_price = models.DecimalField(max_digits=10, decimal_places=2)
    record_date = models.DateField()

    class Meta:
        ordering = ['record_date']

    def __str__(self):
        return f"Price Trend: {self.crop_name} - {self.avg_price} on {self.record_date}"


class MarketInsight(models.Model):
    crop_name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_change_percent = models.DecimalField(max_digits=5, decimal_places=2)
    demand_level = models.CharField(max_length=20, default='Medium')
    forecast_direction = models.CharField(max_length=20, default='Stable')
    region = models.CharField(max_length=100, default='Rajkot, Gujarat')
    volume_tonnes = models.IntegerField(default=120)
    record_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.crop_name} Market Insight - {self.current_price} in {self.region}"


class ReturnRequest(models.Model):
    REASON_CHOICES = (
        ('damaged', 'Damaged Product'),
        ('wrong', 'Wrong Product'),
        ('quality', 'Quality Issue'),
        ('late', 'Late Delivery'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='returns')
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Return Request for Order #{self.order.id} - {self.status}"


class ChatMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Msg from {self.sender.username} to {self.receiver.username}"


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    crop = models.ForeignKey('Crop', on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'crop')
        ordering = ['-added_at']

    def __str__(self):
        return f"Wishlist: {self.user.username} - {self.crop.name}"


class FavoriteFarmer(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_farmers')
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='followers')
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('buyer', 'farmer')
        ordering = ['-followed_at']

    def __str__(self):
        return f"FavoriteFarmer: {self.buyer.username} following {self.farmer.user.username}"


class Report(models.Model):
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    format = models.CharField(max_length=10) # pdf, csv, xlsx
    download_count = models.PositiveIntegerField(default=0)
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    scheduled_interval = models.CharField(max_length=20, blank=True, null=True) # daily, weekly, monthly
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.format.upper()})"

