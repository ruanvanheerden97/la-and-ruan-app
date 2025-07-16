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
            st.session_state.last_login_time = datetime.now(tz)
            placeholder.empty()
            st.experimental_rerun()
        if c2.button("Ruan"):
            st.session_state.current_user = "Ruan"
            st.session_state.last_login_time = datetime.now(tz)
            placeholder.empty()
            st.experimental_rerun()
    st.stop()

current_user = st.session_state.current_user
last_login_time = st.session_state.get("last_login_time", datetime.now(tz) - timedelta(days=1))

# --- FILTER CALENDAR EVENTS ---
calendar_items_sorted = sorted(
    calendar_items,
    key=lambda x: datetime.strptime(x["Date"], "%Y-%m-%d")
)
upcoming_events = [
    e for e in calendar_items_sorted
    if str(e.get("Completed", "")).strip().upper() != "TRUE"
    and datetime.strptime(e["Date"], "%Y-%m-%d").date() >= datetime.now(tz).date()
]
past_events = [
    e for e in calendar_items_sorted
    if str(e.get("Completed", "")).strip().upper() == "TRUE"
]
next_event = upcoming_events[0] if upcoming_events else None

# --- RECENT CHANGES ---
recent_notes = [
    n for n in notes
    if tz.localize(datetime.strptime(n["Timestamp"], "%Y-%m-%d %H:%M:%S")) > last_login_time
]
recent_bucket = [
    item[0] for item in bucket_items
    if len(item) > 1 and item[1]
    and tz.localize(datetime.strptime(item[1], "%Y-%m-%d %H:%M:%S")) > last_login_time
]
recent_calendar = [
    e for e in calendar_items
    if tz.localize(datetime.strptime(e.get("Created", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")) > last_login_time
    and str(e.get("Completed", "")).strip().upper() != "TRUE"
]
recent_mood = [
    m for m in mood_entries
    if tz.localize(datetime.strptime(m["Timestamp"], "%Y-%m-%d %H:%M:%S")) > last_login_time
]

# --- PAGE STYLING ---
st.set_page_config(
    page_title="La & Ruan App",
    layout="centered",
    initial_sidebar_state="collapsed"
)
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
menu = st.sidebar.selectbox(
    "📂 Menu",
    ["🏠 Home", "💌 Notes", "📝 Bucket List", "📅 Calendar", "📊 Mood Tracker"]
)

# --- HOME PAGE ---
if menu == "🏠 Home":
    st.markdown(
        "<h1 style='text-align: center;'>🌻 La & Ruan 🌻</h1>",
        unsafe_allow_html=True
    )
    st.success(f"Welcome back, {current_user}! 🥰")
    days = (datetime.now(tz) - MET_DATE).days
    st.markdown(
        f"<h3 style='text-align: center;'>💛 We've been talking for <strong>{days} days</strong>.</h3>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        oaty_path = "oaty_and_la.png"
        if os.path.exists(oaty_path):
            st.image(
                oaty_path,
                caption="🐾 La & Oaty",
                use_container_width=True
            )
    with col2:
        ruan_path = "ruan.jpg"
        if os.path.exists(ruan_path):
            st.image(
                ruan_path,
                caption="🚴‍♂️ Ruan",
                use_container_width=True
            )

    st.subheader("🔔 New Since Your Last Visit")
    if recent_notes:
        st.markdown("**📝 New Note(s):**")
        for n in recent_notes:
            st.markdown(f"📅 *{n['Timestamp']}* — **{n['Name']}**: {n['Message']}")
    if recent_bucket:
        st.markdown(f"**🗺️ New Bucket List Item:** {recent_bucket[-1]}")
    if recent_calendar:
        event = recent_calendar[-1]
        st.markdown(
            f"**📅 New Event:** {event['Date']} - {event['Title']}: {event['Details']}"
        )
    if recent_mood:
        mood = recent_mood[-1]
        st.markdown(
            f"**🧠 Mood Update:** {mood['Name']} felt {mood['Mood']} — {mood['Note']}"
        )

    if next_event:
        event_datetime = datetime.strptime(
            next_event["Date"], "%Y-%m-%d"
        ).replace(tzinfo=tz)
        time_left = event_datetime - datetime.now(tz)
        days_left = time_left.days
        hours, rem = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        st.info(
            f"📅 Next event in {days_left} days: **{next_event['Title']}** — {next_event['Date']}"
        )
        st.markdown(
            f"<p style='text-align:center; font-size: 0.9em;'>⏳ Countdown: {days_left}d {hours}h {minutes}m {seconds}s</p>",
            unsafe_allow_html=True
        )

# --- NOTES PAGE ---
elif menu == "💌 Notes":
    st.header("💌 Daily Note to Each Other")
    with st.form("note_form"):
        message = st.text_area("Write a new note:")
        submitted = st.form_submit_button("Send Note 💌")
        if submitted:
            if current_user and message:
                timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                notes_ws.append_row(
                    [current_user, message, timestamp, ""]
                )
                st.success("Note saved! ❤️")
                st.experimental_rerun()
            else:
                st.warning("Please write something before submitting.")

    notes_sorted = sorted(
        notes, key=lambda x: x["Timestamp"], reverse=True
    )
    grouped_notes = {}
    for note in notes_sorted:
        month = datetime.strptime(
            note["Timestamp"], "%Y-%m-%d %H:%M:%S"
        ).strftime("%B %Y")
        grouped_notes.setdefault(month, []).append(note)

    for month in grouped_notes:
        st.subheader(f"🗓️ {month}")
        for i, note in enumerate(grouped_notes[month]):
            heart = (
                "❤️"
                if note.get("LikedBy") and note["LikedBy"] != current_user
                else ""
            )
            col1, col2 = st.columns([9, 1])
            col1.markdown(
                f"📅 *{note['Timestamp']}* — **{note['Name']}**: {note['Message']} {heart}"
            )
            if (
                note.get("Name") != current_user
                and note.get("LikedBy") != current_user
            ):
                if col2.button("❤️", key=f"like_{month}_{i}"):
                    row_idx = notes.index(note) + 2
                    notes_ws.update_cell(row_idx, 4, current_user)
                    st.experimental_rerun()

# --- BUCKET LIST PAGE ---
elif menu == "📝 Bucket List":
    st.header("📝 Our Bucket List")
    if "del_b" in st.session_state:
        row = st.session_state.del_b
        st.warning("Delete this item? This action cannot be undone.")
        if st.button("Delete Item"):                    
            bucket_ws.delete_rows(row)
            del st.session_state["del_b"]
            st.success("Item deleted.")
            st.experimental_rerun()
        if st.button("Cancel"):                       
            del st.session_state["del_b"]
    for i, item in enumerate(bucket_items):
        row_idx = i + 2
        col1, col2 = st.columns([9, 1])
        col1.markdown(f"✅ {item[0]}")
        if col2.button("🗑️", key=f"delete_{i}"):
            st.session_state["del_b"] = row_idx

    with st.form("bucket_form"):
        new_item = st.text_input("Add something new to our list:")
        submitted = st.form_submit_button("Add to Bucket List 🗺️")
        if submitted:
            if new_item:
                timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                bucket_ws.append_row([new_item, timestamp])
                st.success("Item added to bucket list! 🥾")
                st.experimental_rerun()
            else:
                st.warning("Please type something before adding.")

# --- CALENDAR PAGE ---
elif menu == "📅 Calendar":
    st.header("📅 Our Shared Calendar")
    view = st.radio("View events:", ["Upcoming", "Past"])
    events = upcoming_events if view == "Upcoming" else past_events
    if "del_c" in st.session_state:
        row = st.session_state.del_c
        st.warning("Delete this event? This action cannot be undone.")
        if st.button("Delete Event"):   
            calendar_ws.delete_rows(row)
            del st.session_state["del_c"]
            st.success("Event deleted.")
            st.experimental_rerun()
        if st.button("Cancel"):           
            del st.session_state["del_c"]
    for i, e in enumerate(events):
        row_idx = calendar_items.index(e) + 2
        col1, col2 = st.columns([8, 1])
        col1.markdown(f"📍 {e['Date']} — **{e['Title']}**")
        col1.markdown(e['Details'])
        col1.markdown(
            f"<span class='small-text'>📝 What to pack: {e['Packing']}</span>",
            unsafe_allow_html=True
        )
        if col2.button("🗑️", key=f"del_cal_{i}"):
            st.session_state["del_c"] = row_idx

    with st.form("calendar_form"):
        event_title = st.text_input("Event title")
        event_date = st.date_input("Event date")
        event_desc = st.text_area("Event details")
        event_pack = st.text_input("What to pack")
        submitted = st.form_submit_button("Add Event")
        if submitted:
            created_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            calendar_ws.append_row([
                str(event_date), event_title, event_desc,
                event_pack, created_time, "", ""
            ])
            st.success("Event added to calendar! 📌")
            st.experimental_rerun()

# --- MOOD TRACKER PAGE ---
elif menu == "📊 Mood Tracker":
    st.header("📊 Daily Mood Check-In")
    mood_options = [
        "😊 Happy", "😔 Sad", "😤 Frustrated", "❤️ In Love",
        "😴 Tired", "😎 Confident", "Custom"
    ]
    with st.form("mood_form"):
        mood = st.selectbox("How are you feeling today?", mood_options)
        custom_mood = ""
        if mood == "Custom":
            custom_mood = st.text_input("Enter your custom mood")
        note = st.text_area("Optional note")
        submitted = st.form_submit_button("Submit Mood")
        if submitted:
            final_mood = custom_mood if mood == "Custom" else mood
            timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            mood_ws.append_row([current_user, final_mood, note, timestamp])
            st.success("Mood logged! 🧠")
            st.experimental_rerun()

    st.subheader("💬 Past Mood Entries")
    for entry in reversed(mood_entries):
        st.markdown(
            f"📅 *{entry['Timestamp']}* — **{entry['Name']}** felt *{entry['Mood']}* — {entry['Note']}"
        )
