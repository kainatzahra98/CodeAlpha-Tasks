import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import os
import base64

# Configure the Streamlit page
st.set_page_config(page_title="LingoBridge Translator", page_icon="🌍")

# List of supported languages by deep-translator
# GoogleTranslator().get_supported_languages(as_dict=True)
SUPPORTED_LANGUAGES = {
    'afrikaans': 'af', 'albanian': 'sq', 'amharic': 'am', 'arabic': 'ar', 'armenian': 'hy', 
    'azerbaijani': 'az', 'basque': 'eu', 'belarusian': 'be', 'bengali': 'bn', 'bosnian': 'bs', 
    'bulgarian': 'bg', 'catalan': 'ca', 'cebuano': 'ceb', 'chichewa': 'ny', 'chinese (simplified)': 'zh-CN', 
    'chinese (traditional)': 'zh-TW', 'corsican': 'co', 'croatian': 'hr', 'czech': 'cs', 'danish': 'da', 
    'dutch': 'nl', 'english': 'en', 'esperanto': 'eo', 'estonian': 'et', 'filipino': 'tl', 'finnish': 'fi', 
    'french': 'fr', 'frisian': 'fy', 'galician': 'gl', 'georgian': 'ka', 'german': 'de', 'greek': 'el', 
    'gujarati': 'gu', 'haitian creole': 'ht', 'hausa': 'ha', 'hawaiian': 'haw', 'hebrew': 'iw', 'hindi': 'hi', 
    'hmong': 'hmn', 'hungarian': 'hu', 'icelandic': 'is', 'igbo': 'ig', 'indonesian': 'id', 'irish': 'ga', 
    'italian': 'it', 'japanese': 'ja', 'javanese': 'jw', 'kannada': 'kn', 'kazakh': 'kk', 'khmer': 'km', 
    'kinyarwanda': 'rw', 'korean': 'ko', 'kurdish (kurmanji)': 'ku', 'kyrgyz': 'ky', 'lao': 'lo', 'latin': 'la', 
    'latvian': 'lv', 'lithuanian': 'lt', 'luxembourgish': 'lb', 'macedonian': 'mk', 'malagasy': 'mg', 
    'malay': 'ms', 'malayalam': 'ml', 'maltese': 'mt', 'maori': 'mi', 'marathi': 'mr', 'mongolian': 'mn', 
    'myanmar (burmese)': 'my', 'nepali': 'ne', 'norwegian': 'no', 'odia (oriya)': 'or', 'pashto': 'ps', 
    'persian': 'fa', 'polish': 'pl', 'portuguese': 'pt', 'punjabi': 'pa', 'romanian': 'ro', 'russian': 'ru', 
    'samoan': 'sm', 'scots gaelic': 'gd', 'serbian': 'sr', 'sesotho': 'st', 'shona': 'sn', 'sindhi': 'sd', 
    'sinhala': 'si', 'slovak': 'sk', 'slovenian': 'sl', 'somali': 'so', 'spanish': 'es', 'sundanese': 'su', 
    'swahili': 'sw', 'swedish': 'sv', 'tajik': 'tg', 'tamil': 'ta', 'tatar': 'tt', 'telugu': 'te', 'thai': 'th', 
    'turkish': 'tr', 'turkmen': 'tk', 'ukrainian': 'uk', 'urdu': 'ur', 'uyghur': 'ug', 'uzbek': 'uz', 
    'vietnamese': 'vi', 'welsh': 'cy', 'xhosa': 'xh', 'yiddish': 'yi', 'yoruba': 'yo', 'zulu': 'zu'
}

# Function to get the audio file as base64 and create a styled audio player
def get_audio_player(text, lang_code):
    try:
        tts = gTTS(text=text, lang=lang_code)
        tts.save("temp_audio.mp3")
        
        with open("temp_audio.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio controls>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                Your browser does not support the audio element.
                </audio>
                """
            st.markdown(md, unsafe_allow_html=True)
            
        # Clean up
        os.remove("temp_audio.mp3")
    except Exception as e:
        st.error(f"Could not generate audio for this language. ({e})")

st.title("🌉 LingoBridge Translator")
st.markdown("Translate text between multiple languages instantly!")

# Layout
col1, col2 = st.columns(2)

with col1:
    source_lang_name = st.selectbox("Source Language", list(SUPPORTED_LANGUAGES.keys()), index=list(SUPPORTED_LANGUAGES.keys()).index('english'))
    source_text = st.text_area("Enter text to translate:", height=200, placeholder="Hello, how are you?")

with col2:
    target_lang_name = st.selectbox("Target Language", list(SUPPORTED_LANGUAGES.keys()), index=list(SUPPORTED_LANGUAGES.keys()).index('spanish'))
    st.markdown("Translated text will appear below:")

# Button to translate
if st.button("Translate", type="primary"):
    if source_text.strip():
        source_code = SUPPORTED_LANGUAGES[source_lang_name]
        target_code = SUPPORTED_LANGUAGES[target_lang_name]
        
        try:
            with st.spinner("Translating..."):
                translator = GoogleTranslator(source=source_code, target=target_code)
                translated_text = translator.translate(source_text)
                
            with col2:
                # Display translated text nicely
                st.success(translated_text)
                
                # Copy button feature using st.code
                st.markdown("**Copy Result:**")
                st.code(translated_text, language=None)
                
                # Text to Speech feature
                st.markdown("**🔊 Listen to Translation:**")
                get_audio_player(translated_text, target_code)
                
        except Exception as e:
            st.error(f"An error occurred during translation: {e}")
    else:
        st.warning("Please enter some text to translate.")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit & deep-translator")
