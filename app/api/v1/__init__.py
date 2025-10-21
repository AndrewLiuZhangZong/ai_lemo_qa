"""API v1版本"""
from fastapi import APIRouter
from .chat import router as chat_router
from .knowledge import router as knowledge_router

api_router = APIRouter()

api_router.include_router(chat_router, prefix="/chat", tags=["聊天"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["知识库"])

