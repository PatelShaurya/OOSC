#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "Freeing existing ports 8000, 8001, 3000..."
fuser -k 8000/tcp 8001/tcp 3000/tcp || true
sleep 1

echo "1. Starting RAG Microservice on http://127.0.0.1:8001..."
nohup ./venv/bin/python -m uvicorn rag.app.api.main:app --host 127.0.0.1 --port 8001 > rag_server.log 2>&1 &
RAG_PID=$!
echo "RAG Microservice PID: $RAG_PID"

echo "2. Starting Main FastAPI Backend on http://127.0.0.1:8000..."
nohup env PYTHONPATH=backend RAG_SERVICE_URL=http://127.0.0.1:8001 ./venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > backend_server.log 2>&1 &
BACKEND_PID=$!
echo "Main Backend PID: $BACKEND_PID"

echo "3. Starting CivicAI Frontend on http://localhost:3000..."
cd frontend
nohup npm run dev > ../frontend_server.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

sleep 3

echo ""
echo "=================================================="
echo " CivicAI All Services Started Successfully!"
echo "=================================================="
echo " - RAG Microservice: http://127.0.0.1:8001 (Log: rag_server.log)"
echo " - Main Backend:     http://127.0.0.1:8000 (Log: backend_server.log)"
echo " - React Frontend:   http://localhost:3000 (Log: frontend_server.log)"
echo "=================================================="
