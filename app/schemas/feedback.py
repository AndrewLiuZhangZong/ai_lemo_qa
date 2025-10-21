"""用户反馈Schema"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FeedbackCreate(BaseModel):
    """创建反馈请求"""
    conversation_id: int = Field(..., description="对话ID", gt=0)
    rating: int = Field(..., description="评分(1-5)", ge=1, le=5)
    feedback_text: Optional[str] = Field(None, description="反馈内容", max_length=1000)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "conversation_id": 1,
                    "rating": 5,
                    "feedback_text": "回答很准确，解决了我的问题"
                }
            ]
        }
    }


class FeedbackResponse(BaseModel):
    """反馈响应"""
    id: int
    conversation_id: int
    rating: int
    feedback_text: Optional[str] = None
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class FeedbackList(BaseModel):
    """反馈列表响应"""
    total: int
    items: list[FeedbackResponse]

