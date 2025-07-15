import streamlit as st
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from pytz import timezone
import time

# --- TIMEZONE SETUP ---
tz = timezone("Africa/Harare")

# --- CONFIG ---
MET_DATE = datetime(2025, 6, 23, tzinfo=tz)
GOOGLE_SHEET_NAME = "La & Ruan App"
NOTES_SHEET = "Notes"
BUCKET_SHEET = "BucketList"
CALENDAR_SHEET = "Calendar"
MOOD_SHEET = "MoodTracker"

# --- AUTHENTICATION ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# --- OPEN GOOGLE SHEET ---
sheet = client.open(GOOGLE_SHEET_NAME)
notes_ws = sheet.worksheet(NOTES_SHEET)
bucket_ws = sheet.worksheet(BUCKET_SHEET)
calendar_ws = sheet.worksheet(CALENDAR_SHEET)
mood_ws = sheet.worksheet(MOOD_SHEET)

# --- LOAD DATA ---
notes = notes_ws.get_all_records()
bucket_items = bucket_ws.get_all_values()
calendar_items = calendar_ws.get_all_records()
mood_entries = mood_ws.get_all_records()

# --- LOGIN POPUP ---
if "current_user" not in st.session_state:
    login_placeholder = st.empty()
    with login_placeholder.container():
        st.markdown("## Who's using the app?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("La"):
                st.session_state.current_user = "La"
                st.session_state.last_login_time = datetime.now(tz)
                login_placeholder.empty()
                st.rerun()
        with col2:
            if st.button("Ruan"):
                st.session_state.current_user = "Ruan"
                st.session_state.last_login_time = datetime.now(tz)
                login_placeholder.empty()
                st.rerun()
    st.stop()

current_user = st.session_state.current_user
last_login_time = st.session_state.get("last_login_time", datetime.now(tz) - timedelta(days=1))

# --- FILTER CALENDAR EVENTS ---
calendar_items_sorted = sorted(calendar_items, key=lambda x: datetime.strptime(x["Date"], "%Y-%m-%d"))
upcoming_events = [e for e in calendar_items_sorted if str(e.get("Completed", "")).strip().upper() != "TRUE" and datetime.strptime(e["Date"], "%Y-%m-%d").date() >= datetime.now(tz).date()]
past_events = [e for e in calendar_items_sorted if str(e.get("Completed", "")).strip().upper() == "TRUE"]
next_event = upcoming_events[0] if upcoming_events else None

# --- RECENT CHANGES ---
recent_notes = [n for n in notes if tz.localize(datetime.strptime(n["Timestamp"], "%Y-%m-%d %H:%M:%S")) > last_login_time]
recent_bucket = [item[0] for item in bucket_items if len(item) > 1 and item[1] and tz.localize(datetime.strptime(item[1], "%Y-%m-%d %H:%M:%S")) > last_login_time]
recent_calendar = [e for e in calendar_items if tz.localize(datetime.strptime(e["Created"], "%Y-%m-%d %H:%M:%S")) > last_login_time and str(e.get("Completed", "")).strip().upper() != "TRUE"]
recent_mood = [m for m in mood_entries if tz.localize(datetime.strptime(m["Timestamp"], "%Y-%m-%d %H:%M:%S")) > last_login_time]

# --- PAGE STYLING ---
st.set_page_config(page_title="La & Ruan App", layout="centered", initial_sidebar_state="collapsed")
page_bg_img = """
<style>
[data-testid="stAppViewContainer"] > .main {
    background-image: url('https://images.unsplash.com/photo-1508973371-d5bd6f29c270?fit=crop&w=800&q=80');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: #333333;
}
[data-testid="stMarkdownContainer"] h1, h2, h3 {
    color: #222222;
    text-align: center;
}
textarea, input, .stButton>button, select {
    background-color: rgba(255, 255, 255, 0.95) !important;
    color: #000000 !important;
    font-weight: 500;
    border-radius: 8px;
    width: 100%;
}
.stButton>button {
    padding: 0.5em 1em;
    transition: all 0.3s ease-in-out;
}
.stButton>button:hover {
    background-color: #ffea00 !important;
    color: #000;
}
.small-text {
    font-size: 0.9em;
    color: #333;
}
.heart {
    color: red;
    font-size: 1.2em;
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- SIDEBAR MENU ---
menu = st.sidebar.selectbox("📂 Menu", ["🏠 Home", "💌 Notes", "📝 Bucket List", "📅 Calendar", "📊 Mood Tracker"])

# --- HOME PAGE ---
if menu == "🏠 Home":
    st.markdown(f"<h1 style='text-align: center;'>🌻 La & Ruan 🌻</h1>", unsafe_allow_html=True)
    st.success(f"Welcome back, {current_user}! 🥰")
    days = (datetime.now(tz) - MET_DATE).days
    st.markdown(f"<h3 style='text-align: center;'>💛 We've been talking for <strong>{days} days</strong>.</h3>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        oaty_path = "oaty_and_la.png"
        if os.path.exists(oaty_path):
            st.image(oaty_path, caption="🐾 La & Oaty", use_container_width=True)
    with col2:
        ruan_path = "ruan.jpg"
        if os.path.exists(ruan_path):
            st.image(ruan_path, caption="🚴‍♂️ Ruan", use_container_width=True)

    st.subheader("🔔 New Since Your Last Visit")
    if recent_notes:
        st.markdown("**📝 New Note(s):**")
        for n in recent_notes:
            st.markdown(f"📅 *{n['Timestamp']}* — **{n['Name']}**: {n['Message']}")
    if recent_bucket:
        st.markdown(f"**🗺️ New Bucket List Item:** {recent_bucket[-1]}")
    if recent_calendar:
        event = recent_calendar[-1]
        st.markdown(f"**📅 New Event:** {event['Date']} - {event['Title']}: {event['Details']}")
    if recent_mood:
        mood = recent_mood[-1]
        st.markdown(f"**🧠 Mood Update:** {mood['Name']} felt {mood['Mood']} — {mood['Note']}")

    if next_event:
        event_datetime = datetime.strptime(next_event["Date"], "%Y-%m-%d").replace(tzinfo=tz)
        time_left = event_datetime - datetime.now(tz)
        days_left = time_left.days
        hours, rem = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        st.info(f"📅 Next event in {days_left} days: **{next_event['Title']}** — {next_event['Date']}")
        st.markdown(f"<p style='text-align:center; font-size: 0.9em;'>�
