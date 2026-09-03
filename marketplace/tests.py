from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Farmer
from .models import Category, Crop, CartItem, Order, OrderItem, Notification, Wishlist, FavoriteFarmer, FarmerRating, Review, Report

User = get_user_model()

class MarketplaceCoreTests(TestCase):
    def setUp(self):
        # Setup farmer
        self.farmer_user = User.objects.create_user(
            username='testfarmer', password='password123', role='farmer'
        )
        self.farmer_profile = Farmer.objects.create(
            user=self.farmer_user, farm_name='Test Farms', farm_location='North'
        )
        
        # Setup buyer
        self.buyer_user = User.objects.create_user(
            username='testbuyer', password='password123', role='buyer', address='123 Test Road'
        )
        
        # Setup category
        self.category = Category.objects.create(name='Fruits', description='Orchard items')
        
        # Setup crop listing
        self.crop = Crop.objects.create(
            farmer=self.farmer_profile,
            category=self.category,
            name='Oranges',
            description='Fresh sweet oranges',
            price_per_kg=2.50,
            quantity_available=100.00,
            unit='kg',
            is_approved=True,
            availability_status='available'
        )

    def test_crop_creation(self):
        self.assertEqual(self.crop.name, 'Oranges')
        self.assertEqual(self.crop.price_per_kg, 2.50)
        self.assertTrue(self.crop.is_approved)

    def test_cart_operations(self):
        cart_item = CartItem.objects.create(
            user=self.buyer_user,
            crop=self.crop,
            quantity=5
        )
        self.assertEqual(cart_item.total_price(), 12.50)
        self.assertEqual(self.buyer_user.cart_items.count(), 1)

    def test_order_checkout_flow(self):
        # Add to cart
        CartItem.objects.create(
            user=self.buyer_user,
            crop=self.crop,
            quantity=10
        )
        
        cart_items = CartItem.objects.filter(user=self.buyer_user)
        total = sum(item.total_price() for item in cart_items)
        
        # Simulated Checkout View Logic
        order = Order.objects.create(
            buyer=self.buyer_user,
            farmer=self.farmer_profile,
            total_amount=total,
            payment_method='COD',
            status='Pending',
            shipping_address=self.buyer_user.address
        )
        
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                crop=item.crop,
                quantity=item.quantity,
                price_per_unit=item.crop.price_per_kg
            )
            item.crop.quantity_available -= item.quantity
            item.crop.save()
            
        cart_items.delete()
        
        # Verification
        self.assertEqual(self.buyer_user.cart_items.count(), 0)
        self.assertEqual(Order.objects.filter(buyer=self.buyer_user).count(), 1)
        self.assertEqual(order.items.count(), 1)
        
        # Stock reduction check
        self.crop.refresh_from_db()
        self.assertEqual(self.crop.quantity_available, 90.00)

    def test_chat_message_creation(self):
        from .models import ChatMessage
        msg = ChatMessage.objects.create(
            sender=self.buyer_user,
            receiver=self.farmer_user,
            crop=self.crop,
            message="Is this price negotiable?"
        )
        self.assertEqual(msg.message, "Is this price negotiable?")
        self.assertEqual(msg.sender, self.buyer_user)
        self.assertEqual(msg.receiver, self.farmer_user)
        self.assertFalse(msg.is_read)

    def test_chat_list_unauthenticated(self):
        response = self.client.get('/chat/')
        self.assertEqual(response.status_code, 302) # Redirect to login

    def test_invoice_pdf_generation(self):
        # Create an order
        order = Order.objects.create(
            buyer=self.buyer_user,
            farmer=self.farmer_profile,
            total_amount=50.00,
            payment_method='COD',
            status='Pending',
            shipping_address=self.buyer_user.address
        )
        OrderItem.objects.create(
            order=order,
            crop=self.crop,
            quantity=20,
            price_per_unit=self.crop.price_per_kg
        )
        
        # Unauthenticated check
        response = self.client.get(f'/orders/{order.id}/invoice/pdf/')
        self.assertEqual(response.status_code, 302) # Redirect to login
        
        # Authenticated check (Buyer)
        self.client.login(username='testbuyer', password='password123')
        response = self.client.get(f'/orders/{order.id}/invoice/pdf/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(len(response.content) > 0)

    def test_notification_center_operations(self):
        # Create notifications
        notif1 = Notification.objects.create(
            user=self.buyer_user,
            message="Alert 1",
            notification_type="order",
            priority="high"
        )
        notif2 = Notification.objects.create(
            user=self.buyer_user,
            message="Alert 2",
            notification_type="weather",
            priority="low"
        )
        
        self.client.login(username='testbuyer', password='password123')
        
        # Test notification listing
        response = self.client.get('/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alert 1")
        self.assertContains(response, "Alert 2")
        
        # Test category filtering
        response = self.client.get('/notifications/?type=order')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['notifications']), 1)
        self.assertEqual(response.context['notifications'][0].message, "Alert 1")
        
        # Test mark read
        response = self.client.get(f'/notifications/{notif1.id}/mark-read/')
        self.assertEqual(response.status_code, 302)
        notif1.refresh_from_db()
        self.assertTrue(notif1.is_read)
        
        # Test delete
        response = self.client.post(f'/notifications/{notif2.id}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Notification.objects.filter(id=notif2.id).exists())

    def test_farmer_verification_workflow(self):
        # Create a mock file upload
        from django.core.files.uploadedfile import SimpleUploadedFile
        aadhaar_file = SimpleUploadedFile("aadhaar.pdf", b"file_content", content_type="application/pdf")
        cert_file = SimpleUploadedFile("certificate.pdf", b"file_content", content_type="application/pdf")
        
        # Login as farmer
        self.client.login(username='testfarmer', password='password123')
        
        # Submit verification
        response = self.client.post('/farmer/verify/', {
            'aadhaar_document': aadhaar_file,
            'farm_certificate': cert_file
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify status updated
        self.farmer_profile.refresh_from_db()
        self.assertEqual(self.farmer_profile.verification_status, 'review')
        
        # Setup admin
        admin_user = User.objects.create_user(
            username='admin', password='password123', role='admin'
        )
        
        # Login as admin to approve
        self.client.login(username='admin', password='password123')
        
        # Approve farmer
        response = self.client.post(f'/admin/farmers/{self.farmer_profile.id}/verify/', {
            'action': 'approve',
            'admin_notes': 'Documents look genuine!'
        })
        self.assertEqual(response.status_code, 302)
        
        self.farmer_profile.refresh_from_db()
        self.assertEqual(self.farmer_profile.verification_status, 'approved')
        self.assertEqual(self.farmer_profile.trust_score, 95)

    def test_wishlist_and_favorites_operations(self):
        self.client.login(username='testbuyer', password='password123')
        
        # Toggle wishlist (adds product)
        response = self.client.get(f'/wishlist/toggle/{self.crop.id}/')
        self.assertEqual(response.status_code, 302)
        
        # Verify wishlist item exists
        self.assertTrue(Wishlist.objects.filter(user=self.buyer_user, crop=self.crop).exists())
        
        # Move to cart
        w_item = Wishlist.objects.get(user=self.buyer_user, crop=self.crop)
        response = self.client.get(f'/wishlist/move-to-cart/{w_item.id}/')
        self.assertEqual(response.status_code, 302)
        
        # Verify cart item exists and wishlist item is deleted
        self.assertTrue(CartItem.objects.filter(user=self.buyer_user, crop=self.crop).exists())
        self.assertFalse(Wishlist.objects.filter(id=w_item.id).exists())
        
        # Follow grower
        response = self.client.get(f'/farmers/follow/{self.farmer_profile.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FavoriteFarmer.objects.filter(buyer=self.buyer_user, farmer=self.farmer_profile).exists())

    def test_advanced_search_and_filtering(self):
        # We have self.crop (Oranges, Fruits category, 2.50 price, North location)
        # Setup another crop (Apples, Fruits category, 4.00 price, organic name)
        crop2 = Crop.objects.create(
            farmer=self.farmer_profile,
            category=self.category,
            name='Organic Apples',
            description='Tasty red organic apples',
            price_per_kg=4.00,
            quantity_available=50.00,
            unit='kg',
            is_approved=True,
            availability_status='available'
        )
        
        # Test query searching
        response = self.client.get('/crops/?q=Apples')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['crops']), 1)
        self.assertEqual(response.context['crops'][0].name, 'Organic Apples')
        
        # Test price limits filtering
        response = self.client.get('/crops/?min_price=3.00&max_price=5.00')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['crops']), 1)
        self.assertEqual(response.context['crops'][0].name, 'Organic Apples')
        
        # Test farmer type filtering (organic)
        response = self.client.get('/crops/?farmer_type=organic')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['crops']), 1)

        # Test pagination: create 10 crops, verify page 1 lists 6 items, page 2 has remaining items
        for i in range(10):
            Crop.objects.create(
                farmer=self.farmer_profile,
                category=self.category,
                name=f'Crop {i}',
                description='desc',
                price_per_kg=1.00,
                quantity_available=10.00,
                unit='kg',
                is_approved=True,
                availability_status='available'
            )
            
        response = self.client.get('/crops/')
        self.assertEqual(response.status_code, 200)
        # crops context parameter is now a Page object containing 6 crops
        self.assertEqual(len(response.context['crops']), 6)
        
        response = self.client.get('/crops/?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context['crops']) > 0)

    def test_reviews_and_ratings_system(self):
        # Create a Review with title and votes
        review = Review.objects.create(
            buyer=self.buyer_user,
            crop=self.crop,
            rating=5,
            title='Very Fresh!',
            comment='Super fresh oranges.'
        )
        
        # Test helpful toggle
        self.client.login(username='testbuyer', password='password123')
        response = self.client.get(f'/reviews/{review.id}/helpful/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(review.helpful_votes.count(), 1)
        
        # Test farmer reply
        self.client.login(username='testfarmer', password='password123')
        response = self.client.post(f'/reviews/{review.id}/reply/', {
            'reply': 'Thank you for your review!'
        })
        self.assertEqual(response.status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.reply, 'Thank you for your review!')
        
        # Setup delivered order to allow farmer rating
        order = Order.objects.create(
            buyer=self.buyer_user,
            farmer=self.farmer_profile,
            total_amount=50.00,
            payment_method='COD',
            status='Delivered'
        )
        
        # Test rate farmer
        self.client.login(username='testbuyer', password='password123')
        response = self.client.post(f'/farmer/{self.farmer_profile.id}/rate/', {
            'rating': 5,
            'quality_rating': 5,
            'communication_rating': 5,
            'delivery_rating': 5,
            'packaging_rating': 5,
            'comment': 'Great grower!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FarmerRating.objects.filter(buyer=self.buyer_user, farmer=self.farmer_profile).exists())

    def test_reports_center(self):
        # Log in as buyer
        self.client.login(username='testbuyer', password='password123')
        
        # Access reports dashboard
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Business Intelligence')
        
        # Generate a report
        response = self.client.post('/reports/generate/', {
            'report_type': 'order',
            'format': 'csv',
            'date_range': '7d',
            'scheduled_interval': ''
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify Report model record creation
        report = Report.objects.filter(generated_by=self.buyer_user).first()
        self.assertIsNotNone(report)
        self.assertEqual(report.report_type, 'order')
        self.assertEqual(report.format, 'csv')
        self.assertIsNone(report.scheduled_interval)
        
        # Download the report
        response = self.client.get(f'/reports/{report.id}/download/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/csv')
        report.refresh_from_db()
        self.assertEqual(report.download_count, 1)
        
        # Delete the report
        response = self.client.get(f'/reports/{report.id}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Report.objects.filter(id=report.id).exists())

    def test_wishlist_features(self):
        # Log in as buyer
        self.client.login(username='testbuyer', password='password123')
        
        # 1. Toggle wishlist (Add)
        response = self.client.get(f'/wishlist/toggle/{self.crop.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Wishlist.objects.filter(user=self.buyer_user, crop=self.crop).exists())
        
        # 2. Access wishlist page
        response = self.client.get('/wishlist/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.crop.name)
        
        # 3. Move to Cart
        wishlist_item = Wishlist.objects.get(user=self.buyer_user, crop=self.crop)
        response = self.client.get(f'/wishlist/move-to-cart/{wishlist_item.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Wishlist.objects.filter(user=self.buyer_user, crop=self.crop).exists())
        self.assertTrue(CartItem.objects.filter(user=self.buyer_user, crop=self.crop).exists())
        
        # 4. Toggle back on & Remove
        self.client.get(f'/wishlist/toggle/{self.crop.id}/')
        wishlist_item = Wishlist.objects.get(user=self.buyer_user, crop=self.crop)
        response = self.client.get(f'/wishlist/remove/{wishlist_item.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Wishlist.objects.filter(user=self.buyer_user, crop=self.crop).exists())

    def test_smart_delivery_eligibility(self):
        from datetime import date
        from accounts.models import Buyer
        
        # Set farmer profile city/state to check same/diff locations
        self.farmer_profile.city = 'Rajkot'
        self.farmer_profile.state = 'Gujarat'
        self.farmer_profile.save()

        # Set buyer profile city/state
        buyer_profile, _ = Buyer.objects.get_or_create(
            user=self.buyer_user,
            defaults={'delivery_address': self.buyer_user.address, 'contact_name': self.buyer_user.username}
        )
        buyer_profile.city = 'Rajkot'
        buyer_profile.state = 'Gujarat'
        buyer_profile.save()

        # Crop 1: Fresh spinach (2 days shelf life) from same city
        spinach = Crop.objects.create(
            farmer=self.farmer_profile,
            category=self.crop.category,
            name='Spinach Same City',
            description='Fresh green spinach',
            price_per_kg=30.00,
            quantity_available=100,
            unit='kg',
            is_approved=True,
            harvest_date=date.today(),
            shelf_life_days=2
        )
        # Same city estimated delivery is 1 day. Spinach remaining life is 2 days.
        self.assertEqual(spinach.estimated_delivery_days(buyer_profile), 1)
        self.assertTrue(spinach.is_eligible_for_delivery(buyer_profile))

        # Crop 2: Fresh spinach (2 days shelf life) from different state
        buyer_profile.city = 'Bangalore'
        buyer_profile.state = 'Karnataka'
        buyer_profile.save()
        # Interstate estimated delivery is 4 days. Spinach remaining life is 2 days.
        self.assertEqual(spinach.estimated_delivery_days(buyer_profile), 4)
        self.assertFalse(spinach.is_eligible_for_delivery(buyer_profile))

        # Try to add Crop 2 (ineligible) to cart
        self.client.login(username='testbuyer', password='password123')
        response = self.client.post(f'/cart/add/{spinach.id}/', {'quantity': 1})
        self.assertEqual(response.status_code, 302)
        # Verify it wasn't added to cart
        self.assertFalse(CartItem.objects.filter(user=self.buyer_user, crop=spinach).exists())



