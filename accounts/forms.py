from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Farmer, Buyer

class StyledModelForm(forms.ModelForm):
    """Base form to automatically apply Bootstrap classes."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-select' if isinstance(field.widget, forms.Select) else 'form-control')

class CustomUserCreationForm(StyledModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}))
    
    # Common location details
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'City'}))
    state = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'State'}))
    pincode = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Pincode'}))

    # Farmer specific fields
    farm_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Farm Name'}))
    farm_location = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Farm Address'}))
    farm_size = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Farm Size (e.g. 5 Acres)'}))
    village = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Village'}))
    farming_experience = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Farming Experience (e.g. 5 Years)'}))
    crops_grown = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Main Crops Grown (e.g. Tomato, Rice)'}))
    
    # Document uploads
    aadhaar_document = forms.FileField(required=False)
    farm_certificate = forms.FileField(required=False)
    organic_certificate = forms.FileField(required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'phone', 'address', 'profile_picture']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Full Address'}),
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


class UserUpdateForm(StyledModelForm):
    class Meta:
        model = User
        fields = ['email', 'phone', 'address', 'profile_picture']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class FarmerProfileUpdateForm(StyledModelForm):
    class Meta:
        model = Farmer
        fields = ['farm_name', 'farm_location', 'farm_size']


class BuyerProfileUpdateForm(StyledModelForm):
    class Meta:
        model = Buyer
        fields = ['delivery_address', 'contact_name']
        widgets = {
            'delivery_address': forms.Textarea(attrs={'rows': 3}),
        }
