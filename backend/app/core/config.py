"""
配置管理模块（运营数据分析独立版）
"""
from typing import List, Optional, Union
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, computed_field


class Settings(BaseSettings):
    """系统配置类"""
    
    # 基础配置
    APP_NAME: str = Field(default="运营数据分析系统", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # 数据库配置
    # 如果提供了 DATABASE_URL，直接使用；否则从组件构建
    DATABASE_URL: Optional[str] = Field(
        default=None,
        env="DATABASE_URL"
    )
    
    # 数据库组件配置（用于构建 DATABASE_URL）
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="password", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(default="operation_analysis", env="POSTGRES_DB")
    POSTGRES_HOST: str = Field(default="postgres", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    
    # Redis配置（可选）
    REDIS_URL: str = Field(default="redis://redis:6379/0", env="REDIS_URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # JWT配置
    JWT_SECRET: str = Field(
        default="your-super-secret-jwt-key-change-this",
        env="JWT_SECRET"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRE_HOURS: int = Field(default=24, env="JWT_EXPIRE_HOURS")
    
    # Session配置
    SESSION_SECRET: str = Field(
        default="your-super-secret-session-key-change-this",
        env="SESSION_SECRET"
    )
    SESSION_EXPIRE_HOURS: int = Field(default=24, env="SESSION_EXPIRE_HOURS")
    
    # AI工作流配置（可选，可通过管理界面配置）
    DIFY_API_KEY: Optional[str] = Field(default=None, env="DIFY_API_KEY")
    DIFY_API_URL: Optional[str] = Field(default=None, env="DIFY_API_URL")
    
    # 阿里百炼DashScope配置
    DASHSCOPE_API_KEY: Optional[str] = Field(default=None, env="DASHSCOPE_API_KEY")
    DASHSCOPE_MODEL: str = Field(
        default="qwen3-32b",  # 默认使用qwen3-32b模型（官方模型名称）
        env="DASHSCOPE_MODEL"
    )
    # API基础URL（如果使用OpenAI兼容接口，可以自定义）
    DASHSCOPE_API_BASE: Optional[str] = Field(default=None, env="DASHSCOPE_API_BASE")
    
    # 管理员默认配置
    DEFAULT_ADMIN_USERNAME: str = Field(default="admin", env="DEFAULT_ADMIN_USERNAME")
    DEFAULT_ADMIN_PASSWORD: str = Field(default="admin123!", env="DEFAULT_ADMIN_PASSWORD")
    DEFAULT_ADMIN_EMAIL: str = Field(default="admin@example.com", env="DEFAULT_ADMIN_EMAIL")
    
    # CORS配置
    CORS_ORIGINS: Union[List[str], str] = Field(
        default="http://localhost:3000,http://localhost:20800",  # 前端端口：20000~20999区间后半段
        env="CORS_ORIGINS"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """解析CORS origins，支持逗号分隔的字符串和列表"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    # API限流配置
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    WORKFLOW_RATE_LIMIT_PER_MINUTE: int = Field(default=20, env="WORKFLOW_RATE_LIMIT_PER_MINUTE")
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = Field(default=20971520, env="MAX_UPLOAD_SIZE")  # 20MB（批量分析需要）
    UPLOAD_DIR: str = Field(default="/app/uploads", env="UPLOAD_DIR")
    
    # 日志配置
    LOG_FILE: str = Field(default="/var/log/operation-analysis/app.log", env="LOG_FILE")
    LOG_ROTATION: str = Field(default="10 MB", env="LOG_ROTATION")
    LOG_RETENTION: str = Field(default="30 days", env="LOG_RETENTION")
    
    @computed_field
    @property
    def database_url(self) -> str:
        """
        构建数据库连接URL，自动处理密码中的特殊字符
        如果 DATABASE_URL 已设置，解析并重新构建以确保密码正确编码
        """
        # 始终从组件构建，确保密码正确编码
        # 这样即使 DATABASE_URL 环境变量存在，也会使用正确编码的版本
        encoded_password = quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql://{self.POSTGRES_USER}:{encoded_password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        # 支持多个环境变量文件，优先级从高到低
        # .env.local > .env
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
# 支持通过 ENV_FILE 环境变量指定配置文件
import os
env_file = os.environ.get("ENV_FILE", ".env")
if env_file != ".env" and os.path.exists(env_file):
    # 如果指定了自定义环境文件且存在，使用它
    settings = Settings(_env_file=env_file)
elif os.path.exists(".env.local"):
    # 如果存在 .env.local，优先使用它（开发环境）
    settings = Settings(_env_file=".env.local")
else:
    # 否则使用默认的 .env
    settings = Settings()

