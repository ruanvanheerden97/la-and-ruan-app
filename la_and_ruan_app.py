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

# --- OPEN GOOGLE SHEET ---
def open_sheet(name):
    try:
        return client.open(name)
    except APIError:
        st.error("Failed to connect to Google Sheets. Please try again later.")
        st.stop()

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

# --- EVENT FILTER UTILITY ---
def get_events(items):
    sorted_items = sorted(items, key=lambda x: datetime.strptime(x.get("Date","1970-01-01"), "%Y-%m-%d"))
    upcoming = [e for e in sorted_items if str(e.get("Completed","")).upper() != "TRUE"
                and datetime.strptime(e.get("Date","1970-01-01"), "%Y-%m-%d").date() >= datetime.now(tz).date()]
    past = [e for e in sorted_items if str(e.get("Completed","")).upper() == "TRUE"]
    return upcoming, past

upcoming_events, past_events = get_events(calendar_items)

# --- RECENT CHANGES ---
now = datetime.now(tz)
last_login = st.session_state.get("last_login_time", now - timedelta(days=1))
recent_notes = [n for n in notes if datetime.strptime(n.get("Timestamp",""), "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz) > last_login]
recent_bucket = [b[0] for b in bucket_items if len(b) > 1 and b[1]
                 and datetime.strptime(b[1], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz) > last_login]
recent_calendar = [e for e in calendar_items if datetime.strptime(e.get("Created","1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz) > last_login
                   and str(e.get("Completed","")).upper() != "TRUE"]
recent_mood = [m for m in mood_entries if datetime.strptime(m.get("Timestamp",""), "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz) > last_login]

# --- LOGIN POPUP WITH PHOTOS ---
if "current_user" not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("## Who's using the app?")
        c1, c2 = st.columns(2)
        with c1:
            if os.path.exists("la.jpg"): st.image("la.jpg", caption="La 🌻", use_container_width=True)
            if st.button("I'm La"): st.session_state.current_user = "La"; st.session_state.last_login_time = now
        with c2:
            if os.path.exists("ruan.jpg"): st.image("ruan.jpg", caption="Ruan 🚴‍♂️", use_container_width=True)
            if st.button("I'm Ruan"): st.session_state.current_user = "Ruan"; st.session_state.last_login_time = now
    if "current_user" not in st.session_state:
        st.stop()
    placeholder.empty()

current_user = st.session_state.current_user
st.set_page_config(page_title="La & Ruan App", layout="centered", initial_sidebar_state="collapsed")

# --- SIDEBAR MENU ---
menu = st.sidebar.selectbox(
    "📂 Menu",
    ["🏠 Home", "💌 Notes", "📝 Bucket List", "📅 Calendar", "📊 Mood Tracker"]
)

# --- HOME PAGE ---
if menu == "🏠 Home":
    st.markdown("<h1 align='center' style='font-family:serif; color:#DEB887;'>La & Ruan 🌻</h1>", unsafe_allow_html=True)
    st.markdown("<h3 align='center' style='color:#444;'>Growing together, one day at a time</h3>", unsafe_allow_html=True)
    days = (now - MET_DATE).days
    st.markdown(f"<div style='text-align:center; font-size:1.2em;'>💛 <strong>{days}</strong> days of sunflowers & smiles</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("🔔 Updates since your last visit")
    for n in recent_notes: st.markdown(f"*{n['Timestamp']}* — **{n['Name']}**: {n['Message']}")
    if recent_bucket: st.markdown(f"🗺️ {recent_bucket[-1]}")
    if recent_calendar:
        ev = recent_calendar[-1]
        st.markdown(f"📅 {ev['Date']} — {ev['Title']}")
    if recent_mood:
        m = recent_mood[-1]
        st.markdown(f"🧠 {m['Name']} felt {m['Mood']}")
    if upcoming_events:
        dt = datetime.strptime(upcoming_events[0]['Date'], "%Y-%m-%d").replace(tzinfo=tz)
        diff = dt - now
        d, rem = diff.days, diff.seconds
        h, mi, s = rem//3600, (rem%3600)//60, rem%60
        st.info(f"Next: **{upcoming_events[0]['Title']}** in {d}d {h}h {mi}m {s}s")

# --- NOTES PAGE ---
elif menu == "💌 Notes":
    st.header("💌 Daily Notes")
    with st.form("note_form"):
        msg = st.text_area("Share a note:")
        if st.form_submit_button("Send 💌") and msg:
            notes_ws.append_row([current_user, msg, now.strftime("%Y-%m-%d %H:%M:%S"), ""])
            notes = fetch_data()[0]
            st.success("Sent! ❤️")
    sorted_notes = sorted(notes, key=lambda x: x['Timestamp'], reverse=True)
    for n in sorted_notes:
        row_idx = notes.index(n) + 2
        heart = '❤️' if n.get('LikedBy') and n['LikedBy'] != current_user else ''
        c1, c2, c3 = st.columns([7, 1, 1])
        c1.markdown(f"*{n['Timestamp']}* — **{n['Name']}**: {n['Message']} {heart}")
        if n['Name'] != current_user and not n.get('LikedBy'):
            if c2.button('❤️', key=f"like_{row_idx}"):
                notes_ws.update_cell(row_idx, 4, current_user)
                notes = fetch_data()[0]
        if c3.button('✏️', key=f"edit_{row_idx}"):
            st.session_state.edit_row = row_idx
            st.session_state.edit_text = n['Message']
        if st.session_state.get('edit_row') == row_idx:
            new_msg = st.text_area("Edit note:", value=st.session_state.get('edit_text', n['Message']), key=f"edit_text_{row_idx}")
            if st.button('Save', key=f"save_{row_idx}"):
                notes_ws.update_cell(row_idx, 2, new_msg)
                del st.session_state['edit_row'], st.session_state['edit_text']
                notes = fetch_data()[0]

# --- BUCKET LIST PAGE ---
elif menu == "📝 Bucket List":
    st.header("📝 Our Bucket List")
    if 'del_b' in st.session_state:
        r = st.session_state.del_b
        st.warning("Delete this item?")
        if st.button('Yes'): bucket_ws.delete_rows(r); notes, bucket_items, calendar_items, mood_entries = fetch_data(); del st.session_state['del_b']; st.success('Deleted')
        if st.button('No'): del st.session_state['del_b']
    for i, b in enumerate(bucket_items):
        c1, c2 = st.columns([9,1])
        c1.markdown(f"✅ {b[0]}")
        if c2.button('🗑️', key=f"del_b_{i}"): st.session_state['del_b'] = i+2
    with st.form('bucket_form'):
        ni = st.text_input('Add new item:')
        if st.form_submit_button('Add') and ni:
            bucket_ws.append_row([ni, now.strftime("%Y-%m-%d %H:%M:%S")])
            notes, bucket_items, calendar_items, mood_entries = fetch_data()
            st.success('Added!')

# --- CALENDAR PAGE ---
elif menu == "📅 Calendar":
    st.header("📅 Our Shared Calendar")
    view = st.radio('View', ['Upcoming Events','Past Events'])
    events = upcoming_events if view=='Upcoming Events' else past_events
    # Deletion prompt
    if 'del_c' in st.session_state:
        r = st.session_state.del_c
        st.warning('Delete this event?')
        if st.button('Yes'): calendar_ws.delete_rows(r); notes, bucket_items, calendar_items, mood_entries = fetch_data(); upcoming_events, past_events = get_events(calendar_items); del st.session_state['del_c']; st.success('Deleted')
        if st.button('No'): del st.session_state['del_c']
    # Display and edit
    for idx, e in enumerate(events):
        ridx = calendar_items.index(e)+2
        c1, c2, c3 = st.columns([6,1,1])
        c1.markdown(f"📍 {e['Date']} — **{e['Title']}**")
        c1.markdown(e['Details'])
        c1.markdown(f"<span class='small-text'>Pack: {e['Packing']}</span>", unsafe_allow_html=True)
        if view=='Upcoming Events':
            if c2.button('✏️', key=f"edit_c_{ridx}"):
                st.session_state['edit_cal'] = ridx
                st.session_state['edit_cal_data'] = e.copy()
            if c3.button('🗑️', key=f"del_c_{ridx}"): st.session_state['del_c'] = ridx
        # Edit form
        if st.session_state.get('edit_cal') == ridx:
            data = st.session_state['edit_cal_data']
            new_date = st.date_input('Date', value=datetime.strptime(data['Date'], "%Y-%m-%d"))
            new_title = st.text_input('Title', value=data['Title'])
            new_details = st.text_area('Details', value=data['Details'])
            new_pack = st.text_input('Packing', value=data['Packing'])
            if st.button('Save Changes', key=f"save_cal_{ridx}"):
                calendar_ws.update(ridx, 1, [[new_date.strftime("%Y-%m-%d"), new_title, new_details, new_pack]])
                del st.session_state['edit_cal'], st.session_state['edit_cal_data']
                notes, bucket_items, calendar_items, mood_entries = fetch_data()
                upcoming_events, past_events = get_events(calendar_items)
                st.success('Event updated!')
    # Add new event
    with st.form('calendar_form'):
        t = st.text_input('Event title')
        d = st.date_input('Event date')
        desc = st.text_area('Event details')
        p = st.text_input('What to pack')
        if st.form_submit_button('Add') and t:
            calendar_ws.append_row([str(d),t,desc,p,now.strftime("%Y-%m-%d %H:%M:%S"),'',''])
            notes, bucket_items, calendar_items, mood_entries = fetch_data()
            upcoming_events, past_events = get_events(calendar_items)
            st.success('Event added!')

# --- MOOD TRACKER PAGE ---
elif menu == "📊 Mood Tracker":
    st.header("📊 Mood Tracker")
    opts = ["😊 Happy","😔 Sad","😤 Frustrated","❤️ In Love","😴 Tired","😎 Confident","Custom"]
    with st.form('mood_form'):
        m = st.selectbox('How are you feeling today?', opts)
        custom = ''
        if m=='Custom': custom = st.text_input('Enter custom mood')
        note = st.text_area('Optional note')
        if st.form_submit_button('Submit'):
            mood_ws.append_row([current_user, custom if custom else m, note, now.strftime("%Y-%m-%d %H:%M:%S")])
            notes, bucket_items, calendar_items, mood_entries = fetch_data()
            st.success('Mood logged!')
    st.subheader("💬 Past Mood Entries")
    for m in reversed(mood_entries): st.markdown(f"*{m['Timestamp']}* — **{m['Name']}** felt *{m['Mood']}* — {m['Note']}")
