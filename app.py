import streamlit as st
import speech_recognition as sr
import datetime
import io

# App Configuration
st.set_page_config(
    page_title="Myanmar Voice App", 
    page_icon="🇲🇲", 
    layout="centered"
)

# Custom CSS for Mobile and Myanmar Font support
style_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pyidaungsu&display=swap');
    
    .stApp { 
        max-width: 500px; 
        margin: 0 auto; 
        font-family: 'Pyidaungsu', sans-serif;
    }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 10px; }
    
    /* Result box styling */
    .result-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        margin-top: 10px;
    }
</style>
"""
st.markdown(style_css, unsafe_allow_html=True)

# Initialize Session State
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'last_processed_audio_hash' not in st.session_state:
    st.session_state.last_processed_audio_hash = None

def transcribe_audio(audio_file, energy_lvl):
    """
    Enhanced Transcription Engine inspired by Google Translate.
    Uses noise calibration and optimized timeouts for Burmese accents.
    """
    recognizer = sr.Recognizer()
    
    # 1. Sensitivity calibration
    recognizer.energy_threshold = energy_lvl 
    
    # 2. Dynamic adjustments (How Google handles different environments)
    # Allows the engine to be more patient with slow Burmese speech
    recognizer.pause_threshold = 1.2  # Seconds of silence before a phrase is considered done
    recognizer.phrase_threshold = 0.3 # Minimum seconds of speaking to be considered a phrase
    recognizer.non_speaking_duration = 0.8
    
    try:
        with sr.AudioFile(audio_file) as source:
            # 3. Ambient Noise Adjustment (Crucial for accuracy)
            # This 'listens' to the file briefly to cancel out background static
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
        
        # 4. Global Speech API with my-MM locale
        return recognizer.recognize_google(audio_data, language="my-MM")
        
    except sr.UnknownValueError:
        return "Error: Speech unclear. Tips: Speak slower, stay close to mic, or lower 'Energy Threshold' in Settings."
    except sr.RequestError:
        return "Error: Connection lost. Google Speech API is unavailable."
    except Exception as e:
        if "PCM" in str(e):
            return "Error: Recording format error. Please try again."
        return f"Error: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.write("Version: 1.8.0")
    
    st.subheader("🎤 Voice Calibration")
    energy_lvl = st.slider(
        "Sensitivity (Energy)", 
        50, 1000, 300, 
        help="Lower this if the app is 'missing' your voice. Raise it if it's picking up too much background noise."
    )
    
    st.markdown("---")
    st.subheader("💡 Expert Tips")
    st.info("""
    - **Burmese Accent:** The engine works best when you speak clearly and pause slightly between sentences.
    - **Noise:** If you are in a noisy room, set the slider to 500+.
    - **Silence:** In a quiet room, set it to 150.
    """)

# --- MAIN UI ---
st.title("🎤 Myanmar Voice")
st.caption("Enhanced Recognition Engine (v1.8)")

tab1, tab2, tab3 = st.tabs(["🔴 Record", "💾 Save", "📂 History"])

with tab1:
    st.write("Record or upload your Burmese speech:")
    
    audio_data = st.audio_input("Press the mic to speak", key="my_audio_input")

    if audio_data is not None:
        file_name = getattr(audio_data, 'name', 'recorded_audio.wav')
        file_size = getattr(audio_data, 'size', 0)
        current_audio_hash = f"{file_name}_{file_size}"
        
        if st.session_state.last_processed_audio_hash != current_audio_hash:
            with st.spinner("AI is analyzing your voice..."):
                result = transcribe_audio(audio_data, energy_lvl)
                
                if "Error:" in result:
                    st.error(result)
                else:
                    st.session_state.current_text = result
                    st.session_state.last_processed_audio_hash = current_audio_hash
                    st.success("Converted successfully!")

    if st.session_state.current_text:
        st.markdown("### 📝 Verification & Correction")
        
        st.session_state.current_text = st.text_area(
            "Check and fix the text here:", 
            value=st.session_state.current_text, 
            height=200,
            key="verify_text_area_v4"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copy Text", use_container_width=True):
                st.toast("Click the copy icon in the box below!")
                st.code(st.session_state.current_text, language=None)
        with col2:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.current_text = ""
                st.session_state.last_processed_audio_hash = None
                st.rerun()

with tab2:
    if st.session_state.current_text:
        st.subheader("Save Document")
        now = datetime.datetime.now().strftime("%d-%b-%Y_%H%M")
        file_name_input = st.text_input("Filename:", value=f"Myanmar_Note_{now}")
        
        if st.button("✅ Save to History", use_container_width=True):
            entry = {
                "name": f"{file_name_input}.txt",
                "content": st.session_state.current_text,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.history.append(entry)
            st.toast("Saved!")
            
        st.download_button(
            label="📥 Download .txt",
            data=st.session_state.current_text,
            file_name=f"{file_name_input}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.warning("Please record your voice first.")

with tab3:
    st.subheader("Saved Records")
    if not st.session_state.history:
        st.write("No history found.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"📄 {item['name']} ({item['time']})"):
                st.write(item['content'])
                if st.button(f"📋 Copy Note", key=f"copy_{i}"):
                    st.code(item['content'], language=None)
