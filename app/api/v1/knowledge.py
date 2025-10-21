"""知识库管理API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sql_delete
from typing import List
from app.schemas.knowledge import KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse
from app.schemas.chat import ApiResponse
from app.models import Knowledge
from app.services.embedding import embedding_service
from app.services.milvus import milvus_service
from app.core.database import get_db
from loguru import logger

router = APIRouter(prefix="/knowledge", tags=["知识库"])


@router.post("", response_model=ApiResponse)
async def create_knowledge(
    knowledge: KnowledgeCreate,
    db: AsyncSession = Depends(get_db)
):
    """添加知识"""
    try:
        # 1. 创建数据库记录
        db_knowledge = Knowledge(
            question=knowledge.question,
            answer=knowledge.answer,
            category=knowledge.category,
            keywords=knowledge.keywords,
            source=knowledge.source,
            status=1
        )
        db.add(db_knowledge)
        await db.flush()  # 获取ID
        
        # 2. 生成向量并存储到Milvus
        embedding = await embedding_service.get_embedding(knowledge.question)
        milvus_id = await milvus_service.insert(db_knowledge.id, embedding)
        
        # 3. 更新milvus_id
        db_knowledge.milvus_id = milvus_id
        await db.commit()
        await db.refresh(db_knowledge)
        
        logger.info(f"添加知识成功: id={db_knowledge.id}, milvus_id={milvus_id}")
        
        return ApiResponse(
            code=200,
            message="添加成功",
            data={"id": db_knowledge.id}
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"添加知识失败: {e}")
        return ApiResponse(
            code=500,
            message=f"添加失败: {str(e)}",
            data=None
        )


@router.get("/{knowledge_id}", response_model=ApiResponse)
async def get_knowledge(
    knowledge_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取知识详情"""
    result = await db.execute(
        select(Knowledge).where(Knowledge.id == knowledge_id)
    )
    knowledge = result.scalar_one_or_none()
    
    if not knowledge:
        return ApiResponse(
            code=404,
            message="知识不存在",
            data=None
        )
    
    return ApiResponse(
        code=200,
        message="success",
        data=KnowledgeResponse.from_orm(knowledge).dict()
    )


@router.get("", response_model=ApiResponse)
async def list_knowledge(
    skip: int = 0,
    limit: int = 20,
    category: str = None,
    db: AsyncSession = Depends(get_db)
):
    """获取知识列表"""
    query = select(Knowledge).where(Knowledge.status == 1)
    
    if category:
        query = query.where(Knowledge.category == category)
    
    query = query.offset(skip).limit(limit).order_by(Knowledge.id.desc())
    
    result = await db.execute(query)
    knowledge_list = result.scalars().all()
    
    return ApiResponse(
        code=200,
        message="success",
        data={
            "items": [KnowledgeResponse.from_orm(k).dict() for k in knowledge_list],
            "total": len(knowledge_list)
        }
    )


@router.put("/{knowledge_id}", response_model=ApiResponse)
async def update_knowledge(
    knowledge_id: int,
    knowledge: KnowledgeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新知识"""
    result = await db.execute(
        select(Knowledge).where(Knowledge.id == knowledge_id)
    )
    db_knowledge = result.scalar_one_or_none()
    
    if not db_knowledge:
        return ApiResponse(
            code=404,
            message="知识不存在",
            data=None
        )
    
    try:
        # 更新字段
        update_data = knowledge.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_knowledge, field, value)
        
        # 如果问题更新了，需要重新生成向量
        if knowledge.question:
            # 删除旧向量
            if db_knowledge.milvus_id:
                await milvus_service.delete(db_knowledge.milvus_id)
            
            # 生成新向量
            embedding = await embedding_service.get_embedding(knowledge.question)
            milvus_id = await milvus_service.insert(db_knowledge.id, embedding)
            db_knowledge.milvus_id = milvus_id
        
        await db.commit()
        
        return ApiResponse(
            code=200,
            message="更新成功",
            data={"id": knowledge_id}
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"更新知识失败: {e}")
        return ApiResponse(
            code=500,
            message=f"更新失败: {str(e)}",
            data=None
        )


@router.delete("/{knowledge_id}", response_model=ApiResponse)
async def delete_knowledge(
    knowledge_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除知识"""
    result = await db.execute(
        select(Knowledge).where(Knowledge.id == knowledge_id)
    )
    knowledge = result.scalar_one_or_none()
    
    if not knowledge:
        return ApiResponse(
            code=404,
            message="知识不存在",
            data=None
        )
    
    try:
        # 删除Milvus向量
        if knowledge.milvus_id:
            await milvus_service.delete(knowledge.milvus_id)
        
        # 删除数据库记录
        await db.execute(
            sql_delete(Knowledge).where(Knowledge.id == knowledge_id)
        )
        await db.commit()
        
        return ApiResponse(
            code=200,
            message="删除成功",
            data={"id": knowledge_id}
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"删除知识失败: {e}")
        return ApiResponse(
            code=500,
            message=f"删除失败: {str(e)}",
            data=None
        )

