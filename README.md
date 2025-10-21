# AI智能客服问答系统

基于大语言模型（LLM）+ 向量检索的智能客服问答系统，支持本地部署。

## 技术栈

- **后端框架**: FastAPI
- **语言模型**: Ollama (Qwen3-8B)
- **向量数据库**: Milvus
- **关系数据库**: PostgreSQL 16
- **缓存**: Redis 7
- **LLM框架**: LangChain
- **容器化**: Docker + Docker Compose

## 快速开始

### 1. 环境准备

确保已安装：
- Docker Desktop
- Python 3.9+
- Ollama（已安装Qwen模型）

### 2. 启动数据库服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3. 验证服务

```bash
# 验证PostgreSQL
docker exec -it ai_lemo_postgres psql -U lemo_user -d ai_lemo_qa -c "SELECT COUNT(*) FROM knowledge_base;"

# 验证Redis
docker exec -it ai_lemo_redis redis-cli -a redis_password_2024 ping

# 验证Milvus（等待1-2分钟启动）
curl http://localhost:9091/healthz
```

### 4. 访问管理界面

- **Milvus管理界面 (Attu)**: http://localhost:8000
- **MinIO控制台**: http://localhost:9001 (用户名/密码: minioadmin/minioadmin)

## 服务端口

| 服务 | 端口 | 说明 |
|-----|------|------|
| PostgreSQL | 5432 | 关系数据库 |
| Redis | 6379 | 缓存服务 |
| Milvus | 19530 | 向量数据库API |
| Milvus Metrics | 9091 | Milvus监控端点 |
| Attu | 8000 | Milvus Web管理界面 |
| MinIO | 9000 | 对象存储API |
| MinIO Console | 9001 | MinIO Web控制台 |
| Etcd | 2379 | 元数据存储 |
| Ollama | 11434 | 本地LLM服务 |

## Docker命令速查

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器和数据卷（注意：会删除所有数据）
docker-compose down -v

# 重启特定服务
docker-compose restart milvus

# 查看日志
docker-compose logs -f [service_name]

# 进入容器
docker exec -it ai_lemo_postgres bash
docker exec -it ai_lemo_milvus bash
```

## 数据库说明

### PostgreSQL数据表

- `knowledge_base`: 知识库（问答对）
- `conversation_history`: 对话历史
- `user_feedback`: 用户反馈
- `system_config`: 系统配置
- `sensitive_words`: 敏感词表

### 初始数据

系统已自动初始化10条示例知识库数据，涵盖：
- 售后服务（退货、换货）
- 支付问题
- 物流配送
- 订单管理
- 账号问题
- 会员权益
- 客服咨询

## 开发指南

### 环境配置

1. 复制环境变量文件：
```bash
cp .env.example .env
```

2. 根据需要修改`.env`中的配置

### Python环境设置

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装依赖（后续步骤）
pip install -r requirements.txt
```

## 故障排查

### Milvus启动失败

```bash
# 检查依赖服务
docker-compose ps etcd minio

# 查看Milvus日志
docker-compose logs milvus

# 重启Milvus
docker-compose restart milvus
```

### PostgreSQL连接失败

```bash
# 检查服务状态
docker-compose ps postgres

# 测试连接
docker exec -it ai_lemo_postgres psql -U lemo_user -d ai_lemo_qa
```

### 重置所有数据

```bash
# 停止并删除所有容器和数据卷
docker-compose down -v

# 重新启动
docker-compose up -d
```

## 应用运行

### 后端API服务

```bash
# 进入项目根目录
cd ai_lemo_qa

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 启动后端服务
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

访问：
- API服务：http://localhost:8080
- API文档：http://localhost:8080/docs

### 前端界面

```bash
# 进入前端目录
cd frontend

# 首次运行需要安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问：http://localhost:3000

### 功能特性

#### 智能问答
- 💬 实时聊天对话
- 🤖 AI智能回答
- 📊 置信度显示
- 🔍 意图识别
- 💡 相关问题推荐

#### 知识库管理
- 📚 知识列表浏览
- ➕ 添加新知识
- ✏️ 编辑现有知识
- 🗑️ 删除知识
- 🔎 关键词搜索
- 📄 分页展示

## 项目结构

```
ai_lemo_qa/
├── app/                        # 后端应用
│   ├── api/v1/                 # API路由
│   │   ├── chat.py             # 问答接口
│   │   ├── knowledge.py        # 知识库接口
│   │   └── feedback.py         # 反馈接口
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   └── logger.py           # 日志配置
│   ├── models/                 # 数据模型
│   │   ├── knowledge.py        # 知识库模型
│   │   ├── conversation.py     # 对话历史模型
│   │   └── feedback.py         # 反馈模型
│   ├── schemas/                # Pydantic数据验证
│   │   ├── chat.py
│   │   ├── knowledge.py
│   │   └── feedback.py
│   ├── services/               # 业务服务
│   │   ├── embedding.py        # Embedding向量化
│   │   ├── milvus.py           # 向量检索
│   │   ├── llm.py              # LLM对话
│   │   └── chat.py             # 问答逻辑
│   └── main.py                 # FastAPI入口
├── frontend/                   # Vue3前端
│   ├── src/
│   │   ├── api/                # API封装
│   │   ├── views/              # 页面组件
│   │   │   ├── ChatView.vue    # 聊天页面
│   │   │   └── KnowledgeView.vue # 知识库管理
│   │   ├── router/             # 路由配置
│   │   ├── App.vue             # 根组件
│   │   └── main.js             # 入口文件
│   ├── package.json            # 依赖配置
│   └── vite.config.js          # Vite配置
├── config/                     # 配置文件
│   └── milvus.yaml
├── scripts/                    # 初始化脚本
│   ├── init.sql                # 数据库初始化
│   └── init_milvus.py          # Milvus初始化
├── docker-compose.yml          # Docker编排
├── requirements.txt            # Python依赖
├── .env                        # 环境变量
├── 需求文档.md
├── 开发计划.md
└── README.md
```

## 许可证

MIT License

