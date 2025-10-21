# 🎯 多Agent架构使用指南

## ✨ 架构概览

系统现在采用**可扩展的多Agent架构**，支持自动路由到专业Agent处理不同类型的问题。

```
AgentManager (自动路由)
├── 天气专家Agent → 处理天气查询
└── 通用助手Agent → 处理其他问题（知识库、计算、百科等）
```

### 🔄 工作流程

1. **用户提问** → Agent Manager
2. **智能路由** → 根据问题内容自动选择最合适的Agent
3. **工具链串联** → Agent调用多个工具完成任务
4. **返回结果** → 生成友好的回答

---

## 🌤️ 天气Agent使用指南

### 功能特性

- ✅ **工具链串联**：时间解析 → 地点解析 → 天气API查询
- ✅ **智能识别**：自动识别天气相关问题
- ✅ **详细信息**：温度、体感、风力、湿度、能见度等
- ✅ **中文支持**：支持中文城市名称查询

### 第一步：注册和风天气API

1. **访问官网**
   ```
   https://dev.qweather.com/
   ```

2. **注册账号**
   - 点击"免费注册"
   - 填写邮箱和密码
   - 验证邮箱

3. **创建应用**
   - 登录后进入"控制台"
   - 点击"创建项目"
   - 项目名称：`ai_lemo_qa`（或任意名称）
   - 点击"创建应用"
   - 应用名称：`天气查询`（或任意名称）
   - **选择方案**：`免费订阅` （每天1000次请求）
   - 提交

4. **获取API Key**
   - 进入"应用管理"
   - 复制 `KEY` 值（形如：`a1b2c3d4e5f6g7h8i9j0`）

5. **配置到系统**
   
   编辑 `.env` 文件，添加：
   ```bash
   # 和风天气 API 配置
   QWEATHER_API_KEY=你的API_KEY
   ```
   
   **示例**：
   ```bash
   QWEATHER_API_KEY=a1b2c3d4e5f6g7h8i9j0
   ```

6. **重启服务**
   ```bash
   # 停止现有服务
   lsof -ti:8080 | xargs kill -9
   
   # 启动服务
   cd /Users/edy/PycharmProjects/ai_lemo_qa
   source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   ```

---

### 第二步：测试天气查询

#### 测试用例

1. **基础查询**
   ```
   北京的天气怎么样？
   上海今天天气如何？
   广州市的天气
   ```

2. **带区县查询**
   ```
   北京市通州区天气
   上海浦东新区的天气
   ```

3. **自然语言查询**
   ```
   今天北京冷不冷？
   上海需要带伞吗？
   广州今天气温多少？
   ```

#### 预期返回格式

```
今天（2025年10月21日）北京的天气情况如下：

🌡️ **温度**：20°C（体感 18°C）
🌤️  **天气**：晴
💨 **风力**：西北风 3级
💧 **湿度**：45%
👁️  **能见度**：10 km

数据更新时间：2025-10-21T19:30:00+08:00
```

#### 路由日志

查看日志可以看到Agent的路由过程：
```
[路由] 天气专家: can_handle=True, confidence=0.90
🎯 路由到专业 Agent: 天气专家 (置信度=0.90)
[工具链-1] 时间上下文: 今天（2025年10月21日）
[工具链-2] 提取城市: 北京
🌍 找到城市: 北京 (ID: 101010100)
🌤️  获取天气成功: 北京 20°C 晴
```

---

## 🤖 通用Agent功能

通用Agent继续保留原有功能，处理非天气类问题：

### 功能列表

1. **知识库查询**
   ```
   如何退货？
   订单怎么查询？
   产品有哪些功能？
   ```

2. **日期时间**
   ```
   今天几号？
   现在几点？
   ```

3. **数学计算**
   ```
   123 * 456 等于多少？
   (100 + 50) / 2
   ```

4. **百科知识**
   ```
   介绍一下人工智能
   什么是区块链？
   ```

---

## 🔧 扩展新Agent（开发者指南）

### 1. 创建新的Agent

在 `app/services/agents/` 目录下创建新文件，例如 `order_agent.py`：

```python
from typing import Dict, List, Optional
from .base import BaseAgent
from loguru import logger

class OrderAgent(BaseAgent):
    """订单处理专家Agent"""
    
    def __init__(self):
        super().__init__(
            name="订单专家",
            description="专门处理订单查询、退货等订单相关问题"
        )
        # 初始化工具...
    
    async def can_handle(self, message: str) -> tuple[bool, float]:
        """判断是否为订单相关问题"""
        keywords = ["订单", "退货", "物流", "快递"]
        if any(kw in message for kw in keywords):
            return True, 0.8
        return False, 0.0
    
    async def chat(self, message: str, chat_history: Optional[List[Dict]] = None) -> Dict:
        """处理订单问题"""
        # 工具链逻辑...
        return {
            "answer": "...",
            "answer_source": "order_agent",
            "confidence": 0.9,
            "tools_used": []
        }
```

### 2. 注册到Manager

在 `app/services/chat.py` 中注册：

```python
from .agents.order_agent import get_order_agent

# 注册订单Agent
agent_manager.register_agent(get_order_agent())
```

### 3. 自动路由

系统会自动根据 `can_handle()` 方法的返回值选择最合适的Agent。

---

## 📊 监控和调试

### 查看Agent路由日志

```bash
tail -f logs/app_$(date +%Y-%m-%d).log | grep "路由"
```

### 查看工具调用链

```bash
tail -f logs/app_$(date +%Y-%m-%d).log | grep "工具链"
```

### 查看Agent执行情况

```bash
tail -f logs/app_$(date +%Y-%m-%d).log | grep "Agent"
```

---

## ❓ 常见问题

### Q1: 天气查询返回"API Key未配置"

**解决方案**：
1. 确认已在 `.env` 文件中配置 `QWEATHER_API_KEY`
2. 确认Key没有多余空格
3. 重启服务

### Q2: 天气查询返回"未找到城市"

**解决方案**：
1. 检查城市名称拼写
2. 尝试使用全名（如：北京市、上海市）
3. 区县查询：北京市通州区

### Q3: 如何查看哪个Agent处理了我的问题？

查看日志中的 `[Agent模式] 完成` 行：
```
[Agent模式] 完成: agent=天气专家, ...
```

### Q4: 为什么天气问题被通用Agent处理了？

如果置信度不够高（< 0.5），会fallback到通用Agent。可以：
1. 使用更明确的关键词（天气、气温等）
2. 完整的城市名称

### Q5: 可以添加未来天气预报吗？

可以！在 `weather_tool.py` 中添加 `get_weather_forecast()` 方法，
然后在 `WeatherAgent` 中识别"明天"、"未来"等关键词。

---

## 🎉 优势总结

### 相比之前的改进

| 方面 | 之前 | 现在 |
|------|------|------|
| **架构** | 单一Agent | 多专业Agent + 自动路由 |
| **天气查询** | 依赖DuckDuckGo（频率限制） | 专业天气API（稳定） |
| **扩展性** | 较难扩展 | 易于添加新Agent |
| **精准度** | 通用处理 | 专业Agent专项优化 |
| **响应** | "无法回答" | 详细结构化数据 |

### 工具链串联示例

**天气查询流程**：
```
用户: "北京今天冷不冷？"
  ↓
AgentManager: 路由到"天气专家" (置信度 0.9)
  ↓
工具链-1: 时间解析 → "今天（2025-10-21）"
  ↓
工具链-2: 地点解析 → "北京"
  ↓
工具链-3: 天气API → 调用和风天气
  ↓
返回: "今天北京20°C，晴，不冷..."
```

---

## 📚 下一步扩展建议

1. **订单Agent** - 处理订单查询、物流追踪
2. **产品Agent** - 产品推荐、参数对比
3. **客服Agent** - 售后服务、投诉处理
4. **数据分析Agent** - 销售数据、用户行为分析

每个Agent都可以有自己的工具链和专业知识！

---

**祝使用愉快！** 🚀

如有问题，请查看日志或联系开发团队。

