from fastapi import APIRouter
from app.api.v1 import auth, complaints, conversations, form_sessions, health, rti

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(conversations.router)
api_router.include_router(form_sessions.router)
api_router.include_router(complaints.router)
api_router.include_router(rti.router)
