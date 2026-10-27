
from pathlib import Path
import csv
import random
from datetime import date, timedelta

random.seed(42)

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def write_csv(filename, rows):
    if not rows:
        return

    filepath = RAW_DIR / filename
    with filepath.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created: {filepath} ({len(rows)} rows)")


# 1. Customers
cities = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Pune"]
customers = []

for customer_id in range(1, 151):
    customers.append({
        "customer_id": customer_id,
        "customer_name": f"Customer {customer_id}",
        "email": f"customer{customer_id}@example.com",
        "city": random.choice(cities),
        "signup_date": (
            date(2025, 1, 1)
            + timedelta(days=random.randint(0, 600))
        ).isoformat()
    })

write_csv("customers.csv", customers)


# 2. Products
catalog = [
    ("Wireless Headphones", "Electronics", 2499),
    ("Running Shoes", "Fashion", 3299),
    ("Coffee Maker", "Home", 1999),
    ("Smart Watch", "Electronics", 4999),
    ("Backpack", "Fashion", 1499),
    ("Desk Lamp", "Home", 899),
    ("Bluetooth Speaker", "Electronics", 1799),
    ("Water Bottle", "Home", 499),
    ("T-Shirt", "Fashion", 799),
    ("Keyboard", "Electronics", 1299),
]

products = []

for product_id, (name, category, price) in enumerate(catalog, start=1):
    products.append({
        "product_id": product_id,
        "product_name": name,
        "category": category,
        "unit_price": price
    })

write_csv("products.csv", products)


# 3. Orders and order items in one flat source file
orders = []
start_date = date(2025, 1, 1)

for order_id in range(1, 2501):
    product = random.choice(products)
    quantity = random.randint(1, 3)
    discount_pct = random.choice([0, 0, 0, 5, 10, 15])
    gross = product["unit_price"] * quantity
    discount = round(gross * discount_pct / 100, 2)

    orders.append({
        "order_id": order_id,
        "customer_id": random.randint(1, 150),
        "product_id": product["product_id"],
        "order_date": (
            start_date + timedelta(days=random.randint(0, 599))
        ).isoformat(),
        "quantity": quantity,
        "unit_price": product["unit_price"],
        "discount_pct": discount_pct,
        "sales_amount": round(gross - discount, 2),
        "order_status": random.choices(
            ["COMPLETED", "CANCELLED", "RETURNED"],
            weights=[90, 6, 4],
            k=1
        )[0]
    })

write_csv("orders.csv", orders)


# 4. Website sessions (synthetic web analytics)
channels = ["Organic Search", "Paid Search", "Social", "Direct", "Email"]
sessions = []

for session_id in range(1, 3001):
    sessions.append({
        "session_id": session_id,
        "customer_id": random.randint(1, 150),
        "session_date": (
            start_date + timedelta(days=random.randint(0, 599))
        ).isoformat(),
        "channel": random.choice(channels),
        "device": random.choice(["Mobile", "Desktop", "Tablet"]),
        "sessions": 1,
        "conversions": random.choices([0, 1], weights=[92, 8], k=1)[0]
    })

write_csv("website_sessions.csv", sessions)


# 5. Google Trends-style interest (synthetic, not live Google data)
trends = []

for day_offset in range(0, 600, 7):
    trend_date = start_date + timedelta(days=day_offset)

    for keyword in ["wireless headphones", "running shoes", "smart watch"]:
        trends.append({
            "trend_date": trend_date.isoformat(),
            "keyword": keyword,
            "search_interest": random.randint(10, 100),
            "source": "synthetic_demo"
        })

write_csv("search_trends.csv", trends)


# 6. Inventory snapshot
inventory = []

for product in products:
    inventory.append({
        "product_id": product["product_id"],
        "snapshot_date": date.today().isoformat(),
        "stock_quantity": random.randint(0, 500),
        "reorder_level": 50
    })

write_csv("inventory.csv", inventory)

print("\nAll synthetic datasets generated successfully.")
