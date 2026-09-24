from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from .forms import CustomUserCreationForm, UserUpdateForm, FarmerProfileUpdateForm, BuyerProfileUpdateForm
from .models import Farmer, Buyer, AuthOTP
from marketplace.utils import send_html_email, generate_otp
from marketplace.models import Notification

User = get_user_model()

# ==========================================
# Helper Functions
# ==========================================

def notify_admins_of_new_user(user, role):
    """
    Sends a system notification to all superusers and active admin users 
    when a new user registers or selects a role.
    """
    try:
        admins = User.objects.filter(Q(is_superuser=True) | Q(role='admin', is_active=True)).distinct()
        msg = f"New {role.capitalize()} registered: {user.get_full_name() or user.username} ({user.email})."
        
        # Optimized: 1 query instead of N queries
        notifications = [
            Notification(user=admin, notification_type='system', priority='medium', message=msg) 
            for admin in admins
        ]
        Notification.objects.bulk_create(notifications)
    except Exception as e:
        # Fail silently if notification creation fails, so we don't break the user's registration flow
        pass

# ==========================================
# Authentication Views
# ==========================================

def register_view(request):
    """Handles user registration and sends an OTP to their email."""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.is_active = False # Require OTP verification first
            user.save()
            
            # Generate Registration OTP
            otp_code = generate_otp()
            auth_otp = AuthOTP.objects.create(
                user=user,
                email=user.email,
                otp_code=otp_code,
                otp_type='registration',
                expires_at=timezone.now() + timedelta(minutes=5)
            )
            
            # Send Email
            send_html_email(
                subject='Verify Your AgriConnect Account',
                template_name='emails/auth_otp_email.html',
                context={'otp_code': otp_code, 'user': user, 'otp_type': 'registration'},
                recipient_list=[user.email]
            )
            
            messages.success(request, f"Account created! We've sent a 6-digit verification code to {user.email}.")
            return redirect('verify_registration_otp', pk=auth_otp.pk)
        else:
            messages.error(request, "There was an error in registration. Please check the details below.")
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Handles user login, allowing either username or email."""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
        
    if request.method == 'POST':
        # Make a copy of POST data to modify username if an email was provided
        post_data = request.POST.copy()
        username_or_email = post_data.get('username', '')
        
        # If input looks like an email, find the associated username
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                post_data['username'] = user_obj.username
            except User.DoesNotExist:
                pass # Let the authentication form handle the invalid credentials

        form = AuthenticationForm(request, data=post_data)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard_redirect')
                
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Logs out the user and redirects to the home page."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


@login_required
def dashboard_redirect_view(request):
    """Routes users to their specific dashboard based on their role."""
    role = 'admin' if request.user.is_superuser else request.user.role
    if role in ['admin', 'farmer', 'buyer']:
        return redirect(f'{role}_dashboard')
    return redirect('select_role')


@login_required
def select_role_view(request):
    """Allows new users to choose whether they are a Farmer or Buyer."""
    if request.user.role in ['buyer', 'farmer', 'admin']:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        selected_role = request.POST.get('role')
        
        if selected_role in ['buyer', 'farmer']:
            request.user.role = selected_role
            request.user.save(update_fields=['role'])

            # Create specific profile based on role
            if selected_role == 'buyer':
                Buyer.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'contact_name': request.user.get_full_name() or request.user.username,
                        'delivery_address': request.user.address or ''
                    }
                )
            else:
                Farmer.objects.get_or_create(
                    user=request.user,
                    defaults={'farm_name': f"{request.user.username}'s Farm"}
                )
                
            # Notify admins of the new completed registration
            notify_admins_of_new_user(request.user, selected_role)

            messages.success(request, f"Welcome to AgriConnect as a {selected_role.capitalize()}!")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Please select a valid role to proceed.")

    return render(request, 'accounts/select_role.html')


@login_required
def profile_view(request):
    """Allows users (farmers and buyers) to update their base user details, upload/change profile pictures, role settings, and change their password."""
    user = request.user
    
    # Map role to profile model and form class
    ROLE_MAP = {
        'farmer': (Farmer, FarmerProfileUpdateForm),
        'buyer': (Buyer, BuyerProfileUpdateForm),
    }
    
    ModelClass, FormClass = ROLE_MAP.get(user.role, (None, None))
    profile_instance = ModelClass.objects.get_or_create(user=user)[0] if ModelClass else None
        
    if request.method == 'POST':
        action = request.POST.get('action', 'update_profile')
        
        # --- Handle Password Change from Profile ---
        if action == 'change_password':
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()
            
            if not new_password or not confirm_password:
                messages.error(request, "Please enter and confirm your new password.")
            elif len(new_password) < 6:
                messages.error(request, "Password must be at least 6 characters long.")
            elif new_password != confirm_password:
                messages.error(request, "Passwords do not match. Please re-enter them carefully.")
            else:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been changed successfully! Your account is secured.")
                return redirect('profile')
                
        # --- Handle Profile Info & Picture Update ---
        else:
            user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
            profile_form = FormClass(request.POST, instance=profile_instance) if FormClass else None
                
            if user_form.is_valid() and (not profile_form or profile_form.is_valid()):
                saved_user = user_form.save(commit=False)
                
                # Check if remove profile picture was requested
                if request.POST.get('remove_picture') == '1':
                    if saved_user.profile_picture:
                        try:
                            saved_user.profile_picture.delete(save=False)
                        except Exception:
                            pass
                    saved_user.profile_picture = None
                    
                saved_user.save()
                if profile_form:
                    profile_form.save()
                    
                messages.success(request, "Your profile details have been saved successfully!")
                return redirect('profile')
            else:
                messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = FormClass(instance=profile_instance) if FormClass else None
            
    context = {
        'u_form': user_form,
        'p_form': profile_form,
        'role': user.role
    }
    return render(request, 'accounts/profile.html', context)


def forgot_password_view(request):
    """Initiates password reset by sending an OTP to the user's registered email."""
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        user = None
        if '@' in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            user = User.objects.filter(username__iexact=identifier).first()

        if user and user.email:
            otp_code = generate_otp()
            auth_otp = AuthOTP.objects.create(
                user=user,
                email=user.email,
                otp_code=otp_code,
                otp_type='password_reset',
                expires_at=timezone.now() + timedelta(minutes=10)
            )

            send_html_email(
                subject='AgriConnect - Password Reset Instructions',
                template_name='emails/auth_otp_email.html',
                context={'otp_code': otp_code, 'user': user, 'otp_type': 'password_reset'},
                recipient_list=[user.email]
            )
            messages.success(request, f"A 6-digit verification code has been sent to {user.email}.")
            return redirect('verify_password_reset_otp', pk=auth_otp.pk)
        else:
            messages.error(request, "No account was found with that username or email address.")

    return render(request, 'accounts/forgot_password.html')


def verify_password_reset_otp_view(request, pk):
    """Verifies the password reset OTP and sets the new password."""
    auth_otp = get_object_or_404(AuthOTP, pk=pk, otp_type='password_reset')

    if auth_otp.is_verified:
        messages.info(request, "This password reset code has already been used. Please log in.")
        return redirect('login')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp_code', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if auth_otp.attempts >= 5:
            messages.error(request, "Too many failed attempts. Please request a new password reset.")
            return redirect('forgot_password')

        auth_otp.attempts += 1
        auth_otp.save(update_fields=['attempts'])

        if auth_otp.is_expired():
            messages.error(request, "Verification code has expired. Please request a new one.")
            return redirect('forgot_password')

        if entered_otp != auth_otp.otp_code:
            messages.error(request, "Invalid verification code.")
        elif not new_password or not confirm_password:
            messages.error(request, "Please enter and confirm your new password.")
        elif len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
        elif new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            auth_otp.is_verified = True
            auth_otp.save(update_fields=['is_verified'])

            user = auth_otp.user
            user.set_password(new_password)
            user.save()

            messages.success(request, "Password reset successful! You can now log in with your new password.")
            return redirect('login')

    return render(request, 'accounts/otp_verify_password_reset.html', {'auth_otp': auth_otp})



# ==========================================
# OTP Verification Views
# ==========================================

def verify_registration_otp_view(request, pk):
    """Verifies the email OTP sent during registration."""
    auth_otp = get_object_or_404(AuthOTP, pk=pk, otp_type='registration')
    
    if auth_otp.is_verified:
        return redirect('login')
        
    if request.method == 'POST':
        entered_otp = request.POST.get('otp_code', '').strip()
        
        # Guard clause: Too many attempts
        if auth_otp.attempts >= 5:
            messages.error(request, "Too many failed attempts. Please register again.")
            return redirect('register')
            
        auth_otp.attempts += 1
        auth_otp.save(update_fields=['attempts'])
        
        # Guard clause: Expired OTP
        if auth_otp.is_expired():
            messages.error(request, "OTP Expired. Please request a new OTP or register again.")
            return redirect('verify_registration_otp', pk=auth_otp.pk)
            
        # Success logic
        if entered_otp == auth_otp.otp_code:
            auth_otp.is_verified = True
            auth_otp.save(update_fields=['is_verified'])
            
            user = auth_otp.user
            user.is_active = True
            user.save()
            
            # Use our new helper instead of inline logic
            notify_admins_of_new_user(user, user.role)
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Account verified successfully! Welcome, {user.username}.")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Invalid OTP code.")
            
    return render(request, 'accounts/otp_verify_registration.html', {'auth_otp': auth_otp})


