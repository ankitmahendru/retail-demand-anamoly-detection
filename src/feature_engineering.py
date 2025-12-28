import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

class FeatureEngineer:
    """
    Transforms raw sales data into features suitable for Machine Learning.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def engineer_features(self, df):
        """Master pipeline to run all feature creation steps."""
        if df.empty:
            return df
            
        df = df.copy()
        df = self.create_temporal_features(df)
        df = self.create_rolling_features(df)
        df = self.create_ratio_features(df)
        df = self.create_aggregate_features(df)
        return df

    def create_temporal_features(self, df):
        """Extracts date-related features including cyclical encodings."""
        df['date'] = pd.to_datetime(df['date'])
        
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Cyclical encoding for Day and Month (preserves 23:59 -> 00:00 continuity)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        return df
    
    def create_rolling_features(self, df, windows=[7, 14]):
        """Calculates moving averages and standard deviations."""
        # Sorting is strictly required for rolling window calculations
        df = df.sort_values(['store_id', 'product', 'date'])
        
        for window in windows:
            # We group by store/product so window doesn't bleed across products
            grouper = df.groupby(['store_id', 'product'])
            
            # Rolling Sales
            df[f'sales_rolling_mean_{window}d'] = grouper['sales'].transform(
                lambda x: x.rolling(window, min_periods=1).mean())
            df[f'sales_rolling_std_{window}d'] = grouper['sales'].transform(
                lambda x: x.rolling(window, min_periods=1).std())
                
            # Rolling Waste
            df[f'waste_rolling_mean_{window}d'] = grouper['waste'].transform(
                lambda x: x.rolling(window, min_periods=1).mean())
                
        return df.fillna(0)
    
    def create_ratio_features(self, df):
        """Calculates efficiency ratios."""
        # Add epsilon (1e-6) to prevent DivisionByZero errors
        df['sales_stock_ratio'] = df['sales'] / (df['stock'] + 1e-6)
        
        # Calculate Z-Score deviation from 7-day mean
        if 'sales_rolling_mean_7d' in df.columns:
            df['sales_deviation_7d'] = (
                (df['sales'] - df['sales_rolling_mean_7d']) /
                (df['sales_rolling_std_7d'] + 1e-6)
            )
            
        df['waste_efficiency'] = 1 - (df['waste'] / (df['stock'] + 1e-6))
        return df
    
    def create_aggregate_features(self, df):
        """Adds global stats per product/store to each row."""
        # Product global stats
        prod_stats = df.groupby('product').agg({
            'sales': ['mean', 'std'],
            'waste_percentage': 'mean'
        }).reset_index()
        prod_stats.columns = ['product', 'prod_sales_mean', 'prod_sales_std', 'prod_waste_mean']
        
        # Store global stats
        store_stats = df.groupby('store_id').agg({
            'sales': 'mean', 
            'waste_percentage': 'mean'
        }).reset_index()
        store_stats.columns = ['store_id', 'store_sales_mean', 'store_waste_mean']
        
        df = df.merge(prod_stats, on='product', how='left')
        df = df.merge(store_stats, on='store_id', how='left')
        return df

    def get_feature_columns(self):
        """Defines the exact columns used for model training."""
        return [
            'sales', 'stock', 'waste', 'waste_percentage', 'price',
            'day_of_week', 'is_weekend', 'day_sin', 'day_cos',
            'month_sin', 'month_cos', 'shelf_life_days',
            'sales_rolling_mean_7d', 'sales_rolling_std_7d',
            'sales_rolling_mean_14d', 'sales_rolling_std_14d',
            'waste_rolling_mean_7d', 'sales_stock_ratio', 
            'sales_deviation_7d', 'waste_efficiency',
            'prod_sales_mean', 'prod_sales_std', 'prod_waste_mean',
            'store_sales_mean', 'store_waste_mean'
        ]