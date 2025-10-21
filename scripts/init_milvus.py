"""初始化Milvus - 将现有知识库数据同步到Milvus"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import Knowledge
from app.services.embedding import embedding_service
from app.services.milvus import milvus_service
from loguru import logger


async def init_milvus_data():
    """初始化Milvus数据"""
    logger.info("开始同步知识库数据到Milvus...")
    
    async with AsyncSessionLocal() as db:
        # 获取所有已发布的知识
        result = await db.execute(
            select(Knowledge).where(
                Knowledge.status == 1,
                Knowledge.milvus_id == None
            )
        )
        knowledge_list = result.scalars().all()
        
        logger.info(f"找到 {len(knowledge_list)} 条待同步的知识")
        
        for knowledge in knowledge_list:
            # 提前获取需要的属性，避免在异常处理中访问
            knowledge_id = knowledge.id
            knowledge_question = knowledge.question
            
            try:
                # 生成向量
                embedding = await embedding_service.get_embedding(knowledge_question)
                
                # 存储到Milvus
                milvus_id = await milvus_service.insert(knowledge_id, embedding)
                
                # 更新数据库
                knowledge.milvus_id = milvus_id
                await db.commit()
                
                logger.info(f"同步成功: id={knowledge_id}, question={knowledge_question[:30]}...")
                
            except Exception as e:
                logger.error(f"同步失败: id={knowledge_id}, error={e}")
                await db.rollback()
        
        logger.info("Milvus数据同步完成！")


if __name__ == "__main__":
    asyncio.run(init_milvus_data())

