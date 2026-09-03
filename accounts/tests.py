from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Farmer, Buyer

User = get_user_model()

class UserRegistrationAndRoleTests(TestCase):
    def test_create_custom_user(self):
        user = User.objects.create_user(
            username='testbuyer',
            email='buyer@test.com',
            password='testpassword123',
            role='buyer',
            phone='1112223333',
            address='123 Test St'
        )
        self.assertEqual(user.username, 'testbuyer')
        self.assertEqual(user.role, 'buyer')
        self.assertTrue(user.is_buyer())
        self.assertFalse(user.is_farmer())
        self.assertFalse(user.is_admin())

    def test_create_farmer_profile(self):
        user = User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpassword123',
            role='farmer'
        )
        farmer = Farmer.objects.create(
            user=user,
            farm_name='Test Orchard',
            farm_location='West region',
            farm_size='10 Acres'
        )
        self.assertEqual(farmer.farm_name, 'Test Orchard')
        self.assertEqual(farmer.user.role, 'farmer')
        self.assertTrue(user.is_farmer())

    def test_create_buyer_profile(self):
        user = User.objects.create_user(
            username='testbuyer2',
            email='buyer2@test.com',
            password='testpassword123',
            role='buyer'
        )
        buyer = Buyer.objects.create(
            user=user,
            delivery_address='456 Shipping Lane',
            contact_name='Alex'
        )
        self.assertEqual(buyer.contact_name, 'Alex')
        self.assertEqual(buyer.user.role, 'buyer')
        self.assertTrue(user.is_buyer())

    def test_onboarding_form_registration(self):
        from accounts.forms import CustomUserCreationForm
        # Mock file inputs
        aadhaar = SimpleUploadedFile("aadhaar.pdf", b"file_content", content_type="application/pdf")
        cert = SimpleUploadedFile("cert.pdf", b"file_content", content_type="application/pdf")
        
        data = {
            'username': 'onboardedfarmer',
            'email': 'onboarded@farmer.com',
            'phone': '9998887777',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
            'role': 'farmer',
            'address': 'Farm Road 10',
            'city': 'Rajkot',
            'state': 'Gujarat',
            'pincode': '360001',
            'farm_name': 'Green Fields',
            'farm_location': 'Green Fields Farm',
            'farm_size': '8 Acres',
            'village': 'Madhapar',
            'farming_experience': '8 Years',
            'crops_grown': 'Tomato, Onion',
        }
        files = {
            'aadhaar_document': aadhaar,
            'farm_certificate': cert,
        }
        form = CustomUserCreationForm(data=data, files=files)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        
        self.assertEqual(user.username, 'onboardedfarmer')
        self.assertEqual(user.farmer_profile.farm_name, 'Green Fields')
        self.assertEqual(user.farmer_profile.village, 'Madhapar')
        self.assertEqual(user.farmer_profile.experience, '8 Years')
        self.assertEqual(user.farmer_profile.specialization, 'Tomato, Onion')
        self.assertEqual(user.farmer_profile.verification_status, 'review')

    def test_dual_login_email(self):
        # Create user
        User.objects.create_user(
            username='dualloginuser',
            email='dual@login.com',
            password='testpassword123',
            role='buyer'
        )
        
        # Log in with email address
        response = self.client.post('/login/', {
            'username': 'dual@login.com',
            'password': 'testpassword123'
        })
        # Resolves email to username, welcomes back, redirects to dashboard
        self.assertEqual(response.status_code, 302)

    def test_password_reset_flow(self):
        from django.core import mail
        # Create user
        User.objects.create_user(
            username='resetuser',
            email='reset@user.com',
            password='oldpassword123',
            role='buyer'
        )
        
        # Request password reset
        response = self.client.post('/password-reset/', {
            'email': 'reset@user.com'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/password-reset/done/')
        
        # Verify email was generated and placed in outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("AgriConnect - Password Reset Instructions", mail.outbox[0].subject)
        self.assertIn("reset@user.com", mail.outbox[0].to)
