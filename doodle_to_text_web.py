# doodle_to_text_web.py
import os
import io
import base64
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import google.generativeai as genai
from gtts import gTTS
import tempfile

# 🔑 Configure Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# 🎨 Streamlit page setup
st.set_page_config(page_title="AI Doodle-to-Text", page_icon="🎨", layout="wide")

# 🌟 Custom CSS for centering + styling
st.markdown(
    """
    <style>
    /* Center container */
    .block-container {
        max-width: 900px;
        margin: auto;
        text-align: center;
    }

    /* Title */
    h1 {
        text-align: center;
        color: #4A90E2;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    /* Subtitle */
    .stMarkdown {
        font-size: 1.1rem;
        color: #444;
    }

    /* Button styling */
    div.stButton > button {
        background: linear-gradient(90deg, #4A90E2, #50E3C2);
        color: white;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        font-size: 1.1rem;
        font-weight: bold;
        border: none;
        cursor: pointer;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        transform: scale(1.05);
        background: linear-gradient(90deg, #50E3C2, #4A90E2);
    }

    /* Center audio */
    audio {
        margin: 10px auto;
        display: block;
    }

    /* Light pastel background */
    body {
        background: linear-gradient(135deg, #f9f9f9, #e6f7ff);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 🏷️ Title & description
st.title("🎨 AI Doodle-to-Text for Children")
st.write("✨ Draw → Gemini describes → Listen to the story aloud!")

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
    ["English", "Hindi", "Spanish", "French", "German", "Chinese", "Japanese", "Arabic"],
)

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

# ✏️ Draw canvas (centered)
st.markdown("### ✏️ Draw Your Doodle Below")
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
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

# 🚀 Interpretation heading (centered & styled)
st.markdown(
    """
    <h2 style='text-align: center; color: #4A90E2; margin-top: 40px;'>
        🚀 Generate Interpretation
    </h2>
    """,
    unsafe_allow_html=True,
)

# Center the button under heading
colA, colB, colC = st.columns([1, 2, 1])
with colB:
    interpret = st.button("✨ Interpret with Gemini", use_container_width=True)

# If button clicked
if interpret:
    if canvas_result.image_data is not None:
        img = Image.fromarray(canvas_result.image_data.astype("uint8")).convert("RGB")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        prompt = (
            f"You are helping a dyslexic child. "
            f"Look at the doodle and describe it simply in **{language}**. "
            f"Then make a short cheerful story idea (1–2 sentences) also in **{language}**."
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
                    st.audio(tmp.name, format="audio/mp3")
            except Exception as e:
                st.error(f"TTS Error: {e}")

        except Exception as e:
            st.error(f"Gemini Error: {e}")
    else:
        st.warning("Please draw something first!")
