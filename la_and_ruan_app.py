import streamlit as st
from datetime import datetime, time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from pytz import timezone

# --- TIMEZONE CONFIG ---
tz = timezone("Africa/Harare")
timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# --- CONFIG ---
MET_DATE = datetime(2025, 6, 23)
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

# --- LOAD EXISTING DATA ---
notes_ws = sheet.worksheet(NOTES_SHEET)
bucket_ws = sheet.worksheet(BUCKET_SHEET)
calendar_ws = sheet.worksheet(CALENDAR_SHEET)

notes = notes_ws.get_all_records()
bucket_items = [row[0] for row in bucket_ws.get_all_values() if row]
calendar_events = calendar_ws.get_all_records()

# --- STYLING ---
page_bg_img = """
<style>
[data-testid="stAppViewContainer"] > .main {
    background-image: url('https://images.unsplash.com/photo-1508973371-d5bd6f29c270?fit=crop&w=1280&q=80');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: #333333;
}
[data-testid="stMarkdownContainer"] > h1, h2, h3 {
    color: #222222;
    text-align: center;
}
textarea, input, .stButton>button {
    background-color: rgba(255, 255, 255, 0.85) !important;
    color: #000000 !important;
    font-weight: 500;
}
.stButton>button {
    border-radius: 10px;
    padding: 0.5em 1em;
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>🌻 La & Ruan 🌻</h1>", unsafe_allow_html=True)

# --- DAYS SINCE MET ---
days = (datetime.now() - MET_DATE).days
st.markdown(f"<h3 style='text-align: center;'>💛 We've been talking for <strong>{days} days</strong>.</h3>", unsafe_allow_html=True)

# --- IMAGE ---
image_path = "oaty_and_la.png"
if os.path.exists(image_path):
    st.image(image_path, caption="🐾 La & Oaty", width=250)

# --- NOTES SECTION ---
st.subheader("💌 Daily Note to Each Other")

st.write("#### Existing Notes:")
for note in reversed(notes):
    st.markdown(f"📅 *{note['Timestamp']}* — **{note['Name']}**: {note['Message']}")

name = st.text_input("Your name")
message = st.text_area("Write a new note:")

if st.button("Send Note 💌"):
    if name and message:
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        notes_ws.append_row([name, message, now])
        st.success("Note saved! ❤️")
    else:
        st.warning("Please fill in both name and message.")

# --- BUCKET LIST ---
st.subheader("📝 Our Bucket List")

st.write("#### Current Bucket List:")
for item in bucket_items:
    st.markdown(f"✅ {item}")

new_item = st.text_input("Add something new to our list:")

if st.button("Add to Bucket List 🗺️"):
    if new_item:
        bucket_ws.append_row([new_item])
        st.success("Item added to bucket list! 🥾")
    else:
        st.warning("Please type something before adding.")

# --- CALENDAR SECTION ---
st.subheader("📅 Our Shared Calendar")

with st.form("calendar_form"):
    event_date = st.date_input("Event Date")
    start_time = st.time_input("Start Time", time(8, 0))
    end_time = st.time_input("End Time", time(17, 0))
    title = st.text_input("Event Title")
    location = st.text_input("Location")
    description = st.text_area("Description / What to Pack")

    submitted = st.form_submit_button("Add to Calendar 🗓️")
    if submitted:
        if title and location:
            calendar_ws.append_row([
                event_date.strftime("%Y-%m-%d"),
                start_time.strftime("%H:%M"),
                end_time.strftime("%H:%M"),
                title,
                location,
                description
            ])
            st.success("Event added to calendar! 🎉")
        else:
            st.warning("Please enter at least a title and location.")

# --- SHOW UPCOMING EVENTS ---
st.write("#### Upcoming Events:")
for event in calendar_events[-5:][::-1]:
    st.markdown(f"📆 **{event['Date']}** — 🗓️ *{event['Event Title']}* at **{event['Location']}**\n\n🕒 {event['Start Time']} - {event['End Time']} \n\n🧳 _{event['Description']}_")
