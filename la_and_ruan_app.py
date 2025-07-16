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
recent_notes = [n for n in notes if datetime.strptime(n["Timestamp"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz) > last_login_time]
recent_bucket = [b[0] for b in bucket_items if len(b) > 1 and datetime.strptime(b[1], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz) > last_login_time]
recent_calendar = [e for e in calendar_items if datetime.strptime(e.get("Created", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz) > last_login_time and str(e.get("Completed", "")).upper() != "TRUE"]
recent_mood = [m for m in mood_entries if datetime.strptime(m["Timestamp"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz) > last_login_time]

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

# --- HOME PAGE ---
if menu == "🏠 Home":
    st.markdown("<h1 align='center'>🌻 La & Ruan 🌻</h1>", unsafe_allow_html=True)
    st.success(f"Welcome back, {current_user}! 🥰")
    days = (datetime.now(tz) - MET_DATE).days
    st.markdown(f"<h3 align='center'>💛 {days} days together</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    if os.path.exists("oaty_and_la.png"): col1.image("oaty_and_la.png", caption="La & Oaty 🐾", use_container_width=True)
    if os.path.exists("ruan.jpg"): col2.image("ruan.jpg", caption="Ruan 🚴‍♂️", use_container_width=True)
    st.subheader("🔔 Updates since you last visited")
    if recent_notes:
        st.markdown("**📝 Notes:**")
        for n in recent_notes:
            st.markdown(f"*{n['Timestamp']}* — **{n['Name']}**: {n['Message']}")
    if recent_bucket:
        st.markdown(f"**🗺️ Bucket:** {recent_bucket[-1]}")
    if recent_calendar:
        ev = recent_calendar[-1]
        st.markdown(f"**📅 Event:** {ev['Date']} — {ev['Title']}")
    if recent_mood:
        m = recent_mood[-1]
        st.markdown(f"**🧠 Mood:** {m['Name']} felt {m['Mood']}")
    if next_event:
        dt = datetime.strptime(next_event['Date'], "%Y-%m-%d").replace(tzinfo=tz)
        diff = dt - datetime.now(tz)
        d, sec = diff.days, diff.seconds
        h, m = divmod(sec, 3600)[0], divmod(sec % 3600, 60)[0]
        s = sec % 60
        st.info(f"Next: {next_event['Title']} in {d}d {h}h {m}m {s}s")

# --- NOTES PAGE ---
elif menu == "💌 Notes":
    st.header("💌 Notes")
    with st.form("note_form"):
        msg = st.text_area("Your note")
        if st.form_submit_button("Send") and msg:
            notes_ws.append_row([current_user, msg, datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"), ""])
            notes, bucket_items, calendar_items, mood_entries = fetch_data()
            st.success("Sent!")
    for n in sorted(notes, key=lambda x: x['Timestamp'], reverse=True):
        heart = '❤️' if n.get('LikedBy') and n['LikedBy'] != current_user else ''
        c1, c2 = st.columns([9, 1])
        c1.markdown(f"*{n['Timestamp']}* — **{n['Name']}**: {n['Message']} {heart}")
        if n['Name'] != current_user and not n.get('LikedBy'):
            if c2.button('❤️', key=n['Timestamp']):
                notes_ws.update_cell(notes.index(n)+2, 4, current_user)

# --- BUCKET LIST PAGE ---
elif menu == "📝 Bucket List":
    st.header("📝 Bucket List")
    if 'del_b' in st.session_state:
        r = st.session_state.del_b
        st.warning("Delete?")
        if st.button('Yes'): bucket_ws.delete_row(r); notes, bucket_items, calendar_items, mood_entries = fetch_data(); del st.session_state['del_b']; st.success('Deleted')
        if st.button('No'): del st.session_state['del_b']
    for i, item in enumerate(bucket_items):
        c1, c2 = st.columns([9, 1])
        c1.markdown(f"✅ {item[0]}")
        if c2.button('🗑️', key=f"del_b_{i}"): st.session_state['del_b'] = i+2
    with st.form('bucket_form'):
        ni = st.text_input('New')
        if st.form_submit_button('Add') and ni:
            bucket_ws.append_row([ni, datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")])
            notes, bucket_items, calendar_items, mood_entries = fetch_data()
            st.success('Added')

# --- CALENDAR PAGE ---
elif menu == "📅 Calendar":
    st.header("📅 Calendar")
    view = st.radio('View', ['Upcoming', 'Past'])
    events = upcoming_events if view == 'Upcoming' else past_events
    if 'del_c' in st.session_state:
        rc = st.session_state.del_c
        st.warning('Delete event?')
        if st.button('Yes'): calendar_ws.delete_row(rc); notes, bucket_items, calendar_items, mood_entries = fetch_data(); upcoming_events, past_events = get_events(calendar_items); del st.session_state['del_c']; st.success('Deleted')
        if st.button('No'): del st.session_state['del_c']
    for idx, e in enumerate(events):
        ridx = calendar_items.index(e) + 2
        c1, c2 = st.columns([8, 1])
        c1.markdown(f"{e['Date']} — **{e['Title']}**")
        c1.markdown(e['Details'])
        c1.markdown(f"<span class='small-text'>Pack: {e['Packing']}</span>", unsafe_allow_html=True)
        if c2.button('🗑️', key=f"del_c_{idx}"): st.session_state['del_c'] = ridx
    with st.form('calendar_form'):
        t = st.text_input('Title')
        d = st.date_input('Date')
        desc = st.text_area('Details')
        p = st.text_input('Pack')
        if st.form_submit_button('Add') and t:
            calendar_ws.append_row([str(d), t, desc, p, datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"), "", ""])
            notes, bucket_items, calendar_items, mood_entries = fetch_data()
            upcoming_events, past_events = get_events(calendar_items)
            st.success('Added')

# --- MOOD TRACKER PAGE ---
elif menu == "📊 Mood Tracker":
    st.header("📊 Mood Tracker")
    opts = ["😊 Happy","😔 Sad","😤 Frustrated","❤️ In Love","😴 Tired","😎 Confident","Custom"]
    with st.form('mood_form'):
        m = st.selectbox('Mood', opts)
        custom = ''
        if m == 'Custom': custom = st.text_input('Custom mood')
        note = st.text_area('Note')
        if st.form_submit_button('Submit'):
            mood_ws.append_row([current_user, custom if custom else m, note, datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")])
            notes, bucket_items, calendar_items, mood_entries = fetch_data()
            st.success('Logged')
    st.subheader('Past Moods')
    for m in reversed(mood_entries):
        st.markdown(f"*{m['Timestamp']}* — **{m['Name']}** felt *{m['Mood']}* — {m['Note']}")
