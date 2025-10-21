"""聊天API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.chat import ChatRequest, ChatResponse, ApiResponse
from app.services.chat import chat_service
from app.core.database import get_db

router = APIRouter(prefix="/chat", tags=["聊天"])


@router.post("", response_model=ApiResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """问答接口"""
    try:
        result = await chat_service.chat(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id,
            db=db
        )
        
        return ApiResponse(
            code=200,
            message="success",
            data=result.dict()
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"处理失败: {str(e)}",
            data=None
        )

