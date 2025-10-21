# AI智能客服问答系统

基于大语言模型（LLM）+ 向量检索的智能客服问答系统，支持本地部署。

## 技术栈

- **后端框架**: FastAPI
- **语言模型**: Ollama (Qwen2.5-7B)
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

## 下一步

- [ ] 安装Python依赖
- [ ] 开发API服务
- [ ] 实现知识库管理功能
- [ ] 集成Embedding模型
- [ ] 实现问答核心逻辑
- [ ] 开发前端界面

## 项目结构

```
ai_lemo_qa/
├── config/              # 配置文件
│   └── milvus.yaml     # Milvus配置
├── scripts/            # 初始化脚本
│   └── init.sql        # 数据库初始化
├── docker-compose.yml  # Docker编排文件
├── .env                # 环境变量（不提交到Git）
├── .env.example        # 环境变量示例
├── .gitignore          # Git忽略文件
├── 需求文档.md          # 项目需求文档
└── README.md           # 本文件
```

## 许可证

MIT License

