# EduPath

EduPath is a hackathon-ready personalized learning and skill-gap assistant. It runs in **demo mode** by default: no API keys, MongoDB, Pinecone, or local model are required to click through onboarding, diagnostics, the live roadmap, resource drawer, mentor chat, and admin view.

## Run locally

```bash
cp .env.example .env
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# second terminal
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`. Or run both services with `docker compose up`.

## Architecture

- React + Vite + Tailwind + Zustand + React Flow frontend
- FastAPI async API with optional Motor persistence and an in-memory demo repository
- Resume text/PDF extraction, confidence-aware adaptive scoring, JSON-safe AI chains
- Gemini multi-key round-robin with 429 rotation and Ollama fallback
- Pinecone semantic-resource lookup with curated-resource fallback

## Environment behavior

Leave credentials blank for demo mode. Configure `MONGODB_URL`, Gemini keys, Pinecone, and optionally Ollama to enable external integrations. The compact demo tokens are intentionally not production authentication; replace them with signed JWTs, password hashing, RBAC, storage, and virus scanning before deployment.
# edupath
