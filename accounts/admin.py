from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import User, Farmer, Buyer


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'role',
        'phone',
        'is_staff',
        'is_superuser',
        'is_active',
        'date_joined'
    )

    list_filter = (
        'role',
        'is_staff',
        'is_superuser',
        'is_active',
        'date_joined'
    )

    search_fields = (
        'username',
        'email',
        'phone'
    )

    ordering = ('-date_joined',)


@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'farm_name',
        'farm_location',
        'farm_size',
        'certification_status'
    )

    list_filter = (
        'certification_status',
    )

    search_fields = (
        'user__username',
        'farm_name',
        'farm_location'
    )

    ordering = ('id',)


@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'contact_name',
        'delivery_address'
    )

    search_fields = (
        'user__username',
        'contact_name'
    )

    ordering = ('id',)
    

    