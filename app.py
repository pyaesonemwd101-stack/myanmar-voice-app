import streamlit as st
import datetime
import io
import time
import base64
import requests

# App Configuration
st.set_page_config(
    page_title="Myanmar AI Story Studio", 
    page_icon="🎙️", 
    layout="centered"
)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pyidaungsu&display=swap');
    .stApp { max-width: 550px; margin: 0 auto; font-family: 'Pyidaungsu', sans-serif; }
    .stTextArea textarea { font-size: 1.1rem !important; line-height: 1.6; }
    .stButton button { border-radius: 20px; transition: 0.3s; }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_KEY = ""  # Provided by the environment
MODEL_ID = "gemini-2.5-flash-preview-09-2025"

# Initialize Session State
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'last_processed_audio_hash' not in st.session_state:
    st.session_state.last_processed_audio_hash = None
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

def transcribe_with_ai(audio_bytes, language_name):
    """
    Advanced AI Transcription using Gemini 2.5 Flash.
    Includes exponential backoff for reliability.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={API_KEY}"
    
    # Convert audio to base64 for the API
    encoded_audio = base64.b64encode(audio_bytes).decode('utf-8')
    
    prompt = f"Please transcribe this audio accurately. The language is {language_name}. If it is a story or novel, ensure the Myanmar punctuation and grammar are natural and beautiful. Only return the transcribed text."
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inlineData": {
                        "mimeType": "audio/wav",
                        "data": encoded_audio
                    }
                }
            ]
        }]
    }

    # Exponential Backoff Implementation
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                text = result.candidates[0].content.parts[0].text
                return text.strip()
            elif response.status_code == 429: # Rate limit
                time.sleep(2**i)
                continue
            else:
                return f"⚠️ API Error ({response.status_code}): {response.text}"
        except Exception as e:
            if i == max_retries - 1:
                return f"⚠️ System error: {str(e)}"
            time.sleep(2**i)
    return "⚠️ Failed to connect to AI after multiple attempts."

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("🤖 AI Settings")
    
    lang_choice = st.radio(
        "Voice Language",
        ["Myanmar (မြန်မာ)", "English (US)"],
        index=0
    )
    
    st.divider()
    st.success("AI Model: Gemini 2.5 Flash")
    st.info("The AI will now analyze your voice and grammar for 30%+ better accuracy.")

# --- MAIN APP ---
st.title("🎙️ AI Story Writer")
st.markdown("Speak your heart out. Our AI will handle the transcription and grammar.")

tab_write, tab_save, tab_lib = st.tabs(["✍️ Dictate", "💾 Chapter Info", "📚 Library"])

with tab_write:
    audio_file = st.audio_input(
        f"Record in {lang_choice}", 
        key=f"mic_widget_{st.session_state.reset_key}"
    )

    if audio_file is not None:
        current_hash = f"{audio_file.name}_{audio_file.size}"
        
        if st.session_state.last_processed_audio_hash != current_hash:
            with st.status("AI is analyzing your voice...", expanded=True) as status:
                audio_bytes = audio_file.read()
                result = transcribe_with_ai(audio_bytes, lang_choice)
                
                if "⚠️" in result:
                    status.update(label="AI Analysis failed", state="error")
                    st.error(result)
                else:
                    if st.session_state.current_text:
                        st.session_state.current_text += "\n" + result
                    else:
                        st.session_state.current_text = result
                    
                    st.session_state.last_processed_audio_hash = current_hash
                    status.update(label="AI Transcription Complete!", state="complete")
                    st.balloons()

    # Story Editor
    if st.session_state.current_text:
        st.markdown("### 📖 Chapter Draft")
        st.session_state.current_text = st.text_area(
            "Edit your text here:", 
            value=st.session_state.current_text, 
            height=400,
            key=f"area_{st.session_state.reset_key}"
        )
        
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if st.button("📋 Copy All", use_container_width=True):
                st.toast("Copied!")
                st.code(st.session_state.current_text, language=None)
        with c2:
            if st.button("🔄 Clear Draft", use_container_width=True):
                st.session_state.current_text = ""
                st.session_state.last_processed_audio_hash = None
                st.session_state.reset_key += 1
                st.rerun()
        with c3:
            st.markdown(f"**Words:** {len(st.session_state.current_text.split())}")

with tab_save:
    if st.session_state.current_text:
        st.subheader("Archive Chapter")
        c_title = st.text_input("Chapter Name", value=f"Chapter {len(st.session_state.history)+1}")
        
        if st.button("📂 Save to Library", type="primary", use_container_width=True):
            st.session_state.history.append({
                "title": c_title,
                "text": st.session_state.current_text,
                "lang": lang_choice,
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.success("Saved successfully!")
    else:
        st.info("Record some text first to save a chapter.")

with tab_lib:
    if not st.session_state.history:
        st.write("Your library is empty.")
    else:
        for idx, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"📜 {item['title']} - {item['date']}"):
                st.caption(f"Language: {item['lang']}")
                st.write(item['text'])
                if st.button("Use this as current draft", key=f"restore_{idx}"):
                    st.session_state.current_text = item['text']
                    st.rerun()
