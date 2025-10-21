"""聊天相关Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=500)
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[str] = Field(None, description="用户ID")


class RelatedQuestion(BaseModel):
    """相关问题"""
    id: int
    question: str
    similarity: float


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str = Field(..., description="会话ID")
    answer: str = Field(..., description="回答")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    sources: List[dict] = Field(default_factory=list, description="来源知识库")
    related_questions: List[str] = Field(default_factory=list, description="相关问题")
    intent: Optional[str] = Field(None, description="识别的意图")
    answer_source: str = Field(default="knowledge_base", description="答案来源：knowledge_base(知识库) 或 general_ai(通用AI)")


class ApiResponse(BaseModel):
    """统一API响应格式"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="消息")
    data: Optional[dict] = Field(None, description="数据")

