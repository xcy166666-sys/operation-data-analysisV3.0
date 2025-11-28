"""
配置管理模块（运营数据分析独立版）
"""
from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """系统配置类"""
    
    # 基础配置
    APP_NAME: str = Field(default="运营数据分析系统", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@postgres:5432/operation_analysis",
        env="DATABASE_URL"
    )
    
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
    
    # 管理员默认配置
    DEFAULT_ADMIN_USERNAME: str = Field(default="admin", env="DEFAULT_ADMIN_USERNAME")
    DEFAULT_ADMIN_PASSWORD: str = Field(default="admin123!", env="DEFAULT_ADMIN_PASSWORD")
    DEFAULT_ADMIN_EMAIL: str = Field(default="admin@example.com", env="DEFAULT_ADMIN_EMAIL")
    
    # CORS配置
    CORS_ORIGINS: Union[List[str], str] = Field(
        default="http://localhost:3000,http://localhost:5173",
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

