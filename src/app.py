from flask import Flask, request, jsonify
from datetime import datetime
import pandas as pd
import logging
import json
import os

# Absolute imports (works because we run via 'python -m src.app' or set PYTHONPATH)
from src.database import DatabaseManager
from src.data_generator import RetailDataGenerator
from src.feature_engineering import FeatureEngineer
from src.anomaly_detector import AnomalyDetector
from src.waste_predictor import WasteRiskPredictor

# Setup Logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('logs/app.log'), logging.StreamHandler()]
)
logger = logging.getLogger("API")

app = Flask(__name__)

# -- Initialization --
db = DatabaseManager()
feature_engineer = FeatureEngineer()
waste_predictor = WasteRiskPredictor()
anomaly_detector = AnomalyDetector()

def initialize_system():
    """Checks for data/model on startup. Trains model if missing."""
    # Try loading model
    if not anomaly_detector.load():
        logger.info("No trained model found. Checking for data...")
        df = db.get_sales_data()
        
        if df.empty:
            logger.info("No data found. Generating synthetic startup data...")
            gen = RetailDataGenerator()
            df = gen.generate_sales_data(n_days=100, n_stores=3)
            db.store_sales_data(df)
        
        logger.info("Training initial model...")
        df = feature_engineer.engineer_features(df)
        cols = feature_engineer.get_feature_columns()
        anomaly_detector.train(df, cols)
        anomaly_detector.save()

# Run initialization explicitly
initialize_system()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "model_trained": anomaly_detector.is_trained})

@app.route('/detect-anomalies', methods=['POST'])
def detect_anomalies():
    """
    API Endpoint: Identifies anomalous sales records.
    Params: start_date, end_date, store_id, top_n
    """
    try:
        data = request.json
        # Fetch Data
        df = db.get_sales_data(data.get('start_date'), data.get('end_date'), data.get('store_id'))
        if df.empty:
            return jsonify({'error': 'No data found'}), 404
            
        # Process
        df = feature_engineer.engineer_features(df)
        preds, scores = anomaly_detector.predict(df)
        
        df['is_anomaly'] = (preds == -1).astype(int)
        df['anomaly_score'] = scores
        
        # Filter Anomalies
        anomalies = df[df['is_anomaly'] == 1].copy()
        anomalies['explanation'] = anomalies.apply(
            lambda row: anomaly_detector.get_anomaly_explanation(row, scores), axis=1
        )
        
        # Save results
        db.store_predictions(anomalies, 'anomaly_predictions', 
                             ['date', 'store_id', 'product', 'is_anomaly', 'anomaly_score', 'explanation'])
        
        # Format Response
        top_anomalies = anomalies.sort_values('anomaly_score').head(data.get('top_n', 20))
        result = top_anomalies[['date', 'store_id', 'product', 'sales', 'waste', 'explanation']].to_dict('records')
        
        return jsonify({
            'count': len(anomalies),
            'anomalies': result
        })
        
    except Exception as e:
        logger.error(f"Error in anomaly detection: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/waste-risk', methods=['POST'])
def waste_risk():
    """
    API Endpoint: Calculates waste risk for inventory.
    """
    try:
        data = request.json
        df = db.get_sales_data(data.get('start_date'), data.get('end_date'), data.get('store_id'))
        
        if df.empty:
            return jsonify({'error': 'No data found'}), 404

        df = feature_engineer.engineer_features(df)
        df = waste_predictor.calculate_risk(df)
        
        # Generate Recommendations
        df['recommendations'] = df.apply(
            lambda row: json.dumps(waste_predictor.get_recommendations(row)), axis=1
        )
        
        # Store
        db.store_predictions(df, 'waste_risk_predictions',
                             ['date', 'store_id', 'product', 'waste_risk_score', 'risk_level', 'recommendations'])
        
        high_risk = df[df['risk_level'] == 'High'].sort_values('waste_risk_score', ascending=False)
        
        # Format Response. We must parse the JSON string back to a list for the API response
        response_data = high_risk[['date', 'product', 'waste_risk_score', 'recommendations']].to_dict('records')
        for item in response_data:
            item['recommendations'] = json.loads(item['recommendations'])

        return jsonify({
            'high_risk_count': len(high_risk),
            'items': response_data
        })
        
    except Exception as e:
        logger.error(f"Error in waste risk: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-data', methods=['POST'])
def generate_data():
    """API Endpoint: Trigger synthetic data generation."""
    try:
        data = request.json
        gen = RetailDataGenerator()
        df = gen.generate_sales_data(
            n_days=data.get('n_days', 30), 
            n_stores=data.get('n_stores', 1)
        )
        db.store_sales_data(df)
        
        # Retrain model with new data
        logger.info("Retraining model with new data...")
        full_df = db.get_sales_data()
        full_df = feature_engineer.engineer_features(full_df)
        anomaly_detector.train(full_df, feature_engineer.get_feature_columns())
        anomaly_detector.save()
        
        return jsonify({'message': f'Generated {len(df)} records and retrained model.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)