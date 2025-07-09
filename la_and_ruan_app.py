import streamlit as st
from datetime import datetime
import os

# --- CONFIG ---
NOTES_FILE = "la_notes.txt"
BUCKET_FILE = "bucket_list.txt"
MET_DATE = datetime(2025, 6, 29)  # Change this if needed

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

# --- NOTES ---
st.subheader("💌 Daily Note to Each Other")
if os.path.exists(NOTES_FILE):
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        existing_note = f.read()
else:
    existing_note = ""

note = st.text_area("Leave a sweet note for La:", value=existing_note, height=150)

if st.button("Save Note"):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        f.write(note)
    st.success("Note saved! ❤️")

# --- BUCKET LIST ---
st.subheader("📝 Our Bucket List")
if os.path.exists(BUCKET_FILE):
    with open(BUCKET_FILE, "r", encoding="utf-8") as f:
        bucket_items = f.read().splitlines()
else:
    bucket_items = ["⛺ Glamping trip in the mountains – bring bikes & trail shoes"]

edited_list = st.text_area("Add your dream plans here (one per line):", value="\n".join(bucket_items), height=150)

if st.button("Update Bucket List"):
    with open(BUCKET_FILE, "w", encoding="utf-8") as f:
        f.write(edited_list)
    st.success("Bucket list updated! 🥾")

# --- FOOTER ---
st.markdown("---")
st.markdown("<div style='text-align: center;'>Made with 🥰 by Ruan for La & Oaty.</div>", unsafe_allow_html=True)
