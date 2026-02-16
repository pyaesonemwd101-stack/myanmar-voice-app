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
    
    /* Highlight the transcription result */
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

def transcribe_audio(audio_bytes):
    recognizer = sr.Recognizer()
    # Increase sensitivity to quiet audio
    # Energy threshold 300 helps pick up voices in quieter environments
    recognizer.energy_threshold = 300 
    audio_file = io.BytesIO(audio_bytes)
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        # Using Google Speech Recognition with Myanmar Language
        return recognizer.recognize_google(audio_data, language="my-MM")
    except sr.UnknownValueError:
        return "Error: Could not understand audio. Try speaking closer to the mic."
    except sr.RequestError:
        return "Error: Internet connection issue."
    except Exception as e:
        return f"Error: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.write("Version: 1.5.0")
    st.markdown("---")
    st.subheader("💡 Tips for Clarity")
    st.info("""
    1. Speak clearly in Burmese.
    2. Reduce background noise.
    3. Hold the mic closer.
    4. Wait 1 second after clicking Start.
    """)

# --- MAIN UI ---
st.title("🎤 Myanmar Voice")
st.caption("Advanced Speech-to-Text with Live Edit")

tab1, tab2, tab3 = st.tabs(["🔴 Record", "💾 Save", "📂 History"])

with tab1:
    from streamlit_mic_recorder import mic_recorder
    st.write("Tap below to start speaking.")
    
    audio = mic_recorder(
        start_prompt="🎤 Start Recording",
        stop_prompt="🛑 Stop & Convert",
        key='recorder',
        use_container_width=True
    )

    if audio:
        st.audio(audio['bytes'])
        with st.spinner("Converting to Myanmar text..."):
            result = transcribe_audio(audio['bytes'])
            if "Error:" in result:
                st.error(result)
            else:
                st.session_state.current_text = result
                st.success("Converted! Please verify below:")

    # LIVE VERIFICATION FEATURE
    # This addresses your request to check whether the text is correct
    if st.session_state.current_text:
        st.markdown("### 📝 Check & Edit Text")
        # Display the result in a text area so the user can edit it
        edited_text = st.text_area(
            "Is this correct? (You can type here to fix)", 
            value=st.session_state.current_text, 
            height=200,
            help="If the AI made a mistake, you can manually correct the Burmese text here before saving."
        )
        # Keep the session state updated with any manual changes
        st.session_state.current_text = edited_text
        
        if st.button("🗑️ Clear Result", use_container_width=True):
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
            st.toast("Saved successfully!")
            
        st.download_button(
            label="📥 Download .txt for WPS",
            data=st.session_state.current_text,
            file_name=f"{file_name}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.warning("Please record and verify your voice text in the 'Record' tab first.")

with tab3:
    st.subheader("Records")
    if not st.session_state.history:
        st.write("Your saved notes will appear here.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"📄 {item['name']} ({item['time']})"):
                st.write(item['content'])
