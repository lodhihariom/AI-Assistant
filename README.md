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

## Features
- Streaming chat, Groq / Gemini switch, editable system prompt
- **Document Q&A:** sidebar se PDF/TXT/MD upload karo, assistant unme se dhundh kar jawab deta hai aur sources dikhata hai (free, local TF-IDF search, koi extra API nahi)

## Oracle knowledge (OIC / Fusion / PL/SQL)
- `knowledge/` me original cheat sheets hain (OIC, Oracle Fusion integrations, PL/SQL). App inhe automatically load karta hai, aur sidebar me **Oracle expert mode** on/off hota hai.
- Aur knowledge add karne ke liye (apni machine par):
  ```bash
  python ingest.py urls                                   # sources.txt ke official docs -> knowledge_cache/web/
  python ingest.py github oracle/cloud-asset-fusion-serverless-vbcs-sample   # kisi repo ke samples -> knowledge_cache/github/
  ```
  `knowledge_cache/` GitHub par push nahi hota (Oracle docs copyrighted hain). robots.txt maana jata hai. Sirf wahi sources add karo jinki licence/terms allow karein.
- Apni notes bhi `knowledge/` me `.md` file ki tarah daal sakte ho.

## Notes
- Document search keyword-based hai, isliye sawal usi language/shabdon me poocho jo document me hain. Scanned (image) PDF ka text nahi padha jayega.
- Free tiers ki limits badalti rehti hain. 429 error aaye to wait karo ya doosra provider chuno.
- Model naam deprecate ho sakta hai. Sidebar me ya `.env` me badal sakte ho.
- Deploy: Streamlit Community Cloud par repo connect karke keys `Secrets` me daalo.
