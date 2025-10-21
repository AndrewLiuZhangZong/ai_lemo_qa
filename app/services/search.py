"""网络搜索服务 - 集成SearXNG"""
import requests
from typing import List, Dict, Optional
from app.core.config import get_settings
from loguru import logger

settings = get_settings()


class SearchService:
    """网络搜索服务类"""
    
    def __init__(self):
        # 使用localhost访问（后端在宿主机运行）
        self.searxng_url = "http://localhost:8888"
        self.timeout = 10
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """使用SearXNG搜索
        
        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            
        Returns:
            搜索结果列表 [{"title": "", "url": "", "content": ""}]
        """
        try:
            logger.info(f"SearXNG搜索: {query}")
            
            response = requests.get(
                f"{self.searxng_url}/search",
                params={
                    "q": query,
                    "format": "json",
                    "language": "zh-CN"
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"SearXNG搜索失败: HTTP {response.status_code}")
                return []
            
            data = response.json()
            raw_results = data.get("results", [])
            
            # 格式化结果
            results = []
            for r in raw_results[:max_results]:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:300],  # 限制长度
                    "engine": r.get("engine", "unknown")
                })
            
            logger.info(f"找到 {len(results)} 条搜索结果")
            return results
            
        except requests.exceptions.Timeout:
            logger.error("SearXNG搜索超时")
            return []
        except Exception as e:
            logger.error(f"SearXNG搜索异常: {e}")
            return []
    
    def format_search_context(self, results: List[Dict[str, str]]) -> str:
        """将搜索结果格式化为上下文
        
        Args:
            results: 搜索结果列表
            
        Returns:
            格式化的上下文文本
        """
        if not results:
            return ""
        
        context_parts = []
        for i, r in enumerate(results, 1):
            context_parts.append(
                f"[搜索结果{i}]\n"
                f"标题：{r['title']}\n"
                f"来源：{r['url']}\n"
                f"摘要：{r['content']}"
            )
        
        return "\n\n".join(context_parts)


# 创建全局实例
search_service = SearchService()

