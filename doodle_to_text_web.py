# doodle_to_text_web.py
import os
import io
import base64
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import google.generativeai as genai
from gtts import gTTS  # NEW
import tempfile        # NEW

# Configure Gemini with secret key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="AI Doodle-to-Text", page_icon="🎨", layout="wide")
st.title("🎨 AI Doodle-to-Text for Children")
st.write("Draw on the canvas → Gemini will describe it simply → Hear it read aloud ✨")

# Sidebar controls
st.sidebar.header("🖌️ Drawing Controls")
stroke_width = st.sidebar.slider("Pen Size", 2, 25, 6)
stroke_color = st.sidebar.color_picker("Pen Color", "#000000")
bg_color = st.sidebar.color_picker("Background Color", "#FFFFFF")
realtime_update = st.sidebar.checkbox("Update in realtime", True)

# Language selector
st.sidebar.header("🌍 Output Language")
language = st.sidebar.selectbox(
    "Choose output language:",
    ["English", "Hindi", "Spanish", "French", "German", "Chinese", "Japanese", "Arabic"]
)

# Map dropdown to gTTS language codes
lang_codes = {
    "English": "en",
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Chinese": "zh-cn",
    "Japanese": "ja",
    "Arabic": "ar",
}

# Draw canvas
canvas_result = st_canvas(
    fill_color="rgba(255, 255, 255, 1)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    width=600,
    height=500,
    drawing_mode="freedraw",
    key="canvas",
    update_streamlit=realtime_update,
)

# Process doodle
if st.button("✨ Interpret with Gemini"):
    if canvas_result.image_data is not None:
        # Convert NumPy array → Image
        img = Image.fromarray(canvas_result.image_data.astype("uint8")).convert("RGB")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        # Prompt for Gemini
        prompt = (
            f"You are helping a dyslexic child. "
            f"Look at the doodle and describe it simply in **{language}**. "
            f"Then make a short cheerful story idea (1–2 sentences) also in **{language}**."
            f"⚠️ Important: ONLY reply in {language}, do not translate or repeat in English."
        )

        try:
            response = model.generate_content([
                {"role": "user", "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": img_b64}}
                ]}
            ])
            text_output = response.text.strip()

            st.subheader(f"📝 Gemini’s Interpretation ({language})")
            st.success(text_output)

            # 🔊 Text-to-Speech
            st.subheader("🔊 Listen")
            try:
                tts = gTTS(text=text_output, lang=lang_codes.get(language, "en"))
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tts.save(tmp.name)
                audio_file = open(tmp.name, "rb").read()
                audio_base64 = base64.b64encode(audio_file).decode("utf-8")

            # Use autoplay audio player
            audio_html = f"""
            <audio autoplay controls>
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
            """
                st.markdown(audio_html, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"TTS Error: {e}")


        except Exception as e:
            st.error(f"Gemini Error: {e}")
    else:
        st.warning("Please draw something first!")

