"""知识库模型"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ARRAY, BigInteger
from sqlalchemy.sql import func
from app.core.database import Base


class Knowledge(Base):
    """知识库表"""
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False, comment="标准问题")
    answer = Column(Text, nullable=False, comment="标准答案")
    category = Column(String(100), index=True, comment="分类")
    keywords = Column(ARRAY(String), comment="关键词数组")
    milvus_id = Column(BigInteger, unique=True, index=True, comment="Milvus向量ID")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    status = Column(Integer, default=1, comment="状态：0-草稿 1-已发布")
    source = Column(String(200), comment="来源")
    
    def __repr__(self):
        return f"<Knowledge(id={self.id}, question='{self.question[:30]}...')>"

