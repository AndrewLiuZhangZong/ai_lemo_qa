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
        history: List[Dict[str, str]] = None
    ) -> str:
        """生成答案
        
        Args:
            question: 用户问题
            context: 从知识库检索到的上下文
            history: 对话历史
            
        Returns:
            生成的答案
        """
        try:
            # 构建prompt
            system_prompt = """你是一个专业的智能客服助手。请根据提供的知识库内容回答用户问题。

规则：
1. 优先使用知识库中的信息回答
2. 回答要准确、专业、友好
3. 如果知识库中没有相关信息，礼貌地告知用户并建议联系人工客服
4. 保持回答简洁明了
"""
            
            user_prompt = f"""知识库内容：
{context}

用户问题：{question}

请根据知识库内容回答用户问题。"""
            
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
            return answer
            
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

