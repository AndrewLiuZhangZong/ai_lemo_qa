"""
Agent 服务模块

支持多种专业 Agent：
- GeneralAgent: 通用问答
- WeatherAgent: 天气查询
- OrderAgent: 订单处理 (未来扩展)
"""

from .manager import AgentManager
from .base import BaseAgent

__all__ = ["AgentManager", "BaseAgent"]

