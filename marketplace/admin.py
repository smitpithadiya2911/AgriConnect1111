from django.contrib import admin

# Register your models here.
from .models import (
    Category,
    Crop,
    CartItem,
    Order,
    OrderItem,
    Payment,
    Review,
    Notification,
    Feedback,
    PriceTrend,
    ChatMessage,
    Wishlist,
    FavoriteFarmer,
    FarmerRating,
    Report,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


from django.utils.safestring import mark_safe

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'image_preview',
        'name',
        'category',
        'farmer',
        'price_per_kg',
        'quantity_available',
        'harvest_date',
        'shelf_life_days',
        'availability_status',
        'is_approved',
        'created_at'
    )

    list_filter = (
        'category',
        'harvest_date',
        'availability_status',
        'is_approved',
        'created_at'
    )

    search_fields = (
        'name',
        'description',
        'farmer__user__username'
    )

    list_editable = (
        'is_approved',
        'availability_status'
    )

    readonly_fields = ('image_preview_detail',)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 6px; border: 1px solid rgba(0,0,0,0.08);" />')
        return "-"
    image_preview.short_description = 'Image'

    def image_preview_detail(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-width: 280px; max-height: 280px; object-fit: cover; border-radius: 8px; border: 1px solid rgba(0,0,0,0.08);" />')
        return "No image uploaded"
    image_preview_detail.short_description = 'Current Crop Image'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'crop',
        'quantity'
    )

    search_fields = (
        'user__username',
        'crop__name'
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'buyer',
        'farmer',
        'total_amount',
        'payment_method',
        'status',
        'created_at'
    )

    list_filter = (
        'status',
        'payment_method',
        'created_at'
    )

    search_fields = (
        'buyer__username',
        'farmer__user__username'
    )

    list_editable = (
        'status',
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'crop',
        'quantity',
        'price_per_unit'
    )

    search_fields = (
        'crop__name',
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'amount',
        'payment_method',
        'status',
        'created_at'
    )

    list_filter = (
        'status',
        'payment_method'
    )

    search_fields = (
        'transaction_id',
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'buyer',
        'crop',
        'rating',
        'created_at'
    )

    list_filter = (
        'rating',
    )

    search_fields = (
        'buyer__username',
        'crop__name'
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'notification_type',
        'is_read',
        'created_at'
    )

    list_filter = (
        'notification_type',
        'is_read'
    )

    search_fields = (
        'user__username',
    )

    list_editable = (
        'is_read',
    )


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'subject',
        'is_resolved',
        'created_at'
    )

    list_filter = (
        'is_resolved',
    )

    search_fields = (
        'subject',
        'user__username'
    )

    list_editable = (
        'is_resolved',
    )


@admin.register(PriceTrend)
class PriceTrendAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'crop_name',
        'category',
        'avg_price',
        'record_date'
    )

    list_filter = (
        'category',
        'record_date'
    )

    search_fields = (
        'crop_name',
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sender',
        'receiver',
        'crop',
        'is_read',
        'created_at'
    )

    list_filter = (
        'is_read',
    )

    search_fields = (
        'sender__username',
        'receiver__username',
        'message'
    )


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'crop', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'crop__name')


@admin.register(FavoriteFarmer)
class FavoriteFarmerAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'farmer', 'followed_at')
    list_filter = ('followed_at',)
    search_fields = ('buyer__username', 'farmer__farm_name')


@admin.register(FarmerRating)
class FarmerRatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'farmer', 'rating', 'quality_rating', 'communication_rating', 'delivery_rating', 'packaging_rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('buyer__username', 'farmer__farm_name')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'report_type', 'generated_by', 'format', 'download_count', 'scheduled_interval', 'created_at')
    list_filter = ('report_type', 'format', 'scheduled_interval', 'created_at')
    search_fields = ('name', 'generated_by__username')