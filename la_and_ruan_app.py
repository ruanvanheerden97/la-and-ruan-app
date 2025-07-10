import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# --- CONFIG ---
MET_DATE = datetime(2025, 6, 23)
GOOGLE_SHEET_NAME = "La & Ruan App"
NOTES_SHEET = "Notes"
BUCKET_SHEET = "BucketList"

# --- AUTHENTICATION ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# --- OPEN GOOGLE SHEET ---
sheet = client.open(GOOGLE_SHEET_NAME)

# --- LOAD EXISTING NOTES ---
notes_ws = sheet.worksheet(NOTES_SHEET)
notes = notes_ws.get_all_records()

# --- LOAD BUCKET LIST ---
bucket_ws = sheet.worksheet(BUCKET_SHEET)
bucket_items = [row[0] for row in bucket_ws.get_all_values() if row]

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
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        notes_ws.append_row([name, message, timestamp])
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
