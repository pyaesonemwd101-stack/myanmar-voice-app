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
    Transcribes audio using SpeechRecognition.
    Expects a file-like object (BytesIO or UploadedFile).
    """
    recognizer = sr.Recognizer()
    # Adjust sensitivity based on sidebar setting
    recognizer.energy_threshold = energy_lvl 
    
    try:
        # We use sr.AudioFile to read the uploaded/recorded file
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        
        # Using Google Speech Recognition with Myanmar Language
        return recognizer.recognize_google(audio_data, language="my-MM")
    except sr.UnknownValueError:
        return "Error: Could not understand audio. Try speaking more clearly or adjusting the sensitivity."
    except sr.RequestError:
        return "Error: Internet connection issue with Speech API."
    except Exception as e:
        if "PCM" in str(e):
            return "Error: Audio format mismatch. Please try recording again."
        return f"Error: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.write("Version: 1.7.3")
    
    # Sensitivity slider to help with different accents/noise
    st.subheader("🎤 Microphone Sensitivity")
    energy_lvl = st.slider("Energy Threshold", 50, 1000, 300, help="Lower = More sensitive to quiet speech. Higher = Ignores more background noise.")
    
    st.markdown("---")
    st.subheader("💡 Tips for Accuracy")
    st.info("""
    - Speak at a steady pace.
    - Avoid high background noise.
    - Ensure your browser has mic permissions.
    """)

# --- MAIN UI ---
st.title("🎤 Myanmar Voice")
st.caption("Advanced Speech-to-Text with Copy Feature")

tab1, tab2, tab3 = st.tabs(["🔴 Record", "💾 Save", "📂 History"])

with tab1:
    st.write("Record your voice below:")
    
    # Using the native Streamlit audio_input
    audio_data = st.audio_input("Record your Myanmar speech", key="my_audio_input")

    # Only process if we have audio and it's different from the one we just processed
    if audio_data is not None:
        # FIX: Use a composite hash (name + size) instead of .id to avoid AttributeErrors on some platforms
        file_name = getattr(audio_data, 'name', 'recorded_audio.wav')
        file_size = getattr(audio_data, 'size', 0)
        current_audio_hash = f"{file_name}_{file_size}"
        
        if st.session_state.last_processed_audio_hash != current_audio_hash:
            with st.spinner("Converting to Myanmar text..."):
                result = transcribe_audio(audio_data, energy_lvl)
                
                if "Error:" in result:
                    st.error(result)
                else:
                    st.session_state.current_text = result
                    st.session_state.last_processed_audio_hash = current_audio_hash
                    st.success("Converted successfully!")

    # LIVE VERIFICATION & EDITING
    if st.session_state.current_text:
        st.markdown("### 📝 Check & Edit Text")
        
        # Text area for corrections
        st.session_state.current_text = st.text_area(
            "Correct the text if needed:", 
            value=st.session_state.current_text, 
            height=200,
            key="verify_text_area_v3"
        )
        
        # Display as a code block for easier manual copying if the button fails
        if st.button("📋 Show Copyable Text", use_container_width=True):
            st.toast("Copy the text inside the box below!")
            st.code(st.session_state.current_text, language=None)
        
        if st.button("🗑️ Clear Everything", use_container_width=True):
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
            st.toast("Saved to History tab!")
            
        st.download_button(
            label="📥 Download .txt for WPS",
            data=st.session_state.current_text,
            file_name=f"{file_name_input}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.warning("Please record and verify your text in the 'Record' tab first.")

with tab3:
    st.subheader("Records")
    if not st.session_state.history:
        st.write("Your saved notes will appear here.")
    else:
        # Using reversed to show newest at the top
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"📄 {item['name']} ({item['time']})"):
                st.write(item['content'])
                if st.button(f"📋 Copy This Note", key=f"copy_{i}"):
                    st.code(item['content'], language=None)
