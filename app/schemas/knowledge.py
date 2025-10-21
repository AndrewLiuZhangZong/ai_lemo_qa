"""知识库Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class KnowledgeBase(BaseModel):
    """知识库基础模型"""
    question: str = Field(..., description="问题", min_length=1)
    answer: str = Field(..., description="答案", min_length=1)
    category: Optional[str] = Field(None, description="分类")
    keywords: Optional[List[str]] = Field(None, description="关键词")
    source: Optional[str] = Field(None, description="来源")


class KnowledgeCreate(KnowledgeBase):
    """创建知识"""
    pass


class KnowledgeUpdate(BaseModel):
    """更新知识"""
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[List[str]] = None
    status: Optional[int] = Field(None, ge=0, le=1)


class KnowledgeResponse(KnowledgeBase):
    """知识响应"""
    id: int
    milvus_id: Optional[int] = None
    status: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

