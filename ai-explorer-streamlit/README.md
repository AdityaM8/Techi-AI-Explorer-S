# AI Explorer — Streamlit Client

A ready-to-run **Streamlit** frontend that connects to your existing **AI Explorer API** (Next.js).

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# set API_BASE to your API (e.g., http://localhost:3000)
streamlit run streamlit_app.py --server.port ${PORT:-8501}
```
Open: http://localhost:8501
