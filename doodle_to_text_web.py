# doodle_to_text_web.py
import os
import io
import base64
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import google.generativeai as genai

# Configure Gemini with secret key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="AI Doodle-to-Text", page_icon="🎨", layout="wide")
st.title("🎨 AI Doodle-to-Text for Children")
st.write("Draw on the canvas → Gemini will describe it simply → Get a cheerful story idea ✨")

# Sidebar controls
st.sidebar.header("🖌️ Drawing Controls")
stroke_width = st.sidebar.slider("Pen Size", 2, 25, 6)
stroke_color = st.sidebar.color_picker("Pen Color", "#000000")
bg_color = st.sidebar.color_picker("Background Color", "#FFFFFF")
realtime_update = st.sidebar.checkbox("Update in realtime", True)

# Draw canvas
canvas_result = st_canvas(
    fill_color="rgba(255, 255, 255, 1)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    width=600,   # bigger canvas
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
            "You are helping a dyslexic child. "
            "Look at the doodle and describe it simply. "
            "Then make a short cheerful story idea in 1–2 sentences."
        )

        try:
            response = model.generate_content([
                {"role": "user", "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": img_b64}}
                ]}
            ])
            st.subheader("📝 Gemini’s Interpretation")
            st.success(response.text.strip())
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please draw something first!")
