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

# --- AUTHENTICATION ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# --- OPEN GOOGLE SHEET ---
sheet = client.open(GOOGLE_SHEET_NAME)
notes_ws = sheet.worksheet(NOTES_SHEET)
bucket_ws = sheet.worksheet(BUCKET_SHEET)
calendar_ws = sheet.worksheet(CALENDAR_SHEET)

# --- LOAD DATA ---
notes = notes_ws.get_all_records()
bucket_items = bucket_ws.get_all_values()
calendar_items = calendar_ws.get_all_records()

# --- RECENT CHANGES ---
now = datetime.now(tz)
last_24_hours = now - timedelta(hours=24)
recent_notes = [n for n in notes if tz.localize(datetime.strptime(n["Timestamp"], "%Y-%m-%d %H:%M:%S")) > last_24_hours]
recent_bucket = [item[0] for item in bucket_items if len(item) > 1 and item[1] and tz.localize(datetime.strptime(item[1], "%Y-%m-%d %H:%M:%S")) > last_24_hours]
recent_calendar = [e for e in calendar_items if tz.localize(datetime.strptime(e["Created"], "%Y-%m-%d %H:%M:%S")) > last_24_hours]

# --- UPCOMING EVENT COUNTDOWN ---
def get_next_event():
    upcoming = []
    for e in calendar_items:
        try:
            event_time = tz.localize(datetime.strptime(e["Date"], "%Y-%m-%d"))
            if event_time > now:
                upcoming.append((event_time, e))
        except:
            continue
    if upcoming:
        return sorted(upcoming, key=lambda x: x[0])[0]
    return None, None

next_event_time, next_event = get_next_event()
if next_event_time:
    countdown = next_event_time - now
    days_left = countdown.days
    hours_left, remainder = divmod(countdown.seconds, 3600)
    minutes_left, seconds_left = divmod(remainder, 60)
    countdown_message = f"⏳ Countdown until we meet again: **{days_left}d {hours_left}h {minutes_left}m {seconds_left}s** 💫"
else:
    countdown_message = "📆 No upcoming events planned yet... Add one in the calendar!"

# --- PAGE STYLING ---
st.set_page_config(page_title="La & Ruan App", layout="centered")
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
textarea, input, .stButton>button {
    background-color: rgba(255, 255, 255, 0.95) !important;
    color: #000000 !important;
    font-weight: 500;
    border-radius: 8px;
}
.stButton>button {
    padding: 0.5em 1em;
    transition: all 0.3s ease-in-out;
}
.stButton>button:hover {
    background-color: #ffea00 !important;
    color: #000;
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- SIDEBAR MENU ---
menu = st.sidebar.selectbox("📂 Menu", ["🏠 Home", "💌 Notes", "📝 Bucket List", "📅 Calendar"])

# --- HOME PAGE ---
if menu == "🏠 Home":
    st.markdown("<h1 style='text-align: center;'>🌻 La & Ruan 🌻</h1>", unsafe_allow_html=True)
    days = (now - MET_DATE).days
    st.markdown(f"<h3 style='text-align: center;'>💛 We've been talking for <strong>{days} days</strong>.</h3>", unsafe_allow_html=True)

    image_path = "oaty_and_la.png"
    if os.path.exists(image_path):
        st.image(image_path, caption="🐾 La & Oaty", width=220)

    image_path2 = "ruan.jpg"
    if os.path.exists(image_path2):
        st.image(image_path2, caption="🚴🏼  Ruan", width=220)

    st.subheader("🕒 Recent Activity (Last 24 Hours)")
    if recent_notes:
        st.markdown("**Latest Note:**")
        note = recent_notes[-1]
        st.markdown(f"📅 *{note['Timestamp']}* — **{note['Name']}**: {note['Message']}")
    if recent_bucket:
        st.markdown(f"**New Bucket List Item:** {recent_bucket[-1]}")
    if recent_calendar:
        event = recent_calendar[-1]
        st.markdown(f"**New Event:** {event['Date']} - {event['Title']}: {event['Details']}")

    st.markdown("---")
    st.markdown(f"### 💕 {countdown_message}")

# --- NOTES PAGE ---
elif menu == "💌 Notes":
    st.header("💌 Daily Note to Each Other")
    for note in reversed(notes):
        st.markdown(f"📅 *{note['Timestamp']}* — **{note['Name']}**: {note['Message']}")

    with st.form("note_form"):
        name = st.text_input("Your name")
        message = st.text_area("Write a new note:")
        submitted = st.form_submit_button("Send Note 💌")
        if submitted:
            if name and message:
                timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                notes_ws.append_row([name, message, timestamp])
                st.success("Note saved! ❤️")
            else:
                st.warning("Please fill in both name and message.")

# --- BUCKET LIST PAGE ---
elif menu == "📝 Bucket List":
    st.header("📝 Our Bucket List")
    for item in bucket_items:
        st.markdown(f"✅ {item[0]}")

    with st.form("bucket_form"):
        new_item = st.text_input("Add something new to our list:")
        submitted = st.form_submit_button("Add to Bucket List 🗺️")
        if submitted:
            if new_item:
                timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                bucket_ws.append_row([new_item, timestamp])
                st.success("Item added to bucket list! 🥾")
            else:
                st.warning("Please type something before adding.")

# --- CALENDAR PAGE ---
elif menu == "📅 Calendar":
    st.header("📅 Our Shared Calendar")
    for event in calendar_items:
        st.markdown(f"📍 {event['Date']} — **{event['Title']}**")
        st.markdown(f"{event['Details']}")
        st.markdown(f"📝 *What to pack: {event['Packing']}*\n---")

    with st.form("calendar_form"):
        event_title = st.text_input("Event title")
        event_date = st.date_input("Event date")
        event_desc = st.text_area("Event details")
        event_pack = st.text_input("What to pack")
        submitted = st.form_submit_button("Add Event")
        if submitted:
            created_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            calendar_ws.append_row([str(event_date), event_title, event_desc, event_pack, created_time])
            st.success("Event added to calendar! 📌")
