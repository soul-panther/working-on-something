# doodle_to_text_web.py
import os
import io
import base64
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import google.generativeai as genai
from gtts import gTTS

# --- Page Config ---
st.set_page_config(page_title="AI Doodle-to-Text", page_icon="🎨", layout="centered")

# --- Inject CSS ---
st.markdown(
    """
    <style>
    /* Make all Streamlit text white */
    .stMarkdown, .stText, .stButton>button, .stRadio label, .stSelectbox label {
        color: white !important;
    }

    /* Fix toolbar buttons (undo, redo, delete, save) */
    button[kind="canvas_toolbar"] svg {
        fill: white !important;   /* Change to cyan: linear-gradient not supported on svg fill */
    }

    /* Optional: hover effect with cyan tint */
    button[kind="canvas_toolbar"]:hover svg {
        fill: cyan !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Title ---
st.markdown(
    "<h1 style='text-align:center;'>🎨 AI Doodle-to-Text for Children</h1>",
    unsafe_allow_html=True,
)
st.markdown("<p style='text-align:center;'>✨ Draw → Gemini describes → Listen aloud!</p>", unsafe_allow_html=True)

# --- Drawing Canvas ---
st.subheader("✏️ Draw Your Doodle Below")
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=5,
    stroke_color="#000000",
    background_color="#FFFFFF",
    update_streamlit=True,
    height=400,
    width=400,
    drawing_mode="freedraw",
    key="canvas",
)

# --- Process Button ---
if st.button("Generate Story from Doodle 🎙️"):
    if canvas_result.image_data is not None:
        img = Image.fromarray(canvas_result.image_data.astype("uint8"))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")

        # Send to Gemini (pseudo - replace with your API)
        description = "A child-like doodle detected. Imagine a fun story about it!"

        # TTS
        tts = gTTS(description)
        tts.save("story.mp3")
        audio_file = open("story.mp3", "rb")
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format="audio/mp3")

        st.success("✨ Story generated and played aloud!")
    else:
        st.warning("Please draw something first!")
