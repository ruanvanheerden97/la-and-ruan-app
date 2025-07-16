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
                st.experimental_rerun()
        with col2:
            if st.button("Ruan"):
                st.session_state.current_user = "Ruan"
                st.session_state.last_login_time = datetime.now(tz)
                login_placeholder.empty()
                st.experimental_rerun()
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
st.markdown("""
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
""", unsafe_allow_html=True)

# --- SIDEBAR MENU ---
menu = st.sidebar.selectbox("📂 Menu", ["🏠 Home", "💌 Notes", "📝 Bucket List", "📅 Calendar", "📊 Mood Tracker"] )

# --- HOME PAGE ---
if menu == "🏠 Home":
    st.markdown("<h1 style='text-align: center;'>🌻 La & Ruan 🌻</h1>", unsafe_allow_html=True)
    st.success(f"Welcome back, {current_user}! 🥰")
    days = (datetime.now(tz) - MET_DATE).days
    st.markdown(f"<h3 style='text-align: center;'>💛 We've been talking for <strong>{days} days</strong>.</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if os.path.exists("oaty_and_la.png"): st.image("oaty_and_la.png", caption="🐾 La & Oaty", use_container_width=True)
    with col2:
        if os.path.exists("ruan.jpg"): st.image("ruan.jpg", caption="🚴‍♂️ Ruan", use_container_width=True)
    st.subheader("🔔 New Since Your Last Visit")
    if recent_notes:
        st.markdown("**📝 New Note(s):**")
        for n in recent_notes: st.markdown(f"📅 {n['Timestamp']} — **{n['Name']}**: {n['Message']}")
    if recent_bucket: st.markdown(f"**🗺️ New Bucket List Item:** {recent_bucket[-1]}")
    if recent_calendar:
        e = recent_calendar[-1]
        st.markdown(f"**📅 New Event:** {e['Date']} — **{e['Title']}**: {e['Details']}")
    if recent_mood:
        m = recent_mood[-1]
        st.markdown(f"**🧠 Mood Update:** {m['Name']} felt {m['Mood']} — {m['Note']}")
    if next_event:
        dt = datetime.strptime(next_event['Date'], "%Y-%m-%d").replace(tzinfo=tz)
        diff = dt - datetime.now(tz)
        d, h = diff.days, diff.seconds // 3600
        m_ss, s = (diff.seconds % 3600) // 60, diff.seconds % 60
        st.info(f"📅 Next event: **{next_event['Title']}** in {d}d {h}h {m_ss}m {s}s")

# --- NOTES PAGE ---
elif menu == "💌 Notes":
    st.header("💌 Daily Note to Each Other")
    # New note form
    with st.form("new_note_form"):
        note_text = st.text_area("Write a new note:")
        if st.form_submit_button("Save Note"):
            if note_text:
                ts = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                notes_ws.append_row([current_user, note_text, ts, ""])
                st.success("Note saved! ❤️")
                st.experimental_rerun()
            else:
                st.warning("Please write a note before saving.")
    # Delete confirmation
    if "delete_note_row" in st.session_state:
        row = st.session_state.delete_note_row
        st.error("Are you sure you want to delete this note? This action cannot be undone.")
        if st.button("Confirm Delete"):
            notes_ws.delete_rows(row)
            del st.session_state["delete_note_row"]
            st.success("Note deleted.")
            st.experimental_rerun()
        if st.button("Cancel"):
            del st.session_state["delete_note_row"]
    # List notes with delete
    notes_sorted = sorted(notes, key=lambda x: x['Timestamp'], reverse=True)
    for idx, n in enumerate(notes_sorted):
        row_idx = notes.index(n) + 2
        heart = "❤️" if n.get('LikedBy') and n['LikedBy'] != current_user else ""
        c1, c2, c3 = st.columns([8, 1, 1])
        c1.markdown(f"📅 {n['Timestamp']} — **{n['Name']}**: {n['Message']} {heart}")
        if n['Name'] != current_user and not n.get('LikedBy'):
            if c2.button("❤️", key=f"like_note_{idx}"):
                notes_ws.update_cell(row_idx, 4, current_user)
                st.experimental_rerun()
        if c3.button("🗑️", key=f"delete_note_{idx}"):
            st.session_state.delete_note_row = row_idx
            st.experimental_rerun()

# --- BUCKET LIST PAGE ---
elif menu == "📝 Bucket List":
    st.header("📝 Our Bucket List")
    # Delete confirmation
    if "delete_bucket_row" in st.session_state:
        row = st.session_state.delete_bucket_row
        st.error("Delete this bucket list item? This action cannot be undone.")
        if st.button("Confirm Delete Item"):
            bucket_ws.delete_rows(row)
            del st.session_state["delete_bucket_row"]
            st.success("Item deleted.")
            st.experimental_rerun()
        if st.button("Cancel"):
            del st.session_state["delete_bucket_row"]
    # List items
    for idx, it in enumerate(bucket_items):
        row_idx = idx + 2
        c1, c2 = st.columns([9, 1])
        c1.markdown(f"✅ {it[0]}")
        if c2.button("🗑️", key=f"delete_bucket_{idx}"):
            st.session_state.delete_bucket_row = row_idx
            st.experimental_rerun()
    # Add item
    with st.form("new_bucket_form"):
        item_text = st.text_input("Add new bucket list item:")
        if st.form_submit_button("Add Item"):
            if item_text:
                ts = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                bucket_ws.append_row([item_text, ts])
                st.success("Item added! 🥾")
                st.experimental_rerun()
            else:
                st.warning("Please enter an item before adding.")

# --- CALENDAR PAGE ---
elif menu == "📅 Calendar":
    st.header("📅 Our Shared Calendar")
    view = st.radio("View events:", ["Upcoming Events", "Past Events"])
    events = upcoming_events if view == "Upcoming Events" else past_events
    # Delete confirmation
    if "delete_event_row" in st.session_state:
        row = st.session_state.delete_event_row
        st.error("Delete this event? This action cannot be undone.")
        if st.button("Confirm Delete Event"):
            calendar_ws.delete_rows(row)
            del st.session_state["delete_event_row"]
            st.success("Event deleted.")
            st.experimental_rerun()
        if st.button("Cancel"):
            del st.session_state["delete_event_row"]
    # List events
    for idx, e in enumerate(events):
        row_idx = calendar_items.index(e) + 2
        c1, c2 = st.columns([8, 1])
        c1.markdown(f"📍 {e['Date']} — **{e['Title']}**")
        c1.markdown(e['Details'])
        c1.markdown(f"<span class='small-text'>Pack: {e['Packing']}</span>", unsafe_allow_html=True)


# --- MOOD TRACKER PAGE ---
elif menu == "📊 Mood Tracker":
    st.header("📊 Daily Mood Check-In")
    moods = ["😊 Happy", "😔 Sad", "😤 Frustrated", "❤️ In Love", "😴 Tired", "😎 Confident", "Custom"]
    with st.form("new_mood_form"):
        mood_choice = st.selectbox("How are you feeling today?", moods)
        custom = ""
        if mood_choice == "Custom":
            custom = st.text_input("Enter your mood:")
        note_text = st.text_area("Optional note:")
        if st.form_submit_button("Log Mood"):
            final = custom if mood_choice == "Custom" and custom else mood_choice
            if final:
                ts = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                mood_ws.append_row([current_user, final, note_text, ts])
                st.success("Mood logged! 🧠")
                st.experimental_rerun()
            else:
                st.warning("Please select or enter a mood before logging.")
    st.subheader("💬 Past Mood Entries")
    for m in reversed(mood_entries):
        st.markdown(f"📅 *{m['Timestamp']}* — **{m['Name']}** felt *{m['Mood']}* — {m['Note']}")
