import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

class RetailDataGenerator:
    """
    Generates synthetic retail data that mimics real-world patterns.
    Includes seasonality, weekly cycles, and random noise/anomalies.
    """
    
    def __init__(self, seed=42):
        np.random.seed(seed)
        random.seed(seed)
        
        self.categories = ['Fresh Produce', 'Dairy', 'Bakery', 'Meat', 'Frozen']
        self.products = {
            'Fresh Produce': ['Apples', 'Bananas', 'Lettuce', 'Tomatoes', 'Carrots'],
            'Dairy': ['Milk', 'Yogurt', 'Cheese', 'Butter', 'Cream'],
            'Bakery': ['Bread', 'Croissants', 'Muffins', 'Bagels', 'Donuts'],
            'Meat': ['Chicken', 'Beef', 'Pork', 'Fish', 'Turkey'],
            'Frozen': ['Ice Cream', 'Frozen Pizza', 'Vegetables', 'Fish Sticks', 'Berries']
        }
        self.shelf_life_days = {
            'Fresh Produce': 7, 'Dairy': 14, 'Bakery': 5, 'Meat': 7, 'Frozen': 180
        }
    
    def generate_sales_data(self, n_days=365, n_stores=5):
        """Generates a DataFrame of daily sales data."""
        data = []
        start_date = datetime.now() - timedelta(days=n_days)
        
        for store_id in range(1, n_stores + 1):
            for day in range(n_days):
                current_date = start_date + timedelta(days=day)
                # 0=Monday, 6=Sunday
                is_weekend = current_date.weekday() >= 5
                
                # Base multiplier: Weekends are busier (1.3x)
                weekend_multiplier = 1.3 if is_weekend else 1.0
                
                for category, prod_list in self.products.items():
                    for product in prod_list:
                        # 1. Determine Demand
                        # Random base demand + Store variation
                        base = np.random.normal(100, 20) * (0.8 + store_id * 0.1)
                        # Yearly seasonality (Sine wave)
                        seasonality = 1 + 0.2 * np.sin(2 * np.pi * day / 365)
                        
                        demand = max(0, base * weekend_multiplier * seasonality)
                        
                        # 2. Determine Stock
                        # Stock is usually 10-40% higher than expected demand
                        stock = demand * np.random.uniform(1.1, 1.4)
                        
                        # 3. Determine Sales
                        # Can't sell more than you have
                        sales = min(demand, stock)
                        
                        # 4. Inject Anomalies (5% chance)
                        if np.random.random() < 0.05:
                            if np.random.random() < 0.5:
                                # Spike (e.g., panic buying)
                                sales *= np.random.uniform(2.5, 4.0)
                            else:
                                # Dip (e.g., snowstorm, bad quality)
                                sales *= np.random.uniform(0.1, 0.3)
                        
                        # 5. Calculate Waste
                        waste = max(0, stock - sales)
                        waste_pct = (waste / stock * 100) if stock > 0 else 0
                        
                        data.append({
                            'date': current_date.date(),
                            'store_id': store_id,
                            'category': category,
                            'product': product,
                            'sales': round(sales, 2),
                            'stock': round(stock, 2),
                            'waste': round(waste, 2),
                            'waste_percentage': round(waste_pct, 2),
                            'price': round(np.random.uniform(2, 15), 2),
                            'day_of_week': current_date.weekday()
                        })
                        
        df = pd.DataFrame(data)
        return self.add_metadata(df)
    
    def add_metadata(self, df):
        """Enriches the dataframe with static product metadata."""
        df['shelf_life_days'] = df['category'].map(self.shelf_life_days)
        df['perishable'] = df['category'].isin(
            ['Fresh Produce', 'Dairy', 'Bakery', 'Meat']
        ).astype(int)
        return df