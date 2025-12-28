import pandas as pd
import sqlite3
from datetime import datetime
import os
import sys

# --- PATH FIX ---
# Add the project root to Python's path so 'src' is found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ----------------

from src.database import DatabaseManager

class DataLoader:
    def __init__(self, db_path='data/retail_sales.db'):
        self.db = DatabaseManager(db_path)

    def load_csv(self, file_path):
        """
        Reads a CSV file and imports it into the database.
        Assumes columns: Date, Product, Category, Sales, Stock, Waste, Price
        """
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return

        print(f"READING: {file_path}...")
        try:
            # Read CSV
            df = pd.read_csv(file_path)
            
            # STANDARDISATION: Rename columns to match our database schema
            # Update this mapping if your CSV headers are different
            column_mapping = {
                'Date': 'date',
                'Product': 'product',
                'Category': 'category',
                'Sales': 'sales', 
                'Stock': 'stock',
                'Waste': 'waste',
                'Price': 'price'
            }
            
            # Normalize headers (lowercase, strip spaces) for easier matching
            df.columns = [c.strip() for c in df.columns]
            
            # Rename available columns
            df = df.rename(columns=column_mapping)
            
            # VALIDATION: Check for required columns
            required = ['date', 'product', 'category', 'sales', 'stock', 'waste', 'price']
            missing = [col for col in required if col not in df.columns]
            if missing:
                print(f"❌ Missing columns in CSV: {missing}")
                return

            # FORMATTING
            df['date'] = pd.to_datetime(df['date']).dt.date
            df['store_id'] = 1  # Default to store 1 if not specified
            
            # Calculated fields needed by the database
            df['waste_percentage'] = 0.0
            mask = df['stock'] > 0
            df.loc[mask, 'waste_percentage'] = (df.loc[mask, 'waste'] / df.loc[mask, 'stock']) * 100
            
            # Shelf life defaults (can be updated later)
            shelf_life_map = {
                'Produce': 7, 'Dairy': 14, 'Bakery': 3, 'Meat': 5, 'Frozen': 180
            }
            df['shelf_life_days'] = df['category'].map(shelf_life_map).fillna(30)
            df['perishable'] = df['category'].isin(['Produce', 'Dairy', 'Bakery', 'Meat']).astype(int)
            df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek

            # INSERT
            print(f"LOADING: {len(df)} records into database...")
            self.db.store_sales_data(df)
            print("✅ Data Import Complete!")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")

if __name__ == "__main__":
    # Test run
    loader = DataLoader()
    # Create a dummy file for testing if none exists
    if not os.path.exists('store_data.csv'):
        print("Creating sample store_data.csv for you...")
        data = {
            'Date': ['2023-10-01', '2023-10-02'],
            'Product': ['Milk', 'Bread'],
            'Category': ['Dairy', 'Bakery'],
            'Sales': [20, 15],
            'Stock': [25, 20],
            'Waste': [1, 2],
            'Price': [2.50, 3.00]
        }
        pd.DataFrame(data).to_csv('store_data.csv', index=False)
    
    loader.load_csv('store_data.csv')