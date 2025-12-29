import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- 1. CONNECTION SETUP ---
# This part looks for your Google Secrets in the Streamlit Dashboard
try:
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    # If running on Streamlit Cloud, use Secrets. If local, use creds.json
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    else:
        creds = Credentials.from_service_account_file("creds.json", scopes=scope)
    
    client = gspread.authorize(creds)
    # MUST match your Google Sheet name exactly
    sh = client.open("Family Workout Tracker")
    worksheet = sh.get_worksheet(0)
except Exception as e:
    st.error(f"Waiting for Configuration: {e}")
    st.stop()

# --- 2. APP INTERFACE ---
st.set_page_config(page_title="Family Workout Log", page_icon="💪")
st.title("🏃 Family Fitness Tracker")

tab1, tab2 = st.tabs(["📝 Log Workout", "📊 View Stats"])

# --- TAB 1: LOGGING DATA ---
with tab1:
    st.header("Log Today's Work")
    with st.form("workout_form", clear_on_submit=True):
        user = st.selectbox("Who are you?", ["Me", "Mom", "Dad"])
        activity = st.selectbox("Activity", ["Walking", "Running", "Cycling", "Gym", "Yoga", "Other"])
        mins = st.number_input("Duration (minutes)", min_value=1, value=30)
        date = st.date_input("Date", datetime.now())
        
        submitted = st.form_submit_button("Save Workout")
        if submitted:
            worksheet.append_row([str(date), user, activity, mins])
            st.balloons()
            st.success(f"Log saved for {user}!")

# --- TAB 2: CALCULATING STATS ---
with tab2:
    # Fetch data from Google Sheets
    raw_data = worksheet.get_all_records()
    if not raw_data:
        st.info("No data found yet. Go log a workout!")
    else:
        df = pd.DataFrame(raw_data)
        df['Date'] = pd.to_datetime(df['Date'])
        
        st.header("Workout Statistics")
        
        # Filter Logic
        view = st.radio("Timeframe", ["Last 7 Days", "This Month", "All Time"], horizontal=True)
        
        now = datetime.now()
        if view == "Last 7 Days":
            start_date = now - timedelta(days=7)
            df_filtered = df[df['Date'] >= start_date]
        elif view == "This Month":
            df_filtered = df[df['Date'].dt.month == now.month]
        else:
            df_filtered = df

        # Metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Workouts", len(df_filtered))
        with col2:
            st.metric("Total Minutes", df_filtered['Duration'].sum())

        # Charts
        st.subheader("Workouts by Family Member")
        chart_data = df_filtered.groupby('Name').size()
        st.bar_chart(chart_data)
        
        st.subheader("Recent Logs")
        st.dataframe(df_filtered.sort_values(by="Date", ascending=False), use_container_width=True)