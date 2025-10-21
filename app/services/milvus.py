"""Milvus向量检索服务"""
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from typing import List, Dict, Tuple
from app.core.config import get_settings
from loguru import logger

settings = get_settings()


class MilvusService:
    """Milvus向量数据库服务"""
    
    def __init__(self):
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.dimension = settings.EMBEDDING_DIMENSION
        self.collection = None
        self._connect()
    
    def _connect(self):
        """连接Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            logger.info(f"已连接到Milvus: {self.host}:{self.port}")
            self._init_collection()
        except Exception as e:
            logger.error(f"连接Milvus失败: {e}")
            raise
    
    def _init_collection(self):
        """初始化集合"""
        try:
            # 检查集合是否存在
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                logger.info(f"加载已存在的集合: {self.collection_name}")
            else:
                # 创建新集合
                fields = [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="knowledge_id", dtype=DataType.INT64),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension)
                ]
                schema = CollectionSchema(fields, description="知识库向量集合")
                self.collection = Collection(self.collection_name, schema)
                
                # 创建索引
                index_params = {
                    "metric_type": "IP",  # 内积（余弦相似度）
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 1024}
                }
                self.collection.create_index("embedding", index_params)
                logger.info(f"创建新集合: {self.collection_name}")
            
            # 加载集合到内存
            self.collection.load()
        except Exception as e:
            logger.error(f"初始化集合失败: {e}")
            raise
    
    async def insert(self, knowledge_id: int, embedding: List[float]) -> int:
        """插入向量
        
        Args:
            knowledge_id: 知识库ID
            embedding: 向量
            
        Returns:
            Milvus ID
        """
        try:
            data = [
                [knowledge_id],
                [embedding]
            ]
            result = self.collection.insert(data)
            self.collection.flush()
            return result.primary_keys[0]
        except Exception as e:
            logger.error(f"插入向量失败: {e}")
            raise
    
    async def search(self, embedding: List[float], top_k: int = 5) -> List[Tuple[int, float]]:
        """搜索相似向量
        
        Args:
            embedding: 查询向量
            top_k: 返回top k个结果
            
        Returns:
            [(knowledge_id, score), ...]
        """
        try:
            search_params = {"metric_type": "IP", "params": {"nprobe": 10}}
            results = self.collection.search(
                data=[embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["knowledge_id"]
            )
            
            # 解析结果
            matches = []
            for hits in results:
                for hit in hits:
                    knowledge_id = hit.entity.get("knowledge_id")
                    score = hit.score
                    matches.append((knowledge_id, score))
            
            return matches
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise
    
    async def delete(self, milvus_id: int):
        """删除向量"""
        try:
            expr = f"id == {milvus_id}"
            self.collection.delete(expr)
            self.collection.flush()
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            raise


# 创建全局实例
try:
    milvus_service = MilvusService()
except Exception as e:
    logger.warning(f"Milvus服务初始化失败，将在运行时重试: {e}")
    milvus_service = None

