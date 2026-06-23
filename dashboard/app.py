import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from streamlit_autorefresh import st_autorefresh

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="CICIDS2017 - Network Attack Detection",
    page_icon="🛡️",
    layout="wide"
)

if "token" not in st.session_state:
    st.session_state.token = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    st.title("🛡️ Network Attack Detection System")
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

def dashboard_page():
    st_autorefresh(interval=5000, key="datarefresh")

    st.title("🛡️ Network Attack Detection — Live Dashboard")

    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    history = requests.get(f"{API_URL}/history", headers=headers).json()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Predictions", history["total"])
    with col2:
        anomalies = sum(1 for p in history["predictions"] if p["is_anomaly"] == "True")
        st.metric("Anomalies Detected", anomalies)
    with col3:
        normal = history["total"] - anomalies
        st.metric("Normal Traffic", normal)

    if history["total"] > 0:
        df = pd.DataFrame(history["predictions"])

        st.subheader("Attack Type Distribution")
        fig = px.bar(
            df["attack_type"].value_counts().reset_index(),
            x="attack_type", y="count",
            color="attack_type"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Recent Predictions")
        st.dataframe(df[["timestamp", "username", "attack_type", "confidence", "is_anomaly"]])
    else:
        st.info("No predictions yet. Waiting for live traffic...")

if not st.session_state.logged_in:
    login_page()
else:
    dashboard_page()
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.token = None
        st.rerun()