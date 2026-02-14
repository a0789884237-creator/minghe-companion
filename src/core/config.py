"""Configuration management for Minghe Companion."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # API Keys
    zhipu_api_key: str = Field(default="", description="智谱GLM API密钥")
    deepseek_api_key: Optional[str] = Field(
        default=None, description="DeepSeek API密钥"
    )
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API密钥")

    # 数据库
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/minghe",
        description="PostgreSQL数据库连接",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis连接")

    # 服务配置
    api_host: str = Field(default="0.0.0.0", description="API服务主机")
    api_port: int = Field(default=8000, description="API服务端口")
    api_debug: bool = Field(default=False, description="调试模式")

    # 日志
    log_level: str = Field(default="INFO", description="日志级别")

    # Agent配置
    max_conversation_turns: int = Field(default=50, description="最大对话轮次")
    short_term_memory_tokens: int = Field(default=8000, description="短期记忆token数")

    # 知识库
    knowledge_base_path: str = Field(default="knowledge_base", description="知识库路径")
    crisis_keywords_path: str = Field(
        default="knowledge_base/crisis_keywords.json", description="危机关键词文件"
    )

    # 安全
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="CORS允许的来源",
    )
    session_timeout: int = Field(default=3600, description="会话超时秒数")
    rate_limit_per_minute: int = Field(default=60, description="每分钟请求限制")

    @property
    def allowed_origins_list(self) -> list[str]:
        """获取允许的来源列表。"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """是否生产环境。"""
        return not self.api_debug


@lru_cache
def get_settings() -> Settings:
    """获取配置单例。"""
    return Settings()


# 全局配置实例
settings = get_settings()
