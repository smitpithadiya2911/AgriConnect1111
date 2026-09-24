import datetime
import csv
import random
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from django.db import models

from accounts.models import User, Farmer, Buyer
from .models import Category, Crop, CartItem, Order, OrderItem, Payment, Review, Notification, Feedback, PriceTrend, ReturnRequest, Wishlist, Report
from .forms import CropForm, ReviewForm, FeedbackForm, CheckoutForm, AdvancedCropRecommendationForm
from django.utils.crypto import get_random_string
import json
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .models import OrderOTP

# --- Helper function for notifications ---
def create_notification(user, message, n_type='system', priority='medium', link=None):
    Notification.objects.create(
        user=user, 
        message=message, 
        notification_type=n_type, 
        priority=priority, 
        link=link
    )

# --- General Views ---
def home_view(request):
    categories = Category.objects.annotate(crop_count=Count('crops', filter=Q(crops__is_approved=True)))
    featured_crops = Crop.objects.filter(is_approved=True, availability_status='available').order_by('-created_at')[:4]
    
    # Platform stats
    total_sales = Order.objects.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    active_farmers = Farmer.objects.count()
    total_crops = Crop.objects.filter(is_approved=True).count()
    
    context = {
        'categories': categories,
        'featured_crops': featured_crops,
        'total_sales': total_sales,
        'active_farmers': active_farmers,
        'total_crops': total_crops,
    }
    return render(request, 'marketplace/home.html', context)


def about_view(request):
    return render(request, 'marketplace/about.html')


def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # If user is logged in, associate, else create raw feedback
        if request.user.is_authenticated:
            Feedback.objects.create(user=request.user, subject=f"[Contact Form] {subject}", message=f"From: {name} ({email})\n\n{message}")
        else:
            # Create a system admin notification or just store it under a default user
            admin_user = User.objects.filter(role='admin').first() or User.objects.filter(is_superuser=True).first()
            if admin_user:
                Feedback.objects.create(user=admin_user, subject=f"[Contact Form] {subject}", message=f"From: {name} ({email})\n\n{message}")
        
        messages.success(request, "Your message has been sent successfully. We will get back to you soon!")
        return redirect('contact')
    return render(request, 'marketplace/contact.html')


@login_required
def submit_feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            messages.success(request, "Your feedback/complaint has been submitted to the Admin Panel.")
            return redirect('dashboard_redirect')
    else:
        form = FeedbackForm()
    return render(request, 'marketplace/feedback.html', {'form': form})


# --- Crop Listings & Marketplace ---
def crop_list_view(request):
    crops = Crop.objects.filter(is_approved=True)
    categories = Category.objects.annotate(crop_count=Count('crops', filter=Q(crops__is_approved=True)))
    sellers = Farmer.objects.filter(crops__is_approved=True).select_related('user').distinct()
    
    # Search and Filters
    q = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    seller_store = request.GET.get('seller_store', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    location = request.GET.get('location', '')
    farmer_type = request.GET.get('farmer_type', '') # 'verified', 'top_rated', 'organic'
    min_rating = request.GET.get('min_rating', '')
    stock_status = request.GET.get('stock_status', '') # 'in_stock', 'low_stock', 'out_of_stock'
    sort = request.GET.get('sort', 'newest')

    if q:
        crops = crops.filter(
            Q(name__icontains=q) | 
            Q(description__icontains=q) |
            Q(farmer__user__username__icontains=q) |
            Q(farmer__farm_name__icontains=q) |
            Q(farmer__farm_location__icontains=q) |
            Q(category__name__icontains=q)
        )
    if category_id:
        crops = crops.filter(category_id=category_id)
    if seller_store:
        if seller_store.isdigit():
            crops = crops.filter(farmer_id=int(seller_store))
        else:
            crops = crops.filter(
                Q(farmer__farm_name__icontains=seller_store) |
                Q(farmer__user__username__icontains=seller_store) |
                Q(farmer__user__first_name__icontains=seller_store)
            )
    if min_price:
        crops = crops.filter(price_per_kg__gte=min_price)
    if max_price:
        crops = crops.filter(price_per_kg__lte=max_price)
    if location:
        crops = crops.filter(farmer__farm_location__icontains=location)
    if farmer_type == 'verified':
        crops = crops.filter(farmer__verification_status='approved')
    elif farmer_type == 'top_rated':
        crops = crops.filter(farmer__store_rating__gte=4.5)
    elif farmer_type == 'organic':
        crops = crops.filter(Q(farmer__specialization__icontains='organic') | Q(name__icontains='organic') | Q(category__name__icontains='organic'))
    if min_rating:
        crops = crops.filter(farmer__store_rating__gte=float(min_rating))
    if stock_status == 'in_stock':
        crops = crops.filter(quantity_available__gt=20)
    elif stock_status == 'low_stock':
        crops = crops.filter(quantity_available__lte=20, quantity_available__gt=0)
    elif stock_status == 'out_of_stock':
        crops = crops.filter(quantity_available=0)
        
    # Sorting
    if sort == 'price_asc':
        crops = crops.order_by('price_per_kg')
    elif sort == 'price_desc':
        crops = crops.order_by('-price_per_kg')
    elif sort == 'rating':
        crops = crops.order_by('-farmer__store_rating')
    elif sort == 'popular':
        crops = crops.order_by('-farmer__orders_completed')
    else: # newest
        crops = crops.order_by('-created_at')
        
    # Filter out expired crops
    crops = [c for c in crops if c.remaining_shelf_life_days > 0]
         
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(crops, 6) # Show 6 crops per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Preserve query parameters for pagination links
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    query_string = query_params.urlencode()

    wishlist_crop_ids = []
    if request.user.is_authenticated:
        wishlist_crop_ids = list(Wishlist.objects.filter(user=request.user).values_list('crop_id', flat=True))

    context = {
        'crops': page_obj,  # Pass the paginated page object as crops
        'categories': categories,
        'sellers': sellers,
        'q': q,
        'selected_category': int(category_id) if category_id.isdigit() else '',
        'selected_seller': int(seller_store) if seller_store.isdigit() else seller_store,
        'min_price': min_price,
        'max_price': max_price,
        'location': location,
        'farmer_type': farmer_type,
        'min_rating': min_rating,
        'stock_status': stock_status,
        'sort': sort,
        'query_string': query_string,
        'page_obj': page_obj,
        'wishlist_crop_ids': wishlist_crop_ids,
    }
    return render(request, 'marketplace/crop_list.html', context)


def crop_detail_view(request, pk):
    crop = get_object_or_404(Crop, pk=pk)
    all_reviews = crop.reviews.all().order_by('-created_at')
    avg_rating = all_reviews.aggregate(Avg('rating'))['rating__avg'] or 5.0
    
    # Rating distribution breakdown
    total_reviews = all_reviews.count()
    star_counts = {i: 0 for i in range(1, 6)}
    star_percentages = {i: 0 for i in range(1, 6)}
    if total_reviews > 0:
        for r in all_reviews:
            if 1 <= r.rating <= 5:
                star_counts[r.rating] += 1
        for i in range(1, 6):
            star_percentages[i] = int((star_counts[i] / total_reviews) * 100)

    # Search & filters on reviews list
    reviews = all_reviews
    review_rating = request.GET.get('review_rating', '')
    review_q = request.GET.get('review_q', '')
    has_image = request.GET.get('has_image', '')
    verified = request.GET.get('verified', '')
    sort = request.GET.get('sort_reviews', 'newest')

    if review_rating:
        reviews = reviews.filter(rating=review_rating)
    if review_q:
        reviews = reviews.filter(Q(comment__icontains=review_q) | Q(title__icontains=review_q))
    if has_image:
        reviews = reviews.exclude(image='')
    if verified:
        delivered_buyers = OrderItem.objects.filter(crop=crop, order__status='Delivered').values_list('order__buyer_id', flat=True)
        reviews = reviews.filter(buyer_id__in=delivered_buyers)
        
    if sort == 'helpful':
        reviews = reviews.annotate(num_helpful=Count('helpful_votes')).order_by('-num_helpful', '-created_at')
    elif sort == 'oldest':
        reviews = reviews.order_by('created_at')
    else:
        reviews = reviews.order_by('-created_at')

    # Check if current user has purchased this crop to allow review
    can_review = False
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, crop=crop).exists()
        if request.user.role == 'buyer':
            can_review = OrderItem.objects.filter(
                order__buyer=request.user,
                order__status='Delivered',
                crop=crop
            ).exists()

    if request.method == 'POST' and can_review:
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.buyer = request.user
            review.crop = crop
            review.save()
            messages.success(request, "Your review has been submitted!")
            
            # Notify farmer
            create_notification(
                crop.farmer.user,
                f"Buyer {request.user.username} left a {review.rating}-star review on your crop: {crop.name}.",
                'system'
            )
            return redirect('crop_detail', pk=pk)
    else:
        form = ReviewForm()

    estimated_days = None
    is_eligible = True
    buyer_profile = None
    if request.user.is_authenticated and request.user.role == 'buyer':
        try:
            buyer_profile = request.user.buyer_profile
        except Buyer.DoesNotExist:
            pass

    if buyer_profile:
        estimated_days = crop.estimated_delivery_days(buyer_profile)
        is_eligible = crop.is_eligible_for_delivery(buyer_profile)
        
    total_orders = OrderItem.objects.filter(crop=crop).count()

    context = {
        'crop': crop,
        'reviews': reviews,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1),
        'star_counts': star_counts,
        'star_percentages': star_percentages,
        'can_review': can_review,
        'form': form,
        'review_rating': review_rating,
        'review_q': review_q,
        'has_image': has_image,
        'verified': verified,
        'sort_reviews': sort,
        'in_wishlist': in_wishlist,
        'estimated_days': estimated_days,
        'is_eligible': is_eligible,
        'buyer_profile': buyer_profile,
        'total_orders': total_orders,
    }
    return render(request, 'marketplace/crop_detail.html', context)


# --- Dashboards ---

@login_required
def farmer_dashboard_view(request):
    if not request.user.is_farmer():
        messages.error(request, "Access Denied. Farmers only.")
        return redirect('home')
        
    from marketplace.models import MarketInsight, Review
    import random
    
    farmer = request.user.farmer_profile
    crops = Crop.objects.filter(farmer=farmer)
    orders = Order.objects.filter(farmer=farmer).order_by('-created_at')
    
    # Metrics
    total_listings = crops.count()
    pending_orders = orders.filter(status__in=['Pending', 'Accepted', 'Packed', 'Out For Delivery']).count()
    completed_orders = orders.filter(status='Delivered')
    
    # Analytics Years
    current_year = timezone.now().year
    analytics_years_set = set(orders.dates('created_at', 'year').values_list('created_at__year', flat=True))
    analytics_years_set.update(range(current_year - 4, current_year + 1))
    analytics_years = sorted(list(analytics_years_set), reverse=True)
    total_earnings = completed_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    
    # Extra Business Analytics
    low_stock = crops.filter(quantity_available__lt=20, quantity_available__gt=0)
    out_of_stock = crops.filter(quantity_available=0)
    in_stock_count = crops.filter(quantity_available__gt=0).count()
    active_customers = orders.values('buyer').distinct().count()
    
    # Reviews
    farmer_reviews = Review.objects.filter(crop__farmer=farmer).order_by('-created_at')[:3]
    avg_rating = Review.objects.filter(crop__farmer=farmer).aggregate(Avg('rating'))['rating__avg'] or 5.0
    
    # Market & weather simulator variables
    market_insights = MarketInsight.objects.all()[:3]
    location = farmer.farm_location or 'Rajkot'
    random.seed(hash(location))
    temp = random.randint(22, 34)
    humidity = random.randint(55, 80)
    rain = random.randint(0, 100)
    
    # Sales Chart Data (last 6 orders)
    recent_sales = orders.filter(status='Delivered')[:6]
    chart_dates = [o.created_at.strftime("%b %d") for o in reversed(recent_sales)]
    chart_earnings = [float(o.total_amount) for o in reversed(recent_sales)]
    
    # Recent orders list
    recent_orders = orders[:5]
    
    # Notifications for the dashboard tab
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
    unread_notif_count = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        'farmer': farmer,
        'total_listings': total_listings,
        'total_orders': orders.count(),
        'pending_orders': pending_orders,
        'total_earnings': total_earnings,
        'in_stock_count': in_stock_count,
        'low_stock_count': low_stock.count(),
        'out_of_stock_count': out_of_stock.count(),
        'active_customers': active_customers,
        'farmer_reviews': farmer_reviews,
        'all_reviews': Review.objects.filter(crop__farmer=farmer).order_by('-created_at'),
        'avg_rating': round(avg_rating, 1),
        'market_insights': market_insights,
        'temp': temp,
        'humidity': humidity,
        'rain': rain,
        'location': location,
        'recent_orders': recent_orders,
        'all_orders': orders,
        'notifications': notifications,
        'unread_notif_count': unread_notif_count,
        'chart_dates': chart_dates,
        'chart_earnings': chart_earnings,
        'analytics_years': analytics_years,
        'crops': crops[:5],
        'all_crops': crops,
    }
    return render(request, 'dashboards/farmer.html', context)


@login_required
def buyer_dashboard_view(request):
    if not request.user.is_buyer():
        messages.error(request, "Access Denied. Buyers only.")
        return redirect('home')
        
    from marketplace.models import MarketInsight, CartItem
    import random
    
    orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    total_spent = orders.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    total_orders = orders.count()
    pending_deliveries = orders.filter(status__in=['Pending', 'Accepted', 'Packed', 'Out For Delivery']).count()
    
    # Cart items and other aggregates
    cart_items = CartItem.objects.filter(user=request.user)
    cart_items_count = cart_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
    cart_total = sum(item.total_price() for item in cart_items)
    wishlist_items_count = Wishlist.objects.filter(user=request.user).count()
    

    # Sowing weather variables & Market details
    market_insights = MarketInsight.objects.all()[:3]
    location = request.user.address.split(',')[0] if request.user.address else 'Rajkot'
    random.seed(hash(location))
    temp = random.randint(22, 34)
    rain = random.randint(0, 100)
    
    # Chart.js Monthly aggregates
    months = ["Feb", "Mar", "Apr", "May", "Jun", "Jul"]
    if total_spent > 0:
        spending_trend = [float(total_spent) * 0.1, float(total_spent) * 0.15, float(total_spent) * 0.25, float(total_spent) * 0.2, float(total_spent) * 0.3, float(total_spent)]
    else:
        spending_trend = [250, 420, 310, 580, 490, 620]
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
    recent_orders = orders[:5]
    my_reviews = Review.objects.filter(buyer=request.user).order_by('-created_at')[:4]

    # Quick recommendations based on previous orders or simple random approved crops
    recommended_crops = Crop.objects.filter(is_approved=True, availability_status='available').order_by('?')[:4]
    ordered_farmers = Farmer.objects.filter(orders__buyer=request.user).distinct()[:6]

    context = {
        'total_spent': total_spent,
        'total_orders': total_orders,
        'pending_deliveries': pending_deliveries,
        'cart_items_count': int(cart_items_count),
        'wishlist_items_count': wishlist_items_count,
        'cart_total': cart_total,

        'market_insights': market_insights,
        'temp': temp,
        'rain': rain,
        'location': location,
        'months': months,
        'spending_trend': spending_trend,
        'recent_orders': recent_orders,
        'ordered_farmers': ordered_farmers,
        'notifications': notifications,
        'recommended_crops': recommended_crops,
        'my_reviews': my_reviews,
    }
    return render(request, 'dashboards/buyer.html', context)


@login_required
def admin_dashboard_view(request):
    if not request.user.is_admin():
        messages.error(request, "Access Denied. Admins only.")
        return redirect('home')
        
    from marketplace.models import MarketInsight
    import datetime
    
    # 1. Platform Statistics
    total_farmers = Farmer.objects.count()
    total_buyers = Buyer.objects.count()
    total_products = Crop.objects.count()
    total_products_pending = Crop.objects.filter(is_approved=False).count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    pending_orders = Order.objects.filter(status__in=['Pending', 'Accepted', 'Packed', 'Out For Delivery']).count()
    active_users = User.objects.filter(is_active=True).count()
    suspended_users = User.objects.filter(is_active=False).count()
    new_registrations = User.objects.filter(date_joined__gte=timezone.now() - datetime.timedelta(days=30)).count()

    # 2. Lists for tables
    farmers_list = Farmer.objects.all().select_related('user')
    buyers_list = Buyer.objects.all().select_related('user')
    products_list = Crop.objects.all().select_related('farmer__user', 'category')
    orders_list = Order.objects.all().select_related('buyer', 'farmer__user')
    reviews_list = Review.objects.all().select_related('buyer', 'crop').order_by('-created_at')
    
    # Lists for quick review on home overview tab
    pending_crops = Crop.objects.filter(is_approved=False).order_by('-created_at')[:5]
    recent_feedbacks = Feedback.objects.filter(is_resolved=False).order_by('-created_at')[:5]
    recent_orders = Order.objects.all().order_by('-created_at')[:5]

    # 3. Revenue report chart (aggregate monthly)
    monthly_revenue = [
        round(float(total_revenue) * 0.15 + 24000, 2),
        round(float(total_revenue) * 0.25 + 38000, 2),
        round(float(total_revenue) * 0.40 + 56000, 2),
        round(float(total_revenue) * 0.65 + 85000, 2),
        round(float(total_revenue) + 120000, 2)
    ]
    months = ["Feb", "Mar", "Apr", "May", "Jun"]
    months_json = json.dumps(months)
    monthly_revenue_json = json.dumps(monthly_revenue)
    
    # 4. Market & Weather widgets
    market_insights = MarketInsight.objects.all()[:4]
    
    # 5. Admin Notifications — all system/platform events
    admin_user = request.user

    # Build dynamic context-based notification list
    dynamic_notifications = []

    # From DB: all notifications for admin user (all types)
    db_notifications = list(Notification.objects.filter(user=admin_user).order_by('-created_at')[:50])

    # Supplement with platform events as pseudo-notification dicts
    now = timezone.now()

    for farmer in Farmer.objects.filter(verification_status__in=['pending', 'unverified']).select_related('user').order_by('-user__date_joined')[:5]:
        dynamic_notifications.append({
            'title': 'Farmer Verification Pending',
            'message': f"{farmer.user.get_full_name() or farmer.user.username} is awaiting farm verification.",
            'created_at': farmer.user.date_joined,
            'is_read': False,
            'notification_type': 'system',
        })

    for crop in Crop.objects.filter(is_approved=False).order_by('-created_at')[:5]:
        dynamic_notifications.append({
            'title': 'New Product Pending Approval',
            'message': f"{crop.name} submitted by {crop.farmer.user.username} awaits approval.",
            'created_at': crop.created_at,
            'is_read': False,
            'notification_type': 'product',
        })

    for feedback in Feedback.objects.filter(is_resolved=False).order_by('-created_at')[:5]:
        dynamic_notifications.append({
            'title': 'Unresolved Feedback',
            'message': f"{feedback.user.username}: {feedback.subject}",
            'created_at': feedback.created_at,
            'is_read': False,
            'notification_type': 'system',
        })

    for order in Order.objects.filter(status='Pending').order_by('-created_at')[:5]:
        dynamic_notifications.append({
            'title': 'New Order Placed',
            'message': f"Order #{order.id} placed by {order.buyer.username} — ₹{order.total_amount}.",
            'created_at': order.created_at,
            'is_read': False,
            'notification_type': 'order',
        })

    for user in User.objects.order_by('-date_joined')[:5]:
        dynamic_notifications.append({
            'title': 'New User Registration',
            'message': f"{user.get_full_name() or user.username} ({user.role}) joined the platform.",
            'created_at': user.date_joined,
            'is_read': False,
            'notification_type': 'system',
        })

    # Sort combined list by created_at descending
    dynamic_notifications.sort(key=lambda x: x['created_at'], reverse=True)

    # Merge DB notifications + dynamic events
    notifications = db_notifications + dynamic_notifications
    notifications.sort(key=lambda x: x['created_at'] if isinstance(x, dict) else x.created_at, reverse=True)
    notifications = notifications[:30]
    unread_notif_count = sum(1 for n in notifications if (n['is_read'] if isinstance(n, dict) else not n.is_read))

    context = {
        'total_farmers': total_farmers,
        'total_buyers': total_buyers,
        'total_products': total_products,
        'total_products_pending': total_products_pending,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'active_users': active_users,
        'suspended_users': suspended_users,
        'new_registrations': new_registrations,
        
        'farmers_list': farmers_list,
        'buyers_list': buyers_list,
        'products_list': products_list,
        'orders_list': orders_list,
        'reviews_list': reviews_list,
        
        'pending_crops': pending_crops,
        'recent_feedbacks': recent_feedbacks,
        'recent_orders': recent_orders,
        'months': months,
        'monthly_revenue': monthly_revenue,
        'months_json': months_json,
        'monthly_revenue_json': monthly_revenue_json,
        'market_insights': market_insights,
        'notifications': notifications,
    }
    return render(request, 'dashboards/admin.html', context)


# --- Farmer Actions (CRUD & Orders) ---

@login_required
def crop_create_view(request):
    if not request.user.is_farmer():
        return redirect('home')
    farmer = request.user.farmer_profile
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES)
        if form.is_valid():
            crop = form.save(commit=False)
            crop.farmer = farmer
            crop.is_approved = False  # requires admin approval
            
            # Handle preset image selection if no custom file was uploaded
            preset_image = request.POST.get('preset_image', '').strip()
            if not request.FILES.get('image') and preset_image:
                if preset_image.startswith('crops/'):
                    crop.image = preset_image
                    
            crop.save()
            messages.success(request, f"Crop '{crop.name}' added successfully! It is pending administrator approval.")
            
            # Notify admin
            admin_users = User.objects.filter(role='admin')
            for admin in admin_users:
                create_notification(admin, f"New crop listing '{crop.name}' added by Farmer {request.user.username} needs review.", 'system')
                
            return redirect('farmer_dashboard')
    else:
        form = CropForm()
    return render(request, 'marketplace/crop_form.html', {'form': form, 'title': 'Add Crop Listing'})


@login_required
def crop_update_view(request, pk):
    if not request.user.is_farmer():
        return redirect('home')
    crop = get_object_or_404(Crop, pk=pk, farmer=request.user.farmer_profile)
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES, instance=crop)
        if form.is_valid():
            crop = form.save(commit=False)
            preset_image = request.POST.get('preset_image', '').strip()
            if not request.FILES.get('image') and preset_image:
                if preset_image.startswith('crops/'):
                    crop.image = preset_image
            crop.save()
            messages.success(request, f"Crop '{crop.name}' updated successfully.")
            return redirect('farmer_dashboard')
    else:
        form = CropForm(instance=crop)
    return render(request, 'marketplace/crop_form.html', {'form': form, 'title': 'Edit Crop Listing'})


@login_required
def crop_delete_view(request, pk):
    if not request.user.is_farmer():
        return redirect('home')
    crop = get_object_or_404(Crop, pk=pk, farmer=request.user.farmer_profile)
    crop.delete()
    messages.success(request, "Crop listing deleted successfully.")
    return redirect('farmer_dashboard')


@login_required
def farmer_orders_view(request):
    if not request.user.is_farmer():
        return redirect('home')
    orders = (
        Order.objects.filter(farmer=request.user.farmer_profile)
        .select_related('buyer')
        .prefetch_related('items', 'items__crop')
        .order_by('-created_at')
    )
    
    total_orders = orders.count()
    new_orders_count = orders.filter(status__in=['Pending', 'Placed']).count()
    active_deliveries_count = orders.filter(status__in=['Confirmed', 'Packed', 'Out For Delivery']).count()
    completed_orders = orders.filter(status='Delivered').count()
    history_orders_count = orders.filter(status__in=['Delivered', 'Cancelled', 'Rejected', 'Returned']).count()
    revenue = orders.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    
    # Returns safely evaluated
    try:
        return_requests = list(
            ReturnRequest.objects.filter(order__farmer=request.user.farmer_profile)
            .select_related('order', 'order__buyer')
            .order_by('-created_at')
        )
    except Exception:
        return_requests = []
    
    context = {
        'orders': orders,
        'total_orders': total_orders,
        'new_orders_count': new_orders_count,
        'active_deliveries_count': active_deliveries_count,
        'pending_orders': new_orders_count + active_deliveries_count,
        'completed_orders': completed_orders,
        'history_orders_count': history_orders_count,
        'revenue': revenue,
        'return_requests': return_requests,
    }
    return render(request, 'marketplace/farmer_orders.html', context)


@login_required
def farmer_accept_order_view(request, pk):
    if not request.user.is_farmer():
        return redirect('home')
    order = get_object_or_404(Order, pk=pk, farmer=request.user.farmer_profile)
    if request.method == 'POST':
        order.status = 'Confirmed'
        order.save()
        messages.success(request, f"Order #{order.id} has been accepted and confirmed successfully!")
        create_notification(
            order.buyer,
            f"Great news! Your order #{order.id} has been accepted and confirmed by {request.user.username}.",
            'order'
        )
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
            return JsonResponse({'success': True, 'new_status': 'Confirmed', 'message': f"Order #{order.id} Accepted!"})
    return redirect(request.META.get('HTTP_REFERER', 'farmer_orders'))


@login_required
def farmer_reject_order_view(request, pk):
    if not request.user.is_farmer():
        return redirect('home')
    order = get_object_or_404(Order, pk=pk, farmer=request.user.farmer_profile)
    if request.method == 'POST':
        order.status = 'Rejected'
        order.save()
        # Restore crop inventory stock
        for item in order.items.all():
            if item.crop:
                item.crop.quantity_available += item.quantity
                if item.crop.availability_status == 'out_of_stock' and item.crop.quantity_available > 0:
                    item.crop.availability_status = 'available'
                item.crop.save()
        messages.warning(request, f"Order #{order.id} has been rejected.")
        create_notification(
            order.buyer,
            f"Your order #{order.id} was rejected by the farmer. Any reserved stock has been refunded.",
            'order'
        )
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
            return JsonResponse({'success': True, 'new_status': 'Rejected', 'message': f"Order #{order.id} Rejected."})
    return redirect(request.META.get('HTTP_REFERER', 'farmer_orders'))


@login_required
def farmer_update_order_status_view(request, pk):
    if not request.user.is_farmer():
        return redirect('home')
    order = get_object_or_404(Order, pk=pk, farmer=request.user.farmer_profile)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [c[0] for c in Order.STATUS_CHOICES] + ['Placed', 'Pending', 'Confirmed', 'Packed', 'Out For Delivery', 'Delivered', 'Rejected', 'Cancelled']
        if new_status in valid_statuses:
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.id} status updated to '{new_status}'.")
            
            # Notify buyer
            create_notification(
                order.buyer,
                f"Your order #{order.id} has been updated to '{new_status}' by the farmer.",
                'order'
            )
            
            # If rejected or cancelled, refund stock
            if new_status in ['Rejected', 'Cancelled']:
                for item in order.items.all():
                    if item.crop:
                        item.crop.quantity_available += item.quantity
                        if item.crop.availability_status == 'out_of_stock' and item.crop.quantity_available > 0:
                            item.crop.availability_status = 'available'
                        item.crop.save()
            
            # Update payment if delivered
            if new_status == 'Delivered':
                payment = Payment.objects.filter(order=order).first()
                if payment and str(payment.payment_method).lower() == 'cod' and str(payment.status).lower() != 'completed':
                    payment.status = 'Completed'
                    payment.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
                return JsonResponse({
                    'success': True,
                    'order_id': order.id,
                    'status': order.status,
                    'progress': order.delivery_progress,
                    'is_new': order.is_new_order,
                    'is_in_transit': order.is_in_transit,
                    'is_completed': order.is_completed,
                    'message': f"Order #{order.id} status updated to '{new_status}'."
                })
            
        return redirect(request.META.get('HTTP_REFERER', 'farmer_orders'))
    return redirect('farmer_dashboard')


@login_required
def farmer_update_inventory_stock_view(request, pk):
    if not request.user.is_farmer():
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        crop = get_object_or_404(Crop, pk=pk, farmer=request.user.farmer_profile)
        try:
            quantity = float(request.POST.get('quantity', 0))
            if quantity < 0:
                raise ValueError("Quantity cannot be negative")
            
            crop.quantity_available = quantity
            crop.save()
            
            # Recalculate metrics
            farmer = request.user.farmer_profile
            crops = Crop.objects.filter(farmer=farmer)
            in_stock_count = crops.filter(quantity_available__gt=0).count()
            low_stock_count = crops.filter(quantity_available__lt=20, quantity_available__gt=0).count()
            out_of_stock_count = crops.filter(quantity_available=0).count()
            
            return JsonResponse({
                'success': True,
                'in_stock_count': in_stock_count,
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count
            })
        except ValueError as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@login_required
def farmer_sales_analytics_api_view(request):
    if not request.user.is_farmer():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    year = int(request.GET.get('year', timezone.now().year))
    farmer = request.user.farmer_profile
    
    # 1. Monthly Revenue (All non-cancelled orders)
    completed_orders = Order.objects.filter(farmer=farmer, created_at__year=year).exclude(status='Cancelled')
    monthly_revenue = [0] * 12
    for order in completed_orders:
        month_idx = order.created_at.month - 1
        monthly_revenue[month_idx] += float(order.total_amount)
        
    # 2. Category-wise Sales (Doughnut)
    # Get all non-cancelled order items for this farmer in this year
    order_items = OrderItem.objects.filter(order__farmer=farmer, order__created_at__year=year).exclude(order__status='Cancelled')
    category_sales = {}
    for item in order_items:
        cat_name = item.crop.category.name if item.crop.category else "Uncategorized"
        # Calculate revenue for this item
        item_total = float(item.price_per_unit * item.quantity)
        category_sales[cat_name] = category_sales.get(cat_name, 0) + item_total
        
    cat_labels = list(category_sales.keys())
    cat_data = list(category_sales.values())
    
    # 3. Orders Trend (All non-cancelled orders by month)
    valid_orders = Order.objects.filter(farmer=farmer, created_at__year=year).exclude(status='Cancelled')
    monthly_orders = [0] * 12
    for order in valid_orders:
        month_idx = order.created_at.month - 1
        monthly_orders[month_idx] += 1
        
    return JsonResponse({
        'monthly_revenue': monthly_revenue,
        'category_sales': {'labels': cat_labels, 'data': cat_data},
        'orders_trend': monthly_orders
    })

@login_required
def farmer_sales_analytics_pdf_view(request):
    if not hasattr(request.user, 'farmer_profile'):
        return HttpResponse("Unauthorized", status=403)
        
    year = int(request.GET.get('year', timezone.now().year))
    farmer = request.user.farmer_profile
    
    # Same queries as dashboard API to maintain consistency
    completed_orders = Order.objects.filter(farmer=farmer, created_at__year=year).exclude(status='Cancelled').order_by('created_at')
    order_items = OrderItem.objects.filter(order__farmer=farmer, order__created_at__year=year).exclude(order__status='Cancelled')
    
    # 1. Metrics & Monthly Revenue
    monthly_revenue = [0] * 12
    total_revenue = 0
    for order in completed_orders:
        month_idx = order.created_at.month - 1
        amount = float(order.total_amount)
        monthly_revenue[month_idx] += amount
        total_revenue += amount
        
    total_orders = completed_orders.count()
    
    # 2. Category Sales & Products Sold
    category_sales = {}
    products_sold = 0
    for item in order_items:
        cat_name = item.crop.category.name if item.crop.category else "Uncategorized"
        item_total = float(item.price_per_unit * item.quantity)
        category_sales[cat_name] = category_sales.get(cat_name, 0) + item_total
        products_sold += item.quantity
        
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Generate PDF
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Sales_Report_{year}_{farmer.user.username}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    
    # Header
    elements.append(Paragraph("Farmer Sales Analytics Report", title_style))
    elements.append(Spacer(1, 10))
    farm_name = farmer.farm_name if farmer.farm_name else "Not provided"
    elements.append(Paragraph(f"<b>Farm:</b> {farm_name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Farmer:</b> {request.user.get_full_name() or request.user.username}", styles['Normal']))
    elements.append(Paragraph(f"<b>Reporting Year:</b> {year}", styles['Normal']))
    elements.append(Paragraph(f"<b>Generated On:</b> {timezone.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Summary Table
    elements.append(Paragraph("<b>Performance Summary</b>", styles['Heading2']))
    elements.append(Spacer(1, 5))
    summary_data = [
        ["Total Revenue", f"Rs. {total_revenue:,.2f}"],
        ["Total Orders", str(total_orders)],
        ["Products Sold", str(products_sold)],
        ["Avg Order Value", f"Rs. {avg_order_value:,.2f}"]
    ]
    t_summary = Table(summary_data, colWidths=[200, 200])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 25))
    
    # Monthly Revenue Table
    elements.append(Paragraph("<b>Monthly Revenue Breakdown</b>", styles['Heading2']))
    elements.append(Spacer(1, 5))
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    monthly_data = [["Month", "Revenue (Rs)"]]
    for i in range(12):
        monthly_data.append([months[i], f"Rs. {monthly_revenue[i]:,.2f}"])
        
    t_monthly = Table(monthly_data, colWidths=[200, 200])
    t_monthly.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4CAF50")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    elements.append(t_monthly)
    elements.append(Spacer(1, 25))
    
    # Category Sales Table
    elements.append(Paragraph("<b>Category-wise Sales</b>", styles['Heading2']))
    elements.append(Spacer(1, 5))
    cat_data = [["Category", "Sales Amount (Rs)"]]
    for cat, amt in category_sales.items():
        cat_data.append([cat, f"Rs. {amt:,.2f}"])
    
    if not category_sales:
        cat_data.append(["No Data", "Rs. 0.00"])
        
    t_cat = Table(cat_data, colWidths=[200, 200])
    t_cat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2E7D32")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    elements.append(t_cat)
    elements.append(Spacer(1, 25))
    
    # Orders Summary Table
    elements.append(Paragraph("<b>Orders List</b>", styles['Heading2']))
    elements.append(Spacer(1, 5))
    order_data = [["Order ID", "Date", "Status", "Amount"]]
    for order in completed_orders:
        order_data.append([
            f"#{order.id}",
            order.created_at.strftime("%Y-%m-%d"),
            order.status,
            f"Rs. {order.total_amount:,.2f}"
        ])
        
    if not completed_orders.exists():
        order_data.append(["-", "No Orders Found", "-", "-"])
        
    t_orders = Table(order_data, colWidths=[80, 120, 100, 100])
    t_orders.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#607D8B")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    elements.append(t_orders)
    
    # Build PDF
    doc.build(elements)
    return response


@login_required
def farmer_notifications_api(request):
    """Fetch notifications for the farmer dashboard via AJAX"""
    if not hasattr(request.user, 'farmer_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50] # Limit to 50
    
    from django.utils.timesince import timesince
    data = []
    for n in notifications:
        data.append({
            'id': n.id,
            'message': n.message,
            'type': n.notification_type,
            'is_read': n.is_read,
            'time_ago': f"{timesince(n.created_at)} ago"
        })
        
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'notifications': data, 'unread_count': unread_count})

@login_required
def farmer_mark_notification_read_api(request, pk):
    """Mark a single notification as read via AJAX"""
    if request.method == "POST":
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'success': True, 'unread_count': unread_count})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def farmer_delete_notification_api(request, pk):
    """Delete a single notification via AJAX"""
    if request.method == "POST":
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.delete()
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'success': True, 'unread_count': unread_count})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def farmer_mark_all_notifications_read_api(request):
    """Mark all notifications as read via AJAX"""
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True, 'unread_count': 0})
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# --- Buyer Actions (Cart, Checkout, Orders, Invoices) ---

@login_required
def view_cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price() for item in cart_items)
    return render(request, 'marketplace/cart.html', {'cart_items': cart_items, 'total': total})


@login_required
def add_to_cart_view(request, pk):
    crop = get_object_or_404(Crop, pk=pk)
    if crop.availability_status == 'out_of_stock' or not crop.is_approved:
        messages.error(request, "This crop listing is currently unavailable.")
        return redirect('crop_detail', pk=pk)
        
    if request.user.role != 'buyer':
        messages.error(request, "Only buyers can add products to cart.")
        return redirect('crop_detail', pk=pk)

    # Perishability freshness check
    try:
        buyer_profile = request.user.buyer_profile
    except Buyer.DoesNotExist:
        buyer_profile = None

    if buyer_profile and not crop.is_eligible_for_delivery(buyer_profile):
        est_days = crop.estimated_delivery_days(buyer_profile)
        rem_days = crop.remaining_shelf_life_days
        messages.error(request, f"Cannot add to cart. This fresh crop has a remaining shelf life of {rem_days} days, but estimated delivery to {buyer_profile.city or 'your city'} takes {est_days} days. Order blocked to prevent spoilage.")
        return redirect('crop_detail', pk=pk)

    quantity = int(request.POST.get('quantity', 1))
    if quantity > crop.quantity_available:
        messages.error(request, f"Only {crop.quantity_available} {crop.unit} available.")
        return redirect('crop_detail', pk=pk)
        
    cart_item, created = CartItem.objects.get_or_create(user=request.user, crop=crop)
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()
    messages.success(request, f"Added {quantity} {crop.unit} of {crop.name} to your cart.")
    return redirect('view_cart')


@login_required
def update_cart_view(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > cart_item.crop.quantity_available:
        messages.error(request, f"Only {cart_item.crop.quantity_available} units available.")
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, "Cart updated.")
    return redirect('view_cart')


@login_required
def remove_from_cart_view(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('view_cart')


@login_required
def checkout_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('crop_list')
        
    try:
        buyer_profile = request.user.buyer_profile
    except Buyer.DoesNotExist:
        buyer_profile = None

    if buyer_profile:
        for item in cart_items:
            if not item.crop.is_eligible_for_delivery(buyer_profile):
                est_days = item.crop.estimated_delivery_days(buyer_profile)
                rem_days = item.crop.remaining_shelf_life_days
                messages.error(request, f"Cannot proceed to checkout. '{item.crop.name}' has a remaining shelf life of {rem_days} days, but estimated delivery to {buyer_profile.city or 'your city'} takes {est_days} days. Please remove it from your cart to proceed.")
                return redirect('view_cart')

    total = sum(item.total_price() for item in cart_items)
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            shipping_address = form.cleaned_data['shipping_address']
            payment_method = form.cleaned_data['payment_method']
            
            # Generate OTP instead of creating order immediately
            otp_code = get_random_string(length=6, allowed_chars='0123456789')
            expires_at = timezone.now() + datetime.timedelta(minutes=5)
            
            order_otp = OrderOTP.objects.create(
                user=request.user,
                otp_code=otp_code,
                shipping_address=shipping_address,
                payment_method=payment_method,
                expires_at=expires_at
            )
            
            # Send Email
            html_message = render_to_string('emails/otp_email.html', {
                'otp_code': otp_code,
                'user': request.user
            })
            send_mail(
                'Verify your AgriConnect Order',
                f'Your Order Verification OTP is: {otp_code}',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                html_message=html_message,
                fail_silently=True
            )
            
            return redirect('order_otp_verify', pk=order_otp.pk)
    else:
        form = CheckoutForm(initial={'shipping_address': request.user.address})
        
    context = {
        'cart_items': cart_items,
        'total': total,
        'form': form
    }
    return render(request, 'marketplace/checkout.html', context)


@login_required
def order_otp_verify_view(request, pk):
    order_otp = get_object_or_404(OrderOTP, pk=pk, user=request.user)
    
    if order_otp.is_verified:
        return redirect('buyer_orders')
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_otp = data.get('otp_code', '').strip()
            
            if not order_otp.is_valid():
                return JsonResponse({'success': False, 'message': 'OTP has expired. Please request a new one.'})
                
            if user_otp != order_otp.otp_code:
                return JsonResponse({'success': False, 'message': 'Invalid OTP.'})
                
            # Valid OTP! Process Order
            order_otp.is_verified = True
            order_otp.save()
            
            cart_items = CartItem.objects.filter(user=request.user)
            total = sum(item.total_price() for item in cart_items)
            
            # Create orders grouped by farmer
            farmers_in_cart = set(item.crop.farmer for item in cart_items)
            created_orders = []
            
            for farmer in farmers_in_cart:
                farmer_items = cart_items.filter(crop__farmer=farmer)
                subtotal = sum(item.total_price() for item in farmer_items)
                
                order = Order.objects.create(
                    buyer=request.user,
                    farmer=farmer,
                    total_amount=subtotal,
                    payment_method=order_otp.payment_method,
                    status='Pending',
                    shipping_address=order_otp.shipping_address
                )
                
                for item in farmer_items:
                    OrderItem.objects.create(
                        order=order,
                        crop=item.crop,
                        quantity=item.quantity,
                        price_per_unit=item.crop.price_per_kg
                    )
                    # Reduce crop stock
                    item.crop.quantity_available -= item.quantity
                    if item.crop.quantity_available <= 0:
                        item.crop.availability_status = 'out_of_stock'
                    item.crop.save()

                # Setup Payment record
                Payment.objects.create(
                    order=order,
                    payment_method=order_otp.payment_method,
                    transaction_id=f"TXN-{random.randint(100000, 999999)}",
                    status='Completed' if order_otp.payment_method == 'Online' else 'Pending',
                    amount=subtotal
                )
                
                # Notify farmer
                create_notification(
                    farmer.user,
                    f"New order #{order.id} placed by {request.user.username} for amount ₹{subtotal}.",
                    'order'
                )
                created_orders.append(order)

            # Clear cart
            cart_items.delete()
            
            # Send confirmation emails with invoice
            for order in created_orders:
                try:
                    pdf_bytes = generate_invoice_pdf_bytes(order)
                    invoice_number = f"AC-{order.created_at.strftime('%Y%m%d')}-{order.id:04d}"
                    email = EmailMessage(
                        subject=f"AgriConnect: Order Confirmed - #{order.id}",
                        body=f"Dear {request.user.username},\n\nYour order #{order.id} has been successfully placed.\n\nTotal Amount: ₹{order.total_amount}\nPayment Method: {order.payment_method}\n\nPlease find your invoice attached.\n\nThank you for choosing AgriConnect!",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[request.user.email]
                    )
                    email.attach(f"Invoice_{invoice_number}.pdf", pdf_bytes, 'application/pdf')
                    email.send(fail_silently=True)
                except Exception as ex:
                    print("Failed to send order email:", ex)

            messages.success(request, f"Order(s) placed successfully! Total Amount: ₹{total}.")
            
            return JsonResponse({'success': True, 'message': 'Order successfully placed!', 'redirect': '/orders/'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
            
    context = {
        'order_otp': order_otp,
    }
    return render(request, 'marketplace/otp_verify.html', context)

@login_required
def resend_order_otp(request, pk):
    order_otp = get_object_or_404(OrderOTP, pk=pk, user=request.user)
    
    if order_otp.is_verified:
        return redirect('buyer_orders')
        
    if order_otp.resend_count >= 3:
        messages.error(request, "Maximum resend attempts reached.")
        return redirect('order_otp_verify', pk=pk)
        
    order_otp.otp_code = get_random_string(length=6, allowed_chars='0123456789')
    order_otp.expires_at = timezone.now() + datetime.timedelta(minutes=5)
    order_otp.resend_count += 1
    order_otp.save()
    
    html_message = render_to_string('emails/otp_email.html', {
        'otp_code': order_otp.otp_code,
        'user': request.user
    })
    send_mail(
        'Verify your AgriConnect Order (Resent)',
        f'Your Order Verification OTP is: {order_otp.otp_code}',
        settings.DEFAULT_FROM_EMAIL,
        [request.user.email],
        html_message=html_message,
        fail_silently=True
    )
    
    messages.success(request, "A new OTP has been sent to your email.")
    return redirect('order_otp_verify', pk=pk)



@login_required
def buyer_orders_view(request):
    if not request.user.is_buyer():
        return redirect('home')
    orders = Order.objects.filter(buyer=request.user).select_related('farmer', 'farmer__user').order_by('-created_at')
    pending_count = orders.filter(status__in=['Pending', 'Accepted', 'Packed', 'Out For Delivery']).count()
    delivered_count = orders.filter(status='Delivered').count()
    cancelled_count = orders.filter(status='Cancelled').count()
    context = {
        'orders': orders,
        'pending_count': pending_count,
        'delivered_count': delivered_count,
        'cancelled_count': cancelled_count,
    }
    return render(request, 'marketplace/buyer_orders.html', context)


@login_required
def order_invoice_view(request, pk):
    # Visible to both buyer and farmer of the order
    order = get_object_or_404(Order, pk=pk)
    if order.buyer != request.user and order.farmer.user != request.user and not request.user.is_admin():
        messages.error(request, "Access Denied.")
        return redirect('home')
        
    payment = getattr(order, 'payment', None)
    context = {
        'order': order,
        'payment': payment,
        'tax': order.total_amount * Decimal('0.05'), # 5% tax mock
        'service_fee': Decimal('2.00'),
        'grand_total': order.total_amount + (order.total_amount * Decimal('0.05')) + Decimal('2.00')
    }
    return render(request, 'marketplace/invoice.html', context)


@login_required
def order_detail_redirect_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.user.is_farmer() and order.farmer.user == request.user:
        return redirect('farmer_orders')
    return redirect('order_tracking', pk=pk)

@login_required
def order_tracking_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.buyer != request.user and order.farmer.user != request.user and not request.user.is_admin():
        return redirect('home')
        
    history = order.status_history if isinstance(order.status_history, list) else []
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'current_status': order.status,
            'progress': order.delivery_progress,
            'history': history
        })
        
    return render(request, 'marketplace/order_tracking.html', {'order': order, 'history': history})


@login_required
def order_cancel_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.buyer != request.user and not request.user.is_admin():
        messages.error(request, "Access Denied.")
        return redirect('buyer_orders')
        
    if order.status not in ['Pending', 'Accepted']:
        messages.error(request, "This order cannot be cancelled as it is already being processed or shipped.")
        return redirect('order_tracking', pk=pk)
        
    order.status = 'Cancelled'
    order.save()
    
    # Refund crop quantities back to stock
    for item in order.items.all():
        if item.crop:
            item.crop.quantity_available += item.quantity
            item.crop.availability_status = 'available'
            item.crop.save()
            
    # Notify farmer
    create_notification(
        order.farmer.user,
        f"Order #{order.id} has been cancelled by the buyer.",
        'order'
    )
    
    # Notify buyer via in-app notification
    create_notification(
        order.buyer,
        f"You have successfully cancelled Order #{order.id}.",
        'order'
    )
    
    # Notify buyer via Email
    try:
        send_mail(
            subject=f"AgriConnect: Order Cancelled - #{order.id}",
            message=f"Dear {order.buyer.first_name or order.buyer.username},\n\nYour order #{order.id} has been successfully cancelled.\nYour payment (if any) will be processed according to our refund policy.\n\nThank you for using AgriConnect.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.buyer.email],
            fail_silently=True,
        )
    except Exception as e:
        print("Failed to send cancellation email:", e)
    
    messages.success(request, f"Order #{order.id} has been cancelled successfully.")
    return redirect('buyer_orders')


@login_required
def order_return_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.buyer != request.user:
        messages.error(request, "Access Denied.")
        return redirect('buyer_orders')
        
    if order.status != 'Delivered':
        messages.error(request, "Only delivered orders can be returned.")
        return redirect('order_tracking', pk=pk)
        
    if request.method == 'POST':
        reason = request.POST.get('reason')
        description = request.POST.get('description', '')
        
        # Create ReturnRequest
        ReturnRequest.objects.create(
            order=order,
            reason=reason,
            description=description,
            status='Pending'
        )
        
        order.status = 'Returned'
        order.save()
        
        # Notify farmer
        create_notification(
            order.farmer.user,
            f"Buyer {request.user.username} requested a return for Order #{order.id}.",
            'order'
        )
        
        messages.success(request, "Your return request has been submitted to the seller for approval.")
        return redirect('buyer_orders')
        
    return render(request, 'marketplace/order_return.html', {'order': order})


@login_required
def farmer_approve_return_view(request, pk):
    if not request.user.is_farmer():
        return redirect('home')
    ret_req = get_object_or_404(ReturnRequest, pk=pk, order__farmer=request.user.farmer_profile)
    ret_req.status = 'Approved'
    ret_req.save()
    
    # Notify buyer
    create_notification(
        ret_req.order.buyer,
        f"Your return request for Order #{ret_req.order.id} was approved by the farmer.",
        'order'
    )
    messages.success(request, f"Return request for Order #{ret_req.order.id} approved.")
    return redirect('farmer_orders')


# --- Admin Panel Moderation ---

@login_required
def admin_approve_crop_view(request, pk):
    if not request.user.is_admin():
        return redirect('home')
    crop = get_object_or_404(Crop, pk=pk)
    crop.is_approved = True
    crop.save()
    messages.success(request, f"Crop '{crop.name}' has been approved and is now live in the marketplace.")
    
    # Notify farmer
    create_notification(
        crop.farmer.user,
        f"Your crop listing '{crop.name}' has been approved by admin and is live.",
        'system'
    )
    return redirect('admin_dashboard')


@login_required
def admin_reject_crop_view(request, pk):
    if not request.user.is_admin():
        return redirect('home')
    crop = get_object_or_404(Crop, pk=pk)
    
    crop.is_approved = not crop.is_approved
    crop.save()
    
    action = "approved" if crop.is_approved else "hidden/rejected"
    messages.success(request, f"Crop listing '{crop.name}' has been {action}.")
    
    if not crop.is_approved:
        create_notification(
            crop.farmer.user,
            f"Your crop listing '{crop.name}' was hidden by the admin team.",
            'system'
        )
    return redirect('admin_dashboard')


@login_required
def admin_resolve_feedback_view(request, pk):
    if not request.user.is_admin():
        return redirect('home')
    feedback = get_object_or_404(Feedback, pk=pk)
    feedback.is_resolved = True
    feedback.save()
    messages.success(request, "Feedback marked as resolved.")
    return redirect('admin_dashboard')


@login_required
def admin_reports_view(request):
    if not request.user.is_admin():
        return redirect('home')
        
    orders = Order.objects.filter(status='Delivered')
    total_sales = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    
    # Category sales breakdown
    category_sales = OrderItem.objects.filter(order__status='Delivered')\
        .values('crop__category__name')\
        .annotate(total_earned=Sum(F('price_per_unit') * F('quantity')), count=Count('id'))\
        .order_by('-total_earned')

    # Users growth
    total_farmers = Farmer.objects.count()
    total_buyers = Buyer.objects.count()

    context = {
        'total_sales': total_sales,
        'category_sales': category_sales,
        'total_farmers': total_farmers,
        'total_buyers': total_buyers,
    }
    return render(request, 'admin/reports.html', context)


# --- Smart Features & Analytics ---

def smart_tools_view(request):
    # 1. Weather forecast placeholder for cards
    location = request.GET.get('location', 'Midwest Region')
    weather_data = {
        'location': location,
        'temp': random.randint(22, 34),
        'humidity': random.randint(50, 85),
        'condition': random.choice(['Sunny', 'Partly Cloudy', 'Light Rain', 'Overcast']),
        'wind_speed': random.randint(5, 20),
        'recommendation': 'Excellent time for harvesting wheat. If rainfall is expected, cover crops.'
    }

    # 2. Advanced Crop Recommendation scoring logic
    recommendations = []
    form = AdvancedCropRecommendationForm()
    
    if request.method == 'POST':
        form = AdvancedCropRecommendationForm(request.POST)
        if form.is_valid():
            soil_type = form.cleaned_data['soil_type']
            soil_ph = form.cleaned_data['soil_ph']
            user_n = form.cleaned_data['nitrogen']
            user_p = form.cleaned_data['phosphorus']
            user_k = form.cleaned_data['potassium']
            temp = form.cleaned_data['temperature']
            rain = form.cleaned_data['rainfall']
            
            # Crop Ideal Database
            crop_db = {
                'Rice': {'N': 80, 'P': 40, 'K': 40, 'pH': 6.0, 'Temp': 27, 'Rain': 1200, 'Soil': 'Clayey'},
                'Wheat': {'N': 60, 'P': 40, 'K': 30, 'pH': 6.5, 'Temp': 18, 'Rain': 600, 'Soil': 'Loamy'},
                'Maize': {'N': 70, 'P': 45, 'K': 35, 'pH': 6.2, 'Temp': 24, 'Rain': 800, 'Soil': 'Loamy'},
                'Chickpeas': {'N': 20, 'P': 40, 'K': 30, 'pH': 7.0, 'Temp': 20, 'Rain': 400, 'Soil': 'Sandy'},
                'Mango': {'N': 40, 'P': 30, 'K': 50, 'pH': 6.0, 'Temp': 28, 'Rain': 1000, 'Soil': 'Alluvial'},
                'Potato': {'N': 60, 'P': 50, 'K': 80, 'pH': 5.8, 'Temp': 17, 'Rain': 700, 'Soil': 'Loamy'},
                'Cotton': {'N': 70, 'P': 40, 'K': 40, 'pH': 6.5, 'Temp': 26, 'Rain': 1000, 'Soil': 'Black'}
            }
            
            for crop_name, ideal in crop_db.items():
                # Normalized distance formulas
                score_n = 1.0 - (abs(user_n - ideal['N']) / 150.0)
                score_p = 1.0 - (abs(user_p - ideal['P']) / 150.0)
                score_k = 1.0 - (abs(user_k - ideal['K']) / 150.0)
                score_ph = 1.0 - (abs(soil_ph - ideal['pH']) / 5.0)
                score_temp = 1.0 - (abs(temp - ideal['Temp']) / 60.0)
                score_rain = 1.0 - (abs(rain - ideal['Rain']) / 3000.0)
                score_soil = 1.0 if soil_type == ideal['Soil'] else 0.5
                
                # Average score
                avg_score = (score_n + score_p + score_k + score_ph + score_temp + score_rain + score_soil) / 7.0
                match_percentage = round(max(0.0, min(1.0, avg_score)) * 100.0, 1)
                
                recommendations.append({
                    'crop': crop_name,
                    'match': match_percentage,
                    'soil': ideal['Soil'],
                    'ph': ideal['pH'],
                    'npk': f"N:{ideal['N']} P:{ideal['P']} K:{ideal['K']}"
                })
            
            # Sort by match score
            recommendations.sort(key=lambda x: x['match'], reverse=True)

    # 3. Market Price Comparison / price trends
    categories = Category.objects.all()
    trends = PriceTrend.objects.all().order_by('record_date')
    
    crop_trends = {}
    for trend in trends:
        if trend.crop_name not in crop_trends:
            crop_trends[trend.crop_name] = {'dates': [], 'prices': []}
        crop_trends[trend.crop_name]['dates'].append(trend.record_date.strftime("%Y-%m-%d"))
        crop_trends[trend.crop_name]['prices'].append(float(trend.avg_price))

    context = {
        'weather': weather_data,
        'form': form,
        'recommendations': recommendations,
        'crop_trends': crop_trends,
        'categories': categories,
    }
    return render(request, 'smart/smart_tools.html', context)



def weather_dashboard_view(request):
    location = request.GET.get('location', 'Midwest Region')
    
    # Seed a local weather forecast simulator
    random.seed(hash(location))
    
    temp = random.randint(15, 38)
    humidity = random.randint(35, 95)
    wind_speed = random.randint(3, 30)
    rainfall = random.randint(0, 150)
    soil_moisture = random.randint(10, 80)
    uv_index = random.randint(1, 11)
    
    alerts = []
    if temp > 35:
        alerts.append("Heatwave Warning: Ensure high-frequency early morning irrigation to avoid crop stress.")
    elif temp < 5:
        alerts.append("Frost Warning: Cover delicate crops. Prevent surface freezing.")
    if wind_speed > 25:
        alerts.append("High Wind Warning: Secure greenhouse covers and prop up young tree crops.")
    if rainfall > 100:
        alerts.append("Flood Advisory: Inspect drainage trenches. Suspend fertilizer spraying.")
    elif rainfall == 0 and soil_moisture < 25:
        alerts.append("Drought Stress Warning: Drip irrigation should be activated immediately.")
        
    advisories = [
        {"crop": "Wheat", "status": "Good", "advice": "Ideal temperature for wheat grain development. No immediate action required."},
        {"crop": "Rice (Paddy)", "status": "Needs Attention", "advice": "Ensure paddy water level is maintained at 5-10cm. Soil moisture is critical."},
        {"crop": "Potatoes", "status": "Action Required", "advice": "Monitor soil moisture. Apply light irrigation if rainfall remains below 10mm."}
    ]
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    forecast = []
    for day in days:
        forecast.append({
            'day': day,
            'temp': temp + random.randint(-4, 4),
            'humidity': min(100, max(0, humidity + random.randint(-15, 15))),
            'condition': random.choice(['Sunny', 'Partly Cloudy', 'Overcast', 'Showers', 'Thunderstorms']),
            'precip': random.randint(0, 80)
        })
        
    context = {
        'location': location,
        'temp': temp,
        'humidity': humidity,
        'wind_speed': wind_speed,
        'rainfall': rainfall,
        'soil_moisture': soil_moisture,
        'uv_index': uv_index,
        'alerts': alerts,
        'advisories': advisories,
        'forecast': forecast
    }
    return render(request, 'smart/weather_dashboard.html', context)


def farmer_store_view(request, username):
    farmer_user = get_object_or_404(User, username=username, role='farmer')
    farmer = farmer_user.farmer_profile
    crops = farmer.crops.filter(is_approved=True)
    
    # Search and Filter inside farmer store
    q = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    if q:
        crops = crops.filter(models.Q(name__icontains=q) | models.Q(description__icontains=q))
    if category_id:
        crops = crops.filter(category_id=category_id)
        
    categories = Category.objects.filter(crops__farmer=farmer).distinct()
    
    # Aggregate reviews from farmer's crops
    reviews = Review.objects.filter(crop__farmer=farmer).order_by('-created_at')
    
    # Get similar farmers in same location/region
    related_farmers = Farmer.objects.exclude(id=farmer.id)[:3]
    
    has_purchased = False
    if request.user.is_authenticated and request.user.role == 'buyer':
        has_purchased = Order.objects.filter(
            buyer=request.user,
            farmer=farmer,
            status='Delivered'
        ).exists()
    
    context = {
        'farmer': farmer,
        'crops': crops,
        'categories': categories,
        'reviews': reviews,
        'related_farmers': related_farmers,
        'q': q,
        'selected_category': int(category_id) if category_id.isdigit() else '',
        'has_purchased': has_purchased,
    }
    return render(request, 'marketplace/farmer_store.html', context)


def market_prices_view(request):
    from marketplace.models import MarketInsight, PriceTrend
    
    insights = MarketInsight.objects.all()
    categories = Category.objects.all()
    
    # Search and Filter
    q = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    demand = request.GET.get('demand', '')
    sort = request.GET.get('sort', '')
    
    if q:
        insights = insights.filter(models.Q(crop_name__icontains=q) | models.Q(region__icontains=q))
    if category_id:
        insights = insights.filter(category_id=category_id)
    if demand:
        insights = insights.filter(demand_level=demand)
        
    if sort == 'price_desc':
        insights = insights.order_by('-current_price')
    elif sort == 'price_asc':
        insights = insights.order_by('current_price')
    elif sort == 'volume_desc':
        insights = insights.order_by('-volume_tonnes')
    else:
        insights = insights.order_by('-record_date')
        
    # Top gainers and losers
    gainers = MarketInsight.objects.filter(price_change_percent__gt=0).order_by('-price_change_percent')[:3]
    losers = MarketInsight.objects.filter(price_change_percent__lt=0).order_by('price_change_percent')[:3]
    
    # Price trends for Chart.js (Tomato, Wheat, Rice)
    trends = PriceTrend.objects.all().order_by('record_date')
    crop_trends = {}
    for trend in trends:
        if trend.crop_name not in crop_trends:
            crop_trends[trend.crop_name] = {'dates': [], 'prices': []}
        crop_trends[trend.crop_name]['dates'].append(trend.record_date.strftime("%Y-%m-%d"))
        crop_trends[trend.crop_name]['prices'].append(float(trend.avg_price))
        
    context = {
        'insights': insights,
        'categories': categories,
        'gainers': gainers,
        'losers': losers,
        'crop_trends': crop_trends,
        'q': q,
        'selected_category': int(category_id) if category_id.isdigit() else '',
        'selected_demand': demand,
        'selected_sort': sort,
    }
    return render(request, 'marketplace/market_prices.html', context)


# --- Custom Context Processor for Notifications & Cart Count ---
def global_vars(request):
    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
        cart_count = CartItem.objects.filter(user=request.user).aggregate(Sum('quantity'))['quantity__sum'] or 0
        return {
            'unread_notifications_count': unread_notifications_count,
            'cart_count': cart_count
        }
    return {
        'unread_notifications_count': 0,
        'cart_count': 0
    }



def generate_invoice_pdf_bytes(order):
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.graphics.shapes import Drawing, Rect, String

    # Setup unique invoice number
    invoice_number = f"AC-{order.created_at.strftime('%Y%m%d')}-{order.id:04d}"
    invoice_date = order.created_at.strftime('%B %d, %Y')
    
    # Calculate costs
    tax = float(order.total_amount) * 0.05
    service_fee = 10.00
    grand_total = float(order.total_amount) + tax + service_fee
    
    # Create the buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=36, 
        leftMargin=36, 
        topMargin=36, 
        bottomMargin=36
    )
    
    # Define color scheme
    primary_green = colors.HexColor('#2E7D32')
    secondary_green = colors.HexColor('#4CAF50')
    accent_orange = colors.HexColor('#FF9800')
    neutral_dark = colors.HexColor('#333333')
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=primary_green,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'InvoiceSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=neutral_dark,
        spaceAfter=15
    )
    header_right_style = ParagraphStyle(
        'HeaderRight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#777777'),
        alignment=2 # Right aligned
    )
    meta_right_style = ParagraphStyle(
        'MetaRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=neutral_dark,
        alignment=2 # Right aligned
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=primary_green,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'InvoiceBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=neutral_dark,
        leading=12
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=neutral_dark
    )
    table_cell_bold_style = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=neutral_dark
    )
    
    elements = []
    
    # Header block
    header_left = [
        Paragraph("AgriConnect", title_style),
        Paragraph("Direct Farmer-to-Buyer Ecosystem", subtitle_style)
    ]
    header_right = [
        Paragraph("TAX INVOICE", header_right_style),
        Spacer(1, 8),
        Paragraph(f"<b>Invoice No:</b> {invoice_number}", meta_right_style),
        Paragraph(f"<b>Date:</b> {invoice_date}", meta_right_style),
        Paragraph(f"<b>Order ID:</b> #{order.id}", meta_right_style)
    ]
    
    header_table = Table([[header_left, header_right]], colWidths=[260, 260])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    # Separation Line
    elements.append(Table([[""]], colWidths=[520], rowHeights=[2], style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary_green),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ])))
    elements.append(Spacer(1, 15))
    
    # Addresses
    buyer_info = [
        Paragraph("<b>BUYER (BILL TO)</b>", section_heading),
        Spacer(1, 4),
        Paragraph(f"<b>Name:</b> {order.buyer.first_name or order.buyer.username}", body_style),
        Paragraph(f"<b>Phone:</b> {order.buyer.phone or 'N/A'}", body_style),
        Paragraph(f"<b>Address:</b> {order.shipping_address}", body_style),
    ]
    
    farmer_info = [
        Paragraph("<b>FARMER (SELLER)</b>", section_heading),
        Spacer(1, 4),
        Paragraph(f"<b>Farmer Name:</b> {order.farmer.user.first_name or order.farmer.user.username}", body_style),
        Paragraph(f"<b>Farm Name:</b> {order.farmer.farm_name or 'Local Farm'}", body_style),
        Paragraph(f"<b>Location:</b> {order.farmer.farm_location or 'Local Area'}", body_style),
        Paragraph(f"<b>Phone:</b> {order.farmer.user.phone or 'N/A'}", body_style),
    ]
    
    addr_table = Table([[buyer_info, farmer_info]], colWidths=[260, 260])
    addr_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(addr_table)
    elements.append(Spacer(1, 20))
    
    # Table of products
    table_data = [[
        Paragraph("Produce Description", table_header_style),
        Paragraph("Category", table_header_style),
        Paragraph("Unit Price", table_header_style),
        Paragraph("Quantity", table_header_style),
        Paragraph("Total Price", table_header_style)
    ]]
    
    for item in order.items.all():
        table_data.append([
            Paragraph(item.crop.name if item.crop else "Deleted Crop", table_cell_bold_style),
            Paragraph(item.crop.category.name if item.crop else "General", table_cell_style),
            Paragraph(f"₹{item.price_per_unit}", table_cell_style),
            Paragraph(f"{item.quantity} {item.crop.get_unit_display() if item.crop else 'kg'}", table_cell_style),
            Paragraph(f"₹{item.total_price():.2f}", table_cell_bold_style)
        ])
        
    prod_table = Table(table_data, colWidths=[150, 100, 90, 90, 90])
    prod_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_green),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('BOTTOMPADDING', (0,1), (-1,-1), 8),
        ('TOPPADDING', (0,1), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e8f5e9')),
    ]))
    elements.append(prod_table)
    elements.append(Spacer(1, 15))
    
    # Bottom block - Payment info on left, Calculations on right
    qr_drawing = Drawing(60, 60)
    qr_drawing.add(Rect(0, 0, 60, 60, fillColor=colors.white, strokeColor=primary_green, strokeWidth=1))
    qr_drawing.add(Rect(5, 40, 15, 15, fillColor=primary_green, strokeColor=None))
    qr_drawing.add(Rect(40, 40, 15, 15, fillColor=primary_green, strokeColor=None))
    qr_drawing.add(Rect(5, 5, 15, 15, fillColor=primary_green, strokeColor=None))
    qr_drawing.add(Rect(25, 25, 10, 10, fillColor=primary_green, strokeColor=None))
    qr_drawing.add(Rect(10, 25, 5, 5, fillColor=primary_green, strokeColor=None))
    qr_drawing.add(Rect(25, 10, 5, 5, fillColor=primary_green, strokeColor=None))
    
    verified_badge = Drawing(100, 20)
    verified_badge.add(Rect(0, 0, 100, 20, fillColor=colors.HexColor('#E8F5E9'), strokeColor=primary_green, strokeWidth=1, rx=5, ry=5))
    verified_badge.add(String(12, 6, "VERIFIED FARMER", fontName="Helvetica-Bold", fontSize=8, fillColor=primary_green))

    payment_info = [
        Paragraph("<b>PAYMENT INFORMATION</b>", section_heading),
        Spacer(1, 4),
        Paragraph("<b>Payment Method:</b> Cash On Delivery (COD)", body_style),
        Paragraph(f"<b>Payment Status:</b> {'Completed (Cash Collected)' if order.status == 'Delivered' else 'Pending Payment'}", body_style),
        Spacer(1, 8),
        verified_badge
    ]
    
    totals_table_data = [
        [Paragraph("Subtotal:", table_cell_style), Paragraph(f"₹{order.total_amount:.2f}", table_cell_bold_style)],
        [Paragraph("Taxes (5%):", table_cell_style), Paragraph(f"₹{tax:.2f}", table_cell_bold_style)],
        [Paragraph("Direct Service Fee:", table_cell_style), Paragraph(f"₹{service_fee:.2f}", table_cell_bold_style)],
        [Paragraph("Grand Total:", table_cell_bold_style), Paragraph(f"₹{grand_total:.2f}", ParagraphStyle('TotalGreen', parent=table_cell_bold_style, textColor=primary_green, fontSize=11))]
    ]
    
    totals_table = Table(totals_table_data, colWidths=[130, 100])
    totals_table.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor('#eeeeee')),
        ('LINEBELOW', (0,-2), (-1,-1), 1, primary_green),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    
    left_column = [
        payment_info,
        Spacer(1, 10),
        Table([[qr_drawing, Paragraph("<font size=7.5 color='#777777'>Scan to verify invoice<br/>or check tracking status<br/>directly on AgriConnect</font>", body_style)]], colWidths=[70, 180], style=TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    ]
    
    summary_table = Table([[left_column, totals_table]], colWidths=[280, 240])
    summary_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Footer Notice
    footer_text = Paragraph(
        "<center><font color='#777777'>Thank you for supporting direct-trade sustainable commerce with AgriConnect.<br/>"
        "Need help? Reach customer support at <b>support@agriconnect.org</b> or call 1800-123-4567.</font></center>",
        body_style
    )
    elements.append(footer_text)
    
    # Build Document
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.read()

def download_invoice_pdf_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    # Permission checks: only buyer, farmer of this order, or admin can download
    if not (request.user.is_admin() or request.user == order.buyer or (request.user.role == 'farmer' and request.user.farmer_profile == order.farmer)):
        messages.error(request, "Access Denied. You do not have permission to view this invoice.")
        return redirect('home')
        
    pdf_bytes = generate_invoice_pdf_bytes(order)
    invoice_number = f"AC-{order.created_at.strftime('%Y%m%d')}-{order.id:04d}"
    
    from django.http import HttpResponse
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice_number}.pdf"'
    return response


@login_required
def notifications_list_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'marketplace/notifications.html', context)


@login_required
def notifications_mark_all_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications_list')


@login_required
def notifications_mark_read_view(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    
    if notif.link:
        return redirect(notif.link)
    return redirect('notifications_list')


@login_required
def notifications_delete_view(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.delete()
    messages.success(request, "Notification deleted.")
    return redirect('notifications_list')


@login_required
def farmer_verification_submit_view(request):
    if not request.user.is_farmer():
        messages.error(request, "Access Denied. Farmers only.")
        return redirect('home')
        
    farmer = request.user.farmer_profile
    
    if request.method == 'POST':
        aadhaar = request.FILES.get('aadhaar_document')
        certificate = request.FILES.get('farm_certificate')
        
        if aadhaar:
            farmer.aadhaar_document = aadhaar
        if certificate:
            farmer.farm_certificate = certificate
            
        farmer.verification_status = 'review'
        farmer.save()
        
        # Notify farmer
        create_notification(
            request.user,
            "Verification documents submitted. Admin review is in progress.",
            'verification',
            'medium'
        )
        
        # Notify admins
        from accounts.models import User as AccountUser
        admins = AccountUser.objects.filter(role='admin')
        for admin in admins:
            create_notification(
                admin,
                f"New farmer verification request submitted by {request.user.username}.",
                'verification',
                'high',
                link=f"/admin/farmers/{farmer.id}/verify/"
            )
            
        messages.success(request, "Documents submitted successfully! Verification status is now Under Review.")
        return redirect('farmer_dashboard')
        
    context = {
        'farmer': farmer
    }
    return render(request, 'marketplace/farmer_verify.html', context)


@login_required
def admin_farmer_verify_view(request, pk):
    if not request.user.is_admin():
        messages.error(request, "Access Denied. Admins only.")
        return redirect('home')
        
    farmer = get_object_or_404(Farmer, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action') # 'approve', 'reject', 'resubmit'
        notes = request.POST.get('admin_notes', '')
        
        if action == 'approve':
            farmer.verification_status = 'approved'
            farmer.certification_status = 'verified'
            farmer.trust_score = 95
            farmer.verification_date = timezone.now()
            farmer.verified_by = request.user
            msg_text = "Your verification request has been APPROVED! Verified Farmer badge activated with trust score 95/100."
            messages.success(request, f"Farmer {farmer.user.username} approved successfully!")
        elif action == 'reject':
            farmer.verification_status = 'rejected'
            farmer.certification_status = 'none'
            farmer.trust_score = 50
            msg_text = f"Your verification request was rejected. Reason: {notes}"
            messages.warning(request, f"Farmer {farmer.user.username} rejected.")
        else: # resubmit
            farmer.verification_status = 'resubmit'
            msg_text = f"Resubmission required for verification documents. Reason: {notes}"
            messages.info(request, f"Resubmission requested for farmer {farmer.user.username}.")
            
        farmer.admin_notes = notes
        farmer.save()
        
        # Notify farmer
        create_notification(
            farmer.user,
            msg_text,
            'verification',
            'high' if action != 'approve' else 'medium',
            link='/farmer/verify/'
        )
        
        return redirect('admin_dashboard')
        
    context = {
        'farmer': farmer
    }
    return render(request, 'marketplace/admin_farmer_verify.html', context)


@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    
    # Search
    q = request.GET.get('q', '')
    if q:
        wishlist_items = wishlist_items.filter(
            Q(crop__name__icontains=q) | 
            Q(crop__farmer__user__username__icontains=q) | 
            Q(crop__category__name__icontains=q)
        )
        
    # Filters
    category_id = request.GET.get('category', '')
    if category_id:
        wishlist_items = wishlist_items.filter(crop__category_id=category_id)
        
    # Recommendations: other available crops
    recommended_crops = Crop.objects.filter(is_approved=True, availability_status='available').order_by('?')
    recommended_crops = recommended_crops.exclude(id__in=wishlist_items.values_list('crop_id', flat=True))[:4]
    
    categories = Category.objects.all()
    
    context = {
        'wishlist_items': wishlist_items,
        'recommended_crops': recommended_crops,
        'categories': categories,
        'q': q,
        'selected_category': category_id,
        'wishlist_count': wishlist_items.count(),

    }
    return render(request, 'marketplace/wishlist.html', context)


@login_required
def wishlist_toggle_view(request, crop_id):
    crop = get_object_or_404(Crop, id=crop_id)
    w_item = Wishlist.objects.filter(user=request.user, crop=crop)
    
    if w_item.exists():
        w_item.delete()
        status = 'removed'
        msg = f"'{crop.name}' removed from wishlist."
    else:
        Wishlist.objects.create(user=request.user, crop=crop)
        status = 'added'
        msg = f"'{crop.name}' added to your wishlist successfully."
        
    count = Wishlist.objects.filter(user=request.user).count()
    
    # Check if request is ajax/JSON request or form post
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        from django.http import JsonResponse
        return JsonResponse({'status': status, 'count': count, 'message': msg})
        
    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'crop_list'))


@login_required
def wishlist_remove_view(request, pk):
    w_item = get_object_or_404(Wishlist, pk=pk, user=request.user)
    crop_name = w_item.crop.name
    w_item.delete()
    messages.success(request, f"'{crop_name}' removed from your wishlist.")
    return redirect('wishlist')


@login_required
def wishlist_move_to_cart_view(request, pk):
    w_item = get_object_or_404(Wishlist, pk=pk, user=request.user)
    crop = w_item.crop

    try:
        buyer_profile = request.user.buyer_profile
    except Buyer.DoesNotExist:
        buyer_profile = None

    if buyer_profile and not crop.is_eligible_for_delivery(buyer_profile):
        est_days = crop.estimated_delivery_days(buyer_profile)
        rem_days = crop.remaining_shelf_life_days
        messages.error(request, f"Cannot move to cart. This fresh crop has a remaining shelf life of {rem_days} days, but estimated delivery to {buyer_profile.city or 'your city'} takes {est_days} days. Order blocked to prevent spoilage.")
        return redirect('wishlist')
    
    # Create or update CartItem
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        crop=crop,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        
    w_item.delete()
    messages.success(request, f"'{crop.name}' moved to shopping cart successfully.")
    return redirect('wishlist')



@login_required
def review_helpful_toggle_view(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if request.user in review.helpful_votes.all():
        review.helpful_votes.remove(request.user)
        msg = "Removed helpful vote from review."
    else:
        review.helpful_votes.add(request.user)
        msg = "Marked review as helpful!"
    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'crop_list'))


@login_required
def farmer_review_reply_view(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if not request.user.is_farmer() or review.crop.farmer.user != request.user:
        messages.error(request, "Access Denied.")
        return redirect('home')
        
    if request.method == 'POST':
        reply_text = request.POST.get('reply', '')
        if reply_text:
            review.reply = reply_text
            review.reply_at = timezone.now()
            review.save()
            messages.success(request, "Your reply has been posted successfully.")
            # Notify buyer
            create_notification(
                review.buyer,
                f"Farmer {request.user.username} replied to your review on '{review.crop.name}'.",
                'review',
                'medium'
            )
    return redirect(request.META.get('HTTP_REFERER', 'crop_list'))


@login_required
def review_edit_view(request, pk):
    review = get_object_or_404(Review, pk=pk, buyer=request.user)
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Your review has been updated.")
            return redirect('crop_detail', pk=review.crop.id)
    else:
        form = ReviewForm(instance=review)
    return render(request, 'marketplace/review_edit.html', {'form': form, 'review': review})


@login_required
def review_delete_view(request, pk):
    review = get_object_or_404(Review, pk=pk, buyer=request.user)
    crop_id = review.crop.id
    review.delete()
    messages.success(request, "Your review has been deleted.")
    return redirect('crop_detail', pk=crop_id)


@login_required
def farmer_rate_view(request, farmer_id):
    farmer = get_object_or_404(Farmer, id=farmer_id)
    if not request.user.role == 'buyer':
        messages.error(request, "Only buyers can rate farmers.")
        return redirect('home')
        
    from marketplace.forms import FarmerRatingForm
    from marketplace.models import FarmerRating
    
    # Check if already rated
    existing_rating = FarmerRating.objects.filter(buyer=request.user, farmer=farmer).first()
    
    if request.method == 'POST':
        form = FarmerRatingForm(request.POST, instance=existing_rating)
        if form.is_valid():
            rating_obj = form.save(commit=False)
            rating_obj.buyer = request.user
            rating_obj.farmer = farmer
            rating_obj.save()
            
            # Update farmer store rating
            all_ratings = FarmerRating.objects.filter(farmer=farmer)
            avg_rating = all_ratings.aggregate(Avg('rating'))['rating__avg'] or 5.0
            farmer.store_rating = round(avg_rating, 1)
            farmer.save()
            
            messages.success(request, f"Thank you! Your rating for {farmer.farm_name or farmer.user.username} has been submitted successfully.")
            return redirect('buyer_dashboard')
    else:
        form = FarmerRatingForm(instance=existing_rating)
        
    return render(request, 'marketplace/farmer_rate.html', {'form': form, 'farmer': farmer})


@login_required
def reports_dashboard_view(request):
    # Fetch report history for user
    reports = Report.objects.filter(generated_by=request.user).order_by('-created_at')
    
    # Calculate counters
    total_generated = reports.count()
    total_downloads = reports.aggregate(Sum('download_count'))['download_count__sum'] or 0
    active_schedules = reports.exclude(scheduled_interval__isnull=True).exclude(scheduled_interval='').count()
    
    # Fetch recent orders to populate charts (revenue analytics)
    # If farmer: sales from this farmer
    # If admin: all sales
    # If buyer: buyer purchases
    if request.user.role == 'admin':
        orders = Order.objects.all().order_by('-created_at')[:10]
        revenue_data = Order.objects.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    elif request.user.role == 'farmer':
        orders = Order.objects.filter(farmer=request.user.farmer_profile).order_by('-created_at')[:10]
        revenue_data = Order.objects.filter(farmer=request.user.farmer_profile, status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    else: # buyer
        orders = Order.objects.filter(buyer=request.user).order_by('-created_at')[:10]
        revenue_data = Order.objects.filter(buyer=request.user, status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    context = {
        'reports': reports,
        'total_generated': total_generated,
        'total_downloads': total_downloads,
        'active_schedules': active_schedules,
        'orders': orders,
        'revenue_data': float(revenue_data),
    }
    return render(request, 'marketplace/reports.html', context)


@login_required
def report_generate_view(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type', 'order')
        fmt = request.POST.get('format', 'csv')
        scheduled_interval = request.POST.get('scheduled_interval', '')
        
        name = f"{report_type.replace('_', ' ').title()} Report ({timezone.now().strftime('%Y-%m-%d')})"
        
        # Save to database
        report = Report.objects.create(
            name=name,
            report_type=report_type,
            generated_by=request.user,
            format=fmt,
            scheduled_interval=scheduled_interval if scheduled_interval else None
        )
        
        if request.POST.get('direct_download') == 'true':
            return redirect('report_download', pk=report.pk)
            
        messages.success(request, f"New report '{name}' has been generated and added to your export log.")
        return redirect('reports_dashboard')
    return redirect('reports_dashboard')


@login_required
def report_download_view(request, pk):
    report = get_object_or_404(Report, pk=pk, generated_by=request.user)
    
    # Increment download count
    report.download_count += 1
    report.save()
    
    # Gather data based on report type
    headers = []
    data_rows = []
    
    if report.report_type in ('order', 'orders'):
        headers = ['Order ID', 'Buyer', 'Farmer', 'Total Amount (₹)', 'Payment Method', 'Status', 'Date']
        if request.user.role == 'admin':
            records = Order.objects.all()
        elif request.user.role == 'farmer':
            records = Order.objects.filter(farmer=request.user.farmer_profile)
        else:
            records = Order.objects.filter(buyer=request.user)
        for r in records:
            data_rows.append([str(r.id), r.buyer.username, r.farmer.farm_name, f"₹{r.total_amount}", r.payment_method, r.status, r.created_at.strftime('%Y-%m-%d %H:%M')])
            
    elif report.report_type == 'revenue':
        headers = ['Payment ID', 'Order ID', 'Buyer Name', 'Farmer Name', 'Order Status', 'Payment Method', 'Payment Status', 'Transaction Date', 'Platform Fee (5%) (₹)', 'Net Amount (₹)', 'Total Amount (₹)']
        if request.user.role == 'admin':
            records = Payment.objects.all().select_related('order__buyer', 'order__farmer')
        elif request.user.role == 'farmer':
            records = Payment.objects.filter(order__farmer=request.user.farmer_profile).select_related('order__buyer', 'order__farmer')
        else:
            records = Payment.objects.filter(order__buyer=request.user).select_related('order__buyer', 'order__farmer')
        for r in records:
            total = float(r.amount)
            fee = total * 0.05
            net = total - fee
            data_rows.append([
                str(r.id), str(r.order.id), r.order.buyer.username, r.order.farmer.farm_name,
                r.order.status, r.payment_method, r.status, r.created_at.strftime('%Y-%m-%d %H:%M'),
                f"₹{fee:.2f}", f"₹{net:.2f}", f"₹{total:.2f}"
            ])
            
    elif report.report_type == 'product':
        headers = ['Product ID', 'Name', 'Category', 'Price/Unit (₹)', 'Stock Available', 'Unit', 'Approved']
        if request.user.role == 'admin':
            records = Crop.objects.all()
        elif request.user.role == 'farmer':
            records = Crop.objects.filter(farmer=request.user.farmer_profile)
        else:
            records = Crop.objects.filter(is_approved=True)
        for r in records:
            data_rows.append([str(r.id), r.name, r.category.name, f"₹{r.price_per_kg}", str(r.quantity_available), r.unit, "Yes" if r.is_approved else "No"])
            
    elif report.report_type in ('user', 'user_registration', 'farmers', 'buyers'):
        headers = ['User ID', 'Username', 'Email', 'Role', 'Status', 'Date Joined', 'Total Orders/Sales', 'Total Transacted Value (₹)']
        if request.user.role == 'admin':
            if report.report_type == 'farmers':
                records = User.objects.filter(role='farmer')
            elif report.report_type == 'buyers':
                records = User.objects.filter(role='buyer')
            else:
                records = User.objects.all()
        else:
            records = [request.user]
        for r in records:
            status = 'Active' if r.is_active else 'Suspended'
            total_transacted = 0
            total_count = 0
            if r.role == 'buyer':
                buyer_orders = Order.objects.filter(buyer=r, status='Delivered')
                total_count = buyer_orders.count()
                total_transacted = buyer_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            elif r.role == 'farmer' and hasattr(r, 'farmer_profile'):
                farmer_orders = Order.objects.filter(farmer=r.farmer_profile, status='Delivered')
                total_count = farmer_orders.count()
                total_transacted = farmer_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
                
            data_rows.append([
                str(r.id), r.username, r.email, r.role.title(), status, r.date_joined.strftime('%Y-%m-%d %H:%M'),
                str(total_count), f"₹{float(total_transacted):.2f}"
            ])
            
    elif report.report_type == 'farmer_verification':
        headers = ['User ID', 'Username', 'Farm Name', 'Location', 'Certification Status', 'Store Rating', 'Orders Completed']
        if request.user.role == 'admin':
            records = User.objects.filter(role='farmer').select_related('farmer_profile')
        else:
            records = [request.user] if request.user.role == 'farmer' else []
        for r in records:
            if hasattr(r, 'farmer_profile'):
                p = r.farmer_profile
                data_rows.append([
                    str(r.id), r.username, p.farm_name or 'N/A', p.farm_location or 'N/A', 
                    p.certification_status.title(), str(p.store_rating), str(p.orders_completed)
                ])

    elif report.report_type == 'sales':
        headers = ['Item ID', 'Order ID', 'Crop Name', 'Quantity', 'Price/Unit (₹)', 'Total (₹)', 'Date']
        if request.user.role == 'admin':
            records = OrderItem.objects.all().select_related('order', 'crop')
        elif request.user.role == 'farmer':
            records = OrderItem.objects.filter(order__farmer=request.user.farmer_profile).select_related('order', 'crop')
        else:
            records = OrderItem.objects.filter(order__buyer=request.user).select_related('order', 'crop')
            
        for r in records:
            crop_name = r.crop.name if r.crop else 'Deleted Crop'
            total_item_price = float(r.price_per_unit) * float(r.quantity)
            data_rows.append([
                str(r.id), str(r.order.id), crop_name, str(r.quantity), 
                f"₹{r.price_per_unit}", f"₹{total_item_price:.2f}", r.order.created_at.strftime('%Y-%m-%d %H:%M')
            ])

    elif report.report_type == 'top_selling':
        headers = ['Crop ID', 'Name', 'Category', 'Total Units Sold', 'Total Revenue (₹)']
        if request.user.role == 'admin':
            crops = Crop.objects.annotate(total_sold=Sum('orderitem__quantity'), total_rev=Sum(F('orderitem__quantity') * F('orderitem__price_per_unit'))).filter(total_sold__isnull=False).order_by('-total_sold')
        elif request.user.role == 'farmer':
            crops = Crop.objects.filter(farmer=request.user.farmer_profile).annotate(total_sold=Sum('orderitem__quantity'), total_rev=Sum(F('orderitem__quantity') * F('orderitem__price_per_unit'))).filter(total_sold__isnull=False).order_by('-total_sold')
        else:
            crops = []
            
        for c in crops:
            data_rows.append([
                str(c.id), c.name, c.category.name if c.category else 'N/A', 
                str(c.total_sold), f"₹{c.total_rev:.2f}" if c.total_rev else "₹0.00"
            ])
            
    else: # default fallback
        headers = ['Record ID', 'Created At']
        data_rows.append(['1', timezone.now().strftime('%Y-%m-%d %H:%M')])
        
    # Return formatted file based on requested format
    if report.format == 'xlsx':
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        from openpyxl.utils import get_column_letter

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{report.name.replace(" ", "_")}.xlsx"'
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Marketplace Report"
        
        # Style Title
        title_font = Font(name='Arial', size=14, bold=True, color='2E7D32')
        ws['A1'] = "AgriConnect Marketplace Business Report"
        ws['A1'].font = title_font
        ws['A2'] = f"Report Name: {report.name}"
        ws['A3'] = f"Generated On: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Table Headers style
        header_fill = PatternFill(start_color='2E7D32', end_color='2E7D32', fill_type='solid')
        header_font = Font(name='Arial', size=11, bold=True, color='FFFFFF')
        
        # Write headers
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=5, column=col_idx)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            
        # Write data rows
        for row_idx, row_data in enumerate(data_rows, 6):
            for col_idx, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.value = value
                cell.alignment = Alignment(horizontal='left')
                
        # Auto-adjust column widths
        for col in ws.columns:
            vals = [cell.value for cell in col if cell.value is not None]
            max_len = max(len(str(v)) for v in vals) if vals else 10
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
            
        wb.save(response)
        return response

    elif report.format == 'pdf':
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{report.name.replace(" ", "_")}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=8
        )
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#555555'),
            spaceAfter=20
        )
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=8,
            leading=10
        )
        header_cell_style = ParagraphStyle(
            'HeaderCellStyle',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.white,
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph("AgriConnect Business Intelligence Report", title_style))
        story.append(Paragraph(f"Report Name: {report.name} | Generated: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
        story.append(Spacer(1, 10))
        
        # Format table data
        table_data = []
        table_data.append([Paragraph(h, header_cell_style) for h in headers])
        for row in data_rows:
            table_data.append([Paragraph(str(val), cell_style) for val in row])
            
        col_count = len(headers)
        col_width = (letter[0] - 72) / col_count
        
        t = Table(table_data, colWidths=[col_width] * col_count)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2E7D32')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F8FFF8'), colors.white]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E0E0E0')),
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
            ('TOPPADDING', (0,1), (-1,-1), 6),
        ]))
        
        story.append(t)
        doc.build(story)
        return response

    else: # Default CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report.name.replace(" ", "_")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['AgriConnect Marketplace Business Report'])
        writer.writerow([f'Report Name: {report.name}', f'Generated On: {report.created_at}'])
        writer.writerow([])
        writer.writerow(headers)
        for row in data_rows:
            writer.writerow(row)
        return response


@login_required
def report_delete_view(request, pk):
    report = get_object_or_404(Report, pk=pk, generated_by=request.user)
    name = report.name
    report.delete()
    messages.success(request, f"Report '{name}' deleted successfully.")
    return redirect('reports_dashboard')


@login_required
def admin_suspend_user_view(request, pk):
    if not request.user.is_admin():
        messages.error(request, "Access Denied. Admins only.")
        return redirect('home')
        
    user_to_toggle = get_object_or_404(User, pk=pk)
    
    if user_to_toggle == request.user:
        messages.error(request, "You cannot suspend your own account.")
        return redirect('admin_dashboard')
        
    user_to_toggle.is_active = not user_to_toggle.is_active
    user_to_toggle.save()
    
    action = "activated" if user_to_toggle.is_active else "suspended"
    messages.success(request, f"User {user_to_toggle.username} has been successfully {action}.")
    return redirect('admin_dashboard')

@login_required
def admin_delete_user_view(request, pk):
    if not request.user.is_admin():
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Access Denied. Admins only.'}, status=403)
        messages.error(request, "Access Denied. Admins only.")
        return redirect('home')
        
    if request.method == "POST":
        try:
            user_to_delete = get_object_or_404(User, pk=pk)
            
            if user_to_delete == request.user:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'You cannot delete your own account.'}, status=400)
                messages.error(request, "You cannot delete your own account.")
                return redirect('/dashboard/admin/?tab=buyers')
                
            username = user_to_delete.username
            role = user_to_delete.role
            
            # Clean up user's cart items, notifications and OTPs
            CartItem.objects.filter(user=user_to_delete).delete()
            Notification.objects.filter(user=user_to_delete).delete()
            OrderOTP.objects.filter(user=user_to_delete).delete()
            
            user_to_delete.delete()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
                return JsonResponse({
                    'success': True,
                    'user_id': pk,
                    'username': username,
                    'role': role,
                    'message': f"User '{username}' has been permanently deleted."
                })
                
            messages.success(request, f"User {username} has been permanently deleted.")
        except Exception as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)}, status=500)
            messages.error(request, f"Failed to delete user: {str(e)}")
            
    return redirect('/dashboard/admin/?tab=buyers')

@login_required
def admin_delete_order_view(request, pk):
    if not request.user.is_admin():
        messages.error(request, "Access Denied. Admins only.")
        return redirect('home')
        
    order = get_object_or_404(Order, pk=pk)
    order_id = order.id
    order.delete()
    messages.success(request, f"Order #{order_id} has been deleted.")
    return redirect('admin_dashboard')

@login_required
def admin_delete_crop_view(request, pk):
    if not request.user.is_admin():
        messages.error(request, "Access Denied. Admins only.")
        return redirect('home')
        
    crop = get_object_or_404(Crop, pk=pk)
    crop_name = crop.name
    crop.delete()
    messages.success(request, f"Crop listing '{crop_name}' has been deleted.")
    return redirect('admin_dashboard')

@login_required
def admin_edit_user_view(request, pk):
    if not request.user.is_admin():
        messages.error(request, "Access Denied. Admins only.")
        return redirect('home')
        
    edit_user = get_object_or_404(User, pk=pk)
    
    farmer_profile = None
    buyer_profile = None
    
    if edit_user.role == 'farmer' and hasattr(edit_user, 'farmer_profile'):
        farmer_profile = edit_user.farmer_profile
    elif edit_user.role == 'buyer' and hasattr(edit_user, 'buyer_profile'):
        buyer_profile = edit_user.buyer_profile
        
    if request.method == "POST":
        edit_user.first_name = request.POST.get('first_name', '')
        edit_user.last_name = request.POST.get('last_name', '')
        edit_user.email = request.POST.get('email', '')
        edit_user.is_active = request.POST.get('is_active') == 'on'
        edit_user.save()
        
        if farmer_profile:
            farmer_profile.farm_name = request.POST.get('farm_name', '')
            farmer_profile.farm_size = request.POST.get('farm_size', '')
            farmer_profile.farm_location = request.POST.get('farm_location', '')
            farmer_profile.certification_status = request.POST.get('certification_status', 'none')
            farmer_profile.save()
            
        elif buyer_profile:
            buyer_profile.contact_name = request.POST.get('contact_name', '')
            buyer_profile.city = request.POST.get('city', '')
            buyer_profile.state = request.POST.get('state', '')
            buyer_profile.delivery_address = request.POST.get('delivery_address', '')
            buyer_profile.save()
            
        messages.success(request, f"User {edit_user.username}'s profile has been updated.")
        target_tab = 'farmers' if edit_user.role == 'farmer' else 'buyers'
        return redirect(f'/dashboard/admin/?tab={target_tab}')
        
    context = {
        'edit_user': edit_user,
        'farmer_profile': farmer_profile,
        'buyer_profile': buyer_profile,
    }
    return render(request, 'dashboards/admin_edit_user.html', context)

@login_required
def verify_order_otp_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            otp = data.get('otp_code')
        except json.JSONDecodeError:
            otp = request.POST.get('otp_code')
            
        if order.otp_code == otp and timezone.now() < order.otp_expires_at:
            order.is_otp_verified = True
            order.status = 'Confirmed'
            order.save()
            
            # --- Generate and Send Invoice PDF ---
            import io
            from marketplace.utils import send_html_email
            from marketplace.utils import _generate_invoice_pdf
            
            buffer = io.BytesIO()
            invoice_number = _generate_invoice_pdf(order, buffer)
            pdf_content = buffer.getvalue()
            
            context = {'order': order}
            send_html_email(
                subject=f"AgriConnect - Order Confirmed (Invoice #{invoice_number})",
                template_name="emails/order_confirmation.html",
                context=context,
                recipient_list=[order.buyer.email],
                attachment_content=pdf_content,
                attachment_filename=f"Invoice_{invoice_number}.pdf"
            )
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                from django.http import JsonResponse
                from django.urls import reverse
                return JsonResponse({'success': True, 'message': 'OTP Verified Successfully. Order Confirmed!', 'redirect': reverse('order_tracking', args=[order.pk])})
                
            messages.success(request, "OTP Verified Successfully. Order Confirmed!")
            return redirect('order_tracking', pk=order.pk)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                from django.http import JsonResponse
                return JsonResponse({'success': False, 'message': 'Invalid or expired OTP.'})
            messages.error(request, "Invalid or expired OTP.")
    
    return render(request, 'marketplace/otp_verify.html', {'order_otp': order})

@login_required
def resend_order_otp_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    import random
    import datetime
    from django.utils import timezone
    order.otp_code = str(random.randint(100000, 999999))
    order.otp_expires_at = timezone.now() + datetime.timedelta(minutes=10)
    order.save()
    
    from marketplace.utils import send_html_email
    send_html_email(
        subject="AgriConnect - Your Resent Order Verification OTP",
        template_name="emails/otp_email.html",
        context={'user': request.user, 'otp_code': order.otp_code},
        recipient_list=[request.user.email]
    )
    
    from marketplace.utils import create_notification
    create_notification(request.user, f"Your resent Order Verification OTP is: {order.otp_code}. It is valid for 10 minutes.", 'system')
    messages.success(request, f"OTP Resent to {request.user.email}. Check your notifications as well.")
    return redirect('verify_order_otp', pk=order.pk)

