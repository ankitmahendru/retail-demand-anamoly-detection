import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Settings
NUM_ENTRIES = 1500
OUTPUT_FILE = 'store_data.csv'

# Setup realistic products
products_map = {
    'Produce': ['Gala Apples', 'Bananas', 'Romaine Lettuce', 'Carrots', 'Tomatoes'],
    'Dairy': ['Whole Milk', 'Greek Yogurt', 'Cheddar Cheese', 'Butter'],
    'Bakery': ['Sourdough Bread', 'Bagels', 'Croissants', 'Muffins'],
    'Meat': ['Chicken Breast', 'Ground Beef', 'Pork Chops', 'Salmon Fillet'],
    'Frozen': ['Ice Cream', 'Frozen Pizza', 'Mixed Vegetables']
}

data = []
start_date = datetime.now() - timedelta(days=90)

print(f"Generating {NUM_ENTRIES} rows of test data...")

for i in range(NUM_ENTRIES):
    # Randomly pick a category and product
    category = random.choice(list(products_map.keys()))
    product = random.choice(products_map[category])
    
    # Random date within the last 90 days
    random_days = random.randint(0, 90)
    date = start_date + timedelta(days=random_days)
    
    # Generate realistic numbers
    stock = random.randint(20, 100)
    
    # Sales depend on stock (can't sell more than you have)
    # Most days you sell 40-90% of stock
    sales_ratio = random.uniform(0.4, 0.9)
    sales = int(stock * sales_ratio)
    
    # Waste is usually low, but sometimes spikes (random anomaly)
    if random.random() < 0.05: # 5% chance of high waste anomaly
        waste = int((stock - sales) * random.uniform(0.8, 1.0)) # Rotten batch
    else:
        waste = int((stock - sales) * random.uniform(0.0, 0.1)) # Normal waste
        
    price = round(random.uniform(1.99, 15.99), 2)

    data.append({
        'Date': date.strftime('%Y-%m-%d'),
        'Product': product,
        'Category': category,
        'Sales': sales,
        'Stock': stock,
        'Waste': waste,
        'Price': price
    })

# Save to CSV
df = pd.DataFrame(data)
df.to_csv(OUTPUT_FILE, index=False)

print(f"✅ Success! Saved {len(df)} rows to '{OUTPUT_FILE}'")
print("You can now run 'python -m src.data_loader' to import this into your dashboard.")