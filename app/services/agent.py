"""
LangChain Agent 服务
"""
from typing import List, Dict, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama
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
        # 初始化 LLM
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.7,
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
        )
        
        logger.info(f"✅ Agent 初始化完成，加载了 {len(self.tools)} 个工具")
    
    def _init_tools(self) -> List[Tool]:
        """初始化所有工具"""
        tools = []
        
        # 1. 自定义工具（知识库、日期时间、计算器）
        custom_tools = get_all_tools()
        tools.extend(custom_tools)
        logger.info(f"  - 加载自定义工具: {len(custom_tools)} 个")
        
        # 2. 网络搜索工具（DuckDuckGo - 免费）
        try:
            search_tool = DuckDuckGoSearchRun(
                name="网络搜索",
                description="""
                在互联网上搜索最新信息。
                适用于：实时新闻、天气、股票价格、最新事件等需要网络查询的问题。
                输入：搜索关键词
                输出：搜索结果摘要
                """
            )
            tools.append(search_tool)
            logger.info("  - 加载 DuckDuckGo 搜索工具")
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
        # 定义系统提示词（React格式）
        template = """你是一个智能客服助手，能够使用多种工具来帮助用户解决问题。

你可以使用以下工具：

{tools}

请按照以下步骤思考和行动：

1. **理解问题**：仔细分析用户的问题
2. **选择工具**：
   - 如果是公司业务问题（退货、订单、产品等）→ 使用"知识库查询"
   - 如果是日期时间问题 → 使用"日期时间查询"
   - 如果是数学计算 → 使用"计算器"
   - 如果需要实时信息（天气、新闻等）→ 使用"网络搜索"
   - 如果是百科知识 → 使用"维基百科"
3. **执行工具**：调用合适的工具获取信息
4. **生成回答**：基于工具返回的结果，生成自然、友好的回答

注意：
- 优先使用知识库查询回答公司业务问题
- 如果知识库没有答案，再考虑其他工具
- 回答要准确、专业、友好
- 如果所有工具都无法解决问题，礼貌地告知用户

使用以下格式（严格遵守）：

Question: 用户的输入问题
Thought: 我应该思考如何解决这个问题
Action: 要使用的工具名称（从上面的工具列表中选择）
Action Input: 工具的输入参数
Observation: 工具的返回结果
... (可以重复 Thought/Action/Action Input/Observation 多次)
Thought: 我现在知道最终答案了
Final Answer: 给用户的最终回答（用中文回答，要友好专业）

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

