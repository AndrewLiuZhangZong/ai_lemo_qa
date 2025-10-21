"""Embedding服务 - 文本向量化"""
import ollama
from typing import List
from app.core.config import get_settings
from loguru import logger

settings = get_settings()


class EmbeddingService:
    """Embedding服务类"""
    
    def __init__(self):
        self.model = settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL
    
    async def get_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示
        
        Args:
            text: 输入文本
            
        Returns:
            向量列表
        """
        try:
            response = ollama.embeddings(
                model=self.model,
                prompt=text
            )
            return response["embedding"]
        except Exception as e:
            logger.error(f"获取embedding失败: {e}")
            raise
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """批量获取文本向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表的列表
        """
        embeddings = []
        for text in texts:
            embedding = await self.get_embedding(text)
            embeddings.append(embedding)
        return embeddings


# 创建全局实例
embedding_service = EmbeddingService()

