# EduPath

EduPath is a personalized learning and skill-gap assistant. Upload a resume, pick a career target, and get an AI-generated skill assessment, an interactive learning roadmap, curated resources, and an AI mentor to chat with along the way.

Personalized resume analysis, assessments, recommendations, and mentoring run on a **local Ollama model** — no external AI API key required. MongoDB and Pinecone are optional add-ons for persistence and semantic resource search; the app runs fully in-memory without them.

## Features

- **Resume parsing** — upload a PDF or TXT resume; skills, technologies, projects, and experience are extracted automatically
- **AI skill assessment** — a local Ollama model analyzes the resume against a chosen career target and scores skill confidence
- **Diagnostic quiz** — AI-generated quiz questions to validate and refine the skill profile
- **Interactive roadmaps** — skill-gap roadmaps rendered as a node graph (via React Flow) for 29 career tracks (frontend, backend, full-stack, data engineer, ML, DevOps, cybersecurity, product management, and more)
- **Resource recommendations** — Pinecone-backed semantic search over learning resources, with a curated fallback when Pinecone isn't configured
- **AI mentor chat** — ask questions and get contextual guidance based on your profile and roadmap
- **Admin dashboard** — overview stats and user table for admins

## Architecture

| Layer | Stack |
|---|---|
| Frontend | React 18 + Vite + Tailwind CSS + Zustand + React Router + React Flow (`@xyflow/react`) |
| Backend | FastAPI (async) with Pydantic v2 |
| AI | Local Ollama model, JSON-validated chains for resume analysis, quiz generation, roadmap generation, and mentoring |
| Persistence | Optional MongoDB (via Motor); falls back to an in-memory demo repository |
| Semantic search | Optional Pinecone; falls back to curated static resources |

The React app never talks to Ollama or the database directly — all of that is handled by the FastAPI backend behind a REST API.

## Prerequisites

- [Ollama](https://ollama.com) installed locally, with a pulled model (default: `llama3.2`)
- Python 3.12+
- Node.js 20+
- (Optional) MongoDB instance and connection string
- (Optional) Pinecone API key and index

## Getting started

```bash
cp .env.example .env

# Install Ollama, then in another terminal:
ollama pull llama3.2
ollama serve

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (in a second terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The API runs at `http://localhost:8000` (docs at `http://localhost:8000/docs`).

### Or with Docker Compose

```bash
cp .env.example .env
docker compose up
```

This starts the FastAPI backend on `:8000` and the Vite dev server on `:5173`.

## Configuration

All configuration lives in `.env` (see `.env.example`):

| Variable | Description | Default |
|---|---|---|
| `MONGODB_URL` | MongoDB connection string. Leave blank to run in in-memory demo mode. | *(empty)* |
| `MONGODB_DB` | Database name | `edupath` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model to use | `llama3.2` |
| `OLLAMA_TIMEOUT_SECONDS` | Request timeout for AI calls | `45` |
| `OLLAMA_DOCKER_BASE_URL` | Overrides the Ollama URL *only* inside Docker Compose (defaults to `host.docker.internal`) | *(empty)* |
| `PINECONE_API_KEY` | Enables semantic resource search when set | *(empty)* |
| `PINECONE_INDEX` | Pinecone index name | *(empty)* |
| `JWT_SECRET` | Secret used to sign demo auth tokens | `change-this-for-production` |
| `VITE_API_URL` | API base URL used by the frontend | `http://localhost:8000/api` |

> **Note on auth:** the built-in tokens are compact demo tokens, not production-grade authentication. Replace them with signed JWTs, password hashing, RBAC, secure storage, and file virus scanning before deploying this anywhere real.

## API overview

All routes are served under `/api`. Interactive docs are available at `/docs` once the backend is running.

| Area | Endpoints |
|---|---|
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/profile/{user_id}` |
| Resume | `POST /api/resume/parse` |
| Assessment | `POST /api/assessment/generate`, `POST /api/assessment/submit` |
| Roadmaps | `GET /api/roadmaps`, `GET /api/roadmaps/{slug}`, `GET /api/roadmap/{slug}`, `POST /api/roadmap/generate`, `GET /api/roadmap/user/{user_id}`, `POST /api/roadmap/resources` |
| Mentor chat | `POST /api/chat` |
| Admin | `GET /api/admin/overview` |
| Health | `GET /health` |

## Project structure

```
Edu-Path/
├── backend/
│   ├── app/
│   │   ├── ai/            # Ollama client, prompt chains (resume, quiz, roadmap, mentor), Pinecone client
│   │   ├── config/        # Settings (env-driven)
│   │   ├── data/          # Static roadmap JSON for 29 career tracks + role metadata
│   │   ├── database/      # MongoDB client + in-memory fallback store
│   │   ├── routers/       # auth, assessment, roadmap, chat, admin
│   │   ├── schemas/       # Pydantic request/response models
│   │   ├── services/      # Resume parsing, scoring, roadmap ingestion
│   │   ├── utils/         # File parsing, security helpers
│   │   └── main.py        # FastAPI app, CORS, lifespan, resume upload endpoint
│   ├── scripts/           # Roadmap ingestion/validation scripts
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # admin, assessment, chatbot, layout, roadmap components
│   │   ├── pages/         # admin, assessment, auth, onboarding, user pages
│   │   ├── routes/        # App routes + protected route wrapper
│   │   ├── services/      # Axios API clients
│   │   └── store/         # Zustand stores (auth, roadmap)
│   └── package.json
├── docker-compose.yml
└── .env.example
```

## Available career roadmaps

`frontend`, `backend`, `full-stack`, `android`, `ios`, `game-developer`, `server-side-game-developer`, `data-analyst`, `data-engineer`, `ai-data-scientist`, `ai-engineer`, `machine-learning`, `mlops`, `bi-analyst`, `devops`, `devsecops`, `cyber-security`, `network-engineer`, `postgresql-dba`, `blockchain`, `software-architect`, `engineering-manager`, `product-manager`, `product-design`, `ux-design`, `qa`, `technical-writer`, `devrel`, `forward-deployed-engineer`

## Scripts

- `backend/scripts/ingest_roadmaps.py` — loads roadmap JSON into the database/vector index
- `backend/scripts/validate_roadmaps.py` — validates roadmap JSON structure
- `backend/test_e2e_ollama.py` — end-to-end smoke test against a running Ollama instance

## License

No license has been specified for this repository yet.
