import streamlit as st
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from pytz import timezone
from gspread.exceptions import APIError

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

# Function to open sheet with error handling
def open_sheet(name):
    try:
        return client.open(name)
    except APIError:
        st.error("Failed to connect to Google Sheets. Please try again later.")
        st.stop()

# --- OPEN GOOGLE SHEET ---
sheet = open_sheet(GOOGLE_SHEET_NAME)
notes_ws = sheet.worksheet(NOTES_SHEET)
bucket_ws = sheet.worksheet(BUCKET_SHEET)
calendar_ws = sheet.worksheet(CALENDAR_SHEET)
mood_ws = sheet.worksheet(MOOD_SHEET)

# --- LOAD DATA ---
@st.cache_data(ttl=60)
def fetch_data():
    notes = notes_ws.get_all_records()
    bucket = bucket_ws.get_all_values()
    calendar = calendar_ws.get_all_records()
    mood = mood_ws.get_all_records()
    return notes, bucket, calendar, mood

notes, bucket_items, calendar_items, mood_entries = fetch_data()

# --- LOGIN POPUP ---
if "current_user" not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("## Who's using the app?")
        c1, c2 = st.columns(2)
        if c1.button("La"):
            st.session_state.current_user = "La"
            st.session_state.last_login_time = datetime.now(tz)
        if c2.button("Ruan"):
            st.session_state.current_user = "Ruan"
            st.session_state.last_login_time = datetime.now(tz)
    if "current_user" not in st.session_state:
        st.stop()
    placeholder.empty()

current_user = st.session_state.current_user
last_login_time = st.session_state.get("last_login_time", datetime.now(tz) - timedelta(days=1))

# --- FILTER CALENDAR EVENTS ---
def get_events(data):
    sorted_events = sorted(data, key=lambda x: datetime.strptime(x["Date"], "%Y-%m-%d"))
    upcoming = [e for e in sorted_events if str(e.get("Completed", "")).upper() != "TRUE" and datetime.strptime(e["Date"], "%Y-%m-%d").date() >= datetime.now(tz).date()]
    past = [e for e in sorted_events if str(e.get("Completed", "")).upper() == "TRUE"]
    return upcoming, past

upcoming_events, past_events = get_events(calendar_items)
next_event = upcoming_events[0] if upcoming_events else None

# --- RECENT CHANGES ---
# Safely parse timestamps, skip empty or invalid entries
recent_notes = []
for n in notes:
    try:
        ts = datetime.strptime(n["Timestamp"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
        if ts > last_login_time:
            recent_notes.append(n)
    except Exception:
        continue

recent_bucket = []
for b in bucket_items:
    if len(b) > 1 and b[1].strip():
        try:
            ts = datetime.strptime(b[1], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
            if ts > last_login_time:
                recent_bucket.append(b[0])
        except Exception:
            continue

recent_calendar = []
for e in calendar_items:
    created = e.get("Created", "").strip()
    if created:
        try:
            ts = datetime.strptime(created, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
            if ts > last_login_time and str(e.get("Completed", "")).upper() != "TRUE":
                recent_calendar.append(e)
        except Exception:
            continue

recent_mood = []
for m in mood_entries:
    try:
        ts = datetime.strptime(m["Timestamp"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
        if ts > last_login_time:
            recent_mood.append(m)
    except Exception:
        continue

# --- PAGE STYLING ---
st.set_page_config(page_title="La & Ruan App", layout="centered", initial_sidebar_state="collapsed")
st.markdown("""
<style>
[data-testid="stAppViewContainer"]>.main { background: rgba(255,255,255,0.8) url('https://images.unsplash.com/photo-1508973371-d5bd6f29c270?fit=crop&w=800&q=80') center/cover fixed; }
textarea, input, .stButton>button, select { background: rgba(255,255,255,0.95) !important; color: #000 !important; border-radius: 8px !important; width: 100% !important; }
.stButton>button { padding: 0.5em 1em; transition: 0.3s; }
.stButton>button:hover { background: #ffea00 !important; color: #000 !important; }
.small-text { font-size: 0.9em; color: #333; }
.heart { color: red; font-size: 1.2em; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR MENU ---
menu = st.sidebar.selectbox("📂 Menu", ["🏠 Home", "💌 Notes", "📝 Bucket List", "📅 Calendar", "📊 Mood Tracker"])

# [Rest of app pages unchanged…]  # keep existing page logic below unchanged
