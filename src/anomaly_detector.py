from sklearn.ensemble import IsolationForest
import joblib
import logging
import os

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """
    Unsupervised Anomaly Detection using Isolation Forest.
    Detects outliers in sales data (spikes, drops, unusual waste).
    """
    
    def __init__(self, contamination=0.05):
        # Contamination = expected percentage of outliers in the dataset
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.feature_cols = []
        self.is_trained = False
    
    def train(self, df, feature_cols):
        """Trains the model on the provided dataframe."""
        self.feature_cols = feature_cols
        # Fill NaNs to ensure training doesn't fail
        X = df[feature_cols].fillna(0)
        
        logger.info(f"Training Isolation Forest on {len(X)} samples.")
        self.model.fit(X)
        self.is_trained = True
        return self
    
    def predict(self, df):
        """Returns predictions (-1: Anomaly, 1: Normal) and anomaly scores."""
        if not self.is_trained:
            raise ValueError("Model is not trained.")
            
        X = df[self.feature_cols].fillna(0)
        preds = self.model.predict(X)
        scores = self.model.score_samples(X) # Lower score = more anomalous
        
        return preds, scores
    
    def get_anomaly_explanation(self, row, scores):
        """Generates a human-readable reason for the anomaly."""
        explanations = []
        
        # 1. Check Sales Deviation (Z-Score)
        if 'sales_deviation_7d' in row.index and abs(row['sales_deviation_7d']) > 2:
            direction = "higher" if row['sales_deviation_7d'] > 0 else "lower"
            explanations.append(f"Sales {abs(row['sales_deviation_7d']):.1f}x std dev {direction} than normal")
            
        # 2. Check Waste
        if row.get('waste_percentage', 0) > 30:
            explanations.append(f"High waste: {row['waste_percentage']:.1f}%")
            
        # 3. Check Stocking Efficiency
        if row.get('sales_stock_ratio', 0) < 0.3:
            explanations.append("Overstocked (Low sales-to-stock ratio)")
            
        if not explanations:
            explanations.append("Unusual combination of factors")
            
        return " | ".join(explanations)
    
    def save(self, path='models/isolation_forest.pkl'):
        """Persists the model to disk."""
        if not self.is_trained:
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({'model': self.model, 'cols': self.feature_cols}, path)
        logger.info(f"Model saved to {path}")
        
    def load(self, path='models/isolation_forest.pkl'):
        """Loads the model from disk."""
        if not os.path.exists(path):
            return False
        data = joblib.load(path)
        self.model = data['model']
        self.feature_cols = data['cols']
        self.is_trained = True
        logger.info(f"Model loaded from {path}")
        return True