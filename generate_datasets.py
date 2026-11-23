import csv
import random
from datetime import datetime, timedelta

# Set fixed seed for reproducibility and consistency
random.seed(42)

# ==========================================
# 1. GENERATE DATASET 1: Retail Products (50 Products)
# ==========================================
categories = {
    "Electronics": [
        ("Wireless Noise-Cancelling Headphones", 65.0, 130.0, 0.4, 4.8, 92, 450),
        ("4K Smart LED TV 43-Inch", 180.0, 320.0, 2.5, 4.6, 88, 120),
        ("Mechanical Gaming Keyboard", 45.0, 95.0, 0.3, 4.7, 85, 380),
        ("Ergonomic Wireless Mouse", 18.0, 42.0, 0.2, 4.5, 80, 520),
        ("Smartwatch Series 5", 85.0, 160.0, 0.2, 4.6, 90, 310),
        ("Portable Bluetooth Speaker", 30.0, 68.0, 0.4, 4.4, 82, 400),
        ("1080p Pro Streaming Webcam", 35.0, 75.0, 0.2, 4.3, 76, 290),
        ("USB-C Fast Charger 65W", 14.0, 32.0, 0.1, 4.7, 84, 600),
        ("External Portable SSD 1TB", 60.0, 115.0, 0.2, 4.8, 89, 350),
        ("Smart Home Security Camera", 40.0, 85.0, 0.3, 4.5, 83, 270),
    ],
    "Home & Kitchen": [
        ("Stainless Steel Cookware Set", 85.0, 165.0, 1.8, 4.6, 86, 160),
        ("Digital Air Fryer 5.5L", 52.0, 105.0, 1.1, 4.7, 91, 340),
        ("Robotic Vacuum Cleaner", 140.0, 270.0, 1.5, 4.5, 89, 190),
        ("Espresso Coffee Machine", 115.0, 230.0, 1.3, 4.8, 93, 210),
        ("Memory Foam Pillow Set", 24.0, 55.0, 0.9, 4.4, 78, 420),
        ("Electric Glass Kettle 1.7L", 18.0, 38.0, 0.5, 4.3, 75, 480),
        ("Non-Stick Granitestone Pan", 22.0, 48.0, 0.6, 4.5, 81, 390),
        ("Ceramic Dinnerware 16-Piece", 42.0, 90.0, 1.4, 4.2, 77, 230),
        ("Compact Microwave Oven 20L", 65.0, 125.0, 2.0, 4.4, 80, 170),
        ("High-Speed Blender 1000W", 38.0, 82.0, 0.8, 4.6, 85, 310),
    ],
    "Apparel & Footwear": [
        ("Men's Athletic Running Shoes", 48.0, 110.0, 0.7, 4.7, 90, 360),
        ("Women's High-Waist Yoga Leggings", 16.0, 42.0, 0.2, 4.8, 92, 580),
        ("Waterproof All-Weather Jacket", 55.0, 120.0, 0.8, 4.5, 84, 220),
        ("Classic Combed Cotton T-Shirt", 8.0, 22.0, 0.2, 4.4, 79, 750),
        ("Slim-Fit Stretch Denim Jeans", 26.0, 65.0, 0.5, 4.5, 83, 460),
        ("Thermal Polar Fleece Hoodie", 22.0, 52.0, 0.6, 4.3, 80, 390),
        ("Breathable Casual Sneakers", 34.0, 78.0, 0.6, 4.6, 87, 410),
        ("Genuine Leather Dress Belt", 14.0, 35.0, 0.2, 4.2, 74, 320),
        ("Heavy-Duty Travel Backpack", 32.0, 75.0, 0.9, 4.6, 88, 330),
        ("Polarized UV Sunglasses", 15.0, 45.0, 0.1, 4.5, 85, 450),
    ],
    "Health & Beauty": [
        ("Sonic Electric Toothbrush", 26.0, 62.0, 0.3, 4.7, 89, 440),
        ("Deep Tissue Percussion Massager", 42.0, 95.0, 0.7, 4.6, 87, 280),
        ("Mineral Sunscreen Lotion SPF 50", 9.0, 24.0, 0.1, 4.8, 91, 620),
        ("Hydrating Facial Cleanser 250ml", 7.5, 19.5, 0.2, 4.5, 83, 580),
        ("Ultrasonic Essential Oil Diffuser", 16.0, 36.0, 0.4, 4.3, 79, 360),
        ("Pure Vitamin C Serum 30ml", 11.0, 28.0, 0.1, 4.7, 88, 490),
        ("Ionic Ceramic Hair Dryer", 28.0, 65.0, 0.6, 4.4, 82, 310),
        ("Comprehensive First Aid Kit", 12.0, 29.0, 0.3, 4.6, 78, 250),
        ("Natural Whey Isolate Powder 1kg", 24.0, 52.0, 0.8, 4.6, 86, 380),
        ("Collagen Peptides Powder 500g", 18.0, 40.0, 0.5, 4.5, 84, 330),
    ],
    "Sports & Outdoors": [
        ("High-Density Eco Yoga Mat", 14.0, 35.0, 0.5, 4.6, 88, 470),
        ("Adjustable Quick-Dial Dumbbell 24kg", 95.0, 195.0, 1.9, 4.8, 93, 140),
        ("Resistance Exercise Band Set", 9.0, 25.0, 0.2, 4.5, 82, 530),
        ("Insulated Stainless Water Flask 1L", 11.0, 28.0, 0.3, 4.7, 89, 610),
        ("Windproof Camping Dome Tent 3P", 68.0, 145.0, 1.6, 4.5, 85, 130),
        ("Ultra-Light Aluminum Trekking Poles", 21.0, 49.0, 0.4, 4.4, 80, 260),
        ("Aerodynamic Road Cycling Helmet", 32.0, 74.0, 0.6, 4.6, 86, 210),
        ("Inflatable Stand-Up Paddle Board", 175.0, 340.0, 2.4, 4.7, 91, 85),
        ("High-Speed Weighted Jump Rope", 7.0, 18.0, 0.1, 4.3, 76, 460),
        ("Hydration Trail Running Vest", 25.0, 58.0, 0.4, 4.5, 83, 290),
    ]
}

products = []
prod_id_counter = 1

for cat, items in categories.items():
    for name, p_cost, s_price, storage, qual, attract, demand in items:
        pid = f"PROD_{prod_id_counter:03d}"
        profit = round(s_price - p_cost, 2)
        products.append({
            "Product_ID": pid,
            "Product_Name": name,
            "Category": cat,
            "Selling_Price": s_price,
            "Purchase_Cost": p_cost,
            "Profit": profit,
            "Demand": demand,
            "Quality_Score": qual,
            "Customer_Attractiveness": attract,
            "Storage_Required": storage
        })
        prod_id_counter += 1

with open("data/retail_products.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "Product_ID", "Product_Name", "Category", "Selling_Price",
        "Purchase_Cost", "Profit", "Demand", "Quality_Score",
        "Customer_Attractiveness", "Storage_Required"
    ])
    writer.writeheader()
    writer.writerows(products)

# ==========================================
# 2. GENERATE DATASET 2: Customer Information (100 Customers)
# ==========================================
segments = ["Budget Conscious", "Mid-Tier Regular", "Premium / VIP", "Young Professional"]
category_list = list(categories.keys())
genders = ["Male", "Female", "Non-Binary"]

customers = []
for i in range(1, 101):
    cid = f"CUST_{i:03d}"
    age = random.randint(19, 65)
    gender = random.choices(genders, weights=[48, 48, 4])[0]
    segment = random.choices(segments, weights=[30, 40, 15, 15])[0]
    pref_cat = random.choice(category_list)
    
    # Satisfaction score correlated with segment slightly
    sat_score = round(random.uniform(3.5, 5.0), 1)
    
    if segment == "Premium / VIP":
        monthly_spend = round(random.uniform(650.0, 1600.0), 2)
    elif segment == "Young Professional":
        monthly_spend = round(random.uniform(350.0, 850.0), 2)
    elif segment == "Mid-Tier Regular":
        monthly_spend = round(random.uniform(200.0, 550.0), 2)
    else: # Budget Conscious
        monthly_spend = round(random.uniform(70.0, 250.0), 2)
        
    customers.append({
        "Customer_ID": cid,
        "Age": age,
        "Gender": gender,
        "Customer_Segment": segment,
        "Preferred_Category": pref_cat,
        "Satisfaction_Score": sat_score,
        "Monthly_Spending": monthly_spend
    })

with open("data/customer_information.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "Customer_ID", "Age", "Gender", "Customer_Segment",
        "Preferred_Category", "Satisfaction_Score", "Monthly_Spending"
    ])
    writer.writeheader()
    writer.writerows(customers)

# ==========================================
# 3. GENERATE DATASET 3: Sales Transactions (500 Transactions)
# ==========================================
# Link transactions to existing products and customers
start_date = datetime(2026, 1, 1)
transactions = []

# Quick product lookup
prod_lookup = {p["Product_ID"]: p for p in products}
cust_ids = [c["Customer_ID"] for c in customers]
prod_ids = [p["Product_ID"] for p in products]

for i in range(1, 501):
    tx_id = f"TXN_{10000 + i}"
    pid = random.choice(prod_ids)
    cid = random.choice(cust_ids)
    prod = prod_lookup[pid]
    
    # High-cost products usually purchased in lower quantities
    if prod["Selling_Price"] > 150.0:
        qty = random.choices([1, 2], weights=[85, 15])[0]
    elif prod["Selling_Price"] > 50.0:
        qty = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
    else:
        qty = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
        
    s_price = prod["Selling_Price"]
    p_cost = prod["Purchase_Cost"]
    tot_rev = round(qty * s_price, 2)
    tot_cost = round(qty * p_cost, 2)
    tot_prof = round(tot_rev - tot_cost, 2)
    
    # Random date within past 300 days
    date_val = start_date + timedelta(days=random.randint(0, 300), hours=random.randint(8, 20), minutes=random.randint(0, 59))
    date_str = date_val.strftime("%Y-%m-%d %H:%M")
    
    transactions.append({
        "Transaction_ID": tx_id,
        "Product_ID": pid,
        "Customer_ID": cid,
        "Quantity": qty,
        "Selling_Price": s_price,
        "Total_Revenue": tot_rev,
        "Total_Cost": tot_cost,
        "Total_Profit": tot_prof,
        "Transaction_Date": date_str
    })

# Sort transactions chronologically
transactions.sort(key=lambda x: x["Transaction_Date"])

with open("data/sales_transactions.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "Transaction_ID", "Product_ID", "Customer_ID", "Quantity",
        "Selling_Price", "Total_Revenue", "Total_Cost", "Total_Profit",
        "Transaction_Date"
    ])
    writer.writeheader()
    writer.writerows(transactions)

# ==========================================
# 4. GENERATE DATASET 4: Inventory Information (50 Products)
# ==========================================
inventory = []
for p in products:
    pid = p["Product_ID"]
    pname = p["Product_Name"]
    demand = p["Demand"]
    storage_req = p["Storage_Required"]
    
    # Minimum stock is ~15-20% of monthly demand
    min_stock = max(10, int(demand * 0.15))
    # Reorder level is ~35-40% of demand
    reorder_level = int(demand * 0.38)
    # Maximum stock is ~120-150% of demand
    max_stock = int(demand * 1.3)
    # Current available stock is between reorder level and max stock
    avail_stock = random.randint(reorder_level, max_stock)
    # Storage capacity dedicated (cu ft)
    storage_cap = round(max_stock * storage_req * 1.15, 1)
    
    inventory.append({
        "Product_ID": pid,
        "Product_Name": pname,
        "Available_Stock": avail_stock,
        "Minimum_Stock": min_stock,
        "Maximum_Stock": max_stock,
        "Storage_Capacity": storage_cap,
        "Reorder_Level": reorder_level
    })

with open("data/inventory_information.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "Product_ID", "Product_Name", "Available_Stock", "Minimum_Stock",
        "Maximum_Stock", "Storage_Capacity", "Reorder_Level"
    ])
    writer.writeheader()
    writer.writerows(inventory)

# ==========================================
# 5. GENERATE DATASET 5: Supplier Information (20 Suppliers)
# ==========================================
supplier_names = [
    "Nexus Electronics Supply Co.",
    "Apex Global Tech Logistics",
    "OmniSource Component Hub",
    "Premier Kitchenware Imports",
    "Vanguard Home Essentials",
    "Apex Lifestyle Innovations",
    "Summit Apparel Distributors",
    "Metro Textile Mills Ltd.",
    "Zenith Footwear & Gear",
    "Horizon Sportswear Source",
    "BioCare Health Supplies",
    "PureLife Botanicals Ltd.",
    "DermaSource Labs International",
    "Elite Fitness Equipment Co.",
    "Peak Trail Gear Suppliers",
    "ProActive Athletics Hub",
    "AeroTech Precision Goods",
    "Nordic Living Warehouses",
    "Titan Industrial Distributors",
    "Global Prime Merchandising"
]

# Map 20 suppliers to distinct products (sampled evenly from the 50 products)
sampled_prod_indices = [int(i * (50 / 20)) for i in range(20)]
suppliers = []

for i, sup_name in enumerate(supplier_names):
    sid = f"SUP_{i+1:03d}"
    pid = products[sampled_prod_indices[i]]["Product_ID"]
    base_cost = products[sampled_prod_indices[i]]["Purchase_Cost"]
    
    # Contract purchase price with supplier (very close to baseline purchase cost, within +/- 3%)
    contract_price = round(base_cost * random.uniform(0.97, 1.02), 2)
    delivery_days = random.randint(3, 18)
    rating = round(random.uniform(4.0, 4.9), 1)
    reliability = round(random.uniform(85.0, 99.0), 1)
    
    suppliers.append({
        "Supplier_ID": sid,
        "Supplier_Name": sup_name,
        "Product_ID": pid,
        "Purchase_Price": contract_price,
        "Delivery_Time": delivery_days,
        "Supplier_Rating": rating,
        "Reliability_Score": reliability
    })

with open("data/supplier_information.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "Supplier_ID", "Supplier_Name", "Product_ID", "Purchase_Price",
        "Delivery_Time", "Supplier_Rating", "Reliability_Score"
    ])
    writer.writeheader()
    writer.writerows(suppliers)

print("SUCCESS: All 5 datasets generated successfully!")
