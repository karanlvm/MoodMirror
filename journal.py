import json
import os
import tempfile
import base64
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import google.generativeai as genai
from gtts import gTTS

# Set page config
st.set_page_config(page_title="AI Mood Mirror", layout="centered")
st.markdown("# 🪞 AI Mood Mirror\nYour reflective AI therapist that connects your mood with your body.")

# Configure Gemini with Gemini 1.5 Flash
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# JSON file to persist journal history (if needed)
HISTORY_FILE = "journal_history.json"
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        journal_history = json.load(f)
else:
    journal_history = []

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# -------------------- Sidebar: State of Mind Logging --------------------
with st.sidebar:
    st.header("State of Mind Logging")
    
    # Gen‑Z mode toggle
    gen_z_mode = st.checkbox("Activate Gen‑Z Mode", value=False, help="Toggle to use a casual, trendy tone with Gen‑Z slang.")
    
    # Upload health data CSV
    st.subheader("📁 Upload Health Data")
    csv_file = st.file_uploader("Upload health_data_extracted.csv", type='csv')
    
    health_df = pd.DataFrame()
    if csv_file:
        health_df = pd.read_csv(csv_file, parse_dates=['startDate'])
        health_df['startDate'] = health_df['startDate'].dt.tz_localize(None)
        if 'endDate' in health_df.columns:
            health_df['endDate'] = pd.to_datetime(health_df['endDate']).dt.tz_localize(None)
    
    # Week picker
    st.subheader("🗓 Select Your Week")
    week_start = st.date_input("Choose week start")
    week_end = week_start + timedelta(days=6)
    
    # Mood and journal entry
    st.subheader("😌 Mood and Journal")
    mood_options = {
        "😄 Happy": "happy",
        "😐 Neutral": "neutral",
        "😢 Sad": "sad",
        "😰 Anxious": "anxious",
        "😠 Angry": "angry"
    }
    mood_choice = st.radio("Select your overall mood:", list(mood_options.keys()), horizontal=True)
    journal = st.text_area("📝 Reflect on your week:", height=200, placeholder="Write about what you experienced this week...")
    
    # Reflect button – generate a brief weekly reflection including health insights
    if st.button("✨ Reflect") and journal:
        if health_df.empty:
            st.warning("Please upload your health data CSV before reflecting.")
        else:
            week_health = health_df[
                (health_df['startDate'] >= pd.to_datetime(week_start)) &
                (health_df['startDate'] <= pd.to_datetime(week_end))
            ]
            if not week_health.empty:
                health_summary = week_health.groupby('type')['value'].apply(list).to_dict()
                health_summary_json = json.dumps(health_summary, indent=2)
            else:
                health_summary_json = "No health data available for this week."
            
            gen_z_instruction = ""
            if gen_z_mode:
                gen_z_instruction = " Please respond in a Gen‑Z style using casual, trendy language with modern slang."
            
            prompt = f"""
I'm a user journaling my emotions and mood for the week {week_start} to {week_end}.

Mood: {mood_choice}
Journal entry: {journal}

Health data summary:
{health_summary_json}

Please act as a supportive AI therapist and provide a very brief summary of my week in 1-2 concise sentences that includes insights drawn from both my mood journal and my health data. Invite further conversation.{gen_z_instruction}
            """
            with st.spinner("Generating your weekly reflection..."):
                response = model.generate_content(prompt)
                reflection_text = response.text.strip()
            
            # Append the reflection as a chat message from the assistant.
            # For display, include the prefix; we'll remove it for audio playback.
            therapist_message = f"🧠 Your Weekly Reflection: {reflection_text}"
            st.session_state.chat_history.append({
                "role": "assistant",
                "text": therapist_message
            })
            
            journal_history.append({
                "week_start": str(week_start),
                "week_end": str(week_end),
                "mood": mood_choice,
                "journal": journal,
                "reflection": reflection_text,
                "gen_z_mode": gen_z_mode
            })
            with open(HISTORY_FILE, "w") as f:
                json.dump(journal_history, f, indent=2)

# -------------------- Main Area: Chat Interface --------------------
# Create a header row with the chat title and New Chat button aligned to the right
col_header1, col_header2 = st.columns([8, 2])
with col_header1:
    st.subheader("💬 Chat with Gemini Therapist")
with col_header2:
    if st.button("New Chat"):
        st.session_state.chat_history = []
        st.rerun()

# Display chat conversation with a "Hear this response" button for therapist messages
if st.session_state.chat_history:
    for i, msg in enumerate(st.session_state.chat_history):
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['text']}")
        else:
            st.markdown(f"**Therapist:** {msg['text']}")
            # Remove the "🧠 Your Weekly Reflection:" prefix for audio conversion
            audio_text = msg["text"]
            if audio_text.startswith("🧠 Your Weekly Reflection:"):
                audio_text = audio_text.replace("🧠 Your Weekly Reflection:", "").strip()
            # Create a button for playing the audio without displaying a player
            if st.button("Hear this response", key=f"audio_{i}"):
                tts = gTTS(text=audio_text, lang='en')
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                    tts.save(fp.name)
                    with open(fp.name, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                    encoded_audio = base64.b64encode(audio_bytes).decode()
                    audio_html = f'''
                    <audio autoplay style="display:none;">
                        <source src="data:audio/mp3;base64,{encoded_audio}" type="audio/mp3">
                    </audio>
                    '''
                    st.components.v1.html(audio_html, height=0)
else:
    st.info("Your conversation will appear here. Start by sending a message!")

# Chat input form (text only)
with st.form("chat_form", clear_on_submit=True):
    user_message = st.text_input("Enter your message:")
    submitted = st.form_submit_button("Send")
    if submitted and user_message:
        st.session_state.chat_history.append({"role": "user", "text": user_message})
        conversation = "\n".join([f"{msg['role']}: {msg['text']}" for msg in st.session_state.chat_history])
        if gen_z_mode:
            conversation = "You are a Gen‑Z style supportive therapist. Use casual, trendy language with modern slang in all your responses. " + conversation
        conversation += "\nassistant:"
        with st.spinner("Gemini is replying..."):
            response = model.generate_content(conversation)
        st.session_state.chat_history.append({"role": "assistant", "text": response.text.strip()})
        st.rerun()
