import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json

# Config
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="CICIDS2017 - Network Attack Detection",
    page_icon="🛡️",
    layout="wide"
)

# Session state for token
if "token" not in st.session_state:
    st.session_state.token = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ==============================
# Login Page
# ==============================
def login_page():
    st.title(" Network Attack Detection System")
    st.subheader("Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        response = requests.post(
            f"{API_URL}/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            st.session_state.token = response.json()["access_token"]
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials !")

# ==============================
# Main Dashboard
# ==============================
def main_dashboard():
    st.title(" Network Attack Detection System")
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox("Select Page", 
            ["Dashboard", " Predict", " History"])
        
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.logged_in = False
            st.rerun()
    
    if page == " Dashboard":
        dashboard_page()
    elif page == " Predict":
        predict_page()
    elif page == " History":
        history_page()

# ==============================
# Dashboard Page
# ==============================
def dashboard_page():
    st.header(" Overview")
    
    # Get model info
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    model_info = requests.get(f"{API_URL}/model-info").json()
    history = requests.get(f"{API_URL}/history", headers=headers).json()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Model", model_info["model"])
    with col2:
        st.metric("Accuracy", f"{model_info['accuracy']}%")
    with col3:
        st.metric("Total Predictions", history["total"])
    with col4:
        anomalies = sum(1 for p in history["predictions"] if p["is_anomaly"] == "True")
        st.metric("Anomalies Detected", anomalies)
    
    if history["total"] > 0:
        df = pd.DataFrame(history["predictions"])
        
        # Attack distribution
        st.subheader("Attack Type Distribution")
        fig = px.bar(
            df["attack_type"].value_counts().reset_index(),
            x="attack_type", y="count",
            color="attack_type",
            title="Detected Attack Types"
        )
        st.plotly_chart(fig, use_container_width=True)

# ==============================
# Predict Page
# ==============================
def predict_page():
    st.header(" Upload CSV for Prediction")
    
    uploaded_file = st.file_uploader("Upload CSV file", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write(f"Loaded {len(df)} rows")
        
        if st.button("Predict"):
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            data = df.to_dict(orient="records")
            
            with st.spinner("Predicting..."):
                response = requests.post(
                    f"{API_URL}/predict",
                    headers=headers,
                    json={"data": data}
                )
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"Total: {result['total']} | Anomalies: {result['anomalies']} | Normal: {result['normal']}")
                
                # Show results
                results_df = pd.DataFrame([
                    {
                        "Attack Type": r["attack_type"],
                        "Confidence": f"{r['confidence']:.2%}",
                        "Is Anomaly": "🚨" if r["is_anomaly"] else "✅"
                    }
                    for r in result["results"]
                ])
                st.dataframe(results_df)
            else:
                st.error("Prediction failed !")

# ==============================
# History Page
# ==============================
def history_page():
    st.header(" Prediction History")
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    history = requests.get(f"{API_URL}/history", headers=headers).json()
    
    if history["total"] == 0:
        st.info("No predictions yet !")
    else:
        df = pd.DataFrame(history["predictions"])
        st.dataframe(df)

# ==============================
# Main
# ==============================
if not st.session_state.logged_in:
    login_page()
else:
    main_dashboard()