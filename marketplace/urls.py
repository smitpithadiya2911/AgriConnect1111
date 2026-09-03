from django.urls import path
from . import views

urlpatterns = [
    # General Pages
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('feedback/submit/', views.submit_feedback_view, name='submit_feedback'),
    
    # Dashboards
    path('dashboard/farmer/', views.farmer_dashboard_view, name='farmer_dashboard'),
    path('dashboard/buyer/', views.buyer_dashboard_view, name='buyer_dashboard'),
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),
    
    # Crop Listings & Catalog
    path('crops/', views.crop_list_view, name='crop_list'),
    path('crops/<int:pk>/', views.crop_detail_view, name='crop_detail'),
    
    # Farmer Actions (Crop CRUD & Orders)
    path('crops/add/', views.crop_create_view, name='crop_create'),
    path('crops/<int:pk>/edit/', views.crop_update_view, name='crop_update'),
    path('crops/<int:pk>/delete/', views.crop_delete_view, name='crop_delete'),
    path('farmer/orders/', views.farmer_orders_view, name='farmer_orders'),
    path('farmer/orders/<int:pk>/status/', views.farmer_update_order_status_view, name='farmer_update_order_status'),
    
    # Buyer Actions (Cart, Checkout, Tracking, Invoice)
    path('cart/', views.view_cart_view, name='view_cart'),
    path('cart/add/<int:pk>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/update/<int:pk>/', views.update_cart_view, name='update_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.buyer_orders_view, name='buyer_orders'),
    path('orders/<int:pk>/invoice/', views.order_invoice_view, name='order_invoice'),
    path('orders/<int:pk>/invoice/pdf/', views.download_invoice_pdf_view, name='download_invoice_pdf'),
    path('orders/<int:pk>/track/', views.order_tracking_view, name='order_tracking'),
    path('orders/<int:pk>/cancel/', views.order_cancel_view, name='order_cancel'),
    path('orders/<int:pk>/return/', views.order_return_view, name='order_return'),
    path('farmer/returns/<int:pk>/approve/', views.farmer_approve_return_view, name='farmer_approve_return'),
    
    # Admin Controls
    path('admin/crops/<int:pk>/approve/', views.admin_approve_crop_view, name='admin_approve_crop'),
    path('admin/crops/<int:pk>/reject/', views.admin_reject_crop_view, name='admin_reject_crop'),
    path('admin/feedback/<int:pk>/resolve/', views.admin_resolve_feedback_view, name='admin_resolve_feedback'),
    path('admin/reports/', views.admin_reports_view, name='admin_reports'),
    path('admin/farmers/<int:pk>/verify/', views.admin_farmer_verify_view, name='admin_farmer_verify'),
    path('farmer/verify/', views.farmer_verification_submit_view, name='farmer_verification_submit'),
    
    # Smart Tools
    path('smart-tools/', views.smart_tools_view, name='smart_tools'),
    path('weather-dashboard/', views.weather_dashboard_view, name='weather_dashboard'),

    # Chat Messaging
    path('chat/', views.chat_list_view, name='chat_list'),
    path('chat/<str:username>/', views.chat_detail_view, name='chat_detail'),
    
    # Public Farmer Profile/Storefront
    path('farmer/<str:username>/', views.farmer_store_view, name='farmer_store'),
    
    # Agricultural Market Intelligence Dashboard
    path('market-prices/', views.market_prices_view, name='market_prices'),
    
    # Notification Center URLs
    path('notifications/', views.notifications_list_view, name='notifications_list'),
    path('notifications/mark-all-read/', views.notifications_mark_all_read_view, name='notifications_mark_all_read'),
    path('notifications/<int:pk>/mark-read/', views.notifications_mark_read_view, name='notifications_mark_read'),
    path('notifications/<int:pk>/delete/', views.notifications_delete_view, name='notifications_delete'),
    
    # Wishlist and Favorites URLs
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:crop_id>/', views.wishlist_toggle_view, name='wishlist_toggle'),
    path('wishlist/remove/<int:pk>/', views.wishlist_remove_view, name='wishlist_remove'),
    path('wishlist/move-to-cart/<int:pk>/', views.wishlist_move_to_cart_view, name='wishlist_move_to_cart'),
    path('farmers/follow/<int:farmer_id>/', views.farmer_follow_view, name='farmer_follow'),

    # Reviews and Ratings System URLs
    path('reviews/<int:pk>/helpful/', views.review_helpful_toggle_view, name='review_helpful_toggle'),
    path('reviews/<int:pk>/reply/', views.farmer_review_reply_view, name='farmer_review_reply'),
    path('reviews/<int:pk>/edit/', views.review_edit_view, name='review_edit'),
    path('reviews/<int:pk>/delete/', views.review_delete_view, name='review_delete'),
    path('farmer/<int:farmer_id>/rate/', views.farmer_rate_view, name='farmer_rate'),

    # Reports and Export Center URLs
    path('reports/', views.reports_dashboard_view, name='reports_dashboard'),
    path('reports/generate/', views.report_generate_view, name='report_generate'),
    path('reports/<int:pk>/download/', views.report_download_view, name='report_download'),
    path('reports/<int:pk>/delete/', views.report_delete_view, name='report_delete'),
]
