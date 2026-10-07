import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Dono providers OpenAI-compatible API dete hain, isliye ek hi SDK chalta hai.
PROVIDERS = {
    "Groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "model_env": "GROQ_MODEL",
        "default_model": "llama-3.3-70b-versatile",
    },
    "Gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL",
        "default_model": "gemini-2.5-flash",
    },
}

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful AI assistant. Reply in the same language the user writes in "
    "(Hindi, English or Hinglish). Keep answers clear and concise."
)

st.set_page_config(page_title="My AI Assistant", page_icon="🤖")
st.title("🤖 My AI Assistant")

with st.sidebar:
    st.header("Settings")
    provider_name = st.selectbox("Provider", list(PROVIDERS.keys()))
    cfg = PROVIDERS[provider_name]
    model = st.text_input("Model", os.getenv(cfg["model_env"], cfg["default_model"]))
    system_prompt = st.text_area("System prompt", DEFAULT_SYSTEM_PROMPT, height=120)
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

api_key = os.getenv(cfg["key_env"])
if not api_key:
    try:
        api_key = st.secrets.get(cfg["key_env"])
    except Exception:
        api_key = None
if not api_key:
    st.warning(f"`{cfg['key_env']}` set nahi hai. `.env` file me apni free API key daalo.")
    st.stop()

client = OpenAI(api_key=api_key, base_url=cfg["base_url"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])


def stream_reply():
    messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
    stream = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature, stream=True
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


if prompt := st.chat_input("Kuch bhi poocho..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(stream_reply())
            st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            msg = str(e)
            if "429" in msg:
                st.error("Free limit khatam ho gayi (429). Thodi der baad try karo ya doosra provider chuno.")
            else:
                st.error(f"Error: {msg}")
