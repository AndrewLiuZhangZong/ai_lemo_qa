"""Embedding服务 - 文本向量化"""
import ollama
import numpy as np
from typing import List
from app.core.config import get_settings
from loguru import logger

settings = get_settings()


class EmbeddingService:
    """Embedding服务类"""
    
    def __init__(self):
        self.model = settings.OLLAMA_EMBEDDING_MODEL
        self.base_url = settings.OLLAMA_BASE_URL
    
    def _normalize(self, embedding: List[float]) -> List[float]:
        """归一化向量（L2范数）
        
        Args:
            embedding: 原始向量
            
        Returns:
            归一化后的向量
        """
        arr = np.array(embedding)
        norm = np.linalg.norm(arr)
        if norm > 0:
            return (arr / norm).tolist()
        return embedding
    
    async def get_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示（归一化）
        
        Args:
            text: 输入文本
            
        Returns:
            归一化后的向量列表
        """
        try:
            response = ollama.embeddings(
                model=self.model,
                prompt=text
            )
            embedding = response["embedding"]
            # 归一化向量，确保IP（内积）等同于余弦相似度
            return self._normalize(embedding)
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

