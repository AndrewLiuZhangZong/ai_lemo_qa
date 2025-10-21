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
    
    # 常见城市Location ID映射表（和风天气）
    CITY_IDS = {
        # 直辖市
        "北京": "101010100", "北京市": "101010100",
        "上海": "101020100", "上海市": "101020100", 
        "天津": "101030100", "天津市": "101030100",
        "重庆": "101040100", "重庆市": "101040100",
        
        # 北京区县
        "通州": "101010600", "通州区": "101010600",
        "海淀": "101010200", "海淀区": "101010200",
        "朝阳": "101010300", "朝阳区": "101010300",
        "东城": "101010400", "东城区": "101010400",
        "西城": "101010500", "西城区": "101010500",
        "丰台": "101010700", "丰台区": "101010700",
        "石景山": "101010800", "石景山区": "101010800",
        "昌平": "101011100", "昌平区": "101011100",
        "大兴": "101011200", "大兴区": "101011200",
        
        # 省会城市
        "广州": "101280101", "广州市": "101280101",
        "深圳": "101280601", "深圳市": "101280601",
        "杭州": "101210101", "杭州市": "101210101",
        "南京": "101190101", "南京市": "101190101",
        "成都": "101270101", "成都市": "101270101",
        "武汉": "101200101", "武汉市": "101200101",
        "西安": "101110101", "西安市": "101110101",
        "郑州": "101180101", "郑州市": "101180101",
        "长沙": "101250101", "长沙市": "101250101",
        "济南": "101120101", "济南市": "101120101",
        "沈阳": "101070101", "沈阳市": "101070101",
        "哈尔滨": "101050101", "哈尔滨市": "101050101",
        "昆明": "101290101", "昆明市": "101290101",
        "南宁": "101300101", "南宁市": "101300101",
        "福州": "101230101", "福州市": "101230101",
        "南昌": "101240101", "南昌市": "101240101",
        "石家庄": "101090101", "石家庄市": "101090101",
        "太原": "101100101", "太原市": "101100101",
        "呼和浩特": "101080101", "呼和浩特市": "101080101",
        "长春": "101060101", "长春市": "101060101",
        "兰州": "101160101", "兰州市": "101160101",
        "西宁": "101150101", "西宁市": "101150101",
        "银川": "101170101", "银川市": "101170101",
        "乌鲁木齐": "101130101", "乌鲁木齐市": "101130101",
        "拉萨": "101140101", "拉萨市": "101140101",
        "贵阳": "101260101", "贵阳市": "101260101",
        "海口": "101310101", "海口市": "101310101",
        "合肥": "101220101", "合肥市": "101220101",
    }
    
    def __init__(self, api_key: Optional[str] = None, api_host: Optional[str] = None):
        """
        初始化天气工具
        
        Args:
            api_key: 和风天气 API Key（如果不提供，从环境变量读取）
            api_host: 和风天气 API Host（如果不提供，从环境变量读取）
        """
        self.api_key = api_key or getattr(settings, "QWEATHER_API_KEY", None)
        self.api_host = api_host or getattr(settings, "QWEATHER_API_HOST", "devapi.qweather.com")
        self.base_url = f"https://{self.api_host}/v7"       # 天气API地址
        self.geo_url = f"https://{self.api_host}/geo/v2"    # 城市查询API地址（注意：需要/geo前缀）
        
        if not self.api_key:
            logger.warning("⚠️  和风天气 API Key 未配置，天气查询功能不可用")
    
    async def get_location_id(self, city_name: str) -> Optional[str]:
        """
        根据城市名称获取 Location ID（优先使用API，失败则使用本地映射）
        
        Args:
            city_name: 城市名称
            
        Returns:
            Location ID 或 None
        """
        if not self.api_key:
            logger.warning("API Key未配置，仅使用本地映射")
            return self._get_location_from_cache(city_name)
        
        # 1. 尝试API查询
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.geo_url}/city/lookup",
                    headers={"X-QW-Api-Key": self.api_key},
                    params={"location": city_name, "lang": "zh"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == "200" and data.get("location"):
                        location = data["location"][0]
                        location_id = location["id"]
                        location_name = location["name"]
                        logger.info(f"🌍 API找到城市: {location_name} (ID: {location_id})")
                        return location_id
                    else:
                        logger.warning(f"API未找到城市: {city_name}, code={data.get('code')}")
                else:
                    logger.error(f"API查询失败: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"API查询异常: {e}")
        
        # 2. API失败，使用本地映射兜底
        logger.info(f"API查询失败，使用本地映射查找: {city_name}")
        return self._get_location_from_cache(city_name)
    
    def _get_location_from_cache(self, city_name: str) -> Optional[str]:
        """从本地映射表查找城市ID"""
        # 清理城市名称
        city_name = city_name.strip().replace("市", "").replace("的天气", "").replace("天气", "")
        
        # 尝试多种匹配方式
        possible_names = [
            city_name,
            city_name + "市",
            city_name + "区",
            city_name.replace("区", ""),
            city_name.replace("市", "")
        ]
        
        for name in possible_names:
            if name in self.CITY_IDS:
                location_id = self.CITY_IDS[name]
                logger.info(f"🌍 本地映射找到城市: {name} (ID: {location_id})")
                return location_id
        
        # 模糊匹配：查找包含关键词的城市
        for key in self.CITY_IDS:
            if city_name in key or key in city_name:
                location_id = self.CITY_IDS[key]
                logger.info(f"🌍 本地模糊匹配到城市: {key} (ID: {location_id})")
                return location_id
        
        logger.warning(f"未找到城市: {city_name}，请尝试：北京、上海、通州区等常见城市")
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
                    headers={
                        "X-QW-Api-Key": self.api_key
                    },
                    params={
                        "location": location_id,
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

