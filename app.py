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

def transcribe_audio(audio_file, energy_lvl, is_story_mode):
    """
    Enhanced Transcription Engine optimized for Long-form Content.
    """
    recognizer = sr.Recognizer()
    
    # Sensitivity calibration
    recognizer.energy_threshold = energy_lvl 
    
    # Adjust thresholds for long-form dictation
    if is_story_mode:
        # High pause threshold allows for long thinking gaps in storytelling
        recognizer.pause_threshold = 3.0  
        recognizer.phrase_threshold = 0.5
        recognizer.non_speaking_duration = 1.5
    else:
        recognizer.pause_threshold = 1.2
        recognizer.phrase_threshold = 0.3
        recognizer.non_speaking_duration = 0.8
    
    try:
        with sr.AudioFile(audio_file) as source:
            # Calibrate for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Record the entire file without duration limits
            audio_data = recognizer.record(source)
        
        # Global Speech API with my-MM locale
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
    st.write("Version: 1.9.0")
    
    st.subheader("📝 Mode Selection")
    story_mode = st.toggle("Story Mode (Long Dictation)", value=True, help="Enable this for writing novels or long ideas. It allows for longer pauses between words.")
    
    st.subheader("🎤 Voice Calibration")
    energy_lvl = st.slider(
        "Sensitivity (Energy)", 
        50, 1000, 200, 
        help="Lower this for quiet storytelling."
    )
    
    st.markdown("---")
    st.subheader("💡 Storytelling Tips")
    st.info("""
    - **Long Pauses:** Story Mode allows up to 3 seconds of silence.
    - **Flow:** Speak naturally as if telling a story to a friend.
    - **Drafting:** Use the Edit box below to combine multiple recordings into one chapter.
    """)

# --- MAIN UI ---
st.title("🎤 Myanmar Story Writer")
st.caption("Optimized for Novels and Long-form Ideas")

tab1, tab2, tab3 = st.tabs(["🔴 Record", "💾 Save", "📂 History"])

with tab1:
    st.write("Dictate your story ideas below:")
    
    audio_data = st.audio_input("Press the mic to start your story", key="my_audio_input")

    if audio_data is not None:
        file_name = getattr(audio_data, 'name', 'recorded_audio.wav')
        file_size = getattr(audio_data, 'size', 0)
        current_audio_hash = f"{file_name}_{file_size}"
        
        if st.session_state.last_processed_audio_hash != current_audio_hash:
            with st.spinner("Processing your story..."):
                result = transcribe_audio(audio_data, energy_lvl, story_mode)
                
                if "Error:" in result:
                    st.error(result)
                else:
                    # For long-form, we often want to append to existing text
                    if st.session_state.current_text:
                        st.session_state.current_text += "\n\n" + result
                    else:
                        st.session_state.current_text = result
                        
                    st.session_state.last_processed_audio_hash = current_audio_hash
                    st.success("Added to draft!")

    if st.session_state.current_text:
        st.markdown("### 📝 Story Draft")
        
        # Larger text area for novel writing
        st.session_state.current_text = st.text_area(
            "Draft Content:", 
            value=st.session_state.current_text, 
            height=350,
            key="verify_text_area_v5"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copy Chapter", use_container_width=True):
                st.toast("Copy the text inside the box below!")
                st.code(st.session_state.current_text, language=None)
        with col2:
            if st.button("🗑️ Reset Draft", use_container_width=True):
                st.session_state.current_text = ""
                st.session_state.last_processed_audio_hash = None
                st.rerun()

with tab2:
    if st.session_state.current_text:
        st.subheader("Save Chapter")
        now = datetime.datetime.now().strftime("%d-%b-%Y_%H%M")
        file_name_input = st.text_input("Chapter/File Name:", value=f"Story_Chapter_{now}")
        
        if st.button("✅ Save to Library", use_container_width=True):
            entry = {
                "name": f"{file_name_input}.txt",
                "content": st.session_state.current_text,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.history.append(entry)
            st.toast("Saved to your history!")
            
        st.download_button(
            label="📥 Download Chapter (.txt)",
            data=st.session_state.current_text,
            file_name=f"{file_name_input}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.warning("Start dictating in the 'Record' tab to create a draft.")

with tab3:
    st.subheader("Saved Chapters")
    if not st.session_state.history:
        st.write("No saved stories yet.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"📖 {item['name']} ({item['time']})"):
                st.write(item['content'])
                if st.button(f"📋 Copy This Chapter", key=f"copy_{i}"):
                    st.code(item['content'], language=None)
