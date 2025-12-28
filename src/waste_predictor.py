import pandas as pd
import numpy as np

class WasteRiskPredictor:
    """
    Rule-based engine to calculate the 'Waste Risk' score of products.
    Used to generate markdown/ordering recommendations.
    """
    
    def __init__(self):
        # Weights for the scoring algorithm
        self.weights = {
            'current_waste': 0.30,
            'historical_waste': 0.20,
            'sales_trend': 0.20,
            'stock_level': 0.20,
            'perishability': 0.10
        }
    
    def calculate_risk(self, df):
        """Calculates a 0-100 Risk Score for each row."""
        df = df.copy()
        
        # 1. Current Waste Score (0-100)
        df['score_current'] = np.clip(df['waste_percentage'], 0, 100)
        
        # 2. Historical Waste Score
        # Normalize: if average waste > 20% of stock, that's max risk (score 100)
        if 'waste_rolling_mean_14d' in df.columns:
            avg_waste_pct = (df['waste_rolling_mean_14d'] / (df['stock'] + 1e-6)) * 100
            df['score_hist'] = np.clip(avg_waste_pct * 5, 0, 100)
        else:
            df['score_hist'] = 0
            
        # 3. Sales Trend Score (Dropping sales = High Risk)
        # Compare 7d avg to 14d avg. If 7d < 14d, trend is negative.
        if 'sales_rolling_mean_7d' in df.columns:
            trend = (df['sales_rolling_mean_7d'] - df['sales_rolling_mean_14d'])
            # If trend is -50% (half sales), score is high
            df['score_trend'] = np.clip(trend * -200, 0, 100) # Negative trend increases score
        else:
            df['score_trend'] = 0
            
        # 4. Stock Level Score
        # If Stock > 2x Sales, Risk is high
        if 'sales_rolling_mean_7d' in df.columns:
            coverage = df['stock'] / (df['sales_rolling_mean_7d'] + 1e-6)
            df['score_stock'] = np.clip((coverage - 1) * 50, 0, 100)
        else:
            df['score_stock'] = 0
            
        # 5. Calculate Weighted Sum
        df['waste_risk_score'] = (
            df['score_current'] * self.weights['current_waste'] +
            df['score_hist'] * self.weights['historical_waste'] +
            df['score_trend'] * self.weights['sales_trend'] +
            df['score_stock'] * self.weights['stock_level'] +
            (df['perishable'] * 100) * self.weights['perishability']
        )
        
        # 6. Assign Levels
        df['risk_level'] = pd.cut(
            df['waste_risk_score'],
            bins=[-1, 30, 60, 101],
            labels=['Low', 'Medium', 'High']
        )
        
        return df

    def get_recommendations(self, row):
        """Returns action items based on risk score."""
        recs = []
        score = row.get('waste_risk_score', 0)
        
        if score > 70:
            recs.append("URGENT: Markdown 30% immediately")
            recs.append("Halve next supplier order")
        elif score > 40:
            recs.append("Apply 15% discount")
            recs.append("Reduce order quantity")
            
        if row.get('perishable') and row.get('waste_percentage', 0) > 10:
            recs.append("Inspect quality / Check expiration")
            
        if not recs:
            recs.append("Monitor Standard Levels")
            
        return recs