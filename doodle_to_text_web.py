# doodle_to_text_web.py
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import google.generativeai as genai
import base64
import io

# 🔑 Gemini API Key
import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="AI Doodle-to-Text", page_icon="🎨")
st.title("🎨 AI Doodle-to-Text for Children")
st.write("Draw below → Gemini will describe it → Get a cheerful story idea ✨")

# Canvas settings
canvas_result = st_canvas(
    fill_color="rgba(255, 255, 255, 1)",  # white background
    stroke_width=6,
    stroke_color="black",
    background_color="white",
    width=400,
    height=400,
    drawing_mode="freedraw",
    key="canvas",
)

if st.button("✨ Interpret with Gemini"):
    if canvas_result.image_data is not None:
        # Convert NumPy image array → PNG
        img = Image.fromarray((canvas_result.image_data).astype("uint8")).convert("RGB")

        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

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


