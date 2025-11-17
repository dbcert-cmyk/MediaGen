#!/usr/bin/env python3
"""
Setup script to create sample data for the Agent Data Flow Visualizer demo.
Creates:
- SQLite database with e-commerce data
- Sample JSON files (IoT sensors, user analytics)
- Sample CSV files (sales reports, logs)
"""

import sqlite3
import json
import csv
import os
from datetime import datetime, timedelta
import random

# Configuration
DB_PATH = "data/demo.db"
SAMPLE_FILES_DIR = "data/sample_files"

def create_directories():
    """Create necessary directories"""
    os.makedirs("data", exist_ok=True)
    os.makedirs(SAMPLE_FILES_DIR, exist_ok=True)
    print("✓ Created directories")

def create_database():
    """Create SQLite database with e-commerce tables"""
    print("\nCreating SQLite database...")

    # Remove existing database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            city TEXT,
            signup_date TEXT,
            lifetime_value REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price REAL,
            stock INTEGER,
            rating REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            total_amount REAL,
            order_date TEXT,
            status TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE analytics_events (
            id INTEGER PRIMARY KEY,
            event_type TEXT,
            event_data TEXT,
            timestamp TEXT
        )
    """)

    print("✓ Created tables")

    # Insert sample customers
    customers = [
        ("Alice Johnson", "alice@example.com", "San Francisco", "2023-01-15", 2450.00),
        ("Bob Smith", "bob@example.com", "New York", "2023-02-20", 1890.50),
        ("Carol Davis", "carol@example.com", "Chicago", "2023-03-10", 3200.75),
        ("David Wilson", "david@example.com", "Austin", "2023-04-05", 1250.00),
        ("Emma Brown", "emma@example.com", "Seattle", "2023-05-12", 4100.25),
        ("Frank Miller", "frank@example.com", "Boston", "2023-06-08", 875.50),
        ("Grace Lee", "grace@example.com", "Denver", "2023-07-15", 2680.00),
        ("Henry Chen", "henry@example.com", "Portland", "2023-08-20", 1540.75),
    ]

    cursor.executemany(
        "INSERT INTO customers (name, email, city, signup_date, lifetime_value) VALUES (?, ?, ?, ?, ?)",
        customers
    )
    print(f"✓ Inserted {len(customers)} customers")

    # Insert sample products
    products = [
        ("Laptop Pro 15", "Electronics", 1299.99, 45, 4.5),
        ("Wireless Mouse", "Electronics", 29.99, 150, 4.2),
        ("Mechanical Keyboard", "Electronics", 89.99, 80, 4.7),
        ("4K Monitor", "Electronics", 399.99, 30, 4.4),
        ("USB-C Hub", "Electronics", 49.99, 200, 4.0),
        ("Noise-Canceling Headphones", "Electronics", 249.99, 60, 4.8),
        ("Webcam HD", "Electronics", 79.99, 95, 4.1),
        ("Desk Lamp LED", "Office", 34.99, 120, 4.3),
        ("Ergonomic Chair", "Office", 299.99, 25, 4.6),
        ("Standing Desk", "Office", 499.99, 15, 4.5),
        ("Coffee Maker", "Kitchen", 89.99, 50, 4.4),
        ("Blender Pro", "Kitchen", 129.99, 40, 4.7),
    ]

    cursor.executemany(
        "INSERT INTO products (name, category, price, stock, rating) VALUES (?, ?, ?, ?, ?)",
        products
    )
    print(f"✓ Inserted {len(products)} products")

    # Insert sample orders
    orders = []
    base_date = datetime.now() - timedelta(days=90)

    for i in range(150):
        customer_id = random.randint(1, 8)
        product_id = random.randint(1, 12)
        quantity = random.randint(1, 5)

        # Get product price (simplified - in real scenario would fetch from DB)
        product_price = products[product_id - 1][2]
        total = round(product_price * quantity, 2)

        order_date = (base_date + timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d")
        status = random.choice(["completed", "completed", "completed", "pending", "shipped"])

        orders.append((customer_id, product_id, quantity, total, order_date, status))

    cursor.executemany(
        "INSERT INTO orders (customer_id, product_id, quantity, total_amount, order_date, status) VALUES (?, ?, ?, ?, ?, ?)",
        orders
    )
    print(f"✓ Inserted {len(orders)} orders")

    # Insert sample analytics events
    events = []
    event_types = ["page_view", "button_click", "form_submit", "purchase", "search"]

    for i in range(500):
        event_type = random.choice(event_types)
        event_data = json.dumps({
            "page": random.choice(["/home", "/products", "/cart", "/checkout", "/account"]),
            "user_id": random.randint(1, 8),
            "session_id": f"sess_{random.randint(1000, 9999)}"
        })
        timestamp = (datetime.now() - timedelta(hours=random.randint(0, 720))).isoformat()

        events.append((event_type, event_data, timestamp))

    cursor.executemany(
        "INSERT INTO analytics_events (event_type, event_data, timestamp) VALUES (?, ?, ?)",
        events
    )
    print(f"✓ Inserted {len(events)} analytics events")

    conn.commit()
    conn.close()
    print(f"✓ Database created at: {DB_PATH}")

def create_json_files():
    """Create sample JSON files"""
    print("\nCreating JSON files...")

    # IoT Sensor Data
    sensor_data = {
        "device_id": "sensor_001",
        "location": "Warehouse A",
        "readings": []
    }

    base_time = datetime.now() - timedelta(hours=24)
    for i in range(100):
        reading = {
            "timestamp": (base_time + timedelta(minutes=i*15)).isoformat(),
            "temperature": round(20 + random.uniform(-5, 10), 2),
            "humidity": round(45 + random.uniform(-10, 20), 2),
            "pressure": round(1013 + random.uniform(-20, 20), 2)
        }
        sensor_data["readings"].append(reading)

    with open(f"{SAMPLE_FILES_DIR}/sensor_data.json", "w") as f:
        json.dump(sensor_data, f, indent=2)
    print(f"✓ Created sensor_data.json ({len(sensor_data['readings'])} readings)")

    # User Analytics
    user_analytics = {
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "metrics": {
            "total_users": 1245,
            "active_users": 892,
            "new_signups": 47,
            "churn_rate": 3.2,
            "avg_session_duration": 342
        },
        "top_pages": [
            {"page": "/products", "views": 8924, "avg_time": 145},
            {"page": "/home", "views": 6543, "avg_time": 89},
            {"page": "/cart", "views": 2341, "avg_time": 234},
            {"page": "/checkout", "views": 1567, "avg_time": 456},
            {"page": "/account", "views": 987, "avg_time": 178}
        ]
    }

    with open(f"{SAMPLE_FILES_DIR}/user_analytics.json", "w") as f:
        json.dump(user_analytics, f, indent=2)
    print("✓ Created user_analytics.json")

    # API Response Log
    api_logs = []
    endpoints = ["/api/users", "/api/products", "/api/orders", "/api/analytics"]
    methods = ["GET", "POST", "PUT", "DELETE"]

    for i in range(200):
        log_entry = {
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 1440))).isoformat(),
            "endpoint": random.choice(endpoints),
            "method": random.choice(methods),
            "status_code": random.choice([200, 200, 200, 201, 400, 404, 500]),
            "response_time_ms": random.randint(50, 2000),
            "user_id": random.randint(1, 8)
        }
        api_logs.append(log_entry)

    with open(f"{SAMPLE_FILES_DIR}/api_logs.json", "w") as f:
        json.dump(api_logs, f, indent=2)
    print(f"✓ Created api_logs.json ({len(api_logs)} entries)")

def create_csv_files():
    """Create sample CSV files"""
    print("\nCreating CSV files...")

    # Sales Report
    with open(f"{SAMPLE_FILES_DIR}/sales_report.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Product", "Category", "Units_Sold", "Revenue", "Region"])

        products = [
            ("Laptop Pro 15", "Electronics"),
            ("Wireless Mouse", "Electronics"),
            ("Mechanical Keyboard", "Electronics"),
            ("Coffee Maker", "Kitchen"),
        ]

        regions = ["North", "South", "East", "West"]
        base_date = datetime.now() - timedelta(days=30)

        for i in range(100):
            date = (base_date + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
            product, category = random.choice(products)
            units = random.randint(1, 20)
            revenue = round(units * random.uniform(50, 500), 2)
            region = random.choice(regions)

            writer.writerow([date, product, category, units, revenue, region])

    print("✓ Created sales_report.csv")

    # Server Logs
    with open(f"{SAMPLE_FILES_DIR}/server_logs.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Level", "Service", "Message", "Duration_ms"])

        levels = ["INFO", "INFO", "INFO", "WARN", "ERROR"]
        services = ["api-gateway", "auth-service", "database", "cache", "worker"]
        messages = [
            "Request processed successfully",
            "Connection established",
            "Query executed",
            "Cache miss",
            "Slow query detected",
            "Connection timeout",
            "Authentication failed",
            "Rate limit exceeded"
        ]

        for i in range(500):
            timestamp = (datetime.now() - timedelta(minutes=random.randint(0, 1440))).isoformat()
            level = random.choice(levels)
            service = random.choice(services)
            message = random.choice(messages)
            duration = random.randint(10, 5000) if "slow" in message.lower() else random.randint(10, 500)

            writer.writerow([timestamp, level, service, message, duration])

    print("✓ Created server_logs.csv")

def main():
    """Main setup function"""
    print("=" * 60)
    print("Agent Data Flow Visualizer - Data Setup")
    print("=" * 60)

    create_directories()
    create_database()
    create_json_files()
    create_csv_files()

    print("\n" + "=" * 60)
    print("✓ Setup complete!")
    print("=" * 60)
    print("\nSample data created:")
    print(f"  - Database: {DB_PATH}")
    print(f"    • 8 customers")
    print(f"    • 12 products")
    print(f"    • 150 orders")
    print(f"    • 500 analytics events")
    print(f"\n  - Sample files in: {SAMPLE_FILES_DIR}")
    print(f"    • sensor_data.json (100 readings)")
    print(f"    • user_analytics.json")
    print(f"    • api_logs.json (200 entries)")
    print(f"    • sales_report.csv (100 rows)")
    print(f"    • server_logs.csv (500 rows)")
    print("\nYou can now run: python app.py")

if __name__ == "__main__":
    main()
