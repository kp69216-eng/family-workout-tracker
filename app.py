import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- 1. CONNECTION SETUP ---
try:
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    else:
        creds = Credentials.from_service_account_file("creds.json", scopes=scope)
    
    client = gspread.authorize(creds)
    sh = client.open("Family Workout Tracker")
    worksheet = sh.get_worksheet(0)
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- 2. DATA LOADING ---
raw_data = worksheet.get_all_records()
df = pd.DataFrame(raw_data)
if not df.empty:
    df['Date'] = pd.to_datetime(df['Date']).dt.date # Keep only the date part

# --- 3. APP INTERFACE ---
st.set_page_config(page_title="Family Fitness", page_icon="🏆")
st.title("🏃 Family Fitness Tracker")

tab1, tab2 = st.tabs(["📝 Log Workout", "📊 View Stats"])

with tab1:
    st.header("New Entry")
    default_options = ["Walking", "Running", "Cycling", "Gym", "Yoga"]
    if not df.empty and 'Workout' in df.columns:
        all_options = df['Workout'].value_counts().index.tolist()
        all_options = all_options + [x for x in default_options if x not in all_options]
    else:
        all_options = default_options

    with st.form("workout_form", clear_on_submit=True):
        user = st.selectbox("Who are you?", ["Me", "Mom", "Dad"])
        activity = st.selectbox("Activity", all_options + ["Add New..."])
        new_activity = st.text_input("New activity name") if activity == "Add New..." else ""
        mins = st.number_input("Duration (minutes)", min_value=1, value=30)
        date = st.date_input("Date", datetime.now().date())
        
        if st.form_submit_button("Save Workout"):
            final_act = new_activity if activity == "Add New..." else activity
            if final_act:
                worksheet.append_row([str(date), user, final_act, mins])
                st.success("Logged!")
                st.rerun()

with tab2:
    if df.empty:
        st.info("No logs yet! Start moving!")
    else:
        st.header("📅 Consistency Tracker")
        
        # Calculate current dates
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday()) # Monday
        start_of_month = today.replace(day=1)

        # Filters for analysis
        df_weekly = df[df['Date'] >= start_of_week]
        df_monthly = df[df['Date'] >= start_of_month]

        # Function to count unique days per person
        def get_day_counts(dataframe):
            return dataframe.groupby('Name')['Date'].nunique()

        weekly_days = get_day_counts(df_weekly)
        monthly_days = get_day_counts(df_monthly)

        # --- Display Stats ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Days This Week")
            for name in ["Me", "Mom", "Dad"]:
                count = weekly_days.get(name, 0)
                st.write(f"**{name}**: {count} / 7 days")
        
        with col2:
            st.subheader("Days This Month")
            for name in ["Me", "Mom", "Dad"]:
                count = monthly_days.get(name, 0)
                st.write(f"**{name}**: {count} days total")

        st.divider()
        st.subheader("🔥 Habit Strength")
        # Visualizing monthly consistency
        st.bar_chart(monthly_days)

        with st.expander("Show Full History"):
            st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
