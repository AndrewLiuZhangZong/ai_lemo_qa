"""
基础 Agent 类

所有专业 Agent 都继承自此类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from loguru import logger


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, name: str, description: str):
        """
        初始化 Agent
        
        Args:
            name: Agent 名称
            description: Agent 描述（用于路由判断）
        """
        self.name = name
        self.description = description
        self.tools = []
        logger.info(f"✅ {name} 初始化完成")
    
    @abstractmethod
    async def can_handle(self, message: str) -> tuple[bool, float]:
        """
        判断是否能处理此问题
        
        Args:
            message: 用户消息
            
        Returns:
            (是否能处理, 置信度 0-1)
        """
        pass
    
    @abstractmethod
    async def chat(self, message: str, chat_history: Optional[List[Dict]] = None) -> Dict:
        """
        处理聊天请求
        
        Args:
            message: 用户消息
            chat_history: 对话历史
            
        Returns:
            {
                "answer": "回答内容",
                "answer_source": "来源标识",
                "confidence": 置信度,
                "tools_used": ["工具1", "工具2"]
            }
        """
        pass
    
    def get_info(self) -> Dict:
        """获取 Agent 信息"""
        return {
            "name": self.name,
            "description": self.description,
            "tools_count": len(self.tools)
        }

