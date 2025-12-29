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
    df['Date'] = pd.to_datetime(df['Date'])

# --- 3. APP INTERFACE ---
st.set_page_config(page_title="Family Fitness", page_icon="🏆")
st.title("🏃 Family Fitness Tracker")

tab1, tab2 = st.tabs(["📝 Log Workout", "📊 View Stats"])

with tab1:
    st.header("New Entry")
    
    # SMART DROPDOWN LOGIC
    default_options = ["Walking", "Running", "Cycling", "Gym", "Yoga"]
    if not df.empty and 'Workout' in df.columns:
        existing_workouts = df['Workout'].value_counts().index.tolist()
        all_options = existing_workouts + [x for x in default_options if x not in existing_workouts]
    else:
        all_options = default_options

    with st.form("workout_form", clear_on_submit=True):
        user = st.selectbox("Who are you?", ["Me", "Mom", "Dad"])
        activity = st.selectbox("Activity", all_options + ["Add New..."])
        
        # Shows only if "Add New..." is picked
        new_activity = ""
        if activity == "Add New...":
            new_activity = st.text_input("What is the new activity?")
            
        mins = st.number_input("Duration (minutes)", min_value=1, value=30)
        date = st.date_input("Date", datetime.now())
        
        submitted = st.form_submit_button("Save Workout")
        if submitted:
            final_act = new_activity if activity == "Add New..." else activity
            if final_act:
                worksheet.append_row([str(date), user, final_act, mins])
                st.success("Logged! Refreshing...")
                st.rerun()

with tab2:
    if df.empty:
        st.info("No logs yet!")
    else:
        # WEEKLY GOAL PROGRESS
        st.header("🏁 Weekly Goal")
        weekly_goal = 500 # Total family minutes
        last_7_days = df[df['Date'] > (datetime.now() - timedelta(days=7))]
        total_mins = last_7_days['Duration'].sum()
        
        progress = min(total_mins / weekly_goal, 1.0)
        st.progress(progress)
        st.write(f"The family has done **{total_mins}** / {weekly_goal} minutes this week!")

        # LEADERBOARD
        st.divider()
        st.subheader("🏆 Leaderboard (Last 7 Days)")
        leaderboard = last_7_days.groupby('Name')['Duration'].sum().sort_values(ascending=False)
        for i, (name, total) in enumerate(leaderboard.items()):
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "🏃"
            st.write(f"{medal} **{name}**: {total} mins")

        # RAW DATA
        st.divider()
        st.subheader("History")
        st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
