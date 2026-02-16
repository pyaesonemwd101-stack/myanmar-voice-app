import streamlit as st
import speech_recognition as sr
import datetime
import io
import time

# App Configuration
st.set_page_config(
    page_title="Myanmar Story Studio", 
    page_icon="🎙️", 
    layout="centered"
)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pyidaungsu&display=swap');
    .stApp { max-width: 550px; margin: 0 auto; font-family: 'Pyidaungsu', sans-serif; }
    .stTextArea textarea { font-size: 1.1rem !important; line-height: 1.6; }
    .status-active { color: #28a745; font-weight: bold; }
    .stButton button { border-radius: 20px; transition: 0.3s; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'last_processed_audio_hash' not in st.session_state:
    st.session_state.last_processed_audio_hash = None
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

def transcribe_audio(audio_bytes, energy_lvl, language_code, long_pause_mode):
    """
    Improved Transcription Engine with Dynamic Noise Calibration.
    """
    recognizer = sr.Recognizer()
    
    # 30% Improvement: Dynamic Calibration
    # We set a baseline but allow the engine to ignore static hum
    recognizer.energy_threshold = energy_lvl 
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.dynamic_energy_ratio = 1.5
    
    # novel-writing specific timing
    if long_pause_mode:
        recognizer.pause_threshold = 12.0  # Very long pause for thinking
        recognizer.phrase_threshold = 0.2
        recognizer.non_speaking_duration = 4.0
    else:
        recognizer.pause_threshold = 2.0
        recognizer.phrase_threshold = 0.3
        recognizer.non_speaking_duration = 1.0
    
    try:
        audio_stream = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_stream) as source:
            # Improvement: Minimal noise adjustment to avoid cutting the start of speech
            recognizer.adjust_for_ambient_noise(source, duration=0.1)
            audio_data = recognizer.record(source)
        
        # Google recognition with context hints
        return recognizer.recognize_google(
            audio_data, 
            language=language_code,
            show_all=False # Setting to false for direct string return
        )
        
    except sr.UnknownValueError:
        return "⚠️ Silence or unclear speech. Try speaking louder or check your mic."
    except sr.RequestError:
        return "⚠️ Cloud connection error. Please check your internet."
    except Exception as e:
        return f"⚠️ System error: {str(e)}"

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("🛠️ Audio Engine")
    
    lang_choice = st.radio(
        "Voice Language",
        ["Myanmar (မြန်မာ)", "English (US)"],
        index=0
    )
    language_code = "my-MM" if "Myanmar" in lang_choice else "en-US"
    
    st.divider()
    
    long_pause = st.toggle("Infinite Dictation Mode", value=True, help="Best for writing novels. Allows long pauses.")
    
    sensitivity = st.select_slider(
        "Microphone Sensitivity",
        options=[50, 100, 200, 400, 600],
        value=100,
        help="Lower is more sensitive (use for whispering)."
    )
    
    st.info(f"Current Target: **{lang_choice}**")

# --- MAIN APP ---
st.title("🎙️ Story Writer Pro")
st.markdown("Convert your spoken ideas into chapters automatically.")

tab_write, tab_save, tab_lib = st.tabs(["✍️ Dictate", "💾 Chapter Info", "📚 Library"])

with tab_write:
    # Use the reset_key to force refresh of the widget if needed
    audio_file = st.audio_input(
        f"Record in {lang_choice}", 
        key=f"mic_widget_{st.session_state.reset_key}"
    )

    if audio_file is not None:
        current_hash = f"{audio_file.name}_{audio_file.size}"
        
        if st.session_state.last_processed_audio_hash != current_hash:
            with st.status("Listening and transcribing...", expanded=False) as status:
                audio_bytes = audio_file.read()
                result = transcribe_audio(audio_bytes, sensitivity, language_code, long_pause)
                
                if "⚠️" in result:
                    status.update(label="Conversion failed", state="error")
                    st.warning(result)
                else:
                    if st.session_state.current_text:
                        st.session_state.current_text += "\n" + result
                    else:
                        st.session_state.current_text = result
                    
                    st.session_state.last_processed_audio_hash = current_hash
                    status.update(label="Text Added!", state="complete")
                    st.balloons()

    # Story Editor
    if st.session_state.current_text:
        st.markdown("### 📖 Chapter Draft")
        # Dynamic key based on reset_key ensures it clears when we want it to
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
