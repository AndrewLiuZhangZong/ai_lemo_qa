"""API v1版本"""
from fastapi import APIRouter
from .chat import router as chat_router
from .knowledge import router as knowledge_router
from .feedback import router as feedback_router

api_router = APIRouter()

api_router.include_router(chat_router)
api_router.include_router(knowledge_router)
api_router.include_router(feedback_router)

