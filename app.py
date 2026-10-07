import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from rag import build_index

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

    st.divider()
    st.subheader("📄 Documents")
    uploads = st.file_uploader("PDF / TXT / MD upload karo", type=["pdf", "txt", "md"], accept_multiple_files=True)
    use_docs = st.toggle("Documents se jawab do", value=True, disabled=not uploads)

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

# Documents ka index sirf tab dobara banta hai jab files badlein.
index = None
if uploads:
    sig = tuple((f.name, f.size) for f in uploads)
    if st.session_state.get("index_sig") != sig:
        with st.spinner("Documents padh raha hu..."):
            st.session_state.index = build_index([(f.name, f.getvalue()) for f in uploads])
        st.session_state.index_sig = sig
    index = st.session_state.get("index")
    if index is None:
        st.sidebar.warning("Files se text nahi mila (scanned PDF ho sakti hai).")
else:
    st.session_state.pop("index", None)
    st.session_state.pop("index_sig", None)

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
        if m.get("sources"):
            with st.expander("Sources"):
                for s in m["sources"]:
                    st.caption(f"**{s[0]}** — {s[1][:300]}...")


def stream_reply(hits):
    system = system_prompt
    if hits:
        context = "\n\n".join(f"[{src}]\n{text}" for src, text, _ in hits)
        system += (
            "\n\nUse the document excerpts below to answer. If the answer is not in them, "
            "say so clearly instead of guessing.\n\n" + context
        )
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}] + history,
        temperature=temperature,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


if prompt := st.chat_input("Kuch bhi poocho..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    hits = index.search(prompt) if (index and use_docs) else []

    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(stream_reply(hits))
            entry = {"role": "assistant", "content": reply}
            if hits:
                entry["sources"] = [(s, t) for s, t, _ in hits]
                with st.expander("Sources"):
                    for s, t, _ in hits:
                        st.caption(f"**{s}** — {t[:300]}...")
            st.session_state.messages.append(entry)
        except Exception as e:
            st.session_state.messages.pop()  # fail hua user message hata do
            if "429" in str(e):
                st.error("Free limit khatam ho gayi (429). Thodi der baad try karo ya doosra provider chuno.")
            else:
                st.error(f"Error: {e}")
