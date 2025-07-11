import streamlit as st
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from pytz import timezone
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import mimetypes


# --- TIMEZONE SETUP ---
tz = timezone("Africa/Harare")

# --- CONFIG ---
MET_DATE = datetime(2025, 6, 23, tzinfo=tz)
GOOGLE_SHEET_NAME = "La & Ruan App"
NOTES_SHEET = "Notes"
BUCKET_SHEET = "BucketList"
CALENDAR_SHEET = "Calendar"
GALLERY_FOLDER = "gallery"
GDRIVE_FOLDER_ID = "1XEmkFAqDiZIVkPdwyEZul0id-esZ24iZ"  # Replace with your actual Google Drive folder ID

# --- AUTHENTICATION ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

drive_creds = service_account.Credentials.from_service_account_info(creds_dict)
drive_service = build("drive", "v3", credentials=drive_creds)

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
menu = st.sidebar.selectbox("📂 Menu", ["🏠 Home", "💌 Notes", "📝 Bucket List", "📅 Calendar", "📸 Gallery"])

# --- HOME PAGE ---
if menu == "🏠 Home":
    st.markdown("<h1 style='text-align: center;'>🌻 La & Ruan 🌻</h1>", unsafe_allow_html=True)
    days = (now - MET_DATE).days
    st.markdown(f"<h3 style='text-align: center;'>💛 We've been talking for <strong>{days} days</strong>.</h3>", unsafe_allow_html=True)

    image_path = "oaty_and_la.png"
    if os.path.exists(image_path):
        st.image(image_path, caption="🐾 La & Oaty", width=220)

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

# --- GALLERY PAGE ---
elif menu == "📸 Gallery":
    st.header("📸 Memories Gallery")
    st.write("Upload and view your favourite moments together 💛")

    with st.form("upload_form"):
        uploaded_file = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png"])
        image_desc = st.text_input("Image description")
        submitted = st.form_submit_button("📤 Upload Photo")
        if submitted and uploaded_file is not None:
            if not os.path.exists(GALLERY_FOLDER):
                os.makedirs(GALLERY_FOLDER)
            filepath = os.path.join(GALLERY_FOLDER, uploaded_file.name)
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())

            mime_type, _ = mimetypes.guess_type(filepath)
            timestamp = datetime.now(tz).strftime('%Y-%m-%d_%H-%M-%S')
            safe_desc = image_desc.replace(":", "").replace("/", "").strip()
            filename = f"{timestamp} - {safe_desc or uploaded_file.name}"

            file_metadata = {
                "name": filename,
                "parents": [GDRIVE_FOLDER_ID]
            }
            media = MediaFileUpload(filepath, mimetype=mime_type)
            drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            st.success("Photo uploaded to gallery!")

    results = drive_service.files().list(q=f"'{GDRIVE_FOLDER_ID}' in parents and mimeType contains 'image/'",
                                         orderBy="createdTime desc",
                                         pageSize=30, fields="files(id, name)").execute()
    items = results.get("files", [])

    cols = st.columns(3)
    for i, file in enumerate(items):
        file_url = f"https://drive.google.com/uc?export=view&id={file['id']}"
        with cols[i % 3]:
            st.image(file_url, caption=file['name'], use_column_width=True)
            if st.button(f"🗑️ Delete", key=file['id']):
                drive_service.files().delete(fileId=file['id']).execute()
                st.warning("Image deleted. Please refresh to update gallery.")
