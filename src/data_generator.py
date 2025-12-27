
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

class RetailDataGenerator:
    """Generate synthetic retail sales data with realistic patterns"""
    
    def __init__(self, seed=42):
        # Setting seeds so results are reproducable
        # Yes this helps a LOT when debugging
        np.random.seed(seed)
        random.seed(seed)
        
        # High level product categorization
        self.categories = ['Fresh Produce', 'Dairy', 'Bakery', 'Meat', 'Frozen']
        
        # Mapping categories to actual sellable products
        self.products = {
            'Fresh Produce': ['Apples', 'Bananas', 'Lettuce', 'Tomatoes', 'Carrots'],
            'Dairy': ['Milk', 'Yogurt', 'Cheese', 'Butter', 'Cream'],
            'Bakery': ['Bread', 'Croissants', 'Muffins', 'Bagels', 'Donuts'],
            'Meat': ['Chicken', 'Beef', 'Pork', 'Fish', 'Turkey'],
            'Frozen': ['Ice Cream', 'Frozen Pizza', 'Vegetables', 'Fish Sticks', 'Berries']
        }
        
        # Approx shelf life per category in days
        # Frozen stuff basically lives forever
        self.shelf_life_days = {
            'Fresh Produce': 7, 'Dairy': 14, 'Bakery': 5,
            'Meat': 7, 'Frozen': 180
        }
    
    def generate_sales_data(self, n_days=365, n_stores=5):
        """Generate synthetic sales data with patterns and anomalies"""
        data = []
        
        # Start date goes back n_days from today
        start_date = datetime.now() - timedelta(days=n_days)
        
        # Loop through each store
        for store_id in range(1, n_stores + 1):
            for day in range(n_days):
                current_date = start_date + timedelta(days=day)
                day_of_week = current_date.weekday()
                
                # Weekends sell more, shocker
                weekend_multiplier = 1.3 if day_of_week >= 5 else 1.0
                
                # Loop through every product in every category
                for category, products in self.products.items():
                    for product in products:
                        
                        # Base demand with some randomness and store variation
                        base_demand = np.random.normal(100, 20) * (0.8 + store_id * 0.1)
                        
                        # Smooth yearly seasonality using sine wave
                        seasonal_factor = 1 + 0.2 * np.sin(2 * np.pi * day / 365)
                        
                        # Final demand calculation
                        demand = base_demand * weekend_multiplier * seasonal_factor
                        demand = max(0, demand)
                        
                        # Stock is intentionally a bit higher than expected demand
                        stock = demand * np.random.uniform(1.1, 1.4)
                        
                        # You cant sell more than you stock
                        sales = min(demand, stock)
                        
                        # Randomly inject weird behavior to simulate real life chaos
                        # About 5 percent of rows will be odd
                        if np.random.random() < 0.05:
                            if np.random.random() < 0.5:
                                # Sudden spike, maybe promotion or supply issue
                                sales *= np.random.uniform(2.5, 4.0)
                            else:
                                # Sudden drop, maybe quality or competition
                                sales *= np.random.uniform(0.1, 0.3)
                        
                        # Waste is what didnt sell
                        waste = max(0, stock - sales)
                        waste_pct = (waste / stock * 100) if stock > 0 else 0
                        
                        # Append one full row of data
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
                            'day_of_week': day_of_week
                        })
        
        # Convert list of dicts into a DataFrame
        return pd.DataFrame(data)
    
    def add_metadata(self, df):
        """Add product metadata"""
        # Attach shelf life info per category
        df['shelf_life_days'] = df['category'].map(self.shelf_life_days)
        
        # Flag items that can rot and make managers sad
        df['perishable'] = df['category'].isin(
            ['Fresh Produce', 'Dairy', 'Bakery', 'Meat']
        )
        return df

