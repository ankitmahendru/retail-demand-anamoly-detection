import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import sys
import os

# --- PATH FIX ---
# Add the parent directory to Python's path so it can find the 'src' package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ----------------

# Now these imports will work correctly
from src.database import DatabaseManager
from src.feature_engineering import FeatureEngineer
from src.waste_predictor import WasteRiskPredictor
from src.anomaly_detector import AnomalyDetector

# Page Config
st.set_page_config(page_title="Retail Smart Manager", layout="wide")

# ... (The rest of the file remains exactly the same)
# Import our backend logic
from src.database import DatabaseManager
from src.feature_engineering import FeatureEngineer
from src.waste_predictor import WasteRiskPredictor
from src.anomaly_detector import AnomalyDetector

# Page Config
st.set_page_config(page_title="Retail Smart Manager", layout="wide")

# Initialize Logic
db = DatabaseManager()
fe = FeatureEngineer()
waste_model = WasteRiskPredictor()
anomaly_model = AnomalyDetector()

# --- HEADER ---
st.title("🛒 Retail Demand & Waste Manager")
st.markdown("Optimize stock, reduce waste, and protect revenue.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Settings")
store_id = st.sidebar.selectbox("Select Store", [1, 2, 3])
days_lookback = st.sidebar.slider("Analysis Period (Days)", 7, 90, 30)

if st.sidebar.button("🔄 Run Full Analysis"):
    with st.spinner("Analyzing Sales & Waste Patterns..."):
        # Fetch fresh data
        df = db.get_sales_data(store_id=store_id)
        if not df.empty:
            # 1. Feature Engineering
            df = fe.engineer_features(df)
            
            # 2. Train/Predict Anomalies
            if not anomaly_model.is_trained:
                cols = fe.get_feature_columns()
                anomaly_model.train(df, cols)
            preds, scores = anomaly_model.predict(df)
            df['anomaly_score'] = scores
            df['is_anomaly'] = (preds == -1)
            
            # 3. Calculate Waste Risk
            df = waste_model.calculate_risk(df)
            df['recommendations'] = df.apply(lambda row: json.dumps(waste_model.get_recommendations(row)), axis=1)
            
            # Save results back to DB for history
            db.store_predictions(df, 'waste_risk_predictions', 
                               ['date', 'store_id', 'product', 'waste_risk_score', 'risk_level', 'recommendations'])
            st.success("Analysis Complete!")
        else:
            st.error("No data found for this store.")

# --- MAIN DASHBOARD ---

# Load Data for Visualization
df = db.get_sales_data(store_id=store_id)

if df.empty:
    st.warning("No data loaded yet. Please use the Data Loader to import your CSV.")
    st.stop()

# Ensure dates are datetime
df['date'] = pd.to_datetime(df['date'])
# Filter by date slider
latest_date = df['date'].max()
start_date = latest_date - pd.Timedelta(days=days_lookback)
mask = (df['date'] >= start_date) & (df['date'] <= latest_date)
filtered_df = df.loc[mask]

# 1. KPI ROW
col1, col2, col3, col4 = st.columns(4)

total_revenue = (filtered_df['sales'] * filtered_df['price']).sum()
total_waste_cost = (filtered_df['waste'] * filtered_df['price']).sum()
waste_rate = (filtered_df['waste'].sum() / filtered_df['stock'].sum()) * 100
revenue_saved = total_waste_cost * 0.3  # Estimate if we markdown items instead of tossing them

col1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
col2.metric("Lost to Waste", f"₹{total_waste_cost:,.2f}", delta_color="inverse")
col3.metric("Avg Waste Rate", f"{waste_rate:.1f}%")
col4.metric("Potential Savings", f"₹{revenue_saved:,.2f}", help="Estimated savings if high-risk items are marked down early")

# 2. ACTION CENTER (The most important part for you)
st.markdown("### 🚨 Action Center: High Waste Risk Items")
st.info("These items are predicted to spoil or are overstocked. **Action required.**")

# Load latest risk predictions
try:
    risk_df = fe.engineer_features(filtered_df)
    risk_df = waste_model.calculate_risk(risk_df)
    
    # Get only the most recent status for each product
    latest_risk = risk_df.sort_values('date').groupby('product').tail(1)
    high_risk = latest_risk[latest_risk['risk_level'] == 'High'].sort_values('waste_risk_score', ascending=False)
    
    if not high_risk.empty:
        # Format for display
        display_cols = ['product', 'stock', 'waste_percentage', 'risk_level', 'waste_risk_score']
        
        for idx, row in high_risk.head(5).iterrows():
            with st.expander(f"🔴 {row['product']} (Risk Score: {row['waste_risk_score']:.0f})"):
                c1, c2 = st.columns([3, 1])
                recs = waste_model.get_recommendations(row)
                c1.write("**Recommendations:**")
                for r in recs:
                    c1.markdown(f"- {r}")
                
                c2.metric("Current Stock", int(row['stock']))
                c2.metric("Recent Waste %", f"{row['waste_percentage']:.1f}%")
    else:
        st.success("No high-risk items detected right now! Good job.")
except Exception as e:
    st.error(f"Could not calculate risk: {e}")

# 3. CHARTS
st.markdown("### 📊 Trends & Analysis")
tab1, tab2 = st.tabs(["Sales vs Waste", "Anomaly Detection"])

with tab1:
    # Daily aggregation
    daily = filtered_df.groupby('date')[['sales', 'waste']].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily['date'], y=daily['sales'], name='Sales', line=dict(color='green')))
    fig.add_trace(go.Bar(x=daily['date'], y=daily['waste'], name='Waste', marker=dict(color='red')))
    fig.update_layout(title="Daily Sales vs Waste", barmode='overlay')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.write("Anomalies detect unusual spikes in sales (panic buying) or waste (fridge failure).")
    try:
        # Re-run prediction quickly for visualization
        anom_df = risk_df.copy() # Reuse engineered features
        if not anomaly_model.is_trained:
             # Just a fallback if button wasn't pressed
             cols = fe.get_feature_columns()
             anomaly_model.train(anom_df, cols)
        
        preds, scores = anomaly_model.predict(anom_df)
        anom_df['is_anomaly'] = (preds == -1)
        
        anomalies = anom_df[anom_df['is_anomaly']]
        if not anomalies.empty:
            fig_anom = px.scatter(
                anom_df, x='date', y='sales', 
                color='is_anomaly', 
                color_discrete_map={True: 'red', False: 'blue'},
                hover_data=['product', 'waste'],
                title="Sales Anomalies Over Time"
            )
            st.plotly_chart(fig_anom, use_container_width=True)
            
            st.dataframe(anomalies[['date', 'product', 'sales', 'waste', 'explanation']].head(10))
        else:
            st.write("No anomalies detected in the selected period.")
            
    except Exception as e:
        st.write("Click 'Run Full Analysis' to see anomalies.")