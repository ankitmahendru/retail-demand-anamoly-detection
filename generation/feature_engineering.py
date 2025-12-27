
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

class FeatureEngineer:
    """Engineer features for anomaly detection and waste prediction"""
    
    def __init__(self):
        # StandardScaler is here if you wanna scale later
        self.scaler = StandardScaler()
        
    def create_temporal_features(self, df):
        """Create time-based features"""
        df = df.copy()
        
        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Basic calendar features
        df['day_of_year'] = df['date'].dt.dayofyear
        df['week_of_year'] = df['date'].dt.isocalendar().week
        df['month'] = df['date'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Cyclical encoding so models dont think sunday and monday are far apart
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        return df
    
    def create_rolling_features(self, df, windows=[7, 14, 30]):
        """Create rolling window statistics"""
        df = df.copy()
        
        # Sorting is critical before rolling, dont skip this
        df = df.sort_values(['store_id', 'product', 'date'])
        
        for window in windows:
            # Rolling mean of sales
            df[f'sales_rolling_mean_{window}d'] = (
                df.groupby(['store_id', 'product'])['sales']
                .transform(lambda x: x.rolling(window, min_periods=1).mean())
            )
            
            # Rolling std dev of sales
            df[f'sales_rolling_std_{window}d'] = (
                df.groupby(['store_id', 'product'])['sales']
                .transform(lambda x: x.rolling(window, min_periods=1).std())
            )
            
            # Rolling waste mean
            df[f'waste_rolling_mean_{window}d'] = (
                df.groupby(['store_id', 'product'])['waste']
                .transform(lambda x: x.rolling(window, min_periods=1).mean())
            )
        
        # Replace NaNs from early rolling windows
        df = df.fillna(0)
        return df
    
    def create_ratio_features(self, df):
        """Create ratio-based features"""
        df = df.copy()
        
        # Ratio of what sold vs what was stocked
        # Tiny epsilon avoids divide by zero drama
        df['sales_stock_ratio'] = df['sales'] / (df['stock'] + 1e-6)
        
        # How far today is from recent average
        if 'sales_rolling_mean_7d' in df.columns:
            df['sales_deviation_7d'] = (
                (df['sales'] - df['sales_rolling_mean_7d']) /
                (df['sales_rolling_std_7d'] + 1e-6)
            )
        
        # Higher means less waste
        df['waste_efficiency'] = 1 - (df['waste'] / (df['stock'] + 1e-6))
        
        return df
    
    def create_aggregate_features(self, df):
        """Create product and store-level aggregates"""
        df = df.copy()
        
        # Product level historical behavior
        product_stats = df.groupby('product').agg({
            'sales': ['mean', 'std'],
            'waste_percentage': 'mean'
        }).reset_index()
        
        product_stats.columns = [
            'product', 'product_sales_mean',
            'product_sales_std', 'product_waste_mean'
        ]
        
        df = df.merge(product_stats, on='product', how='left')
        
        # Store level behavior
        store_stats = df.groupby('store_id').agg({
            'sales': 'mean',
            'waste_percentage': 'mean'
        }).reset_index()
        
        store_stats.columns = [
            'store_id', 'store_sales_mean', 'store_waste_mean'
        ]
        
        df = df.merge(store_stats, on='store_id', how='left')
        
        return df
    
    def engineer_features(self, df):
        """Full feature engineering pipeline"""
        df = self.create_temporal_features(df)
        df = self.create_rolling_features(df)
        df = self.create_ratio_features(df)
        df = self.create_aggregate_features(df)
        return df
    
    def get_feature_columns(self):
        """Return list of feature columns for modeling"""
        # Central place to control what goes into the model
        return [
            'sales', 'stock', 'waste', 'waste_percentage', 'price',
            'day_of_week', 'is_weekend', 'day_sin', 'day_cos',
            'month_sin', 'month_cos', 'shelf_life_days',
            'sales_rolling_mean_7d', 'sales_rolling_std_7d',
            'sales_rolling_mean_14d', 'sales_rolling_std_14d',
            'waste_rolling_mean_7d', 'waste_rolling_mean_14d',
            'sales_stock_ratio', 'sales_deviation_7d', 'waste_efficiency',
            'product_sales_mean', 'product_sales_std', 'product_waste_mean',
            'store_sales_mean', 'store_waste_mean'
        ]
