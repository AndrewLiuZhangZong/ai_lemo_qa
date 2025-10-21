"""用户反馈模型"""
from sqlalchemy import Column, Integer, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class Feedback(Base):
    """用户反馈表"""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversation_history.id", ondelete="CASCADE"), nullable=False, comment="对话ID")
    rating = Column(Integer, comment="评分(1-5)")
    feedback_text = Column(Text, comment="反馈内容")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, conversation_id={self.conversation_id}, rating={self.rating})>"

