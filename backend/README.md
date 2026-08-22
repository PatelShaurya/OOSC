# CivicAI - Backend Orchestration Layer

CivicAI is an AI-powered legal and civic empowerment platform designed to assist citizens with legal queries, guided civic form filings (RTI, Consumer Complaints, Municipal Grievances), and formal complaint/document generation.

This repository contains the **FastAPI Backend Application** that acts as the orchestration and business logic layer between the frontend client and the external RAG/AI microservice.

---

## 🏛️ System Architecture

```
┌─────────────────┐       HTTP / REST       ┌──────────────────────┐       HTTP / Async      ┌─────────────────┐
│                 │ ──────────────────────> │                      │ ──────────────────────> │                 │
│ Frontend Client │                         │ CivicAI FastAPI App  │                         │ RAG / AI Engine │
│ (Web / Mobile)  │ <────────────────────── │ (Orchestration Layer)│ <────────────────────── │  (Microservice) │
└─────────────────┘       JSON Responses    └──────────┬───────────┘       Citations & Drafts└─────────────────┘
                                                       │
                                                       │ PostgreSQL & Auth
                                                       ▼
                                            ┌──────────────────────┐
                                            │       Supabase       │
                                            │ (Auth & PostgreSQL)  │
                                            └──────────────────────┘
```

### Separation of Concerns
- **Backend Responsibilities**: REST APIs, authentication verification, user session management, conversation history, multi-step civic form sessions, legal complaint workflows, request/response validation, error handling, logging, and database operations.
- **RAG/AI Microservice**: Vector search, embeddings, PDF ingestion, chunking, reranking, and legal document generation models. Communication with the RAG microservice is strictly isolated within [`app/integrations/rag_client.py`](file:///d:/OOSC/backend/app/integrations/rag_client.py).

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py                     # FastAPI entry point, middleware, exception handlers
│   ├── config.py                   # Pydantic Settings & env configuration
│   ├── api/
│   │   ├── deps.py                 # Dependency injection (Auth, Services, Repositories)
│   │   └── v1/
│   │       ├── api.py              # Master v1 router
│   │       ├── health.py           # Health checks & readiness probes
│   │       ├── auth.py             # User profile endpoints
│   │       ├── conversations.py    # Legal advice chat & message threads
│   │       ├── form_sessions.py    # Guided multi-step form workflows
│   │       └── complaints.py       # Formal legal complaint drafting & export
│   ├── services/
│   │   ├── conversation_service.py # Orchestrates chat & statutory citations
│   │   ├── form_service.py         # Multi-step civic form validation & guidance
│   │   ├── complaint_service.py    # Complaint lifecycle & document drafting
│   │   └── user_service.py         # User profile management
│   ├── integrations/
│   │   └── rag_client.py           # Isolated async HTTP client for RAG microservice
│   ├── auth/
│   │   └── dependencies.py         # Supabase JWT token verification
│   ├── schemas/
│   │   ├── common.py               # Standard APIResponse[T], pagination, error models
│   │   ├── auth.py                 # User profile schemas
│   │   ├── conversation.py         # Messages & conversation schemas
│   │   ├── form_session.py         # Multi-step form session schemas
│   │   ├── complaint.py            # Complaint & generated document schemas
│   │   └── rag.py                  # RAG request/response contracts
│   ├── database/
│   │   ├── supabase_client.py      # Supabase connection manager
│   │   └── repositories/
│   │       ├── base.py             # Base repository interface
│   │       ├── user_repo.py        # User profile repository
│   │       ├── conversation_repo.py# Conversation & message repository
│   │       ├── form_session_repo.py# Form session repository
│   │       └── complaint_repo.py   # Complaints repository
│   └── utils/
│       ├── logger.py               # Structured logging
│       └── exceptions.py           # Custom application exceptions
├── database/
│   └── supabase_schema.sql         # Supabase PostgreSQL DDL, indexes, and RLS policies
├── tests/
│   ├── conftest.py                 # Pytest fixtures & test client
│   ├── test_health.py              # Health check tests
│   ├── test_auth.py                # Authentication tests
│   ├── test_conversations.py       # Chat & message flow tests
│   ├── test_form_sessions.py       # Guided form session tests
│   ├── test_complaints.py          # Complaint & drafting tests
│   └── test_rag_client.py          # RAG client integration tests
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.12+
- Supabase project (optional for local mock mode)

### 2. Setup Virtual Environment
```bash
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your Supabase and RAG service credentials:
```bash
cp .env.example .env
```

| Key | Description | Default |
|-----|-------------|---------|
| `PROJECT_NAME` | Name of the FastAPI project | `CivicAI Backend` |
| `ENVIRONMENT` | Runtime environment (`development`, `production`, `test`) | `development` |
| `DEBUG` | Enable debug logs & reload | `true` |
| `API_V1_STR` | API prefix | `/api/v1` |
| `SUPABASE_URL` | Supabase project URL | `https://your-project.supabase.co` |
| `SUPABASE_KEY` | Supabase Anon or Service Role key | `your-key` |
| `SUPABASE_JWT_SECRET` | Secret key used to decode Supabase JWTs | `your-jwt-secret` |
| `RAG_SERVICE_URL` | Base URL of the RAG/AI microservice | `http://localhost:8001` |
| `RAG_TIMEOUT_SECONDS` | Timeout for RAG queries | `45.0` |

---

## 🏃 Running the Application

### Start Development Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API Base URL**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 🧪 Running Automated Tests

Run the full pytest test suite with:
```bash
pytest tests/ -v
```

---

## 🗄️ Database Setup (Supabase)

To initialize the PostgreSQL database schema, tables, indexes, and Row Level Security (RLS) policies:
1. Open your [Supabase Dashboard](https://supabase.com/dashboard).
2. Navigate to the **SQL Editor**.
3. Copy and run the entire contents of [`database/supabase_schema.sql`](file:///d:/OOSC/backend/database/supabase_schema.sql).

---

## 📡 Key API Endpoints

### 🩺 Health & System
- `GET /health` - Health check
- `GET /health/ready` - Readiness check (DB & RAG connectivity)

### 🔐 Authentication & User Profile
- `GET /api/v1/auth/me` - Get current authenticated user profile
- `PATCH /api/v1/auth/profile` - Update profile (state, district, preferred language)

### 💬 Legal Conversations & Chat
- `GET /api/v1/conversations` - List user conversations
- `POST /api/v1/conversations` - Start new conversation (with optional initial message)
- `GET /api/v1/conversations/{id}` - Get conversation thread with all messages & citations
- `PATCH /api/v1/conversations/{id}` - Update title/metadata
- `DELETE /api/v1/conversations/{id}` - Delete conversation
- `POST /api/v1/conversations/{id}/messages` - Send message, query RAG, return AI response with statutory citations
- `POST /api/v1/conversations/{id}/messages/{msg_id}/feedback` - Submit user feedback

### 📋 Guided Civic Form Sessions
- `GET /api/v1/form-sessions` - List form sessions
- `POST /api/v1/form-sessions` - Initiate guided session (RTI, Consumer Complaint, Municipal Grievance)
- `GET /api/v1/form-sessions/{id}` - Get progress & step-by-step guidance
- `POST /api/v1/form-sessions/{id}/steps` - Submit step fields or natural language input
- `POST /api/v1/form-sessions/{id}/complete` - Finalize session & convert into filing draft

### ⚖️ Complaint & Document Drafting
- `GET /api/v1/complaints` - List complaints & drafts (with category/status filters)
- `POST /api/v1/complaints` - Create complaint
- `GET /api/v1/complaints/{id}` - Get complaint details
- `PATCH /api/v1/complaints/{id}` - Update status or facts
- `DELETE /api/v1/complaints/{id}` - Delete complaint
- `POST /api/v1/complaints/{id}/generate-document` - Synthesize formalized legal notice/draft via RAG
- `POST /api/v1/complaints/{id}/export` - Export formatted Markdown or plain text
