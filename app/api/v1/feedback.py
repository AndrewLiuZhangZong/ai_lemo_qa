"""用户反馈API"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.models.feedback import Feedback
from app.models.conversation import Conversation
from app.schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackList
from app.core.logger import setup_logger

router = APIRouter(prefix="/feedback", tags=["用户反馈"])
logger = setup_logger()


@router.post("", response_model=FeedbackResponse, status_code=201)
async def create_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    创建用户反馈
    
    - **conversation_id**: 对话ID
    - **rating**: 评分(1-5)
    - **feedback_text**: 反馈内容（可选）
    """
    try:
        # 检查对话是否存在
        conversation = db.query(Conversation).filter(Conversation.id == feedback.conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="对话记录不存在")
        
        # 检查是否已经反馈过
        existing_feedback = db.query(Feedback).filter(
            Feedback.conversation_id == feedback.conversation_id
        ).first()
        if existing_feedback:
            raise HTTPException(status_code=400, detail="该对话已经提交过反馈")
        
        # 创建反馈
        db_feedback = Feedback(
            conversation_id=feedback.conversation_id,
            rating=feedback.rating,
            feedback_text=feedback.feedback_text
        )
        db.add(db_feedback)
        
        # 更新对话记录的反馈状态
        if feedback.rating >= 4:
            conversation.feedback = 1  # 满意
        elif feedback.rating <= 2:
            conversation.feedback = -1  # 不满意
        else:
            conversation.feedback = 0  # 一般
        
        db.commit()
        db.refresh(db_feedback)
        
        logger.info(f"用户反馈已创建: ID={db_feedback.id}, 对话ID={feedback.conversation_id}, 评分={feedback.rating}")
        
        return db_feedback
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建反馈失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建反馈失败: {str(e)}")


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: int,
    db: Session = Depends(get_db)
):
    """
    获取反馈详情
    
    - **feedback_id**: 反馈ID
    """
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    return feedback


@router.get("", response_model=FeedbackList)
async def list_feedbacks(
    conversation_id: Optional[int] = Query(None, description="按对话ID过滤"),
    rating: Optional[int] = Query(None, description="按评分过滤", ge=1, le=5),
    limit: int = Query(20, description="每页数量", ge=1, le=100),
    offset: int = Query(0, description="偏移量", ge=0),
    db: Session = Depends(get_db)
):
    """
    获取反馈列表
    
    - **conversation_id**: 按对话ID过滤（可选）
    - **rating**: 按评分过滤（可选）
    - **limit**: 每页数量
    - **offset**: 偏移量
    """
    try:
        # 构建查询
        query = db.query(Feedback)
        
        # 过滤条件
        if conversation_id is not None:
            query = query.filter(Feedback.conversation_id == conversation_id)
        if rating is not None:
            query = query.filter(Feedback.rating == rating)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        feedbacks = query.order_by(Feedback.created_at.desc()).offset(offset).limit(limit).all()
        
        return FeedbackList(total=total, items=feedbacks)
        
    except Exception as e:
        logger.error(f"查询反馈列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.delete("/{feedback_id}", status_code=204)
async def delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_db)
):
    """
    删除反馈
    
    - **feedback_id**: 反馈ID
    """
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    try:
        db.delete(feedback)
        db.commit()
        logger.info(f"反馈已删除: ID={feedback_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"删除反馈失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/stats/summary")
async def get_feedback_stats(db: Session = Depends(get_db)):
    """
    获取反馈统计信息
    
    返回各评分的数量统计
    """
    try:
        stats = {
            "total": db.query(Feedback).count(),
            "rating_distribution": {}
        }
        
        # 统计各评分数量
        for rating in range(1, 6):
            count = db.query(Feedback).filter(Feedback.rating == rating).count()
            stats["rating_distribution"][rating] = count
        
        # 计算平均评分
        feedbacks = db.query(Feedback).all()
        if feedbacks:
            avg_rating = sum(f.rating for f in feedbacks) / len(feedbacks)
            stats["average_rating"] = round(avg_rating, 2)
        else:
            stats["average_rating"] = 0
        
        return stats
        
    except Exception as e:
        logger.error(f"获取反馈统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"统计失败: {str(e)}")

