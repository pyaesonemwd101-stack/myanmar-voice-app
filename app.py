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

# Custom CSS for Mobile
st.markdown("""
<style>
    .stApp { max-width: 500px; margin: 0 auto; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 10px; }
</style>
""", unsafe_allow_stdio=True)

# Initialize Session State
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""

def transcribe_audio(audio_bytes):
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        # Using Google Speech Recognition with Myanmar Language
        return recognizer.recognize_google(audio_data, language="my-MM")
    except Exception as e:
        return f"Error: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.write("Version: 1.4.0")
    st.markdown("---")
    st.subheader("📱 Mobile")
    st.info("Status: Online")

# --- MAIN UI ---
st.title("🎤 Myanmar Voice")

tab1, tab2, tab3 = st.tabs(["🔴 Record", "💾 Save", "📂 History"])

with tab1:
    from streamlit_mic_recorder import mic_recorder
    st.write("Tap to speak in Myanmar.")
    
    # The recorder handles the browser microphone access
    audio = mic_recorder(
        start_prompt="🎤 Start Recording",
        stop_prompt="🛑 Stop & Process",
        key='recorder',
        use_container_width=True
    )

    if audio:
        st.audio(audio['bytes'])
        with st.spinner("Transcribing..."):
            text = transcribe_audio(audio['bytes'])
            if "Error:" in text:
                st.error("Audio unclear. Please speak louder and try again.")
            else:
                st.session_state.current_text = text
                st.success("Converted!")
                st.text_area("Result:", value=text, height=150)

with tab2:
    if st.session_state.current_text:
        st.subheader("Save Note")
        now = datetime.datetime.now().strftime("%d-%b-%Y_%H%M")
        file_name = st.text_input("Name:", value=f"Myanmar_Note_{now}")
        
        if st.button("✅ Save to History", use_container_width=True):
            entry = {
                "name": f"{file_name}.txt",
                "content": st.session_state.current_text,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.history.append(entry)
            st.toast("Saved!")
            
        st.download_button(
            label="📥 Download .txt",
            data=st.session_state.current_text,
            file_name=f"{file_name}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.warning("Please record your voice first.")

with tab3:
    st.subheader("Records")
    if not st.session_state.history:
        st.write("No saved notes.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"📄 {item['name']}"):
                st.write(item['content'])
                st.caption(f"Recorded: {item['time']}")
