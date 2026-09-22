import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

os.makedirs('report_assets', exist_ok=True)

screens = [
    ("screen_login.png", "Login & Registration Screen", [
        "Multi-role user authentication (Farmer, Buyer, Admin)",
        "Username and Password authentication fields",
        "Mobile OTP verification fallback for seamless login",
        "Secure session management with Django Authentication framework"
    ], "#1E4D2B"),
    ("screen_admin_dashboard.png", "Admin Control Dashboard", [
        "System overview metrics: Total Users, Total Crops, Active Orders, Revenue",
        "Crop approval management interface",
        "User account management & role-based access control (RBAC)",
        "System reports generation and activity audit log"
    ], "#2E7D32"),
    ("screen_farmer_dashboard.png", "Farmer Portal & Dashboard", [
        "Farmer product inventory overview & harvest stock status",
        "Direct orders received with status (Pending, Processing, Delivered)",
        "Revenue & earnings analytics summary",
        "Quick action buttons: Add New Crop, Update Price, Manage Orders"
    ], "#388E3C"),
    ("screen_marketplace.png", "Buyer Marketplace & Crop Listings", [
        "Dynamic crop catalog with images, categories, and price per kg/unit",
        "Search bar and category filter (Grains, Vegetables, Fruits, Spices)",
        "Real-time availability status indicators",
        "Farmer profile badges and direct crop rating display"
    ], "#1565C0"),
    ("screen_crop_detail.png", "Crop Detail & Quantity Selector", [
        "High-resolution crop image display and description",
        "Quantity counter in Kg / Units with automated price calculation",
        "Harvest date and remaining shelf-life metrics",
        "Add to Cart and Direct Buy Now buttons"
    ], "#0288D1"),
    ("screen_cart_checkout.png", "Shopping Cart & Checkout Page", [
        "Selected items summary with itemized breakdown and total cost",
        "Delivery address entry and address book selector",
        "Payment method selection: Cash on Delivery (COD), UPI, Card",
        "Order verification code (OTP) security prompt"
    ], "#7B1FA2"),
    ("screen_farmer_store.png", "Public Farmer Storefront", [
        "Farmer profile header with location, verification status, and contact info",
        "List of all crops published by the specific farmer",
        "Overall farmer ratings (Quality, Delivery, Communication)",
        "Direct Send Message / Inquiry button"
    ], "#E65100"),
    ("screen_order_history.png", "Order Tracking & History Page", [
        "Detailed list of past and active orders for buyers & farmers",
        "Live order status tracker (Ordered -> Packed -> Shipped -> Delivered)",
        "Download Tax Invoice PDF button",
        "Return / Refund request submit workflow"
    ], "#455A64"),
    ("screen_price_trends.png", "Market Price Trends & Analytics", [
        "Historical price charts per crop category over time",
        "Market demand forecast indicator (High, Medium, Low demand)",
        "Price change percentage trends (+/- %) vs previous week",
        "Regional market insights to help farmers price competitively"
    ], "#00695C"),
    ("screen_chat.png", "Direct Messaging & Chat System", [
        "Real-time conversation thread between Buyer and Farmer",
        "Crop context attachment in chat window",
        "Message read receipt indicators",
        "Instant notification trigger upon receiving new messages"
    ], "#C2185B")
]

for filename, title, highlights, col in screens:
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    # Browser Frame Outer
    frame = patches.FancyBboxPatch((0.5, 0.5), 9.0, 5.0, boxstyle="round,pad=0.2", ec="#BDBDBD", fc="#FFFFFF", lw=2)
    ax.add_patch(frame)

    # Top Browser Header Bar
    header = patches.FancyBboxPatch((0.5, 4.7), 9.0, 0.8, boxstyle="square,pad=0.0", ec="#BDBDBD", fc="#ECEFF1", lw=1)
    ax.add_patch(header)
    
    # Browser Buttons (Red, Yellow, Green)
    for i, c in enumerate(["#FF5252", "#FFD740", "#69F0AE"]):
        circle = patches.Circle((0.9 + i*0.3, 5.1), 0.1, color=c)
        ax.add_patch(circle)

    # URL Bar
    url_box = patches.FancyBboxPatch((2.0, 4.85), 5.5, 0.5, boxstyle="round,pad=0.05", ec="#CFD8DC", fc="#FFFFFF")
    ax.add_patch(url_box)
    ax.text(2.2, 5.05, f"http://127.0.0.1:8000/{title.lower().replace(' ', '-')}/", fontsize=8, color="#546E7A", va="center")

    # Content Title Header
    title_box = patches.FancyBboxPatch((0.8, 3.8), 8.4, 0.6, boxstyle="round,pad=0.05", ec=col, fc=col)
    ax.add_patch(title_box)
    ax.text(5.0, 4.1, title, fontsize=12, fontweight="bold", color="#FFFFFF", ha="center", va="center")

    # Highlights content box
    content_box = patches.FancyBboxPatch((0.8, 0.8), 8.4, 2.8, boxstyle="round,pad=0.1", ec="#E0E0E0", fc="#FAFAFA")
    ax.add_patch(content_box)
    
    ax.text(1.1, 3.3, "Module Interface Key Features:", fontsize=10, fontweight="bold", color="#212121")
    for idx, h in enumerate(highlights):
        ax.text(1.3, 2.9 - idx*0.5, f"•  {h}", fontsize=9, color="#424242", va="center")

    plt.tight_layout()
    plt.savefig(f'report_assets/{filename}')
    plt.close()

print("Screen graphics generated successfully!")
