# EduPath

EduPath is a personalized learning and skill-gap assistant. MongoDB and Pinecone remain optional; personalized resume analysis, assessments, recommendations, and mentoring use a local Ollama model.

## Run locally

```bash
cp .env.example .env
# Install Ollama, then in another terminal:
ollama pull llama3.2
ollama serve
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# second terminal
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`. Or run both services with `docker compose up`.

## Architecture

- React + Vite + Tailwind + Zustand + React Flow frontend
- FastAPI async API with optional Motor persistence and an in-memory demo repository
- Resume text/PDF extraction, confidence-aware cumulative scoring, JSON-validated Ollama AI chains
- Single Ollama provider configured only in the FastAPI backend
- Pinecone semantic-resource lookup with curated-resource fallback

## Environment behavior

Set `OLLAMA_BASE_URL=http://localhost:11434`, `OLLAMA_MODEL=llama3.2`, and optionally `OLLAMA_TIMEOUT_SECONDS=45` in `.env`. For Docker Compose, it uses `host.docker.internal` by default; override it with `OLLAMA_DOCKER_BASE_URL` only if Ollama runs elsewhere. The React app never receives this configuration or contacts Ollama directly. The compact demo tokens are intentionally not production authentication; replace them with signed JWTs, password hashing, RBAC, storage, and virus scanning before deployment.
# edupath
