import streamlit as st
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from pytz import timezone

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
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("## Who's using the app?")
        c1, c2 = st.columns(2)
        if c1.button("La"):
            st.session_state.current_user = "La"
            st.session_state.last_login = datetime.now(tz)
            placeholder.empty()
        if c2.button("Ruan"):
            st.session_state.current_user = "Ruan"
            st.session_state.last_login = datetime.now(tz)
            placeholder.empty()
    st.stop()

current_user = st.session_state.current_user
last_login = st.session_state.get("last_login", datetime.now(tz) - timedelta(days=1))

# --- CALENDAR FILTERS ---
calendar_sorted = sorted(calendar_items, key=lambda x: datetime.strptime(x["Date"], "%Y-%m-%d"))
upcoming = [e for e in calendar_sorted if str(e.get("Completed", "")).upper() != "TRUE" and datetime.strptime(e["Date"], "%Y-%m-%d").date() >= datetime.now(tz).date()]
past = [e for e in calendar_sorted if str(e.get("Completed", "")).upper() == "TRUE"]
next_event = upcoming[0] if upcoming else None

# --- RECENT SINCE LAST LOGIN ---
recent_notes = [n for n in notes if tz.localize(datetime.strptime(n["Timestamp"], "%Y-%m-%d %H:%M:%S")) > last_login]
recent_bucket = [b[0] for b in bucket_items if len(b) > 1 and b[1] and tz.localize(datetime.strptime(b[1], "%Y-%m-%d %H:%M:%S")) > last_login]
recent_events = [e for e in calendar_items if tz.localize(datetime.strptime(e.get("Created", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")) > last_login and str(e.get("Completed", "")).upper() != "TRUE"]
recent_mood = [m for m in mood_entries if tz.localize(datetime.strptime(m["Timestamp"], "%Y-%m-%d %H:%M:%S")) > last_login]

# --- STYLING ---
st.set_page_config(page_title="La & Ruan App", layout="centered", initial_sidebar_state="collapsed")
st.markdown("""
<style>
[data-testid="stAppViewContainer"]>.main { background: rgba(255,255,255,0.8); }
h1, h2, h3 { text-align: center; }
textarea, input, button, select { border-radius: 8px; }
button:hover { background: #ffea00; }
.small-text { font-size: .9em; }
.heart { color: red; }
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
menu = st.sidebar.selectbox("Menu", ["🏠 Home", "💌 Notes", "📝 Bucket List", "📅 Calendar", "📊 Mood Tracker"])

# --- HOME ---
if menu == "🏠 Home":
    st.title("🌻 La & Ruan 🌻")
    st.success(f"Welcome back, {current_user}!")
    days = (datetime.now(tz) - MET_DATE).days
    st.subheader(f"💛 We've been talking for {days} days")
    col1, col2 = st.columns(2)
    if os.path.exists("oaty_and_la.png"): col1.image("oaty_and_la.png", caption="🐾 La & Oaty", use_container_width=True)
    if os.path.exists("ruan.jpg"):     col2.image("ruan.jpg",    caption="🚴‍♂️ Ruan",   use_container_width=True)
    st.markdown("### 🔔 Since your last visit")
    for n in recent_notes:
        st.markdown(f"📅 {n['Timestamp']} — **{n['Name']}**: {n['Message']}")
    if recent_bucket:
        st.markdown(f"**🗺️ {recent_bucket[-1]}**")
    for e in recent_events:
        st.markdown(f"**📅 Upcoming: {e['Date']} — {e['Title']}**")
    for m in recent_mood:
        st.markdown(f"**🧠 Mood: {m['Name']} felt {m['Mood']}**")
    if next_event:
        dt = datetime.strptime(next_event['Date'], "%Y-%m-%d").replace(tzinfo=tz)
        diff = dt - datetime.now(tz)
        days_left, hours = diff.days, diff.seconds // 3600
        minutes, seconds = (diff.seconds % 3600) // 60, diff.seconds % 60
        st.info(f"Next: {next_event['Title']} in {days_left}d {hours}h {minutes}m {seconds}s")

# --- NOTES ---
elif menu == "💌 Notes":
    st.header("💌 Notes")
    with st.form("new_note_form"):
        msg = st.text_area("New note:")
        if st.form_submit_button("Send"):
            notes_ws.append_row([current_user, msg, datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"), ""])
            st.experimental_rerun()
    if "del_row" in st.session_state:
        row = st.session_state.del_row
        st.warning("Confirm delete? This action cannot be undone.")
        if st.button("Delete"):    notes_ws.delete_rows(row); st.session_state.pop("del_row"); st.experimental_rerun()
        if st.button("Cancel"):    st.session_state.pop("del_row")
    notes_sorted = sorted(notes, key=lambda x: x['Timestamp'], reverse=True)
    for i, n in enumerate(notes_sorted):
        row_idx = notes.index(n) + 2
        heart = "❤️" if n.get('LikedBy') and n['LikedBy'] != current_user else ""
        c1, c2, c3 = st.columns([8, 1, 1])
        c1.markdown(f"📅 {n['Timestamp']} — **{n['Name']}**: {n['Message']} {heart}")
        if n['Name'] != current_user and not n.get('LikedBy'):
            if c2.button("❤️", key=f"like_{i}"): notes_ws.update_cell(row_idx, 4, current_user)
        if c3.button("🗑️", key=f"delete_{i}"): st.session_state.del_row = row_idx

# --- BUCKET LIST ---
elif menu == "📝 Bucket List":
    st.header("📝 Bucket List")
    if "del_b" in st.session_state:
        row = st.session_state.del_b
        st.warning("Delete this item? Cannot be undone.")
        if st.button("Delete Item"): bucket_ws.delete_rows(row); st.session_state.pop("del_b"); st.experimental_rerun()
        if st.button("Cancel"):      st.session_state.pop("del_b")
    for i, b in enumerate(bucket_items):
        row_idx = i + 2
        c1, c2 = st.columns([9, 1])
        c1.markdown(f"✅ {b[0]}")
        if c2.button("🗑️", key=f"bb{i}"): st.session_state.del_b = row_idx
    with st.form("new_bucket_form"):
        bi = st.text_input("New item:")
        if st.form_submit_button("Add Item"): bucket_ws.append_row([bi, datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")]); st.experimental_rerun()

# --- CALENDAR ---
elif menu == "📅 Calendar":
    st.header("📅 Calendar")
    view = st.radio("View events:", ["Upcoming", "Past"])
    events = upcoming if view == 'Upcoming' else past
    if "del_c" in st.session_state:
        row = st.session_state.del_c
        st.warning("Delete this event? Cannot be undone.")
        if st.button("Delete Event"): calendar_ws.delete_rows(row); st.session_state.pop("del_c"); st.experimental_rerun()
        if st.button("Cancel"):      st.session_state.pop("del_c")
    for i, e in enumerate(events):
        row_idx = calendar_items.index(e) + 2
        c1, c2 = st.columns([8, 1])
        c1.markdown(f"📍 {e['Date']} — **{e['Title']}**")
        c1.markdown(e['Details'])
        c1.markdown(f"<span class='small-text'>Pack: {e['Packing']}</span>", unsafe_allow_html=True)
        if c2.button("🗑️", key=f"cc{i}"): st.session_state.del_c = row_idx
    with st.form("new_event_form"):
        t = st.text_input("Title:")
        d = st.date_input("Date:")
        det = st.text_area("Details:")
        p = st.text_input("What to pack:")
        if st.form_submit_button("Add Event"): calendar_ws.append_row([str(d), t, det, p, datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"), "", ""]); st.experimental_rerun()

# --- MOOD TRACKER ---
elif menu == "📊 Mood Tracker":
    st.header("📊 Mood Tracker")
    opts = ["😊 Happy", "😔 Sad", "😤 Frustrated", "❤️ In Love", "😴 Tired", "😎 Confident", "Custom"]
    with st.form("new_mood_form"):
        mo = st.selectbox("How are you feeling?", opts)
        cm = ""
        if mo == "Custom": cm = st.text_input("Enter mood:")
        note = st.text_area("Note (optional):")
        if st.form_submit_button("Log Mood"): mood_ws.append_row([current_user, cm if cm else mo, note, datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")]); st.experimental_rerun()
    for m in reversed(mood_entries):
        st.markdown(f"📅 {m['Timestamp']} — **{m['Name']}** felt *{m['Mood']}* — {m['Note']}")
