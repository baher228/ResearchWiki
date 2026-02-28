# 📚 ResearchWiki API

> Convert research papers into clean, wiki-style summary pages — powered by **Mistral AI**.

---

## 🏗 Project Structure

```
backend/
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
└── app/
    ├── main.py                   # FastAPI entry-point, CORS & routing
    ├── config.py                 # Settings (reads .env)
    ├── routers/
    │   └── papers.py             # POST /papers/summarize
    ├── services/
    │   └── mistral_service.py    # Mistral API client
    └── schemas/
        └── paper.py              # Request / Response models
```

---

## ⚡ Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file (or edit the existing one):

```env
MISTRAL_API_KEY=your_key_here
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

The API will be live at **http://localhost:8000**  
Interactive docs at **http://localhost:8000/docs**

---

## 🔌 API Endpoints

| Method | Path                | Description                              |
|--------|---------------------|------------------------------------------|
| `GET`  | `/health`           | Health check → `{"status": "ok"}`        |
| `POST` | `/papers/summarize` | Summarize a research paper into wiki format |

### `POST /papers/summarize`

**Request**
```json
{
  "text": "Full text of the research paper (min 50 chars)..."
}
```

**Response**
```json
{
  "title": "Wiki-Style Title",
  "summary": "Brief lead paragraph...",
  "sections": [
    { "title": "Background", "content": "..." },
    { "title": "Methodology", "content": "..." },
    { "title": "Key Findings", "content": "..." }
  ]
}
```

---

## 🛠 Tech Stack

- **FastAPI** — async web framework
- **Mistral AI** — LLM for paper summarization
- **Pydantic** — data validation & settings
- **Uvicorn** — ASGI server
