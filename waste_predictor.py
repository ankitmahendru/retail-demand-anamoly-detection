
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class WasteRiskPredictor:
    """Rule-based waste risk scoring system"""
    
    def __init__(self):
        self.risk_weights = {
            'current_waste': 0.25,
            'historical_waste': 0.20,
            'sales_trend': 0.20,
            'stock_level': 0.15,
            'perishability': 0.10,
            'seasonality': 0.10
        }
    
    def calculate_waste_risk(self, df):
        """Calculate waste risk score for each product"""
        df = df.copy()
        
        # Current waste score (0-100)
        df['score_current_waste'] = np.clip(df['waste_percentage'], 0, 100)
        
        # Historical waste score
        if 'waste_rolling_mean_14d' in df.columns:
            df['score_historical_waste'] = np.clip(
                df['waste_rolling_mean_14d'] / (df['stock'] + 1e-6) * 100, 0, 100
            )
        else:
            df['score_historical_waste'] = 0
        
        # Sales trend score (declining sales = higher risk)
        if 'sales_rolling_mean_7d' in df.columns and 'sales_rolling_mean_14d' in df.columns:
            trend = (df['sales_rolling_mean_7d'] - df['sales_rolling_mean_14d']) / \
                    (df['sales_rolling_mean_14d'] + 1e-6)
            df['score_sales_trend'] = np.clip((-trend + 0.5) * 100, 0, 100)
        else:
            df['score_sales_trend'] = 50
        
        # Stock level score (overstocking = higher risk)
        if 'sales_rolling_mean_7d' in df.columns:
            df['score_stock_level'] = np.clip(
                (df['stock'] / (df['sales_rolling_mean_7d'] + 1e-6) - 1) * 50, 0, 100
            )
        else:
            df['score_stock_level'] = 50
        
        # Perishability score
        df['score_perishability'] = df['perishable'].astype(int) * 100
        
        # Seasonality score (simplified - can be enhanced with actual seasonal data)
        df['score_seasonality'] = 50  # Neutral score by default
        
        # Calculate weighted risk score
        df['waste_risk_score'] = (
            df['score_current_waste'] * self.risk_weights['current_waste'] +
            df['score_historical_waste'] * self.risk_weights['historical_waste'] +
            df['score_sales_trend'] * self.risk_weights['sales_trend'] +
            df['score_stock_level'] * self.risk_weights['stock_level'] +
            df['score_perishability'] * self.risk_weights['perishability'] +
            df['score_seasonality'] * self.risk_weights['seasonality']
        )
        
        # Classify risk level
        df['risk_level'] = pd.cut(
            df['waste_risk_score'],
            bins=[0, 30, 60, 100],
            labels=['Low', 'Medium', 'High']
        )
        
        return df
    
    def get_risk_explanation(self, row):
        """Explain why a product has high waste risk"""
        explanations = []
        
        if row.get('score_current_waste', 0) > 40:
            explanations.append(
                f"Current waste is {row['waste_percentage']:.1f}% of stock"
            )
        
        if row.get('score_historical_waste', 0) > 40:
            explanations.append("Consistent waste pattern over past 2 weeks")
        
        if row.get('score_sales_trend', 0) > 60:
            explanations.append("Declining sales trend detected")
        
        if row.get('score_stock_level', 0) > 50:
            explanations.append("Stock level significantly exceeds recent sales")
        
        if row.get('perishable', False):
            explanations.append(
                f"Perishable product (shelf life: {row.get('shelf_life_days', 'N/A')} days)"
            )
        
        return " | ".join(explanations) if explanations else "Multiple minor risk factors"
    
    def get_recommendations(self, row):
        """Provide actionable recommendations"""
        recommendations = []
        risk_score = row.get('waste_risk_score', 0)
        
        if risk_score > 60:
            recommendations.append("URGENT: Consider immediate markdown (20-30% off)")
            recommendations.append("Reduce next order quantity by 30-50%")
            if row.get('perishable', False):
                recommendations.append("Move to prominent display location")
        elif risk_score > 40:
            recommendations.append("Apply promotional discount (10-15% off)")
            recommendations.append("Reduce next order quantity by 15-25%")
        
        if row.get('perishable', False) and row.get('waste_percentage', 0) > 30:
            days_left = row.get('shelf_life_days', 7) * (1 - row.get('waste_percentage', 0) / 200)
            if days_left < 2:
                recommendations.append(f"Only ~{days_left:.0f} days until expiry - urgent action needed")
        
        if row.get('sales_stock_ratio', 1) < 0.5:
            recommendations.append("Improve product placement/visibility")
        
        return recommendations if recommendations else ["Monitor closely", "Continue normal operations"]