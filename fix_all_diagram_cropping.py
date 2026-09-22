import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

os.makedirs('report_assets', exist_ok=True)

# Set global font family
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'

# -------------------------------------------------------------
# 1. DFD LEVEL 0 (CONTEXT DIAGRAM) - PERFECT SPACING
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
ax.set_xlim(0, 11)
ax.set_ylim(0, 7)
ax.axis('off')

# Central System Box (0.0)
sys_box = patches.FancyBboxPatch((3.8, 2.3), 3.4, 2.4, boxstyle="round,pad=0.2", ec="#1B4332", fc="#E8F5E9", lw=3.0)
ax.add_patch(sys_box)
ax.text(5.5, 3.8, "0.0", ha="center", va="center", fontsize=16, fontweight="bold", color="#1B4332")
ax.text(5.5, 3.0, "AgriConnect\nSystem", ha="center", va="center", fontsize=14, fontweight="bold", color="#1B4332")

# External Entities
box_f = patches.FancyBboxPatch((0.5, 5.0), 2.4, 1.2, boxstyle="square,pad=0.1", ec="#2E7D32", fc="#F1F8E9", lw=2.5)
ax.add_patch(box_f)
ax.text(1.7, 5.6, "FARMER", ha="center", va="center", fontsize=13, fontweight="bold", color="#1B4332")

box_b = patches.FancyBboxPatch((0.5, 0.8), 2.4, 1.2, boxstyle="square,pad=0.1", ec="#1565C0", fc="#E3F2FD", lw=2.5)
ax.add_patch(box_b)
ax.text(1.7, 1.4, "BUYER", ha="center", va="center", fontsize=13, fontweight="bold", color="#0D47A1")

box_a = patches.FancyBboxPatch((8.1, 2.9), 2.4, 1.2, boxstyle="square,pad=0.1", ec="#C62828", fc="#FFEBEE", lw=2.5)
ax.add_patch(box_a)
ax.text(9.3, 3.5, "ADMIN", ha="center", va="center", fontsize=13, fontweight="bold", color="#B71C1C")

# Flow Arrows & Badges
ax.annotate("", xy=(3.8, 4.3), xytext=(2.9, 5.6), arrowprops=dict(arrowstyle="->", lw=2.2, color="#2E7D32"))
ax.text(3.35, 5.2, "Crop Listings & Docs", ha="center", va="center", fontsize=10.5, fontweight="bold", color="#1B4332",
        bbox=dict(boxstyle="round,pad=0.3", fc="#FFFFFF", ec="#2E7D32", lw=1.5))

ax.annotate("", xy=(2.9, 5.0), xytext=(3.8, 3.7), arrowprops=dict(arrowstyle="->", lw=2.2, color="#2E7D32", linestyle="--"))
ax.text(2.9, 4.3, "Orders & Price Trends", ha="center", va="center", fontsize=10.5, fontweight="bold", color="#1B4332",
        bbox=dict(boxstyle="round,pad=0.3", fc="#FFFFFF", ec="#2E7D32", lw=1.5))

ax.annotate("", xy=(3.8, 2.7), xytext=(2.9, 1.6), arrowprops=dict(arrowstyle="->", lw=2.2, color="#1565C0"))
ax.text(3.35, 2.1, "Cart, Orders & OTP", ha="center", va="center", fontsize=10.5, fontweight="bold", color="#0D47A1",
        bbox=dict(boxstyle="round,pad=0.3", fc="#FFFFFF", ec="#1565C0", lw=1.5))

ax.annotate("", xy=(2.9, 1.2), xytext=(3.8, 2.3), arrowprops=dict(arrowstyle="->", lw=2.2, color="#1565C0", linestyle="--"))
ax.text(3.8, 1.0, "Catalog & Invoices", ha="center", va="center", fontsize=10.5, fontweight="bold", color="#0D47A1",
        bbox=dict(boxstyle="round,pad=0.3", fc="#FFFFFF", ec="#1565C0", lw=1.5))

ax.annotate("", xy=(7.2, 3.8), xytext=(8.1, 3.8), arrowprops=dict(arrowstyle="->", lw=2.2, color="#C62828"))
ax.text(7.65, 4.2, "Approvals", ha="center", va="center", fontsize=10.5, fontweight="bold", color="#B71C1C",
        bbox=dict(boxstyle="round,pad=0.3", fc="#FFFFFF", ec="#C62828", lw=1.5))

ax.annotate("", xy=(8.1, 3.2), xytext=(7.2, 3.2), arrowprops=dict(arrowstyle="->", lw=2.2, color="#C62828", linestyle="--"))
ax.text(7.65, 2.8, "Reports & Logs", ha="center", va="center", fontsize=10.5, fontweight="bold", color="#B71C1C",
        bbox=dict(boxstyle="round,pad=0.3", fc="#FFFFFF", ec="#C62828", lw=1.5))

plt.title("Data Flow Diagram (DFD Level 0) - AgriConnect Context Diagram", fontsize=15, fontweight="bold", pad=20)
plt.savefig('report_assets/dfd_level0.png', bbox_inches='tight', pad_inches=0.4)
plt.close()

# -------------------------------------------------------------
# 2. DFD LEVEL 1 (SUBSYSTEMS BREAKDOWN) - EXTRA VERTICAL SPACE
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 9.5), dpi=300)
ax.set_xlim(0, 12)
ax.set_ylim(0, 9.5)
ax.axis('off')

# Processes (1.0 to 6.0)
processes = [
    ("1.0\nAuth & Profile", 2.0, 7.5, "#1B4332"),
    ("2.0\nCrop Listings", 6.0, 7.5, "#2D6A4F"),
    ("3.0\nCart & Checkout", 10.0, 7.5, "#40916C"),
    ("4.0\nOrders & PDF", 2.0, 2.8, "#081C15"),
    ("5.0\nPrice Analytics", 6.0, 2.8, "#1B4332"),
    ("6.0\nChat & Reviews", 10.0, 2.8, "#52B788")
]

for p_text, x, y, col in processes:
    circle = patches.Circle((x, y), 1.05, ec=col, fc="#E8F5E9", lw=2.8)
    ax.add_patch(circle)
    ax.text(x, y, p_text, ha="center", va="center", fontsize=11.5, fontweight="bold", color=col)

# Data Stores (D1 to D5) - Plenty of room above bottom!
stores = [
    ("D1: Users & Profiles DB", 2.0, 5.15),
    ("D2: Crops & Categories DB", 6.0, 5.15),
    ("D3: Shopping Cart DB", 10.0, 5.15),
    ("D4: Orders & Payments DB", 4.0, 1.0),
    ("D5: Price Analytics DB", 8.0, 1.0)
]

for s_text, x, y in stores:
    box = patches.FancyBboxPatch((x-1.5, y-0.4), 3.0, 0.8, boxstyle="round,pad=0.1", ec="#1B4332", fc="#FFFFFF", lw=2.2)
    ax.add_patch(box)
    ax.text(x, y, s_text, ha="center", va="center", fontsize=11, fontweight="bold", color="#1B4332")

# Clean Connections
ax.annotate("", xy=(2.0, 5.95), xytext=(2.0, 6.45), arrowprops=dict(arrowstyle="->", lw=2.2, color="#1B4332"))
ax.annotate("", xy=(6.0, 5.95), xytext=(6.0, 6.45), arrowprops=dict(arrowstyle="->", lw=2.2, color="#2D6A4F"))
ax.annotate("", xy=(10.0, 5.95), xytext=(10.0, 6.45), arrowprops=dict(arrowstyle="->", lw=2.2, color="#40916C"))

ax.annotate("", xy=(2.0, 3.85), xytext=(2.0, 4.35), arrowprops=dict(arrowstyle="->", lw=2.2, color="#081C15"))
ax.annotate("", xy=(6.0, 3.85), xytext=(6.0, 4.35), arrowprops=dict(arrowstyle="->", lw=2.2, color="#1B4332"))

ax.annotate("", xy=(4.95, 7.5), xytext=(3.05, 7.5), arrowprops=dict(arrowstyle="->", lw=2.2, color="#1B4332"))
ax.annotate("", xy=(8.95, 7.5), xytext=(7.05, 7.5), arrowprops=dict(arrowstyle="->", lw=2.2, color="#2D6A4F"))

# Bottom connectors to D4 and D5
ax.annotate("", xy=(4.0, 1.4), xytext=(2.6, 1.8), arrowprops=dict(arrowstyle="->", lw=2.2, color="#081C15"))
ax.annotate("", xy=(8.0, 1.4), xytext=(6.6, 1.8), arrowprops=dict(arrowstyle="->", lw=2.2, color="#1B4332"))

plt.title("Data Flow Diagram (DFD Level 1) - AgriConnect Subsystems Breakdown", fontsize=15, fontweight="bold", pad=20)
plt.savefig('report_assets/dfd_level1.png', bbox_inches='tight', pad_inches=0.4)
plt.close()

# -------------------------------------------------------------
# 3. ENTITY RELATIONSHIP (ER) DIAGRAM - FULL EXPANDED CANVAS
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(13, 11.5), dpi=300)
ax.set_xlim(0, 13)
ax.set_ylim(0, 11.5)
ax.axis('off')

def draw_er_table(x, y, w, title, fields):
    h = 0.60 + len(fields) * 0.42
    box = patches.FancyBboxPatch((x, y - h), w, h, boxstyle="square,pad=0.0", ec="#1B4332", fc="#FFFFFF", lw=2.5)
    ax.add_patch(box)
    
    hdr = patches.FancyBboxPatch((x, y - 0.60), w, 0.60, boxstyle="square,pad=0.0", ec="#1B4332", fc="#1B4332", lw=2.5)
    ax.add_patch(hdr)
    ax.text(x + w/2, y - 0.30, title, ha="center", va="center", fontsize=12.5, fontweight="bold", color="#FFFFFF")
    
    for i, (fname, ftype, is_pk) in enumerate(fields):
        fy = y - 0.9 - i * 0.42
        prefix = f"[PK] {fname}" if is_pk=="PK" else (f"[FK] {fname}" if is_pk=="FK" else f"  {fname}")
        weight = "bold" if is_pk else "normal"
        col = "#1B4332" if is_pk else "#222222"
        ax.text(x + 0.15, fy, prefix, fontsize=11, fontweight=weight, color=col, va="center")
        ax.text(x + w - 0.15, fy, ftype, fontsize=10, color="#444444", ha="right", va="center")

# Row 1 (Y = 10.8)
draw_er_table(0.5, 10.8, 3.6, "USER (Custom User)", [
    ("id", "BigAutoField", "PK"),
    ("username", "VarChar(150)", ""),
    ("email", "EmailField", ""),
    ("role", "VarChar(20)", ""),
    ("phone", "VarChar(15)", "")
])

draw_er_table(4.7, 10.8, 3.6, "FARMER Profile", [
    ("id", "BigAutoField", "PK"),
    ("user_id", "OneToOne", "FK"),
    ("farm_name", "VarChar(100)", ""),
    ("farm_location", "VarChar(255)", ""),
    ("trust_score", "Int", "")
])

draw_er_table(8.9, 10.8, 3.6, "BUYER Profile", [
    ("id", "BigAutoField", "PK"),
    ("user_id", "OneToOne", "FK"),
    ("delivery_address", "TextField", ""),
    ("city", "VarChar(100)", ""),
    ("state", "VarChar(100)", "")
])

# Row 2 (Y = 6.8)
draw_er_table(4.7, 6.8, 3.6, "CROP (Produce Listing)", [
    ("id", "BigAutoField", "PK"),
    ("farmer_id", "ForeignKey", "FK"),
    ("category_id", "ForeignKey", "FK"),
    ("name", "VarChar(100)", ""),
    ("price_per_kg", "Decimal(10,2)", ""),
    ("quantity_available", "Decimal(10,2)", "")
])

draw_er_table(8.9, 6.8, 3.6, "CATEGORY", [
    ("id", "BigAutoField", "PK"),
    ("name", "VarChar(100)", ""),
    ("description", "TextField", "")
])

# Row 3 (Y = 2.8 - Raised to give generous bottom margin!)
draw_er_table(0.5, 2.8, 3.6, "ORDER Master", [
    ("id", "BigAutoField", "PK"),
    ("buyer_id", "ForeignKey", "FK"),
    ("farmer_id", "ForeignKey", "FK"),
    ("total_amount", "Decimal(12,2)", "")
])

draw_er_table(4.7, 2.8, 3.6, "ORDER_ITEM", [
    ("id", "BigAutoField", "PK"),
    ("order_id", "ForeignKey", "FK"),
    ("crop_id", "ForeignKey", "FK"),
    ("quantity", "Decimal(10,2)", "")
])

draw_er_table(8.9, 2.8, 3.6, "PAYMENT Transaction", [
    ("id", "BigAutoField", "PK"),
    ("order_id", "OneToOne", "FK"),
    ("payment_method", "VarChar(50)", ""),
    ("amount", "Decimal(12,2)", "")
])

# Cardinality Connections & Badges
def draw_er_badge(p1, p2, label):
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#1B4332", lw=2.5)
    mx, my = (p1[0] + p2[0])/2, (p1[1] + p2[1])/2
    ax.text(mx, my, label, fontsize=11.5, fontweight="bold", color="#1B4332",
            bbox=dict(boxstyle="round,pad=0.25", fc="#FFFFFF", ec="#1B4332", lw=1.8), ha="center", va="center")

draw_er_badge((4.1, 9.4), (4.7, 9.4), "1 : 1")
draw_er_badge((8.3, 9.4), (8.9, 9.4), "1 : 1")
draw_er_badge((6.5, 7.8), (6.5, 6.8), "1 : N")
draw_er_badge((8.3, 5.5), (8.9, 5.5), "N : 1")
draw_er_badge((2.3, 7.6), (2.3, 2.8), "1 : N")
draw_er_badge((4.1, 1.8), (4.7, 1.8), "1 : N")
draw_er_badge((8.3, 1.8), (8.9, 1.8), "1 : 1")

plt.title("AgriConnect Entity Relationship (ER) Diagram - Core Relational Schema", fontsize=16, fontweight="bold", pad=20)
plt.savefig('report_assets/er_diagram.png', bbox_inches='tight', pad_inches=0.5)
plt.close()

# -------------------------------------------------------------
# 4. USE CASE DIAGRAM - CLEAR SPACING
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
ax.set_xlim(0, 11)
ax.set_ylim(0, 7.5)
ax.axis('off')

# System Box
sys_b = patches.FancyBboxPatch((3.0, 0.5), 5.0, 6.4, boxstyle="round,pad=0.1", ec="#1B4332", fc="#FAFDFB", lw=2.5)
ax.add_patch(sys_b)
ax.text(5.5, 6.5, "AgriConnect System", ha="center", fontsize=13, fontweight="bold", color="#1B4332")

# Actors
ax.add_patch(patches.Circle((1.1, 5.5), 0.28, ec="#2E7D32", fc="#FFFFFF", lw=2.2))
ax.plot([1.1, 1.1], [4.75, 5.22], color="#2E7D32", lw=2.2)
ax.plot([0.75, 1.45], [5.0, 5.0], color="#2E7D32", lw=2.2)
ax.text(1.1, 4.35, "Farmer", ha="center", fontsize=11.5, fontweight="bold", color="#2E7D32")

ax.add_patch(patches.Circle((1.1, 2.1), 0.28, ec="#1565C0", fc="#FFFFFF", lw=2.2))
ax.plot([1.1, 1.1], [1.35, 1.82], color="#1565C0", lw=2.2)
ax.plot([0.75, 1.45], [1.6, 1.6], color="#1565C0", lw=2.2)
ax.text(1.1, 0.95, "Buyer", ha="center", fontsize=11.5, fontweight="bold", color="#1565C0")

ax.add_patch(patches.Circle((9.9, 3.8), 0.28, ec="#C62828", fc="#FFFFFF", lw=2.2))
ax.plot([9.9, 9.9], [3.05, 3.52], color="#C62828", lw=2.2)
ax.plot([9.55, 10.25], [3.3, 3.3], color="#C62828", lw=2.2)
ax.text(9.9, 2.65, "Admin", ha="center", fontsize=11.5, fontweight="bold", color="#C62828")

ucs = [
    ("Register & Login / Auth OTP", 5.5, 5.9),
    ("Submit & Verify Farm Docs", 5.5, 4.9),
    ("Manage Crop Listings", 5.5, 3.9),
    ("Browse Catalog & Search", 5.5, 2.9),
    ("Cart, Checkout & OTP Order", 5.5, 1.9),
    ("Direct Chat & PDF Invoice", 5.5, 0.9)
]

for text, x, y in ucs:
    ellipse = patches.Ellipse((x, y), 4.0, 0.75, ec="#1B4332", fc="#E8F5E9", lw=2.0)
    ax.add_patch(ellipse)
    ax.text(x, y, text, ha="center", va="center", fontsize=10.5, fontweight="bold", color="#1B4332")

for y_uc in [5.9, 4.9, 3.9, 0.9]:
    ax.plot([1.45, 3.5], [4.9, y_uc], color="#2E7D32", lw=1.5, linestyle="--")

for y_uc in [5.9, 2.9, 1.9, 0.9]:
    ax.plot([1.45, 3.5], [1.6, y_uc], color="#1565C0", lw=1.5, linestyle="--")

for y_uc in [5.9, 4.9, 3.9]:
    ax.plot([9.55, 7.5], [3.3, y_uc], color="#C62828", lw=1.5, linestyle="--")

plt.title("Use Case Diagram - AgriConnect System Roles", fontsize=15, fontweight="bold", pad=20)
plt.savefig('report_assets/use_case_diagram.png', bbox_inches='tight', pad_inches=0.4)
plt.close()

# -------------------------------------------------------------
# 5. ARCHITECTURE DIAGRAM - CLEAR SPACING
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
ax.set_xlim(0, 11)
ax.set_ylim(0, 7.5)
ax.axis('off')

layers_arch = [
    ("Client Presentation Layer", 0.5, 5.4, 10.0, 1.4, "#E8F5E9", "#1B4332", "Web Browsers & Mobile Devices\nHTML5 | CSS3 | JavaScript (ES6+) | Bootstrap 5"),
    ("Application Logic Layer (Django MVT)", 0.5, 3.0, 10.0, 1.8, "#E0F2F1", "#00695C", "URL Router | View Controllers | Authentication & OTP Services\nReportLab PDF Invoice Engine | Freshness Calculator"),
    ("Database & File Storage Layer", 0.5, 0.6, 10.0, 1.8, "#E1F5FE", "#0277BD", "MySQL 8.0 DBMS (21 Relational Tables)\nUploaded Documents | Product Images | Static Assets")
]

for title, x, y, w, h, bg, border, subtitle in layers_arch:
    box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1", ec=border, fc=bg, lw=2.8)
    ax.add_patch(box)
    ax.text(x + w/2, y + h - 0.4, title, ha="center", va="center", fontsize=14, fontweight="bold", color=border)
    ax.text(x + w/2, y + 0.5, subtitle, ha="center", va="center", fontsize=11, fontweight="bold", color="#333333")

ax.annotate("", xy=(5.5, 5.4), xytext=(5.5, 4.8), arrowprops=dict(arrowstyle="<->", lw=2.8, color="#1B4332"))
ax.annotate("", xy=(5.5, 3.0), xytext=(5.5, 2.4), arrowprops=dict(arrowstyle="<->", lw=2.8, color="#00695C"))

plt.title("System Architecture Diagram - Django MVT Pattern", fontsize=15, fontweight="bold", pad=20)
plt.savefig('report_assets/architecture_diagram.png', bbox_inches='tight', pad_inches=0.4)
plt.close()

print("All diagrams regenerated with extra padding and generous canvas dimensions!")
