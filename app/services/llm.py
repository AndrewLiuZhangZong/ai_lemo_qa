"""LLM对话服务"""
import ollama
from typing import List, Dict
from app.core.config import get_settings
from loguru import logger

settings = get_settings()


class LLMService:
    """LLM对话服务类"""
    
    def __init__(self):
        self.model = settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL
    
    async def generate_answer(
        self,
        question: str,
        context: str,
        history: List[Dict[str, str]] = None,
        confidence: float = 0.0
    ) -> tuple[str, str]:
        """生成答案
        
        Args:
            question: 用户问题
            context: 从知识库检索到的上下文
            history: 对话历史
            confidence: 知识库匹配置信度
            
        Returns:
            (生成的答案, 答案来源标识)
        """
        try:
            # 根据置信度调整回答策略
            if confidence >= 0.6:
                # 高置信度：严格基于知识库
                system_prompt = """你是一个专业的智能客服助手。请严格根据提供的知识库内容回答用户问题。

回答规则：
1. 必须基于知识库内容回答
2. 回答要准确、专业、友好
3. 保持回答简洁明了
"""
                user_prompt = f"""知识库内容：
{context}

用户问题：{question}

请严格根据上述知识库内容回答问题。"""
                answer_source = "knowledge_base"
                
            else:
                # 低置信度：允许通用回答
                system_prompt = """你是一个智能AI助手，既可以回答专业客服问题，也可以进行日常对话。

回答规则：
1. 如果知识库中有相关内容，优先参考使用
2. 如果知识库中没有，使用你的通用知识友好地回答
3. 回答要自然、有帮助、友好
4. 保持专业但不失亲和力
"""
                
                if context.strip():
                    user_prompt = f"""参考知识库（可能相关度不高）：
{context}

用户问题：{question}

请回答用户问题。如果知识库内容相关，可以参考；如果不相关，请直接根据问题本身回答。"""
                else:
                    user_prompt = f"""用户问题：{question}

请友好地回答用户问题。"""
                
                answer_source = "general_ai"
            
            # 构建消息列表
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # 添加历史对话
            if history:
                for msg in history[-settings.MAX_CONTEXT_TURNS:]:
                    messages.append(msg)
            
            # 添加当前问题
            messages.append({"role": "user", "content": user_prompt})
            
            # 调用LLM
            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            
            answer = response["message"]["content"]
            return answer, answer_source
            
        except Exception as e:
            logger.error(f"LLM生成答案失败: {e}")
            raise
    
    async def detect_intent(self, question: str) -> str:
        """检测用户意图
        
        Args:
            question: 用户问题
            
        Returns:
            意图类别
        """
        try:
            prompt = f"""请判断以下用户问题属于哪个类别，只返回类别名称，不要其他内容：

类别：
- 产品咨询
- 售后服务  
- 订单查询
- 投诉建议
- 闲聊
- 其他

用户问题：{question}

类别："""
            
            response = ollama.generate(
                model=self.model,
                prompt=prompt
            )
            
            intent = response["response"].strip()
            return intent
            
        except Exception as e:
            logger.error(f"意图识别失败: {e}")
            return "其他"


# 创建全局实例
llm_service = LLMService()

