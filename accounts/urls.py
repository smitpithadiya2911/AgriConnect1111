from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('register/verify/<int:pk>/', views.verify_registration_otp_view, name='verify_registration_otp'),
    
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    

    
    path('dashboard/redirect/', views.dashboard_redirect_view, name='dashboard_redirect'),
    path('select-role/', views.select_role_view, name='select_role'),
    path('profile/', views.profile_view, name='profile'),
]
