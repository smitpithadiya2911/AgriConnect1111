import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

os.makedirs('report_assets', exist_ok=True)

# 1. DFD Level 0
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')

# System Box
sys_box = patches.FancyBboxPatch((3.5, 2.0), 3.0, 2.0, boxstyle="round,pad=0.3", ec="#1E4D2B", fc="#E8F5E9", lw=2)
ax.add_patch(sys_box)
ax.text(5.0, 3.0, "0.0\nAgriConnect\nSystem", ha="center", va="center", fontsize=14, fontweight="bold", color="#1E4D2B")

# External Entities
entities = [
    ("Farmer", 1.0, 4.5, "#2E7D32"),
    ("Buyer", 1.0, 1.5, "#1565C0"),
    ("Admin", 9.0, 3.0, "#C62828")
]

for name, x, y, col in entities:
    box = patches.FancyBboxPatch((x-0.8, y-0.5), 1.6, 1.0, boxstyle="square,pad=0.2", ec=col, fc="#F5F5F5", lw=2)
    ax.add_patch(box)
    ax.text(x, y, name, ha="center", va="center", fontsize=12, fontweight="bold", color=col)

# Flow Arrows & Labels
arrows = [
    ((1.8, 4.5), (3.5, 3.5), "Crop Listings, Orders", "above"),
    ((3.5, 2.5), (1.8, 1.5), "Order Placement", "below"),
    ((6.5, 3.0), (8.2, 3.0), "Analytics, Approvals", "above")
]

for start, end, label, pos in arrows:
    ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", lw=1.5, color="#424242"))
    mid_x, mid_y = (start[0] + end[0])/2, (start[1] + end[1])/2
    ax.text(mid_x, mid_y + (0.2 if pos=="above" else -0.3), label, ha="center", fontsize=9, color="#333333")

plt.title("Data Flow Diagram (DFD Level 0) - AgriConnect System", fontsize=14, fontweight="bold", pad=20)
plt.tight_layout()
plt.savefig('report_assets/dfd_level0.png')
plt.close()

# 2. DFD Level 1
fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
ax.set_xlim(0, 11)
ax.set_ylim(0, 7)
ax.axis('off')

processes = [
    ("1.0\nAuth & Profile", 2.0, 5.5),
    ("2.0\nCrop Listing", 5.5, 5.5),
    ("3.0\nCart & Checkout", 9.0, 5.5),
    ("4.0\nOrder & OTP", 3.5, 2.0),
    ("5.0\nPayment & Review", 7.5, 2.0)
]

for p_text, x, y in processes:
    circle = patches.Circle((x, y), 0.9, ec="#2D6A4F", fc="#D8F3DC", lw=2)
    ax.add_patch(circle)
    ax.text(x, y, p_text, ha="center", va="center", fontsize=10, fontweight="bold", color="#1B4332")

# Data Stores
stores = [
    ("D1: Users DB", 2.0, 3.7),
    ("D2: Crops DB", 5.5, 3.7),
    ("D3: Orders DB", 5.5, 0.7)
]

for s_text, x, y in stores:
    box = patches.FancyBboxPatch((x-1.0, y-0.3), 2.0, 0.6, boxstyle="round,pad=0.1", ec="#52B788", fc="#F7F7F7", lw=1.5)
    ax.add_patch(box)
    ax.text(x, y, s_text, ha="center", va="center", fontsize=10, fontweight="bold", color="#2D6A4F")

plt.title("Data Flow Diagram (DFD Level 1) - Detailed Process Breakdown", fontsize=14, fontweight="bold", pad=20)
plt.tight_layout()
plt.savefig('report_assets/dfd_level1.png')
plt.close()

# 3. ER Diagram
fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
ax.set_xlim(0, 11)
ax.set_ylim(0, 7)
ax.axis('off')

entities_er = [
    ("User\n(User, Farmer, Buyer)", 2.0, 5.5, "#1B4332"),
    ("Crop\n(Products)", 5.5, 5.5, "#2D6A4F"),
    ("Category", 9.0, 5.5, "#40916C"),
    ("Order", 2.0, 2.0, "#081C15"),
    ("OrderItem", 5.5, 2.0, "#1B4332"),
    ("Payment", 9.0, 2.0, "#52B788")
]

for name, x, y, col in entities_er:
    box = patches.FancyBboxPatch((x-1.2, y-0.6), 2.4, 1.2, boxstyle="square,pad=0.2", ec=col, fc="#E8F5E9", lw=2)
    ax.add_patch(box)
    ax.text(x, y, name, ha="center", va="center", fontsize=10, fontweight="bold", color=col)

# ER Lines
lines = [
    ((3.2, 5.5), (4.3, 5.5), "1 : N\nOwns"),
    ((6.7, 5.5), (7.8, 5.5), "N : 1\nBelongs"),
    ((2.0, 4.9), (2.0, 2.6), "1 : N\nPlaces"),
    ((3.2, 2.0), (4.3, 2.0), "1 : N\nContains"),
    ((6.7, 2.0), (7.8, 2.0), "1 : 1\nGenerates")
]

for start, end, label in lines:
    ax.plot([start[0], end[0]], [start[1], end[1]], color="#2D6A4F", lw=1.5, ls="--")
    mid_x, mid_y = (start[0]+end[0])/2, (start[1]+end[1])/2
    ax.text(mid_x, mid_y+0.2, label, ha="center", fontsize=8, color="#1B4332", fontweight="bold")

plt.title("Entity Relationship Diagram (ERD) - AgriConnect Database", fontsize=14, fontweight="bold", pad=20)
plt.tight_layout()
plt.savefig('report_assets/er_diagram.png')
plt.close()

# 4. System Architecture
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')

layers = [
    ("Presentation Layer\n(HTML5, CSS3, Bootstrap 5, JS)", 1.5, 3.0, "#2D6A4F"),
    ("Application Layer\n(Django Web Server, Views, URLs)", 5.0, 3.0, "#1B4332"),
    ("Data Layer\n(SQLite / PostgreSQL, Media Storage)", 8.5, 3.0, "#081C15")
]

for name, x, y, col in layers:
    box = patches.FancyBboxPatch((x-1.3, y-1.5), 2.6, 3.0, boxstyle="round,pad=0.2", ec=col, fc="#F4F9F4", lw=2)
    ax.add_patch(box)
    ax.text(x, y, name, ha="center", va="center", fontsize=10, fontweight="bold", color=col)

ax.annotate("", xy=(3.7, 3.0), xytext=(2.8, 3.0), arrowprops=dict(arrowstyle="<->", lw=2, color="#2D6A4F"))
ax.annotate("", xy=(7.2, 3.0), xytext=(6.3, 3.0), arrowprops=dict(arrowstyle="<->", lw=2, color="#2D6A4F"))

plt.title("System Architecture Diagram - 3-Tier Django Web Architecture", fontsize=14, fontweight="bold", pad=20)
plt.tight_layout()
plt.savefig('report_assets/architecture_diagram.png')
plt.close()

print("Diagrams generated successfully!")
