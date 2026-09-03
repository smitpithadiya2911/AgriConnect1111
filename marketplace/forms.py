from django import forms
from .models import Crop, Review, Feedback, Order, FarmerRating

class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = ['category', 'name', 'description', 'price_per_kg', 'quantity_available', 'unit', 'image', 'availability_status', 'harvest_date', 'shelf_life_days']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Crop Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Crop Description'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Price per unit'}),
            'quantity_available': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Quantity available'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'availability_status': forms.Select(attrs={'class': 'form-select'}),
            'harvest_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'shelf_life_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Shelf life (in days)'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment', 'image']
        widgets = {
            'rating': forms.Select(choices=[(i, f"{i} Stars") for i in range(5, 0, -1)], attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title of your review (e.g. Excellent fresh vegetables!)'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Share your experience with this product...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class FarmerRatingForm(forms.ModelForm):
    class Meta:
        model = FarmerRating
        fields = ['rating', 'quality_rating', 'communication_rating', 'delivery_rating', 'packaging_rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f"{i} Stars") for i in range(5, 0, -1)], attrs={'class': 'form-select'}),
            'quality_rating': forms.Select(choices=[(i, f"{i} Stars") for i in range(5, 0, -1)], attrs={'class': 'form-select'}),
            'communication_rating': forms.Select(choices=[(i, f"{i} Stars") for i in range(5, 0, -1)], attrs={'class': 'form-select'}),
            'delivery_rating': forms.Select(choices=[(i, f"{i} Stars") for i in range(5, 0, -1)], attrs={'class': 'form-select'}),
            'packaging_rating': forms.Select(choices=[(i, f"{i} Stars") for i in range(5, 0, -1)], attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Share your feedback on the farmer...'}),
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['subject', 'message']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject of Complaint/Feedback'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your issue or feedback in detail...'}),
        }


class CheckoutForm(forms.Form):
    PAYMENT_CHOICES = (
        ('COD', 'Cash on Delivery'),
        ('Online', 'Debit / Credit Card / UPI (Simulated Online)'),
    )
    shipping_address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Complete shipping address'}),
        required=True
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=True,
        initial='COD'
    )
    card_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1234 5678 9012 3456'})
    )
    card_expiry = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'MM/YY'})
    )
    card_cvv = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '123'})
    )

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        if payment_method == 'Online':
            if not cleaned_data.get('card_number'):
                self.add_error('card_number', 'Card number is required for online payments.')
            if not cleaned_data.get('card_expiry'):
                self.add_error('card_expiry', 'Card expiry date is required.')
            if not cleaned_data.get('card_cvv'):
                self.add_error('card_cvv', 'CVV is required.')
        return cleaned_data


class ChatMessageForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Type your message here...',
            'style': 'resize: none; border-radius: 12px;'
        }),
        required=True
    )


class AdvancedCropRecommendationForm(forms.Form):
    SOIL_CHOICES = (
        ('Loamy', 'Loamy'),
        ('Clayey', 'Clayey'),
        ('Sandy', 'Sandy'),
        ('Alluvial', 'Alluvial'),
        ('Red', 'Red Soil'),
        ('Black', 'Black Soil'),
    )
    soil_type = forms.ChoiceField(choices=SOIL_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    soil_ph = forms.FloatField(min_value=4.0, max_value=9.0, initial=6.5, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}))
    nitrogen = forms.FloatField(min_value=0.0, max_value=150.0, initial=50.0, label='Nitrogen (N) kg/ha', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    phosphorus = forms.FloatField(min_value=0.0, max_value=150.0, initial=40.0, label='Phosphorus (P) kg/ha', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    potassium = forms.FloatField(min_value=0.0, max_value=150.0, initial=40.0, label='Potassium (K) kg/ha', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    temperature = forms.FloatField(min_value=-10.0, max_value=50.0, initial=25.0, label='Average Temp (°C)', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    rainfall = forms.FloatField(min_value=0.0, max_value=3000.0, initial=800.0, label='Annual Rainfall (mm)', widget=forms.NumberInput(attrs={'class': 'form-control'}))

