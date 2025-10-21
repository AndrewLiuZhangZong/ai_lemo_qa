"""
天气查询工具

集成和风天气 API (QWeather)
- 免费额度：每天 1000 次请求
- 文档：https://dev.qweather.com/
"""

import httpx
from typing import Dict, Optional
from loguru import logger

from app.core.config import get_settings

settings = get_settings()


class WeatherTool:
    """天气查询工具"""
    
    name = "天气查询"
    description = """
    查询指定城市的实时天气和天气预报。
    适用于：用户询问天气、温度、天气状况等。
    输入：城市名称（例如：北京、上海、通州区）
    输出：实时天气信息（温度、天气状况、风力、湿度等）
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化天气工具
        
        Args:
            api_key: 和风天气 API Key（如果不提供，从环境变量读取）
        """
        self.api_key = api_key or getattr(settings, "QWEATHER_API_KEY", None)
        self.base_url = "https://devapi.qweather.com/v7"  # 免费版 API 地址
        self.geo_url = "https://geoapi.qweather.com/v2"
        
        if not self.api_key:
            logger.warning("⚠️  和风天气 API Key 未配置，天气查询功能不可用")
    
    async def get_location_id(self, city_name: str) -> Optional[str]:
        """
        根据城市名称获取 Location ID
        
        Args:
            city_name: 城市名称
            
        Returns:
            Location ID 或 None
        """
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.geo_url}/city/lookup",
                    params={
                        "location": city_name,
                        "key": self.api_key,
                        "lang": "zh"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == "200" and data.get("location"):
                        # 返回第一个匹配的城市
                        location = data["location"][0]
                        location_id = location["id"]
                        location_name = location["name"]
                        logger.info(f"🌍 找到城市: {location_name} (ID: {location_id})")
                        return location_id
                    else:
                        logger.warning(f"未找到城市: {city_name}, code={data.get('code')}")
                        return None
                else:
                    logger.error(f"城市查询失败: HTTP {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"城市查询异常: {e}")
            return None
    
    async def get_weather_now(self, city_name: str) -> Dict:
        """
        获取实时天气
        
        Args:
            city_name: 城市名称
            
        Returns:
            天气信息字典
        """
        if not self.api_key:
            return {
                "success": False,
                "message": "天气 API Key 未配置，请联系管理员配置 QWEATHER_API_KEY"
            }
        
        # 1. 获取城市 Location ID
        location_id = await self.get_location_id(city_name)
        if not location_id:
            return {
                "success": False,
                "message": f"未找到城市：{city_name}，请检查城市名称是否正确"
            }
        
        # 2. 获取实时天气
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/weather/now",
                    params={
                        "location": location_id,
                        "key": self.api_key,
                        "lang": "zh"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == "200" and data.get("now"):
                        now = data["now"]
                        update_time = data.get("updateTime", "")
                        
                        weather_info = {
                            "success": True,
                            "city": city_name,
                            "temperature": f"{now.get('temp', 'N/A')}°C",
                            "feels_like": f"{now.get('feelsLike', 'N/A')}°C",
                            "weather": now.get("text", "未知"),
                            "wind_dir": now.get("windDir", "未知"),
                            "wind_scale": now.get("windScale", "未知"),
                            "humidity": f"{now.get('humidity', 'N/A')}%",
                            "pressure": f"{now.get('pressure', 'N/A')} hPa",
                            "visibility": f"{now.get('vis', 'N/A')} km",
                            "update_time": update_time,
                            "raw": now  # 原始数据
                        }
                        
                        logger.info(f"🌤️  获取天气成功: {city_name} {weather_info['temperature']} {weather_info['weather']}")
                        return weather_info
                    else:
                        return {
                            "success": False,
                            "message": f"获取天气失败: code={data.get('code')}"
                        }
                else:
                    return {
                        "success": False,
                        "message": f"天气 API 请求失败: HTTP {response.status_code}"
                    }
        except Exception as e:
            logger.error(f"获取天气异常: {e}")
            return {
                "success": False,
                "message": f"获取天气异常: {str(e)}"
            }
    
    async def _arun(self, city_name: str) -> str:
        """异步执行天气查询（供 LangChain Agent 调用）"""
        logger.info(f"[工具] 天气查询: {city_name}")
        
        result = await self.get_weather_now(city_name)
        
        if result["success"]:
            # 格式化输出
            output = f"""天气查询结果：
城市：{result['city']}
天气：{result['weather']}
温度：{result['temperature']}
体感温度：{result['feels_like']}
风向：{result['wind_dir']}
风力：{result['wind_scale']}级
湿度：{result['humidity']}
气压：{result['pressure']}
能见度：{result['visibility']}
更新时间：{result['update_time']}"""
            return output
        else:
            return f"天气查询失败：{result['message']}"
    
    def run(self, city_name: str) -> str:
        """同步执行天气查询（供 Agent 调用）"""
        import asyncio
        return asyncio.run(self._arun(city_name))


# 单例
_weather_tool_instance: Optional[WeatherTool] = None


def get_weather_tool() -> WeatherTool:
    """获取天气工具单例"""
    global _weather_tool_instance
    if _weather_tool_instance is None:
        _weather_tool_instance = WeatherTool()
    return _weather_tool_instance

