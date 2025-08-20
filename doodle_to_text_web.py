import streamlit as st
from streamlit_drawable_canvas import st_canvas
import google.generativeai as genai
from gtts import gTTS
import tempfile
import base64

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Doodle to Story", layout="wide")

st.title("🎨 Doodle → 📖 Story + 🔊 Voice")

# Configure Gemini API
import os
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Language options
lang_codes = {
    "English": "en",
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
}
language = st.selectbox("🌐 Select Language", list(lang_codes.keys()))

# ---------------- CANVAS ----------------
st.subheader("Draw your doodle here 🖌️")
canvas_result = st_canvas(
    fill_color="rgba(255, 255, 255, 0.3)",
    stroke_width=6,
    stroke_color=st.color_picker("✏️ Pick a color", "#000000"),
    background_color="#FFFFFF",
    height=400,   # bigger canvas
    width=600,
    drawing_mode="freedraw",
    key="canvas",
)

# ---------------- PROCESS ----------------
if st.button("✨ Generate Story"):
    if canvas_result.image_data is not None:
        with st.spinner("Thinking... 🧠"):
            try:
                # Convert doodle to story
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = (
                    f"You are helping a dyslexic child. "
                    f"Look at the doodle and describe it simply in {language}. "
                    f"Then make a short cheerful story idea (1–2 sentences) in {language}. "
                    f"⚠️ Important: ONLY reply in {language}, do not translate or repeat in English."
                )

                img = canvas_result.image_data
                response = model.generate_content([prompt, img])
                text_output = response.text

                st.subheader("📖 Story")
                st.success(text_output)

                # ---------------- TTS ----------------
                st.subheader("🔊 Listen")
                try:
                    tts = gTTS(text=text_output, lang=lang_codes.get(language, "en"))
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                        tts.save(tmp.name)
                        audio_file = open(tmp.name, "rb").read()
                        audio_base64 = base64.b64encode(audio_file).decode("utf-8")

                        # Autoplay audio
                        audio_html = f"""
                        <audio autoplay controls>
                            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                        </audio>
                        """
                        st.markdown(audio_html, unsafe_allow_html=True)

                        # Download button
                        st.download_button("💾 Download Story Audio", audio_file, "story.mp3")

                except Exception as e:
                    st.error(f"TTS Error: {e}")

            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("⚠️ Please draw something first!")
