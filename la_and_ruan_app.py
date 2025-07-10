import streamlit as st
from datetime import datetime
import os

# --- CONFIG ---
NOTES_FILE = "la_notes.txt"
BUCKET_FILE = "bucket_list.txt"
MET_DATE = datetime(2025, 6, 23)

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
h1, h2, h3 {
    color: #222222;
    text-align: center;
}
textarea, input, .stButton>button {
    background-color: rgba(255, 255, 255, 0.85) !important;
    color: #000 !important;
    font-weight: 500;
}
.stButton>button {
    border-radius: 10px;
    padding: 0.5em 1em;
}
.note-box {
    background-color: rgba(255,255,255,0.75);
    padding: 1em;
    border-radius: 10px;
    margin-bottom: 1em;
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h1>🌻 La & Ruan 🌻</h1>", unsafe_allow_html=True)

# --- DAYS TOGETHER ---
days = (datetime.now() - MET_DATE).days
st.markdown(f"<h3>💛 We've been talking for <strong>{days} days</strong>.</h3>", unsafe_allow_html=True)

# --- IMAGE ---
if os.path.exists("oaty_and_la.png"):
    st.image("oaty_and_la.png", caption="🐾 La & Oaty", width=250)

# --- WRITE NOTE ---
st.subheader("💌 Leave a New Note")

with st.form("note_form"):
    name = st.text_input("Your name (La or Ruan)")
    message = st.text_area("Write your note:")
    if st.form_submit_button("Send Note 💌"):
        if name.strip() and message.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_note = f"{timestamp} - {name}:\n{message.strip()}\n---\n"
            with open(NOTES_FILE, "a", encoding="utf-8") as f:
                f.write(new_note)
            st.success("Note saved! 🥰")
        else:
            st.warning("Please fill in both name and message.")

# --- DISPLAY NOTES ---
st.subheader("📜 Note History")

if os.path.exists(NOTES_FILE):
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        all_notes = f.read().strip()
        if all_notes:
            st.markdown(f"<div class='note-box'>{all_notes.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
        else:
            st.info("No notes yet – start the love story! 💬")
else:
    st.info("No notes file found.")

# --- BUCKET LIST ---
st.subheader("🌄 Our Bucket List")

if os.path.exists(BUCKET_FILE):
    with open(BUCKET_FILE, "r", encoding="utf-8") as f:
        bucket_content = f.read().strip()
else:
    bucket_content = "⛺ Glamping trip in the mountains – bring bikes & trail shoes"

bucket_input = st.text_area("Add or update our bucket list (one per line):", value=bucket_content, height=150)

if st.button("Update Bucket List"):
    with open(BUCKET_FILE, "w", encoding="utf-8") as f:
        f.write(bucket_input.strip())
    st.success("Bucket list saved! 🎯")

# --- FOOTER ---
st.markdown("---")
st.markdown("<div style='text-align: center;'>Made with 🥰 by Ruan for La & Oaty.</div>", unsafe_allow_html=True)
