"""
LangChain 自定义工具定义
"""
from typing import Optional, Type
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field
from loguru import logger

from app.services.milvus import milvus_service
from app.services.embedding import embedding_service
from app.models.knowledge import Knowledge
from app.core.database import get_db
from sqlalchemy import select


class KnowledgeBaseInput(BaseModel):
    """知识库查询输入"""
    query: str = Field(description="要查询的问题")


class KnowledgeBaseTool(BaseTool):
    """知识库查询工具"""
    name: str = "知识库查询"
    description: str = """
    查询公司内部知识库，获取客服相关问题的标准答案。
    适用于：退货政策、订单查询、产品信息、售后服务等公司业务相关问题。
    输入：用户的问题
    输出：知识库中的相关答案
    """
    args_schema: Type[BaseModel] = KnowledgeBaseInput
    
    def _run(
        self, 
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """同步执行（LangChain 要求）"""
        try:
            logger.info(f"[知识库工具] 查询: {query}")
            
            # 1. 获取问题向量
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            question_embedding = loop.run_until_complete(
                embedding_service.get_embedding(query)
            )
            
            # 2. 在 Milvus 中搜索
            matches = loop.run_until_complete(
                milvus_service.search(question_embedding, top_k=3)
            )
            
            if not matches:
                return "知识库中未找到相关信息。"
            
            # 3. 获取知识详情
            knowledge_ids = [match[0] for match in matches]
            
            # 使用同步数据库连接
            from app.core.database import SessionLocal
            db = SessionLocal()
            try:
                result = db.execute(
                    select(Knowledge).where(
                        Knowledge.id.in_(knowledge_ids),
                        Knowledge.status == 1
                    )
                )
                knowledge_list = result.scalars().all()
                
                # 构建知识库映射
                knowledge_map = {k.id: k for k in knowledge_list}
                
                # 4. 构建结果
                results = []
                for kid, score in matches:
                    if kid in knowledge_map:
                        k = knowledge_map[kid]
                        # 计算标准化相似度
                        baseline = 0.58
                        raw = float(score)
                        normalized_score = max(0.0, (raw - baseline) / (1.0 - baseline)) if raw >= baseline else 0.0
                        
                        if normalized_score >= 0.2:  # 只返回相关度较高的
                            results.append(f"问题：{k.question}\n答案：{k.answer}\n相似度：{normalized_score:.2%}")
                
                if results:
                    return "\n\n".join(results)
                else:
                    return "知识库中未找到足够相关的信息。"
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"[知识库工具] 查询失败: {e}")
            return f"查询知识库时出错: {str(e)}"


class CalculatorInput(BaseModel):
    """计算器输入"""
    expression: str = Field(description="要计算的数学表达式，例如：2+2*3")


class CalculatorTool(BaseTool):
    """计算器工具"""
    name: str = "计算器"
    description: str = """
    执行数学计算。
    可以计算：加减乘除、幂运算、三角函数等。
    输入：数学表达式，例如 "2+2*3" 或 "sqrt(16)"
    输出：计算结果
    """
    args_schema: Type[BaseModel] = CalculatorInput
    
    def _run(
        self,
        expression: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """执行计算"""
        try:
            import math
            import re
            
            # 安全的数学函数
            safe_dict = {
                'abs': abs, 'round': round,
                'sqrt': math.sqrt, 'pow': math.pow,
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'log': math.log, 'log10': math.log10,
                'exp': math.exp, 'pi': math.pi, 'e': math.e,
            }
            
            # 清理表达式
            expression = re.sub(r'[^0-9+\-*/().a-z ]', '', expression.lower())
            
            # 计算
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return f"计算结果：{result}"
            
        except Exception as e:
            return f"计算错误：{str(e)}"


class DateTimeInput(BaseModel):
    """日期时间查询输入"""
    query: str = Field(description="要查询的日期时间问题")


class DateTimeTool(BaseTool):
    """日期时间工具"""
    name: str = "日期时间查询"
    description: str = """
    获取当前日期、时间、星期等信息。
    适用于：查询今天日期、现在几点、星期几等问题。
    输入：日期时间相关的问题
    输出：当前的日期时间信息
    """
    args_schema: Type[BaseModel] = DateTimeInput
    
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """获取日期时间"""
        from datetime import datetime
        
        now = datetime.now()
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        
        return f"""当前时间信息：
日期：{now.strftime('%Y年%m月%d日')}
时间：{now.strftime('%H:%M:%S')}
星期：{weekdays[now.weekday()]}
"""


# 导出所有工具
def get_all_tools():
    """获取所有可用工具"""
    return [
        KnowledgeBaseTool(),
        DateTimeTool(),
        CalculatorTool(),
    ]

