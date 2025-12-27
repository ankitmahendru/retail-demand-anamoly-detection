
from sklearn.ensemble import IsolationForest
import numpy as np
import joblib
import logging

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """Detect anomalies in sales data using Isolation Forest"""
    
    def __init__(self, contamination=0.05, random_state=42):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
            max_samples='auto',
            max_features=1.0
        )
        self.feature_cols = None
        self.is_trained = False
    
    def train(self, X, feature_cols):
        """Train the isolation forest model"""
        self.feature_cols = feature_cols
        X_train = X[feature_cols].fillna(0)
        
        logger.info(f"Training Isolation Forest on {len(X_train)} samples")
        self.model.fit(X_train)
        self.is_trained = True
        
        logger.info("Training complete")
        return self
    
    def predict(self, X):
        """Predict anomalies (-1 for anomaly, 1 for normal)"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        X_pred = X[self.feature_cols].fillna(0)
        predictions = self.model.predict(X_pred)
        scores = self.model.score_samples(X_pred)
        
        return predictions, scores
    
    def get_anomaly_explanation(self, row, scores):
        """Explain why a record is flagged as anomalous"""
        explanations = []
        
        # Check sales deviation
        if 'sales_deviation_7d' in row.index and abs(row['sales_deviation_7d']) > 2:
            direction = "higher" if row['sales_deviation_7d'] > 0 else "lower"
            explanations.append(
                f"Sales are {abs(row['sales_deviation_7d']):.1f} std devs {direction} than 7-day average"
            )
        
        # Check waste percentage
        if row.get('waste_percentage', 0) > 30:
            explanations.append(f"High waste percentage: {row['waste_percentage']:.1f}%")
        
        # Check sales-stock ratio
        if row.get('sales_stock_ratio', 0) < 0.3:
            explanations.append(f"Low sales-to-stock ratio: {row['sales_stock_ratio']:.2f}")
        
        # Check anomaly score
        anomaly_percentile = (scores < row.get('anomaly_score', 0)).sum() / len(scores) * 100
        explanations.append(f"Anomaly score in bottom {100-anomaly_percentile:.1f}% of records")
        
        return " | ".join(explanations) if explanations else "General pattern deviation"
    
    def save_model(self, path):
        """Save trained model to disk"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        joblib.dump(self, path)
        logger.info(f"Model saved to {path}")
    
    @staticmethod
    def load_model(path):
        """Load trained model from disk"""
        model = joblib.load(path)
        logger.info(f"Model loaded from {path}")
        return model
