from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('register/verify/<int:pk>/', views.verify_registration_otp_view, name='verify_registration_otp'),
    
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password Reset & Forgot Password
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('forgot-password/verify/<int:pk>/', views.verify_password_reset_otp_view, name='verify_password_reset_otp'),
    
    # Django Auth standard reset endpoints (email / test compatibility)
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/forgot_password.html',
        email_template_name='emails/auth_otp_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url='/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/password-reset/complete/'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    path('dashboard/redirect/', views.dashboard_redirect_view, name='dashboard_redirect'),
    path('select-role/', views.select_role_view, name='select_role'),
    path('profile/', views.profile_view, name='profile'),
]
