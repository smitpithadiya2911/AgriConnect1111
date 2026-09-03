from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Farmer, Buyer

class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    
    # Common location details
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}))
    state = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}))
    pincode = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}))

    # Farmer specific fields
    farm_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Farm Name'}))
    farm_location = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Farm Address'}))
    farm_size = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Farm Size (e.g. 5 Acres)'}))
    village = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Village'}))
    farming_experience = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Farming Experience (e.g. 5 Years)'}))
    crops_grown = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Main Crops Grown (e.g. Tomato, Rice)'}))
    
    # Document uploads
    aadhaar_document = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    farm_certificate = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    organic_certificate = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'phone', 'address', 'profile_picture']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        role = cleaned_data.get("role")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        if role == 'farmer':
            if not cleaned_data.get("farm_name"):
                self.add_error('farm_name', "Farm name is required for Farmers.")
            if not cleaned_data.get("farm_location"):
                self.add_error('farm_location', "Farm address is required for Farmers.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            if user.role == 'farmer':
                has_docs = bool(self.cleaned_data.get('aadhaar_document') or self.cleaned_data.get('farm_certificate'))
                Farmer.objects.create(
                    user=user,
                    farm_name=self.cleaned_data.get('farm_name'),
                    farm_location=self.cleaned_data.get('farm_location'),
                    farm_size=self.cleaned_data.get('farm_size'),
                    village=self.cleaned_data.get('village'),
                    city=self.cleaned_data.get('city'),
                    state=self.cleaned_data.get('state'),
                    pincode=self.cleaned_data.get('pincode'),
                    experience=self.cleaned_data.get('farming_experience') or '5 Years',
                    specialization=self.cleaned_data.get('crops_grown') or 'General Farming',
                    aadhaar_document=self.cleaned_data.get('aadhaar_document'),
                    farm_certificate=self.cleaned_data.get('farm_certificate'),
                    organic_certificate=self.cleaned_data.get('organic_certificate'),
                    verification_status='review' if has_docs else 'pending'
                )
            elif user.role == 'buyer':
                Buyer.objects.create(
                    user=user,
                    delivery_address=user.address,
                    contact_name=user.username,
                    city=self.cleaned_data.get('city'),
                    state=self.cleaned_data.get('state'),
                    pincode=self.cleaned_data.get('pincode')
                )
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'phone', 'address', 'profile_picture']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }


class FarmerProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Farmer
        fields = ['farm_name', 'farm_location', 'farm_size']
        widgets = {
            'farm_name': forms.TextInput(attrs={'class': 'form-control'}),
            'farm_location': forms.TextInput(attrs={'class': 'form-control'}),
            'farm_size': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BuyerProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Buyer
        fields = ['delivery_address', 'contact_name']
        widgets = {
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
