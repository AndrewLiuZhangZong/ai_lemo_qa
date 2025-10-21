"""配置管理模块"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "AI智能客服问答系统"
    APP_VERSION: str = "0.1.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    DEBUG: bool = True
    
    # PostgreSQL配置
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ai_lemo_qa"
    POSTGRES_USER: str = "lemo_user"
    POSTGRES_PASSWORD: str = "lemo_password_2024"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redis_password_2024"
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Milvus配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION_NAME: str = "knowledge_embeddings"
    
    # Ollama配置
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"  # 对话模型
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"  # Embedding模型
    OLLAMA_TIMEOUT: int = 60
    
    # Embedding配置
    EMBEDDING_DIMENSION: int = 768  # nomic-embed-text的embedding维度
    
    # SearXNG搜索引擎配置
    SEARXNG_URL: str = "http://localhost:8888"  # SearXNG服务地址
    SEARXNG_TIMEOUT: int = 10  # 搜索超时时间(秒)
    SEARXNG_MAX_RESULTS: int = 3  # 最大搜索结果数
    
    # 业务配置
    CONFIDENCE_THRESHOLD: float = 0.7  # 答案置信度阈值
    CONFIDENCE_THRESHOLD_WEB_SEARCH: float = 0.2  # 启用网络搜索的置信度阈值
    MAX_CONTEXT_TURNS: int = 5  # 最大上下文轮数
    SESSION_TIMEOUT: int = 1800  # 会话超时时间(秒)
    SIMILAR_QUESTIONS_COUNT: int = 3  # 推荐相似问题数量
    
    # LangChain Agent 配置
    ENABLE_AGENT: bool = True  # 是否启用Agent模式
    AGENT_MAX_ITERATIONS: int = 5  # Agent最大迭代次数
    AGENT_MAX_EXECUTION_TIME: int = 60  # Agent最大执行时间（秒）
    AGENT_VERBOSE: bool = True  # 是否显示Agent思考过程
    
    # CORS配置
    CORS_ORIGINS: list = ["*"]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()

