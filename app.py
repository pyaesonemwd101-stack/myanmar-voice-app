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

def transcribe_audio(audio_file):
    """
    Transcribes audio using SpeechRecognition.
    Expects a file-like object (BytesIO or UploadedFile).
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300 
    
    try:
        # We use sr.AudioFile to read the uploaded/recorded file
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        
        # Using Google Speech Recognition with Myanmar Language
        return recognizer.recognize_google(audio_data, language="my-MM")
    except sr.UnknownValueError:
        return "Error: Could not understand audio. Try speaking more clearly."
    except sr.RequestError:
        return "Error: Internet connection issue with Speech API."
    except Exception as e:
        # Catch the PCM/WAV error specifically and provide guidance
        if "PCM" in str(e):
            return "Error: Audio format mismatch. Please try recording again."
        return f"Error: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.write("Version: 1.6.0")
    st.markdown("---")
    st.subheader("💡 Tips for Clarity")
    st.info("""
    1. Click the microphone icon to start.
    2. Speak clearly in Burmese.
    3. Click the stop/square icon when finished.
    4. The system will convert automatically.
    """)

# --- MAIN UI ---
st.title("🎤 Myanmar Voice")
st.caption("Advanced Speech-to-Text with Format Fix")

tab1, tab2, tab3 = st.tabs(["🔴 Record", "💾 Save", "📂 History"])

with tab1:
    st.write("Record your voice below:")
    
    # Using the native Streamlit audio_input for better compatibility
    audio_data = st.audio_input("Record your Myanmar speech")

    if audio_data:
        # The built-in widget returns a file-like object that works well with sr.AudioFile
        with st.spinner("Converting to Myanmar text..."):
            result = transcribe_audio(audio_data)
            
            if "Error:" in result:
                st.error(result)
            else:
                st.session_state.current_text = result
                st.success("Converted successfully!")

    # LIVE VERIFICATION & EDITING
    if st.session_state.current_text:
        st.markdown("### 📝 Check & Edit Text")
        edited_text = st.text_area(
            "Correct the text if needed:", 
            value=st.session_state.current_text, 
            height=200,
            key="verify_text_area"
        )
        st.session_state.current_text = edited_text
        
        if st.button("🗑️ Clear Everything", use_container_width=True):
            st.session_state.current_text = ""
            st.rerun()

with tab2:
    if st.session_state.current_text:
        st.subheader("Save Document")
        now = datetime.datetime.now().strftime("%d-%b-%Y_%H%M")
        file_name = st.text_input("Filename:", value=f"Myanmar_Note_{now}")
        
        if st.button("✅ Save to History", use_container_width=True):
            entry = {
                "name": f"{file_name}.txt",
                "content": st.session_state.current_text,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.history.append(entry)
            st.toast("Saved to History tab!")
            
        st.download_button(
            label="📥 Download .txt for WPS",
            data=st.session_state.current_text,
            file_name=f"{file_name}.txt",
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
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"📄 {item['name']} ({item['time']})"):
                st.write(item['content'])
