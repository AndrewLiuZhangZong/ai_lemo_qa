"""问答业务逻辑服务"""
import uuid
import time
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Knowledge, Conversation
from app.schemas.chat import ChatResponse
from app.core.config import get_settings
from .embedding import embedding_service
from .milvus import milvus_service
from .llm import llm_service
from .search import search_service
from loguru import logger

settings = get_settings()


class ChatService:
    """问答服务"""
    
    async def chat(
        self,
        message: str,
        session_id: str = None,
        user_id: str = None,
        db: AsyncSession = None
    ) -> ChatResponse:
        """处理聊天请求
        
        Args:
            message: 用户消息
            session_id: 会话ID
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            聊天响应
        """
        start_time = time.time()
        
        # 生成会话ID
        if not session_id:
            session_id = str(uuid.uuid4())
        
        try:
            # 1. 获取问题的向量表示
            question_embedding = await embedding_service.get_embedding(message)
            
            # 2. 在Milvus中搜索相似问题
            matches = await milvus_service.search(question_embedding, top_k=5)
            
            # 判断是否需要网络搜索（无匹配或置信度极低）
            use_web_search = False
            if not matches:
                use_web_search = True
            else:
                # 计算初步置信度
                raw_score = float(matches[0][1]) if matches else 0.0
                baseline = 0.58
                if raw_score < baseline:
                    preliminary_confidence = 0.0
                else:
                    preliminary_confidence = (raw_score - baseline) / (1.0 - baseline)
                
                # 如果置信度太低（<0.2），启用网络搜索
                if preliminary_confidence < 0.2:
                    use_web_search = True
                    logger.info(f"置信度过低({preliminary_confidence:.2%})，启用网络搜索")
            
            if use_web_search:
                # 使用SearXNG网络搜索
                search_results = await search_service.search(message, max_results=3)
                
                if search_results:
                    # 基于搜索结果生成答案
                    search_context = search_service.format_search_context(search_results)
                    answer, answer_source = await llm_service.generate_answer(
                        message, search_context, confidence=0.0
                    )
                    answer_source = "web_search"  # 标记为网络搜索
                    confidence = 0.1  # 网络搜索给一个固定的低置信度
                    sources = [{
                        "title": r["title"],
                        "url": r["url"],
                        "similarity": 0.0
                    } for r in search_results]
                    related_questions = []
                    logger.info(f"使用网络搜索回答，找到{len(search_results)}条结果")
                else:
                    # 网络搜索也失败，使用通用AI
                    answer, answer_source = await llm_service.generate_answer(
                        message, "", confidence=0.0
                    )
                    confidence = 0.0
                    sources = []
                    related_questions = []
            else:
                # 3. 从数据库获取知识详情
                knowledge_ids = [match[0] for match in matches]
                result = await db.execute(
                    select(Knowledge).where(
                        Knowledge.id.in_(knowledge_ids),
                        Knowledge.status == 1
                    )
                )
                knowledge_list = result.scalars().all()
                
                # 构建知识库映射
                knowledge_map = {k.id: k for k in knowledge_list}
                
                # 4. 构建上下文
                context_parts = []
                sources = []
                for kid, score in matches[:3]:  # 取前3个最相关的
                    if kid in knowledge_map:
                        k = knowledge_map[kid]
                        context_parts.append(f"问题：{k.question}\n答案：{k.answer}")
                        # IP（内积）分数：考虑基线相似度
                        baseline = 0.58
                        raw = float(score)
                        normalized_score = max(0.0, (raw - baseline) / (1.0 - baseline)) if raw >= baseline else 0.0
                        sources.append({
                            "id": k.id,
                            "question": k.question,
                            "similarity": normalized_score
                        })
                
                context = "\n\n".join(context_parts)
                
                # 5. 计算置信度（使用最高的相似度作为置信度）
                # IP（内积）分数：考虑模型的基线相似度（约0.58）
                raw_score = float(matches[0][1]) if matches else 0.0
                baseline = 0.58  # nomic-embed-text的基线相似度
                if raw_score < baseline:
                    confidence = 0.0
                else:
                    # 将[baseline, 1.0]映射到[0, 1]
                    confidence = (raw_score - baseline) / (1.0 - baseline)
                
                # 6. 使用LLM生成答案（根据置信度自动调整策略）
                answer, answer_source = await llm_service.generate_answer(
                    message, context, confidence=confidence
                )
                
                # 7. 获取相关问题推荐
                related_questions = [
                    knowledge_map[kid].question 
                    for kid, _ in matches[1:4] 
                    if kid in knowledge_map
                ]
            
            # 8. 识别意图
            intent = await llm_service.detect_intent(message)
            
            # 9. 保存对话历史
            response_time = int((time.time() - start_time) * 1000)
            if db:
                conversation = Conversation(
                    session_id=session_id,
                    user_id=user_id,
                    user_message=message,
                    bot_response=answer,
                    intent=intent,
                    confidence=confidence,
                    knowledge_id=sources[0]["id"] if sources else None,
                    response_time=response_time
                )
                db.add(conversation)
                await db.commit()
            
            # 10. 构建响应
            response = ChatResponse(
                session_id=session_id,
                answer=answer,
                confidence=confidence,
                sources=sources,
                related_questions=related_questions,
                intent=intent,
                answer_source=answer_source
            )
            
            logger.info(f"问答完成: session={session_id}, 耗时={response_time}ms, 置信度={confidence:.2f}, 来源={answer_source}")
            return response
            
        except Exception as e:
            logger.error(f"问答处理失败: {e}")
            # 返回默认错误响应
            return ChatResponse(
                session_id=session_id,
                answer="抱歉，系统出现错误，请稍后重试。",
                confidence=0.0,
                sources=[],
                related_questions=[],
                answer_source="error"
            )


# 创建全局实例
chat_service = ChatService()

