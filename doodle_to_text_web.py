"""
Streamlit app with a custom white toolbar for the drawable canvas
- Removes the big "Clear image" button (per request)
- Hides the component's built‑in toolbar and replaces it with white icon buttons (Undo/Redo/Delete/Download)
- Keeps the rest of the app from the fixed version
- Adds simple undo/redo history on our side
Note: streamlit-drawable-canvas' toolbar icons aren't themeable from the app; it renders in an iframe and does not expose color props.
"""

from __future__ import annotations

import os
import io
import tempfile
import json
from typing import Tuple

import streamlit as st
from PIL import Image, ImageChops
from streamlit_drawable_canvas import st_canvas
import google.generativeai as genai
from gtts import gTTS

# ──────────────────────────────────────────────────────────────────────────────
# Config & helpers
# ──────────────────────────────────────────────────────────────────────────────

def _get_api_key() -> str | None:
    try:
        key = st.secrets.get("GEMINI_API_KEY")  # type: ignore[attr-defined]
    except Exception:
        key = None
    return key or os.getenv("GEMINI_API_KEY")


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(ch * 2 for ch in hex_color)
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _is_blank(img: Image.Image, bg_hex: str) -> bool:
    bg = Image.new("RGB", img.size, _hex_to_rgb(bg_hex))
    diff = ImageChops.difference(img.convert("RGB"), bg)
    return diff.getbbox() is None


LANG_CODES = {
    "English": "en",
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Chinese": "zh-cn",
    "Japanese": "ja",
    "Arabic": "ar",
}

API_KEY = _get_api_key()
if not API_KEY:
    st.set_page_config(page_title="AI Doodle‑to‑Text", page_icon="🖌️", layout="wide")
    st.error("GEMINI_API_KEY not found. Add it to Streamlit secrets or your environment.")
    st.stop()

genai.configure(api_key=API_KEY)
MODEL_NAME = st.secrets.get("GEMINI_MODEL", "gemini-1.5-flash") if hasattr(st, "secrets") else "gemini-1.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

st.set_page_config(page_title="AI Doodle‑to‑Text", page_icon="🖌️", layout="wide")

# Minimal CSS and white icon buttons
st.markdown(
    """
    <style>
    .block-container{max-width:900px;margin:auto;text-align:center}
    html,body,[class*="css"]{background:#0e1117;color:#fff}
    h1{font-size:2.8rem;margin-bottom:0.2rem}
    div.stButton > button{background:linear-gradient(90deg,#2563eb,#14b8a6);color:#fff;border-radius:12px;padding:0.6rem 1.2rem;font-weight:600;border:none}
    div.stButton > button:hover{transform:scale(1.04)}

    /* Compact white toolbar buttons */
    .white-tool button{background:rgba(255,255,255,0.12) !important;color:#fff !important;border-radius:10px !important;padding:6px 10px !important;font-size:1.1rem}
    .white-tool button:hover{background:rgba(255,255,255,0.2) !important}
    .white-tool{display:flex;gap:.5rem;justify-content:flex-end;margin:.25rem 0 .5rem}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <h1>AI Doodle‑to‑Text</h1>
    <p style='text-align:center;font-size:1.2rem;color:#e2e8f0;margin-bottom:30px;'>
      Transform your drawings into simple descriptions and short stories
    </p>
    """,
    unsafe_allow_html=True,
)

# Sidebar controls
st.sidebar.header("Drawing Controls")
stroke_width = st.sidebar.slider("Pen Size", 2, 25, 6)
stroke_color = st.sidebar.color_picker("Pen Color", "#000000")
bg_color = st.sidebar.color_picker("Background Color", "#FFFFFF")
realtime_update = st.sidebar.checkbox("Update in realtime", True)

st.sidebar.header("Output Language")
language = st.sidebar.selectbox("Choose output language:", list(LANG_CODES.keys()))

# Draw or Upload
st.markdown("<h3 style='text-align:center;margin-top:20px;'>Draw a doodle or upload an image</h3>", unsafe_allow_html=True)

col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
with col_r2:
    upload_option = st.radio(
        "Choose Input Method:",
        ["Draw on Canvas", "Upload Image"],
        horizontal=True,
        label_visibility="collapsed",
        key="input_method",
    )

# State
img = st.session_state.get("img")
CANVAS_SIZE = 600

# ── Custom white toolbar (undo/redo/delete/download) state
st.session_state.setdefault("_history", [])
st.session_state.setdefault("_redo", [])
st.session_state.setdefault("_initial_drawing", None)

if upload_option == "Draw on Canvas":
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        # White toolbar row (icons only)
        tool = st.container()
        with tool:
            cols = st.columns([1,1,1,1,6])
            with cols[0]:
                undo_click = st.button("↶", help="Undo", key="undo_btn", use_container_width=True)
            with cols[1]:
                redo_click = st.button("↷", help="Redo", key="redo_btn", use_container_width=True)
            with cols[2]:
                del_click = st.button("🗑", help="Delete", key="del_btn", use_container_width=True)
            with cols[3]:
                dl_ph = st.empty()
        tool_html = "<div class='white-tool'></div>"
        st.markdown(tool_html, unsafe_allow_html=True)

        # Handle toolbar actions (set initial drawing accordingly)
        if undo_click and st.session_state["_history"]:
            st.session_state["_redo"].append(st.session_state["_history"].pop())
            st.session_state["_initial_drawing"] = st.session_state["_history"][-1] if st.session_state["_history"] else {"objects": []}
        if redo_click and st.session_state["_redo"]:
            st.session_state["_history"].append(st.session_state["_redo"].pop())
            st.session_state["_initial_drawing"] = st.session_state["_history"][-1]
        if del_click:
            st.session_state["_history"].append({"objects": []})
            st.session_state["_redo"].clear()
            st.session_state["_initial_drawing"] = {"objects": []}

        # Canvas with toolbar hidden; we control via initial_drawing from history
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 1)",
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_color=bg_color,
            width=CANVAS_SIZE,
            height=CANVAS_SIZE,
            drawing_mode="freedraw",
            key="canvas",
            update_streamlit=realtime_update,
            display_toolbar=False,
            initial_drawing=st.session_state.get("_initial_drawing"),
        )

        # Update image + history
        if canvas_result.image_data is not None:
            fresh_img = Image.fromarray(canvas_result.image_data.astype("uint8")).convert("RGB")
            if not _is_blank(fresh_img, bg_color):
                st.session_state["img"] = fresh_img
                img = fresh_img

        if canvas_result.json_data is not None:
            jd = canvas_result.json_data
            # dedupe consecutive states
            jd_str = json.dumps(jd, sort_keys=True)
            hist = st.session_state["_history"]
            last_str = json.dumps(hist[-1], sort_keys=True) if hist else None
            if jd_str != last_str:
                st.session_state["_history"].append(jd)
                st.session_state["_redo"].clear()

        # Download current PNG
        if canvas_result.image_data is not None:
            buf = io.BytesIO()
            Image.fromarray(canvas_result.image_data.astype("uint8")).save(buf, format="PNG")
            dl_ph.download_button("⬇️", buf.getvalue(), file_name="doodle.png", help="Download PNG")
else:
    uploaded_file = st.file_uploader("Upload a drawing (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"]) 
    if uploaded_file is not None:
        try:
            up_img = Image.open(uploaded_file).convert("RGB")
            st.image(up_img, caption="Uploaded Image", use_container_width=True)
            st.session_state["img"] = up_img
            img = up_img
        except Exception as e:
            st.error(f"Could not open image: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# Generate Interpretation (unchanged)
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("""<h2 style='text-align:center;color:white;margin-top:40px;'>Generate Interpretation</h2>""", unsafe_allow_html=True)
colA, colB, colC = st.columns([1, 2, 1])
with colB:
    interpret = st.button("Interpret with Gemini", use_container_width=True)

if interpret:
    if img is None:
        st.warning("Please draw something or upload an image first!")
    else:
        prompt = (
            f"You are helping a child. "
            f"Look at the doodle and describe it simply in {language}. "
            f"Then write a short cheerful story idea (1–2 sentences) also in {language}."
        )
        try:
            with st.spinner("Interpreting your doodle…"):
                response = model.generate_content([prompt, img], request_options={"timeout": 60})
            text_output = (response.text or "").strip() if response else ""
            if not text_output:
                st.warning("No text returned by the model.")
            else:
                st.subheader(f"Gemini’s Interpretation ({language})")
                st.write(text_output)

                st.subheader("Listen")
                lang_code = LANG_CODES.get(language, "en")
                try:
                    tts = gTTS(text=text_output, lang=lang_code)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                        tts.save(tmp.name)
                        st.audio(tmp.name, format="audio/mp3")
                except Exception as e:
                    st.error(f"TTS error: {e}")
        except Exception as e:
            st.error(f"Gemini error: {e}")
