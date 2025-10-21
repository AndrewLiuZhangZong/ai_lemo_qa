"""
Agent 服务模块

支持多种专业 Agent：
- GeneralAgent: 通用问答
- WeatherAgent: 天气查询
- OrderAgent: 订单处理 (未来扩展)
"""

from .manager import AgentManager, get_agent_manager
from .base import BaseAgent

__all__ = ["AgentManager", "BaseAgent", "get_agent_manager"]

