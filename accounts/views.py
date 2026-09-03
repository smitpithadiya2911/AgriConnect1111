from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, UserUpdateForm, FarmerProfileUpdateForm, BuyerProfileUpdateForm
from .models import Farmer, Buyer

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created successfully for {user.username}! You can now login.")
            return redirect('login')
        else:
            messages.error(request, "There was an error in registration. Please check the details below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    if request.method == 'POST':
        # Make request.POST data mutable to resolve email to username before form validation
        post_data = request.POST.copy()
        username_or_email = post_data.get('username', '')
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                post_data['username'] = user_obj.username
            except User.DoesNotExist:
                pass

        form = AuthenticationForm(request, data=post_data)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('dashboard_redirect')
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


@login_required
def dashboard_redirect_view(request):
    if request.user.is_superuser or request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'farmer':
        return redirect('farmer_dashboard')
    elif request.user.role == 'buyer':
        return redirect('buyer_dashboard')
    else:
        return redirect('select_role')


@login_required
def select_role_view(request):
    if request.user.role in ['buyer', 'farmer', 'admin']:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        selected_role = request.POST.get('role')
        if selected_role in ['buyer', 'farmer']:
            request.user.role = selected_role
            request.user.save()

            if selected_role == 'buyer':
                Buyer.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'contact_name': request.user.get_full_name() or request.user.username,
                        'delivery_address': request.user.address or ''
                    }
                )
            elif selected_role == 'farmer':
                Farmer.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'farm_name': f"{request.user.username}'s Farm"
                    }
                )
            messages.success(request, f"Welcome to AgriConnect as a {selected_role.capitalize()}!")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Please select a valid role to proceed.")

    return render(request, 'accounts/select_role.html')



@login_required
def profile_view(request):
    user = request.user
    
    # Forms initialization
    u_form = UserUpdateForm(instance=user)
    p_form = None
    
    if user.role == 'farmer':
        farmer_profile, created = Farmer.objects.get_or_create(user=user)
        p_form = FarmerProfileUpdateForm(instance=farmer_profile)
    elif user.role == 'buyer':
        buyer_profile, created = Buyer.objects.get_or_create(user=user)
        p_form = BuyerProfileUpdateForm(instance=buyer_profile)
        
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if user.role == 'farmer':
            farmer_profile = Farmer.objects.get(user=user)
            p_form = FarmerProfileUpdateForm(request.POST, instance=farmer_profile)
        elif user.role == 'buyer':
            buyer_profile = Buyer.objects.get(user=user)
            p_form = BuyerProfileUpdateForm(request.POST, instance=buyer_profile)
            
        if u_form.is_valid() and (p_form is None or p_form.is_valid()):
            u_form.save()
            if p_form:
                p_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
            
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'role': user.role
    }
    return render(request, 'accounts/profile.html', context)
