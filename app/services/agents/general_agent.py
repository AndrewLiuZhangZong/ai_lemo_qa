"""
通用 Agent

处理所有非专业领域的问题
使用 LangChain + Ollama + 多种工具
"""

import datetime
from typing import List, Dict, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain.tools import Tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from loguru import logger
import time

from .base import BaseAgent
from app.core.config import get_settings
from app.services.custom_tools import get_all_tools

settings = get_settings()


class GeneralAgent(BaseAgent):
    """通用 Agent（使用 LangChain）"""
    
    def __init__(self):
        """初始化通用 Agent"""
        super().__init__(
            name="通用助手",
            description="处理知识库查询、计算、百科等通用问题"
        )
        
        # 初始化 LLM
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.7,
            num_predict=2048,
        )
        
        # 初始化工具
        self.tools = self._init_tools()
        
        # 创建 Agent
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            max_execution_time=60,
            handle_parsing_errors=True,
            early_stopping_method="generate",
            return_intermediate_steps=True,
        )
        
        logger.info(f"✅ {self.name} 初始化完成，加载了 {len(self.tools)} 个工具")
    
    def _init_tools(self) -> List[Tool]:
        """初始化所有工具"""
        tools = []
        
        # 1. 自定义工具（知识库、日期时间、计算器）
        custom_tools = get_all_tools()
        tools.extend(custom_tools)
        logger.info(f"  - 加载自定义工具: {len(custom_tools)} 个")
        
        # 2. 维基百科工具
        try:
            wikipedia_wrapper = WikipediaAPIWrapper(
                lang="zh",
                top_k_results=2,
                doc_content_chars_max=500
            )
            wikipedia_tool = WikipediaQueryRun(
                name="维基百科",
                api_wrapper=wikipedia_wrapper,
                description="""
                查询维基百科获取百科知识。
                适用于：历史事件、人物介绍、科学概念、地理信息等百科类问题。
                输入：查询关键词（中文）
                输出：维基百科词条摘要
                """
            )
            tools.append(wikipedia_tool)
            logger.info("  - 加载维基百科工具")
        except Exception as e:
            logger.warning(f"  - 维基百科工具加载失败: {e}")
        
        return tools
    
    def _create_agent(self):
        """创建 React Agent"""
        template = """你是一个智能助手，可以使用工具来帮助用户。

可用工具：
{tools}

工具名称：{tool_names}

重要规则：
1. 公司业务问题 → 优先使用"知识库查询"
2. 日期时间问题 → 使用"日期时间查询"
3. 数学计算 → 使用"计算器"
4. 百科知识 → 使用"维基百科"
5. **最多使用2个工具**，然后必须给出最终回答

格式（严格遵守）：
Question: 用户问题
Thought: 我需要什么工具
Action: 工具名
Action Input: 参数
Observation: 结果
Thought: 我现在可以回答了
Final Answer: 中文回答

开始！

Question: {input}
Thought: {agent_scratchpad}"""
        
        prompt = PromptTemplate.from_template(template)
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )
        
        return agent
    
    async def can_handle(self, message: str) -> tuple[bool, float]:
        """
        通用 Agent 可以处理任何问题（兜底）
        
        Returns:
            (True, 0.5)  # 低优先级
        """
        return True, 0.5  # 低优先级，作为兜底
    
    async def chat(
        self,
        message: str,
        chat_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        使用 LangChain Agent 处理聊天
        """
        logger.info(f"[通用Agent] 收到问题: {message}")
        
        try:
            # 调用 Agent
            result = self.agent_executor.invoke({"input": message})
            
            # 提取回答
            answer = result.get("output", "抱歉，我无法回答这个问题。")
            
            # 提取使用的工具
            tools_used = []
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if len(step) >= 1:
                        action = step[0]
                        tool_name = getattr(action, "tool", "未知工具")
                        tools_used.append(tool_name)
            
            logger.info(f"[通用Agent] 使用工具: {tools_used}")
            logger.info(f"[通用Agent] 回答: {answer[:100]}...")
            
            return {
                "answer": answer,
                "answer_source": "general_agent",
                "confidence": 0.8,
                "tools_used": tools_used
            }
        
        except Exception as e:
            logger.error(f"[通用Agent] 执行失败: {e}")
            return {
                "answer": "抱歉，处理您的问题时出现了错误，请稍后重试。",
                "answer_source": "error",
                "confidence": 0.0,
                "tools_used": []
            }


# 单例
_general_agent_instance: Optional[GeneralAgent] = None


def get_general_agent() -> GeneralAgent:
    """获取通用 Agent 单例"""
    global _general_agent_instance
    if _general_agent_instance is None:
        _general_agent_instance = GeneralAgent()
    return _general_agent_instance

