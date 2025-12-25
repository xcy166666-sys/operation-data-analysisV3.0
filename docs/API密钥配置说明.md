# API密钥配置说明

## ✅ 已配置的API密钥

### 1. 阿里百炼DashScope API（Qwen-3 32B）

**API Key**: `sk-f72852ce679f42019f669589a51e2639`  
**模型**: `qwen-3-32b`

**配置位置**: `.env` 文件

```env
# 阿里百炼DashScope配置（Qwen-3 32B）
DASHSCOPE_API_KEY=sk-f72852ce679f42019f669589a51e2639
DASHSCOPE_MODEL=qwen-3-32b
```

### 2. Dify文本生成API

**API Key**: `app-2i0887SmxI5cn4q7QGv7OpMg`  
**配置位置**: 数据库 `workflows` 表

已通过脚本更新到数据库。

## 📋 配置验证

### 验证阿里百炼API配置

```bash
# 进入后端容器
docker-compose exec backend python

# 在Python中执行
from app.core.config import settings
print("API Key:", "已配置" if settings.DASHSCOPE_API_KEY else "未配置")
print("Model:", settings.DASHSCOPE_MODEL)
```

### 验证Dify API配置

```bash
# 查看工作流配置
docker-compose exec backend python scripts/check_workflows.py
```

## 🔧 如果配置未生效

1. **检查.env文件**：
   - 确保 `.env` 文件在项目根目录
   - 确保配置格式正确（没有多余的空格或特殊字符）

2. **重启服务**：
   ```bash
   docker-compose restart backend
   ```

3. **查看日志**：
   ```bash
   docker-compose logs backend --tail 50
   ```

## 📝 配置位置总结

| API类型 | 配置位置 | 配置项 |
|---------|---------|--------|
| **阿里百炼** | `.env` 文件 | `DASHSCOPE_API_KEY`<br>`DASHSCOPE_MODEL` |
| **Dify文本生成** | 数据库 `workflows` 表 | `config.api_key` |

---

**最后更新**: 2025-12-04


