"""
天气专家 Agent

负责处理所有与天气相关的查询
支持工具链串联：日期时间 → 地点解析 → 天气查询
"""

import re
import datetime
from typing import Dict, List, Optional
from loguru import logger

from .base import BaseAgent
from app.services.tools.weather_tool import get_weather_tool


class WeatherAgent(BaseAgent):
    """天气专家 Agent"""
    
    # 天气相关关键词
    WEATHER_KEYWORDS = [
        "天气", "气温", "温度", "下雨", "晴天", "阴天", "多云",
        "刮风", "风力", "湿度", "降雨", "降水", "雾霾", "空气",
        "穿什么", "需要带伞", "热不热", "冷不冷"
    ]
    
    def __init__(self):
        """初始化天气 Agent"""
        super().__init__(
            name="天气专家",
            description="专门处理天气查询相关的问题"
        )
        
        # 加载天气工具
        self.weather_tool = get_weather_tool()
        self.tools = [self.weather_tool]
    
    async def can_handle(self, message: str) -> tuple[bool, float]:
        """
        判断是否为天气相关问题
        
        Returns:
            (是否能处理, 置信度)
        """
        message_lower = message.lower()
        
        # 检查是否包含天气关键词
        keyword_count = sum(1 for keyword in self.WEATHER_KEYWORDS if keyword in message_lower)
        
        if keyword_count > 0:
            # 根据关键词数量计算置信度
            confidence = min(0.9, 0.6 + keyword_count * 0.15)
            logger.debug(f"[天气Agent] 匹配关键词数={keyword_count}, 置信度={confidence:.2f}")
            return True, confidence
        
        return False, 0.0
    
    def extract_city(self, message: str) -> Optional[str]:
        """
        从消息中提取城市名称
        
        Args:
            message: 用户消息
            
        Returns:
            城市名称或 None
        """
        # 常见城市模式
        city_patterns = [
            r"([\u4e00-\u9fa5]{2,10}?)(?:市|区|县|镇)?(?:的)?(?:天气|气温|温度)",
            r"(?:天气|气温|温度).*?([\u4e00-\u9fa5]{2,10}?)(?:市|区|县|镇)?",
            r"([\u4e00-\u9fa5]{2,10}?)(?:市|区|县|镇)(?:的)?(?:天气|气温|温度)?",
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, message)
            if match:
                city = match.group(1)
                # 过滤一些常见的非城市词
                exclude_words = ["今天", "明天", "现在", "怎么样", "如何", "多少"]
                if city not in exclude_words:
                    logger.info(f"[地点解析] 提取城市: {city}")
                    return city
        
        return None
    
    def extract_time_context(self, message: str) -> str:
        """
        提取时间上下文
        
        Args:
            message: 用户消息
            
        Returns:
            时间描述
        """
        now = datetime.datetime.now()
        
        # 检查是否询问明天
        if "明天" in message or "明日" in message:
            tomorrow = now + datetime.timedelta(days=1)
            return f"明天（{tomorrow.strftime('%Y年%m月%d日')}）"
        
        # 检查是否询问后天
        if "后天" in message:
            day_after = now + datetime.timedelta(days=2)
            return f"后天（{day_after.strftime('%Y年%m月%d日')}）"
        
        # 默认今天
        return f"今天（{now.strftime('%Y年%m月%d日')}）"
    
    async def chat(self, message: str, chat_history: Optional[List[Dict]] = None) -> Dict:
        """
        处理天气查询（工具链串联）
        
        工具链：
        1. 提取时间上下文
        2. 提取地点信息
        3. 调用天气 API
        4. 生成友好回答
        """
        tools_used = []
        
        try:
            # 步骤 1: 提取时间上下文
            time_context = self.extract_time_context(message)
            tools_used.append("时间解析")
            logger.info(f"[工具链-1] 时间上下文: {time_context}")
            
            # 步骤 2: 提取城市名称
            city = self.extract_city(message)
            tools_used.append("地点解析")
            
            if not city:
                return {
                    "answer": "抱歉，我没有识别到您要查询的城市。请告诉我具体的城市名称，例如：北京的天气怎么样？",
                    "answer_source": "weather_agent",
                    "confidence": 0.3,
                    "tools_used": tools_used
                }
            
            logger.info(f"[工具链-2] 提取城市: {city}")
            
            # 步骤 3: 调用天气工具
            tools_used.append("天气API")
            weather_result = await self.weather_tool.get_weather_now(city)
            
            if weather_result["success"]:
                # 步骤 4: 生成友好回答
                w = weather_result
                answer = f"""{time_context}{city}的天气情况如下：

🌡️ **温度**：{w['temperature']}（体感 {w['feels_like']}）
🌤️  **天气**：{w['weather']}
💨 **风力**：{w['wind_dir']} {w['wind_scale']}级
💧 **湿度**：{w['humidity']}
👁️  **能见度**：{w['visibility']}

数据更新时间：{w['update_time']}"""
                
                return {
                    "answer": answer,
                    "answer_source": "weather_api",
                    "confidence": 0.95,
                    "tools_used": tools_used,
                    "weather_data": weather_result
                }
            else:
                # API 调用失败
                return {
                    "answer": f"抱歉，获取{city}的天气信息失败。{weather_result.get('message', '')}",
                    "answer_source": "weather_agent",
                    "confidence": 0.5,
                    "tools_used": tools_used
                }
        
        except Exception as e:
            logger.error(f"[天气Agent] 处理失败: {e}")
            return {
                "answer": f"抱歉，天气查询过程中出现错误：{str(e)}",
                "answer_source": "weather_agent",
                "confidence": 0.3,
                "tools_used": tools_used
            }


# 单例
_weather_agent_instance: Optional[WeatherAgent] = None


def get_weather_agent() -> WeatherAgent:
    """获取天气 Agent 单例"""
    global _weather_agent_instance
    if _weather_agent_instance is None:
        _weather_agent_instance = WeatherAgent()
    return _weather_agent_instance

