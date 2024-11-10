import streamlit as st
from googletrans import Translator
from gtts import gTTS
import tempfile
import io
import numpy as np
import sounddevice as sd
from google.cloud import speech
from io import BytesIO
import google.auth
from google.auth import exceptions


# Initialize translator
translator = Translator()

# Define language codes
languages = {
    'Afrikaans': 'af', 'Albanian': 'sq', 'Amharic': 'am', 'Arabic': 'ar', 'Armenian': 'hy',
    'Azerbaijani': 'az', 'Basque': 'eu', 'Belarusian': 'be', 'Bengali': 'bn', 'Bosnian': 'bs',
    'Bulgarian': 'bg', 'Catalan': 'ca', 'Cebuano': 'ceb', 'Chinese (Simplified)': 'zh-CN',
    'Chinese (Traditional)': 'zh-TW', 'Corsican': 'co', 'Croatian': 'hr', 'Czech': 'cs',
    'Danish': 'da', 'Dutch': 'nl', 'English': 'en', 'Esperanto': 'eo', 'Estonian': 'et',
    'Finnish': 'fi', 'French': 'fr', 'Frisian': 'fy', 'Galician': 'gl', 'Georgian': 'ka',
    'German': 'de', 'Greek': 'el', 'Gujarati': 'gu', 'Haitian Creole': 'ht', 'Hausa': 'ha',
    'Hawaiian': 'haw', 'Hebrew': 'he', 'Hindi': 'hi', 'Hmong': 'hmn', 'Hungarian': 'hu',
    'Icelandic': 'is', 'Igbo': 'ig', 'Indonesian': 'id', 'Irish': 'ga', 'Italian': 'it',
    'Japanese': 'ja', 'Javanese': 'jw', 'Kannada': 'kn', 'Kazakh': 'kk', 'Khmer': 'km',
    'Kinyarwanda': 'rw', 'Korean': 'ko', 'Kurdish': 'ku', 'Kyrgyz': 'ky', 'Lao': 'lo',
    'Latin': 'la', 'Latvian': 'lv', 'Lithuanian': 'lt', 'Luxembourgish': 'lb', 'Macedonian': 'mk',
    'Malagasy': 'mg', 'Malay': 'ms', 'Malayalam': 'ml', 'Maltese': 'mt', 'Maori': 'mi',
    'Marathi': 'mr', 'Mongolian': 'mn', 'Myanmar (Burmese)': 'my', 'Nepali': 'ne',
    'Norwegian': 'no', 'Nyanja (Chichewa)': 'ny', 'Odia (Oriya)': 'or', 'Pashto': 'ps',
    'Persian': 'fa', 'Polish': 'pl', 'Portuguese': 'pt', 'Punjabi': 'pa', 'Romanian': 'ro',
    'Russian': 'ru', 'Samoan': 'sm', 'Scots Gaelic': 'gd', 'Serbian': 'sr', 'Sesotho': 'st',
    'Shona': 'sn', 'Sindhi': 'sd', 'Sinhala (Sinhalese)': 'si', 'Slovak': 'sk', 'Slovenian': 'sl',
    'Somali': 'so', 'Spanish': 'es', 'Sundanese': 'su', 'Swahili': 'sw', 'Swedish': 'sv',
    'Tagalog (Filipino)': 'tl', 'Tajik': 'tg', 'Tamil': 'ta', 'Tatar': 'tt', 'Telugu': 'te',
    'Thai': 'th', 'Turkish': 'tr', 'Turkmen': 'tk', 'Ukrainian': 'uk', 'Urdu': 'ur',
    'Uyghur': 'ug', 'Uzbek': 'uz', 'Vietnamese': 'vi', 'Welsh': 'cy', 'Xhosa': 'xh',
    'Yiddish': 'yi', 'Yoruba': 'yo', 'Zulu': 'zu'
}

# Set session state for conversation log
if 'languages_selected' not in st.session_state:
    st.session_state.languages_selected = {}

if 'conversation_log' not in st.session_state:
    st.session_state.conversation_started = False

def language_selection():
    # Title for the page
    st.title("Healthcare Translation App")

    # Add dropdowns for language selection
    st.subheader("Select Languages")

    # Patient's language selection
    patient_lang = st.selectbox("Select speaking language for Patient", options=list(languages.keys()))
    patient_desired_lang = st.selectbox("Select output desired language for Patient", options=list(languages.keys()))

    # Healthcare Provider's language selection
    healthcare_lang = st.selectbox("Select speaking language for Healthcare Provider", options=list(languages.keys()))
    healthcare_desired_lang = st.selectbox("Select output desired language for Healthcare Provider", options=list(languages.keys()))

    # Proceed button
    proceed = st.button("Proceed")

    # Step 2: Store language codes based on selection
    if proceed:
        # Save the language selection in session state
        st.session_state.languages_selected = {
            'patient_lang_code': languages[patient_lang],
            'patient_desired_lang_code': languages[patient_desired_lang],
            'healthcare_lang_code': languages[healthcare_lang],
            'healthcare_desired_lang_code': languages[healthcare_desired_lang]
        }

        st.write("Language selection complete. Proceed to start the conversation.")
        st.session_state.conversation_started = True  # Automatically start conversation after selection

        st.write(f"Patient Language: {patient_lang} ({languages[patient_lang]})")
        st.write(f"Patient desired Language: {patient_desired_lang} ({languages[patient_desired_lang]})")
        st.write(f"Healthcare Language: {healthcare_lang} ({languages[healthcare_lang]})")
        st.write(f"Healthcare desired Language: {healthcare_desired_lang} ({languages[healthcare_desired_lang]})")

# Function to capture and translate speech
def capture_and_translate(input_lang_code, output_lang_code):
    try:
        # Load credentials from the service account file
        credentials, project = google.auth.load_credentials_from_file(r"C:\Users\Hp\Downloads\healthcare-441317-834f74a710d0.json")
        client = speech.SpeechClient(credentials=credentials)
    except exceptions.DefaultCredentialsError as e:
        st.error(f"Error loading credentials: {e}")
        return None, None

    st.write("Listening...")
    # Record audio using sounddevice
    audio_data = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='int16')
    sd.wait()

    # Convert audio data to bytes
    audio_bytes = BytesIO(audio_data.tobytes())

    # Send audio to Google Cloud Speech-to-Text API
    audio = speech.RecognitionAudio(content=audio_bytes.getvalue())
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=input_lang_code,
    )

    try:
        response = client.recognize(config=config, audio=audio)
        recognized_text = response.results[0].alternatives[0].transcript
        translated_text = translator.translate(recognized_text, src=input_lang_code, dest=output_lang_code).text
        return recognized_text, translated_text
    except Exception as e:
        st.error(f"Error recognizing or translating: {str(e)}")
        return None, None


# Function to generate and play audio for the translated text
def play_audio(text, lang_code):
    tts = gTTS(text=text, lang=lang_code)
    tmp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp_audio_file.name)
    return tmp_audio_file


# Conversation interface
def show_conversation_interface():
    # Fetch languages from session state
    patient_lang_code = st.session_state.languages_selected['patient_lang_code']
    healthcare_lang_code = st.session_state.languages_selected['healthcare_lang_code']
    patient_desired_lang_code = st.session_state.languages_selected['patient_desired_lang_code']
    healthcare_desired_lang_code = st.session_state.languages_selected['healthcare_desired_lang_code']

    # Ensure conversation_started and conversation_log are initialized in session state
    if 'conversation_started' not in st.session_state:
        st.session_state.conversation_started = False
    if 'conversation_log' not in st.session_state:
        st.session_state.conversation_log = []


    # Start and End buttons
    st.markdown("<h3 style='text-align: center;'>Conversation Controls</h3>", unsafe_allow_html=True)

    # Add the Start and End Conversation buttons

    # Check if the 'conversation_started' key exists in session_state
    if 'conversation_started' not in st.session_state:
        st.session_state.conversation_started = False  # Initialize to False

    # Create a button for starting conversation
    if st.button("Start Conversation"):
        st.session_state.conversation_started = True  # Set to True when clicked

        # Check the state of the conversation and display messages
        if st.session_state.conversation_started:
            st.write("Conversation started. Press Speak to communicate.")
        else:
            st.write("Click the button to start the conversation.")

    # End Conversation button
    if st.button("End Conversation"):
        st.session_state.conversation_started = False
        st.write("Conversation ended. Download the conversation log below.")

        # If the conversation has ended, display the log and provide a download link
        if not st.session_state.conversation_started and st.session_state.conversation_log:

            conversation_log_text = "\n".join(
                [
                    f"{entry['speaker']}:\nOriginal: {entry['original_text']}\nTranslated: {entry['translated_text']}\n"
                    for entry in st.session_state.conversation_log
                ]
            )
            st.text_area("Conversation Log", value=conversation_log_text, height=300)

            # Create download button after "Download Log" is clicked
            conversation_log_file = io.StringIO(conversation_log_text)
            st.download_button(
                label="Download Conversation Log",
                data=conversation_log_file.getvalue(),
                file_name="conversation_log.txt",
                mime="text/plain"
            )
            st.session_state.conversation_log = []
            st.session_state.conversation_started = False

    # If conversation has started, show the interface
    if st.session_state.conversation_started:
        # Columns for Patient and Healthcare Provider
        col1, col2 = st.columns(2)

        with col1:
            st.header("Patient")
            if st.button("Speak - Patient"):
                st.write("Listening to Patient...")
                patient_text, patient_translated = capture_and_translate(patient_lang_code, healthcare_desired_lang_code)
                if patient_text:
                    st.write("Patient's Original Text:", patient_text)
                    st.write("Patient's Translated Text:", patient_translated)
                    st.session_state.conversation_log.append({"speaker": "Patient", "original_text": patient_text, "translated_text": patient_translated})
                    # Generate audio for the translated text
                    patient_audio = play_audio(patient_translated, healthcare_desired_lang_code)
                    st.audio(patient_audio.name)

        with col2:
            st.header("Healthcare Provider")
            if st.button("Speak - Healthcare Provider"):
                st.write("Listening to Healthcare Provider...")
                healthcare_text, healthcare_translated = capture_and_translate(healthcare_lang_code, patient_desired_lang_code)
                if healthcare_text:
                    st.write("Provider's Original Text:", healthcare_text)
                    st.write("Provider's Translated Text:", healthcare_translated)
                    st.session_state.conversation_log.append({"speaker": "Healthcare Provider", "original_text": healthcare_text, "translated_text": healthcare_translated})
                    # Generate audio for the translated text
                    healthcare_audio = play_audio(healthcare_translated, patient_desired_lang_code)
                    st.audio(healthcare_audio.name)



# Run language selection
language_selection()
if st.session_state.conversation_started:
    show_conversation_interface()