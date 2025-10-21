"""
Agent 管理器

负责：
1. 注册和管理所有 Agent
2. 根据问题自动路由到合适的 Agent
3. 如果没有专业 Agent，使用通用 Agent
"""

from typing import Dict, List, Optional
from loguru import logger

from .base import BaseAgent


class AgentManager:
    """Agent 管理器"""
    
    def __init__(self):
        """初始化 Agent 管理器"""
        self.agents: List[BaseAgent] = []
        self.default_agent: Optional[BaseAgent] = None
        logger.info("🔧 Agent Manager 初始化完成")
    
    def register_agent(self, agent: BaseAgent, is_default: bool = False):
        """
        注册 Agent
        
        Args:
            agent: Agent 实例
            is_default: 是否为默认 Agent（用于兜底）
        """
        self.agents.append(agent)
        if is_default:
            self.default_agent = agent
        logger.info(f"📝 注册 Agent: {agent.name} (默认={is_default})")
    
    async def route(self, message: str) -> BaseAgent:
        """
        路由到合适的 Agent
        
        Args:
            message: 用户消息
            
        Returns:
            最合适的 Agent
        """
        best_agent = None
        best_confidence = 0.0
        
        # 遍历所有 Agent，找到最合适的
        for agent in self.agents:
            try:
                can_handle, confidence = await agent.can_handle(message)
                logger.debug(f"[路由] {agent.name}: can_handle={can_handle}, confidence={confidence:.2f}")
                
                if can_handle and confidence > best_confidence:
                    best_agent = agent
                    best_confidence = confidence
            except Exception as e:
                logger.error(f"[路由] {agent.name} 判断失败: {e}")
        
        # 如果找到了专业 Agent
        if best_agent and best_confidence > 0.5:  # 阈值 0.5
            logger.info(f"🎯 路由到专业 Agent: {best_agent.name} (置信度={best_confidence:.2f})")
            return best_agent
        
        # 否则使用默认 Agent
        if self.default_agent:
            logger.info(f"🔄 使用默认 Agent: {self.default_agent.name}")
            return self.default_agent
        
        # 如果没有默认 Agent，返回第一个
        if self.agents:
            logger.warning(f"⚠️  没有默认 Agent，使用第一个: {self.agents[0].name}")
            return self.agents[0]
        
        raise RuntimeError("没有可用的 Agent")
    
    async def chat(self, message: str, chat_history: Optional[List[Dict]] = None) -> Dict:
        """
        处理聊天请求（自动路由）
        
        Args:
            message: 用户消息
            chat_history: 对话历史
            
        Returns:
            聊天响应
        """
        # 路由到合适的 Agent
        agent = await self.route(message)
        
        # 调用 Agent 处理
        result = await agent.chat(message, chat_history)
        
        # 添加 Agent 信息
        result["agent_name"] = agent.name
        
        return result
    
    def list_agents(self) -> List[Dict]:
        """列出所有已注册的 Agent"""
        return [agent.get_info() for agent in self.agents]


# 全局单例
_agent_manager: Optional[AgentManager] = None


def get_agent_manager() -> AgentManager:
    """获取全局 Agent Manager"""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager

