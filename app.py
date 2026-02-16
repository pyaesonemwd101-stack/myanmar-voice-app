import streamlit as st
import speech_recognition as sr
import datetime
import io

# Custom component for web/mobile compatibility
try:
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    st.error("Please install the recorder component: pip install streamlit-mic-recorder")

# Configuration for the page
st.set_page_config(
    page_title="Myanmar Voice To Text", 
    page_icon="🇲🇲", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a more "App-like" feel on mobile
st.markdown("""
    <style>
    .stApp {
        max-width: 500px;
        margin: 0 auto;
    }
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    /* Style for the tabs to look better on Android */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #eeeeee;
        border-radius: 10px 10px 0px 0px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_stdio=True)

# Initialize session state for storage
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""

def transcribe_audio(audio_bytes):
    """Helper to convert audio bytes to Myanmar text using Google Speech-to-Text"""
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    try:
        # High-accuracy Myanmar (Burmese) language recognition
        return recognizer.recognize_google(audio, language="my-MM")
    except sr.UnknownValueError:
        return "Error: Could not understand audio. Please speak clearly in Myanmar accent."
    except sr.RequestError:
        return "Error: Internet connection issue. Please check your data/wifi."
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    # --- SETTINGS SIDEBAR (Access via Top Left Icon) ---
    with st.sidebar:
        st.header("⚙️ Settings")
        st.write("App Version: 1.0.0")
        st.write("Engine: Google Myanmar ASR")
        st.markdown("---")
        
        # Placeholder for your APK link
        # After you convert this to an APK, replace this link
        apk_url = "https://your-apk-download-link.com" 
        st.subheader("📱 Android App")
        st.info("Download the dedicated Android installer below:")
        st.link_button("📥 Download APK Version", apk_url, use_container_width=True)
        
        st.markdown("---")
        st.caption("Developed for Myanmar Voice-to-Text Purpose")

    # --- MAIN UI ---
    st.title("🎤 Myanmar Voice")
    st.write("Instant Burmese speech to text conversion.")
    
    tab1, tab2, tab3 = st.tabs(["🔴 Record", "💾 Save & Name", "📂 Check History"])

    # --- TAB 1: RECORD ---
    with tab1:
        st.write("Tap the mic button and speak clearly.")
        audio = mic_recorder(
            start_prompt="🎤 Start Recording (Myanmar)",
            stop_prompt="🛑 Stop & Process Text",
            key='recorder',
            use_container_width=True
        )

        if audio:
            st.audio(audio['bytes'])
            with st.spinner("Converting Myanmar Voice to Text..."):
                text = transcribe_audio(audio['bytes'])
                if "Error:" in text:
                    st.error(text)
                else:
                    st.session_state.current_text = text
                    st.success("Successfully Transcribed!")
                    st.text_area("Your Text:", value=st.session_state.current_text, height=180)

    # --- TAB 2: SAVE & RENAME ---
    with tab2:
        if st.session_state.current_text:
            st.subheader("Save as Document")
            st.write("Content:")
            st.info(st.session_state.current_text)
            
            # Timestamp for auto-naming
            now = datetime.datetime.now().strftime("%d-%b-%Y_%H%M")
            file_name = st.text_input("Enter File Name:", value=f"Myanmar_Note_{now}")
            
            if st.button("✅ Confirm Save to History", use_container_width=True):
                entry = {
                    "name": f"{file_name}.txt",
                    "content": st.session_state.current_text,
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.session_state.history.append(entry)
                st.toast("Saved to your local history!")
            
            # Direct download for WPS/Notepad
            st.download_button(
                label="📥 Download .txt File (for WPS)",
                data=st.session_state.current_text,
                file_name=f"{file_name}.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.warning("Nothing to save. Go to the 'Record' tab first.")

    # --- TAB 3: CHECK MESSAGES/HISTORY ---
    with tab3:
        st.subheader("Saved Records")
        if not st.session_state.history:
            st.write("You have no saved messages yet.")
        else:
            for i, item in enumerate(reversed(st.session_state.history)):
                with st.expander(f"📄 {item['name']} - {item['time']}"):
                    st.write(item['content'])
                    st.download_button(
                        "Download Again", 
                        item['content'], 
                        item['name'], 
                        key=f"hist_btn_{i}",
                        use_container_width=True
                    )

if __name__ == "__main__":
    main()