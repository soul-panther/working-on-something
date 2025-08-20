# doodle_to_text_web.py
import streamlit as st
from PIL import Image
import google.generativeai as genai
import base64

# 🔑 Your Gemini API key
API_KEY = "AIzaSyDeI4pQxe7puD1Ron2Vmo-5iRVblAeck48"

# Configure Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="AI Doodle-to-Text", page_icon="🎨")
st.title("🎨 AI Doodle-to-Text for Children")
st.write("Upload your doodle → Gemini will describe it simply → Get a cheerful story idea ✨")

# Upload doodle
uploaded_file = st.file_uploader("Upload your doodle (PNG/JPG)", type=["png","jpg","jpeg"])

if uploaded_file:
    # Show doodle
    img = Image.open(uploaded_file).convert("RGB")
    st.image(img, caption="Your Doodle", use_column_width=True)

    # Convert to base64 for Gemini
    with open("temp.png", "wb") as f:
        f.write(uploaded_file.read())
    with open("temp.png", "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    prompt = (
        "You are helping a dyslexic child. "
        "Look at the doodle and describe it in simple words. "
        "Then make a short cheerful story idea in 1–2 sentences."
    )

    if st.button("✨ Interpret with Gemini"):
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
