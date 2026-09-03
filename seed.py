import os
import django
import shutil
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agriconnect_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Farmer, Buyer
from marketplace.models import Category, Crop, PriceTrend, Review, Notification

User = get_user_model()

def seed_db():
    print("Starting database seeding with 5 realistic Indian farmer profiles...")

    # Ensure media/crops directory exists
    media_crops_dir = os.path.join('media', 'crops')
    os.makedirs(media_crops_dir, exist_ok=True)
    
    # Copy images from static to media/crops
    static_crops_dir = os.path.join('static', 'images', 'crops')
    
    image_filenames = [
        "tomato.jpg", "potato.jpg", "onion.jpg", "chili_green.jpg", "cabbage.jpg",
        "mango.jpg", "banana.jpg", "apple.jpg", "orange.jpg", "watermelon.jpg",
        "wheat.jpg", "rice.jpg", "corn.jpg", "millet.jpg", "barley.jpg",
        "chickpea.jpg", "moong.jpg", "urad.jpg", "toor.jpg", "masoor.jpg",
        "organic_tomato.jpg", "cucumber.jpg", "spinach.jpg", "carrot.jpg", "broccoli.jpg",
        "milk.jpg", "curd.jpg", "butter.jpg", "paneer.jpg", "cheese.jpg",
        "turmeric.jpg", "red_chili.jpg", "coriander.jpg", "cumin.jpg", "black_pepper.jpg",
        "wheat_seeds.jpg", "rice_seeds.jpg", "corn_seeds.jpg", "vegetable_seeds.jpg", "sunflower_seeds.jpg"
    ]
    
    for filename in image_filenames:
        src_path = os.path.join(static_crops_dir, filename)
        dest_path = os.path.join(media_crops_dir, filename)
        if os.path.exists(src_path):
            shutil.copy(src_path, dest_path)

    # 1. Create Users
    # Admin
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@agriconnect.org',
            'role': 'admin',
            'is_superuser': True,
            'is_staff': True,
            'phone': '9998887770',
            'address': 'AgriConnect Headquarters, Bangalore'
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()

    # Create the 5 Farmer Users & Profiles
    farmers_spec = [
        {
            'username': 'ramesh_patel',
            'name': 'Ramesh Patel',
            'email': 'ramesh@agriconnect.org',
            'phone': '9812345671',
            'address': 'Plot 45, Rajkot Farm Colony, Gujarat',
            'farm_name': 'Green Valley Farms',
            'farm_location': 'Rajkot, Gujarat, India',
            'farm_size': '25 Acres',
            'experience': '15 Years',
            'orders_completed': 150,
            'store_rating': 4.8,
            'specialization': 'Fresh Vegetables',
            'about': 'Experienced vegetable farmer with 15 years of farming expertise. Producing fresh, chemical-safe vegetables directly from farm to consumers.',
            'certifications': 'Organic Certified, ISO 22000, FSSAI Approved',
            'awards': 'Gujarat Krishi Ratna 2024, Best Vegetable Producer Award',
            'repeat_customers': 88,
            'ontime_delivery': 99,
            'satisfaction_rate': 98,
            'cover_banner': 'crops/tomato.jpg'
        },
        {
            'username': 'suresh_kumar',
            'name': 'Suresh Kumar',
            'email': 'suresh@agriconnect.org',
            'phone': '9812345672',
            'address': 'Grains Sector 4, Ludhiana Rural, Punjab',
            'farm_name': 'Fresh Harvest Farm',
            'farm_location': 'Ludhiana, Punjab, India',
            'farm_size': '18 Acres',
            'experience': '12 Years',
            'orders_completed': 120,
            'store_rating': 4.7,
            'specialization': 'Grains',
            'about': 'Dedicated grain producer specializing in wheat and rice cultivation using modern farming techniques.',
            'certifications': 'Certified Seed Producer, APMC Registered Seller',
            'awards': 'Punjab Progressive Farmer Award 2025',
            'repeat_customers': 75,
            'ontime_delivery': 98,
            'satisfaction_rate': 96,
            'cover_banner': 'crops/wheat.jpg'
        },
        {
            'username': 'mahesh_singh',
            'name': 'Mahesh Singh',
            'email': 'mahesh@agriconnect.org',
            'phone': '9812345673',
            'address': 'Eco Farm Path, Jaipur Rural, Rajasthan',
            'farm_name': 'Organic Earth Farm',
            'farm_location': 'Jaipur, Rajasthan, India',
            'farm_size': '30 Acres',
            'experience': '10 Years',
            'orders_completed': 210,
            'store_rating': 4.9,
            'specialization': 'Organic Products',
            'about': 'Certified organic farmer promoting sustainable agriculture and chemical-free food production.',
            'certifications': 'NPOP Organic India Certificate, PGS Organic Status',
            'awards': 'Organic Farming Champion Rajasthan 2024',
            'repeat_customers': 92,
            'ontime_delivery': 97,
            'satisfaction_rate': 99,
            'cover_banner': 'crops/organic_tomato.jpg'
        },
        {
            'username': 'rajesh_verma',
            'name': 'Rajesh Verma',
            'email': 'rajesh@agriconnect.org',
            'phone': '9812345674',
            'address': 'Orchard Lane 10, Nashik Valley, Maharashtra',
            'farm_name': 'Sunrise Agriculture',
            'farm_location': 'Nashik, Maharashtra, India',
            'farm_size': '22 Acres',
            'experience': '8 Years',
            'orders_completed': 175,
            'store_rating': 4.8,
            'specialization': 'Fruits',
            'about': 'Fruit cultivation expert producing premium-quality grapes, mangoes, and seasonal fruits.',
            'certifications': 'Good Agricultural Practices (GAP), APMC Certified Orchardist',
            'awards': 'Maharashtra Fruits Export Excellence Award',
            'repeat_customers': 82,
            'ontime_delivery': 96,
            'satisfaction_rate': 97,
            'cover_banner': 'crops/orange.jpg'
        },
        {
            'username': 'amit_chauhan',
            'name': 'Amit Chauhan',
            'email': 'amit@agriconnect.org',
            'phone': '9812345675',
            'address': 'Seed Center Road, Karnal District, Haryana',
            'farm_name': 'Golden Crop Farms',
            'farm_location': 'Karnal, Haryana, India',
            'farm_size': '20 Acres',
            'experience': '14 Years',
            'orders_completed': 140,
            'store_rating': 4.7,
            'specialization': 'Seeds & Pulses',
            'about': 'Specialized in certified seeds and high-quality pulse production for farmers and buyers.',
            'certifications': 'National Seed Association Certificate, Certified Breeder Status',
            'awards': 'Haryana Krishi Vigyan Kendra Excellence Award',
            'repeat_customers': 80,
            'ontime_delivery': 99,
            'satisfaction_rate': 98,
            'cover_banner': 'crops/sunflower_seeds.jpg'
        }
    ]

    farmer_profiles = {}
    for spec in farmers_spec:
        user, created = User.objects.get_or_create(
            username=spec['username'],
            defaults={
                'email': spec['email'],
                'role': 'farmer',
                'phone': spec['phone'],
                'address': spec['address']
            }
        )
        if created:
            user.set_password('farmer123')
            user.save()
            
        profile, p_created = Farmer.objects.get_or_create(
            user=user,
            defaults={
                'farm_name': spec['farm_name'],
                'farm_location': spec['farm_location'],
                'farm_size': spec['farm_size'],
                'certification_status': 'verified',
                'experience': spec['experience'],
                'orders_completed': spec['orders_completed'],
                'store_rating': spec['store_rating'],
                'specialization': spec['specialization'],
                'about': spec['about'],
                'cover_banner': spec['cover_banner'],
                'certifications': spec['certifications'],
                'awards': spec['awards'],
                'repeat_customers': spec['repeat_customers'],
                'ontime_delivery': spec['ontime_delivery'],
                'satisfaction_rate': spec['satisfaction_rate']
            }
        )
        profile.farm_name = spec['farm_name']
        profile.farm_location = spec['farm_location']
        profile.farm_size = spec['farm_size']
        profile.experience = spec['experience']
        profile.orders_completed = spec['orders_completed']
        profile.store_rating = spec['store_rating']
        profile.specialization = spec['specialization']
        profile.about = spec['about']
        profile.cover_banner = spec['cover_banner']
        profile.certifications = spec['certifications']
        profile.awards = spec['awards']
        profile.repeat_customers = spec['repeat_customers']
        profile.ontime_delivery = spec['ontime_delivery']
        profile.satisfaction_rate = spec['satisfaction_rate']
        profile.save()
        
        farmer_profiles[spec['username']] = profile
        print(f"Farmer '{spec['name']}' verified/created with DB fields.")

    # Buyer
    buyer_user, created = User.objects.get_or_create(
        username='buyer',
        defaults={
            'email': 'buyer@agriconnect.org',
            'role': 'buyer',
            'phone': '8887776660',
            'address': 'Flat 402, Metro Towers, Bangalore'
        }
    )
    if created:
        buyer_user.set_password('buyer123')
        buyer_user.save()

    buyer_profile, created = Buyer.objects.get_or_create(
        user=buyer_user,
        defaults={
            'delivery_address': 'Flat 402, Metro Towers, Bangalore City, Karnataka',
            'contact_name': 'Alex Buyer'
        }
    )

    # 2. Create the 8 categories
    categories_data = [
        ('Vegetables', 'Fresh farm-harvested organic and wholesale vegetables.'),
        ('Fruits', 'Seasonal orchard-fresh sweet fruits.'),
        ('Grains', 'High-quality staple grains, wheat, rice and millets.'),
        ('Pulses', 'Healthy protein-rich farm lentils and grams.'),
        ('Organic Products', 'Certified organic produce grown without synthetic chemicals.'),
        ('Dairy Products', 'Farm-fresh pure dairy, milk, paneer, and butter.'),
        ('Spices', 'Highly aromatic whole and ground spices.'),
        ('Seeds', 'Certified high-germination hybrid and organic farm seeds.')
    ]
    categories = {}
    for name, desc in categories_data:
        cat, created = Category.objects.get_or_create(
            name=name,
            defaults={'description': desc}
        )
        categories[name] = cat

    # 3. Create Crops (40 crops, distributed to the 5 farmers based on specialization)
    # Spec: Category, Name, SKU, Farmer Username, Price, Stock, Unit, Image, Description
    crops_data = [
        # VEGETABLES -> Ramesh Patel
        ('Vegetables', 'Tomato', 'VEG-TOM-01', 'ramesh_patel', 35.00, 500, 'kg', 'crops/tomato.jpg', 'Fresh red vine-ripened tomatoes in wooden crates.'),
        ('Vegetables', 'Potato', 'VEG-POT-01', 'ramesh_patel', 22.00, 1000, 'kg', 'crops/potato.jpg', 'Fresh organic russet potatoes harvested directly from soil.'),
        ('Vegetables', 'Onion', 'VEG-ONI-01', 'ramesh_patel', 28.00, 800, 'kg', 'crops/onion.jpg', 'Farm-fresh purple red onions stacked in wholesale packs.'),
        ('Vegetables', 'Green Chili', 'VEG-CHI-01', 'ramesh_patel', 45.00, 150, 'kg', 'crops/green_chili.jpg', 'Spicy fresh green chilies harvested directly from plants.'),
        ('Vegetables', 'Cabbage', 'VEG-CAB-01', 'ramesh_patel', 30.00, 300, 'kg', 'crops/cabbage.jpg', 'Large, leafy organic green cabbages from vegetable fields.'),

        # FRUITS -> Rajesh Verma
        ('Fruits', 'Mango', 'FRU-MAN-01', 'rajesh_verma', 120.00, 200, 'piece', 'crops/mango.jpg', 'Juicy and sweet Alphonso mangoes, hand-packed in baskets.'),
        ('Fruits', 'Banana', 'FRU-BAN-01', 'rajesh_verma', 40.00, 400, 'piece', 'crops/banana.jpg', 'Sweet and ripe yellow Cavendish bananas cluster.'),
        ('Fruits', 'Apple', 'FRU-APP-01', 'rajesh_verma', 135.00, 300, 'kg', 'crops/apple.jpg', 'Crispy red orchard Gala apples, fresh harvest.'),
        ('Fruits', 'Orange', 'FRU-ORA-01', 'rajesh_verma', 75.00, 250, 'kg', 'crops/orange.jpg', 'Juicy and tangy sweet oranges picked from orchard trees.'),
        ('Fruits', 'Watermelon', 'FRU-WAT-01', 'rajesh_verma', 50.00, 100, 'piece', 'crops/watermelon.jpg', 'Large, sweet watermelons with juicy red pulp.'),

        # GRAINS -> Suresh Kumar
        ('Grains', 'Wheat', 'GRA-WHE-01', 'suresh_kumar', 38.00, 1500, 'kg', 'crops/wheat.jpg', 'Premium golden wheat crop grains ready for milling.'),
        ('Grains', 'Rice', 'GRA-RIC-01', 'suresh_kumar', 85.00, 1200, 'kg', 'crops/rice.jpg', 'Aromatic long-grain basmati rice from paddy fields.'),
        ('Grains', 'Corn (Maize)', 'GRA-COR-01', 'suresh_kumar', 25.00, 600, 'kg', 'crops/corn.jpg', 'Sweet corn cobs harvested from golden maize farms.'),
        ('Grains', 'Millet (Bajra)', 'GRA-MIL-01', 'suresh_kumar', 28.00, 400, 'kg', 'crops/millet.jpg', 'Nutrient-rich pearl millet grains from Rajasthan.'),
        ('Grains', 'Barley', 'GRA-BAR-01', 'suresh_kumar', 32.00, 500, 'kg', 'crops/barley.jpg', 'Premium organic pearl barley crop in golden sunbeams.'),

        # PULSES -> Amit Chauhan
        ('Pulses', 'Chickpea (Chana)', 'PUL-CHI-01', 'amit_chauhan', 65.00, 700, 'kg', 'crops/chickpea.jpg', 'Premium quality brown chickpeas harvested from fields.'),
        ('Pulses', 'Green Gram (Moong)', 'PUL-GRN-01', 'amit_chauhan', 90.00, 400, 'kg', 'crops/moong.jpg', 'Organic green gram moong beans displayed in sacks.'),
        ('Pulses', 'Black Gram (Urad)', 'PUL-BLK-01', 'amit_chauhan', 95.00, 350, 'kg', 'crops/urad.jpg', 'Whole black gram grains, rich in proteins.'),
        ('Pulses', 'Pigeon Pea (Toor)', 'PUL-PIG-01', 'amit_chauhan', 115.00, 500, 'kg', 'crops/toor.jpg', 'Traditional yellow split toor dal grains.'),
        ('Pulses', 'Lentils (Masoor)', 'PUL-LEN-01', 'amit_chauhan', 80.00, 450, 'kg', 'crops/masoor.jpg', 'Red split masoor lentils stored under climate controls.'),

        # ORGANIC PRODUCTS -> Mahesh Singh
        ('Organic Products', 'Organic Tomato', 'ORG-TOM-01', 'mahesh_singh', 55.00, 200, 'kg', 'crops/organic_tomato.jpg', 'Certified organic red tomatoes grown without chemicals.'),
        ('Organic Products', 'Organic Cucumber', 'ORG-CUC-01', 'mahesh_singh', 35.00, 250, 'kg', 'crops/organic_cucumber.jpg', 'Crisp green organic cucumbers freshly plucked.'),
        ('Organic Products', 'Organic Spinach', 'ORG-SPI-01', 'mahesh_singh', 40.00, 150, 'kg', 'crops/organic_spinach.jpg', 'Fresh leafy spinach greens harvested naturally.'),
        ('Organic Products', 'Organic Carrot', 'ORG-CAR-01', 'mahesh_singh', 60.00, 300, 'kg', 'crops/organic_carrot.jpg', 'Sweet organic orange carrots pulled directly from soil.'),
        ('Organic Products', 'Organic Broccoli', 'ORG-BRO-01', 'mahesh_singh', 95.00, 150, 'kg', 'crops/organic_broccoli.jpg', 'Fresh organic broccoli crowns from certified green farms.'),

        # DAIRY PRODUCTS -> Ramesh Patel
        ('Dairy Products', 'Fresh Milk', 'DAI-MIL-01', 'ramesh_patel', 58.00, 300, 'piece', 'crops/milk.jpg', 'Pure pasteurized cow milk, direct from dairy farm.'),
        ('Dairy Products', 'Curd (Yogurt)', 'DAI-CUR-01', 'ramesh_patel', 45.00, 200, 'piece', 'crops/curd.jpg', 'Fresh thick yogurt prepared traditionally in clay bowls.'),
        ('Dairy Products', 'Butter', 'DAI-BUT-01', 'ramesh_patel', 120.00, 150, 'piece', 'crops/butter.jpg', 'Organic unsalted butter block prepared from rich cream.'),
        ('Dairy Products', 'Paneer', 'DAI-PAN-01', 'ramesh_patel', 150.00, 180, 'piece', 'crops/paneer.jpg', 'Soft and fresh cottage cheese paneer cubes.'),
        ('Dairy Products', 'Cheese', 'DAI-CHE-01', 'ramesh_patel', 280.00, 80, 'piece', 'crops/cheese.jpg', 'Premium farm-aged cheese wheels.'),

        # SPICES -> Amit Chauhan
        ('Spices', 'Turmeric', 'SPI-TUR-01', 'amit_chauhan', 135.00, 250, 'kg', 'crops/turmeric.jpg', 'High-curcumin raw turmeric roots and organic powder.'),
        ('Spices', 'Red Chili', 'SPI-RCH-01', 'amit_chauhan', 180.00, 200, 'kg', 'crops/red_chili.jpg', 'Sun-dried hot red chili pods in woven baskets.'),
        ('Spices', 'Coriander', 'SPI-COR-01', 'amit_chauhan', 95.00, 300, 'kg', 'crops/coriander.jpg', 'Fragrant coriander seeds and green leaves.'),
        ('Spices', 'Cumin', 'SPI-CUM-01', 'amit_chauhan', 220.00, 180, 'kg', 'crops/cumin.jpg', 'Highly aromatic whole cumin seeds, cleaned and sorted.'),
        ('Spices', 'Black Pepper', 'SPI-BPE-01', 'amit_chauhan', 480.00, 120, 'kg', 'crops/black_pepper.jpg', 'Organic black pepper berries harvested from vines.'),

        # SEEDS -> Amit Chauhan
        ('Seeds', 'Wheat Seeds', 'SEE-WHE-01', 'amit_chauhan', 45.00, 600, 'kg', 'crops/wheat_seeds.jpg', 'Certified high-germination wheat seeds for sowing.'),
        ('Seeds', 'Rice Seeds', 'SEE-RIC-01', 'amit_chauhan', 95.00, 400, 'kg', 'crops/rice_seeds.jpg', 'Sorted and treated rice paddy seeds for nurseries.'),
        ('Seeds', 'Corn Seeds', 'SEE-COR-01', 'amit_chauhan', 150.00, 200, 'kg', 'crops/corn_seeds.jpg', 'Hybrid high-yield sweet corn seeds in packages.'),
        ('Seeds', 'Vegetable Seeds', 'SEE-VEG-01', 'amit_chauhan', 80.00, 500, 'piece', 'crops/vegetable_seeds.jpg', 'Mixed vegetable organic seeds package for kitchen gardens.'),
        ('Seeds', 'Sunflower Seeds', 'SEE-SUN-01', 'amit_chauhan', 110.00, 300, 'kg', 'crops/sunflower_seeds.jpg', 'Premium sunflower seeds ready for oil cultivation.')
    ]

    for cat_name, name, sku, farmer_username, price, qty, unit, img_path, desc in crops_data:
        farmer_prof = farmer_profiles[farmer_username]
        
        # Determine shelf life based on crop name/category
        lower_name = name.lower()
        cat_lower = cat_name.lower()
        
        if 'spinach' in lower_name or 'coriander' in lower_name or 'milk' in lower_name or 'curd' in lower_name:
            shelf_life = 2
        elif 'paneer' in lower_name or 'banana' in lower_name or 'chili' in lower_name:
            shelf_life = 4
        elif cat_lower in ['vegetables', 'organic products']:
            if 'tomato' in lower_name or 'cucumber' in lower_name:
                shelf_life = 7
            else:
                shelf_life = 14
        elif cat_lower == 'dairy products':
            if 'butter' in lower_name:
                shelf_life = 30
            else:
                shelf_life = 90  # cheese
        elif cat_lower == 'fruits':
            if 'watermelon' in lower_name:
                shelf_life = 7
            else:
                shelf_life = 15
        else:
            shelf_life = 180  # grains, pulses, spices, seeds

        crop, created = Crop.objects.get_or_create(
            name=name,
            farmer=farmer_prof,
            defaults={
                'category': categories[cat_name],
                'description': desc,
                'price_per_kg': price,
                'quantity_available': qty,
                'unit': unit,
                'is_approved': True,
                'availability_status': 'available',
                'image': img_path,
                'harvest_date': date.today(),
                'shelf_life_days': shelf_life
            }
        )
        crop.price_per_kg = price
        crop.quantity_available = qty
        crop.category = categories[cat_name]
        crop.image = img_path
        crop.harvest_date = date.today()
        crop.shelf_life_days = shelf_life
        crop.save()
        print(f"Crop '{name}' verified/seeded for Farmer '{farmer_username}' (Shelf life: {shelf_life} days).")

    # 4. Create Price Trends
    crop_trends = [
        ('Wheat', 'Grains', [32.00, 34.00, 35.00, 36.00, 37.00, 38.00]),
        ('Rice', 'Grains', [78.00, 80.00, 82.00, 81.00, 84.00, 85.00]),
        ('Tomato', 'Vegetables', [25.00, 30.00, 45.00, 28.00, 32.00, 35.00]),
    ]
    start_date = date(2026, 1, 15)
    for crop_name, cat_name, prices in crop_trends:
        cat = categories[cat_name]
        for idx, price in enumerate(prices):
            record_date = start_date + timedelta(days=idx*30)
            PriceTrend.objects.get_or_create(
                crop_name=crop_name,
                category=cat,
                record_date=record_date,
                defaults={'avg_price': price}
            )
            
    # 5. Create Market Insights
    from marketplace.models import MarketInsight
    insights_data = [
        ('Tomato', 'Vegetables', 35.00, 4.20, 'High', 'Up', 'Rajkot, Gujarat', 180),
        ('Potato', 'Vegetables', 22.00, -1.50, 'Medium', 'Down', 'Ludhiana, Punjab', 310),
        ('Onion', 'Vegetables', 28.00, 2.80, 'High', 'Up', 'Nashik, Maharashtra', 250),
        ('Wheat', 'Grains', 38.00, 1.10, 'High', 'Up', 'Karnal, Haryana', 420),
        ('Rice', 'Grains', 85.00, -0.50, 'Medium', 'Stable', 'Ludhiana, Punjab', 150),
        ('Mango', 'Fruits', 120.00, 5.60, 'High', 'Up', 'Valsad, Gujarat', 80),
        ('Chickpea (Chana)', 'Pulses', 75.00, -2.00, 'Low', 'Down', 'Jaipur, Rajasthan', 95),
    ]
    for crop_name, cat_name, price, change, demand, forecast, reg, vol in insights_data:
        cat = categories[cat_name]
        MarketInsight.objects.get_or_create(
            crop_name=crop_name,
            category=cat,
            defaults={
                'current_price': price,
                'price_change_percent': change,
                'demand_level': demand,
                'forecast_direction': forecast,
                'region': reg,
                'volume_tonnes': vol
            }
        )
    print("Database seeding with 5 distinct farmer accounts and MarketInsights completed successfully!")

if __name__ == '__main__':
    seed_db()
