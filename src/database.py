import sqlite3
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Handles all interactions with the SQLite database.
    Ensures thread-safe connections by creating a new connection per request.
    """
    
    def __init__(self, db_path='data/retail_sales.db'):
        self.db_path = db_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Creates the necessary tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Sales Data: Stores raw transaction/daily summary data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                store_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                product TEXT NOT NULL,
                sales REAL NOT NULL,
                stock REAL NOT NULL,
                waste REAL NOT NULL,
                waste_percentage REAL NOT NULL,
                price REAL NOT NULL,
                day_of_week INTEGER,
                shelf_life_days INTEGER,
                perishable INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Anomaly Predictions: Stores results from the Isolation Forest model
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anomaly_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                store_id INTEGER NOT NULL,
                product TEXT NOT NULL,
                is_anomaly INTEGER NOT NULL,
                anomaly_score REAL NOT NULL,
                explanation TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3. Waste Risk: Stores results from the rule-based risk engine
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS waste_risk_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                store_id INTEGER NOT NULL,
                product TEXT NOT NULL,
                waste_risk_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                explanation TEXT,
                recommendations TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_sales_data(self, df):
        """Bulk inserts sales data into the database."""
        if df.empty:
            return
        conn = sqlite3.connect(self.db_path)
        df.to_sql('sales_data', conn, if_exists='append', index=False)
        conn.close()
        logger.info(f"Stored {len(df)} sales records.")
    
    def get_sales_data(self, start_date=None, end_date=None, store_id=None):
        """
        Fetches sales data with optional filtering.
        Returns a Pandas DataFrame.
        """
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM sales_data WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        if store_id:
            query += " AND store_id = ?"
            params.append(store_id)
            
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    def store_predictions(self, df, table_name, columns):
        """Generic helper to store predictions (anomalies or waste risk)."""
        if df.empty:
            return
        conn = sqlite3.connect(self.db_path)
        # Filter dataframe to only relevant columns before inserting
        df[columns].to_sql(table_name, conn, if_exists='append', index=False)
        conn.close()