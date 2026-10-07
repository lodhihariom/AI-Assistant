# My AI Assistant

Streamlit chatbot jo free APIs (Groq / Google Gemini) use karta hai. Hindi, English aur Hinglish me chalta hai.

## Setup

1. Free API key lo:
   - Groq: https://console.groq.com
   - Gemini: https://aistudio.google.com
2. Install:
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env             # phir .env me key daalo
   ```
3. Run:
   ```bash
   streamlit run app.py
   ```

## Notes
- Free tiers ki limits badalti rehti hain. 429 error aaye to wait karo ya doosra provider chuno.
- Model naam deprecate ho sakta hai. Sidebar me ya `.env` me badal sakte ho.
- Deploy: Streamlit Community Cloud par repo connect karke keys `Secrets` me daalo.
