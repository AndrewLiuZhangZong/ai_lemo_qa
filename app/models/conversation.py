"""对话历史模型"""
from sqlalchemy import Column, Integer, String, Text, Float, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class Conversation(Base):
    """对话历史表"""
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True, comment="会话ID")
    user_id = Column(String(100), index=True, comment="用户ID")
    user_message = Column(Text, nullable=False, comment="用户消息")
    bot_response = Column(Text, nullable=False, comment="机器人回复")
    intent = Column(String(100), comment="识别的意图")
    confidence = Column(Float, comment="置信度")
    knowledge_id = Column(Integer, ForeignKey("knowledge_base.id"), comment="关联的知识库ID")
    feedback = Column(Integer, default=0, comment="用户反馈：-1-不满意 0-未评价 1-满意")
    response_time = Column(Integer, comment="响应时间(毫秒)")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, session_id='{self.session_id}')>"

