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
    # Ensure Date column is handled correctly
    df['Date'] = pd.to_datetime(df['Date']).dt.date

# --- 3. APP INTERFACE ---
st.set_page_config(page_title="Family Fitness Tracker", page_icon="🏆", layout="centered")
st.title("🏃 Family Fitness Tracker")

tab1, tab2 = st.tabs(["📝 Log Workout", "📊 View Stats"])

# --- TAB 1: LOGGING DATA ---
with tab1:
    st.header("New Entry")
    
    # Logic to build the dropdown list
    default_options = ["Walking", "Running", "Cycling", "Gym", "Yoga"]
    if not df.empty and 'Workout' in df.columns:
        existing_workouts = df['Workout'].unique().tolist()
        all_options = sorted(list(set(existing_workouts + default_options)))
    else:
        all_options = sorted(default_options)
    
    all_options.append("➕ Add New...")

    with st.form("workout_form", clear_on_submit=True):
        user = st.selectbox("Who are you?", ["Me", "Mom", "Dad"])
        
        activity_choice = st.selectbox("Activity", all_options)
        
        # This box appears instantly if "Add New..." is selected
        new_activity_name = ""
        if activity_choice == "➕ Add New...":
            new_activity_name = st.text_input("Enter the new activity name:")
            
        mins = st.number_input("Duration (minutes)", min_value=1, value=30)
        date = st.date_input("Date", datetime.now().date())
        
        if st.form_submit_button("Save Workout"):
            final_act = new_activity_name if activity_choice == "➕ Add New..." else activity_choice
            
            if not final_act:
                st.error("Please provide an activity name!")
            else:
                worksheet.append_row([str(date), user, final_act, mins])
                st.success(f"Successfully logged {final_act}!")
                st.rerun()

# --- TAB 2: CALCULATING STATS ---
with tab2:
    if df.empty:
        st.info("No data found yet. Go log a workout!")
    else:
        # 1. TIME CALCULATIONS
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday()) # Monday
        start_of_month = today.replace(day=1)

        df_weekly = df[df['Date'] >= start_of_week]
        df_monthly = df[df['Date'] >= start_of_month]

        # 2. FREQUENCY STATS (Number of Days)
        st.header("📅 Consistency (Days Active)")
        
        def get_day_counts(dataframe):
            if dataframe.empty: return pd.Series(dtype=int)
            return dataframe.groupby('Name')['Date'].nunique()

        weekly_days = get_day_counts(df_weekly)
        monthly_days = get_day_counts(df_monthly)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("This Week")
            for name in ["Me", "Mom", "Dad"]:
                d = weekly_days.get(name, 0)
                st.write(f"**{name}**: {d} / 7 days")
        
        with col2:
            st.subheader("This Month")
            for name in ["Me", "Mom", "Dad"]:
                d = monthly_days.get(name, 0)
                st.write(f"**{name}**: {d} days")

        # 3. LEADERBOARD (Total Minutes)
        st.divider()
        st.header("🏆 Minutes Leaderboard")
        leaderboard = df_weekly.groupby('Name')['Duration'].sum().sort_values(ascending=False)
        
        if not leaderboard.empty:
            for i, (name, total) in enumerate(leaderboard.items()):
                medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "🏃"
                st.write(f"{medal} **{name}**: {total} mins this week")
        else:
            st.write("No workouts this week yet!")

        # 4. RAW HISTORY
        st.divider()
        with st.expander("See Raw History"):
            st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
