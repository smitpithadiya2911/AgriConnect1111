import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agriconnect_project.settings')
django.setup()

from marketplace.models import Category, Crop, PriceTrend, Review, CartItem, OrderItem

print("Cleaning outdated marketplace records...")
# Delete items referencing Crop first to avoid foreign key issues
CartItem.objects.all().delete()
OrderItem.objects.all().delete()
Review.objects.all().delete()
PriceTrend.objects.all().delete()
Crop.objects.all().delete()
Category.objects.all().delete()

print("Marketplace database cleared successfully!")
