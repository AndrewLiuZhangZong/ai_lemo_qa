"""
LangChain Agent 服务
"""
from typing import List, Dict, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from loguru import logger

from app.core.config import get_settings
from app.services.tools import get_all_tools

settings = get_settings()


class AgentService:
    """LangChain Agent 服务"""
    
    def __init__(self):
        """初始化 Agent"""
        # 初始化 LLM（使用标准 Ollama LLM）
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.7,
            num_predict=2048,  # 最大输出token数
        )
        
        # 初始化工具
        self.tools = self._init_tools()
        
        # 创建 Agent
        self.agent = self._create_agent()
        
        # 创建 Agent Executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,  # 显示思考过程
            max_iterations=5,  # 最大迭代次数
            max_execution_time=60,  # 最大执行时间（秒）
            handle_parsing_errors=True,  # 处理解析错误
            early_stopping_method="generate",  # 达到限制时强制生成回答
            return_intermediate_steps=True,  # 返回中间步骤
        )
        
        logger.info(f"✅ Agent 初始化完成，加载了 {len(self.tools)} 个工具")
    
    def _init_tools(self) -> List[Tool]:
        """初始化所有工具"""
        tools = []
        
        # 1. 自定义工具（知识库、日期时间、计算器）
        custom_tools = get_all_tools()
        tools.extend(custom_tools)
        logger.info(f"  - 加载自定义工具: {len(custom_tools)} 个")
        
        # 2. 网络搜索工具（DuckDuckGo - 免费，带错误处理）
        try:
            from langchain.tools import Tool
            
            def safe_duckduckgo_search(query: str) -> str:
                """安全的 DuckDuckGo 搜索，带错误处理"""
                try:
                    from duckduckgo_search import DDGS
                    import time
                    
                    # 添加延迟避免频率限制
                    time.sleep(1)
                    
                    with DDGS() as ddgs:
                        results = list(ddgs.text(query, max_results=3))
                        
                    if results:
                        formatted = []
                        for r in results:
                            formatted.append(f"标题: {r.get('title', 'N/A')}\n内容: {r.get('body', 'N/A')}\n链接: {r.get('href', 'N/A')}")
                        return "\n\n".join(formatted)
                    else:
                        return "未找到搜索结果。"
                        
                except Exception as e:
                    error_msg = str(e)
                    if "Ratelimit" in error_msg or "202" in error_msg:
                        return "搜索服务暂时繁忙（频率限制），请稍后再试。建议：1) 稍等片刻后重试 2) 使用更具体的关键词 3) 尝试其他信息源。"
                    else:
                        return f"网络搜索暂时不可用：{error_msg}。建议使用其他方式获取信息。"
            
            search_tool = Tool(
                name="网络搜索",
                func=safe_duckduckgo_search,
                description="""
                在互联网上搜索最新信息。
                适用于：实时新闻、天气、股票价格、最新事件等需要网络查询的问题。
                输入：搜索关键词
                输出：搜索结果摘要
                注意：如果遇到频率限制，建议使用其他工具或告知用户稍后重试。
                """
            )
            tools.append(search_tool)
            logger.info("  - 加载 DuckDuckGo 搜索工具（带容错）")
        except Exception as e:
            logger.warning(f"  - DuckDuckGo 工具加载失败: {e}")
        
        # 3. 维基百科工具（免费）
        try:
            wikipedia_wrapper = WikipediaAPIWrapper(
                lang="zh",
                top_k_results=2,
                doc_content_chars_max=2000
            )
            wiki_tool = WikipediaQueryRun(
                api_wrapper=wikipedia_wrapper,
                name="维基百科",
                description="""
                查询维基百科获取百科知识。
                适用于：历史事件、人物传记、科学概念、地理信息等百科类问题。
                输入：要查询的主题
                输出：维基百科条目内容
                """
            )
            tools.append(wiki_tool)
            logger.info("  - 加载维基百科工具")
        except Exception as e:
            logger.warning(f"  - 维基百科工具加载失败: {e}")
        
        return tools
    
    def _create_agent(self):
        """创建 React Agent"""
        # 定义系统提示词（React格式）- 简化版
        template = """你是一个智能助手，可以使用工具来帮助用户。

可用工具：
{tools}

工具名称：{tool_names}

重要规则：
1. 天气、新闻等实时信息 → 使用"网络搜索"
2. 百科知识 → 使用"维基百科"
3. 日期时间 → 使用"日期时间查询"
4. 计算 → 使用"计算器"
5. 公司业务 → 使用"知识库查询"
6. **如果工具返回错误或无结果，直接告知用户，不要重复尝试**
7. **最多使用2个工具，然后必须给出最终回答**

格式（严格遵守）：
Question: 用户问题
Thought: 我需要使用什么工具
Action: 工具名
Action Input: 工具参数
Observation: 工具结果
Thought: 我现在可以回答了
Final Answer: 中文回答

开始！

Question: {input}
Thought: {agent_scratchpad}"""
        
        # 创建提示模板
        prompt = PromptTemplate.from_template(template)
        
        # 创建 React Agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )
        
        return agent
    
    async def chat(
        self, 
        message: str, 
        chat_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Agent 聊天
        
        Args:
            message: 用户消息
            chat_history: 对话历史（暂不使用）
            
        Returns:
            {
                "answer": "回答内容",
                "tool_used": "使用的工具",
                "confidence": 置信度
            }
        """
        try:
            logger.info(f"[Agent] 收到问题: {message}")
            
            # 执行 Agent (React agent 不需要 chat_history 参数)
            response = await self.agent_executor.ainvoke({
                "input": message
            })
            
            answer = response.get("output", "抱歉，我无法回答这个问题。")
            
            # 分析使用了哪些工具
            intermediate_steps = response.get("intermediate_steps", [])
            tools_used = []
            if intermediate_steps:
                for step in intermediate_steps:
                    if hasattr(step[0], 'tool'):
                        tools_used.append(step[0].tool)
            
            logger.info(f"[Agent] 使用工具: {tools_used}")
            logger.info(f"[Agent] 回答: {answer[:100]}...")
            
            # 判断答案来源
            answer_source = self._determine_source(tools_used)
            
            # 计算置信度（简单策略）
            confidence = 0.8 if tools_used else 0.5
            if "知识库查询" in tools_used:
                confidence = 0.9
            
            return {
                "answer": answer,
                "tools_used": tools_used,
                "answer_source": answer_source,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"[Agent] 执行失败: {e}")
            return {
                "answer": f"抱歉，处理您的问题时出现错误：{str(e)}",
                "tools_used": [],
                "answer_source": "error",
                "confidence": 0.0
            }
    
    def _determine_source(self, tools_used: List[str]) -> str:
        """判断答案来源"""
        if "知识库查询" in tools_used:
            return "knowledge_base"
        elif "网络搜索" in tools_used:
            return "web_search"
        elif "维基百科" in tools_used:
            return "wikipedia"
        elif any(tool in tools_used for tool in ["计算器", "日期时间查询"]):
            return "tool"
        else:
            return "general_ai"


# 全局 Agent 实例
agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """获取 Agent 服务实例（单例）"""
    global agent_service
    if agent_service is None:
        agent_service = AgentService()
    return agent_service

