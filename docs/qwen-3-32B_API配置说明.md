# Qwen-3 32B API 配置说明

## API密钥信息

已配置的API密钥：`sk-f72852ce679f42019f669589a51e2639`

这是用于访问 Qwen-3 32B 模型的API密钥。

## 配置方法

### 方法1：环境变量配置（推荐）

在项目根目录的 `.env` 文件中添加：

```env
# Qwen-3 32B API配置
DASHSCOPE_API_KEY=sk-f72852ce679f42019f669589a51e2639
DASHSCOPE_MODEL=qwen-3-32b

# 如果使用OpenAI兼容接口，需要配置API基础URL
# DASHSCOPE_API_BASE=https://api.example.com
```

### 方法2：直接修改配置（不推荐，仅用于测试）

如果需要临时测试，可以直接在代码中设置，但不建议在生产环境使用。

## API接口类型

根据API密钥格式（`sk-`开头），这可能是：

1. **OpenAI兼容接口**：如果API提供商使用OpenAI兼容格式
2. **DashScope原生接口**：如果直接使用阿里云DashScope

系统已自动支持两种格式：
- 如果配置了 `DASHSCOPE_API_BASE`，将使用OpenAI兼容格式
- 否则使用DashScope原生API格式

## 模型名称

根据Qwen-3 32B模型，可能的模型名称包括：
- `qwen-3-32b`
- `qwen/qwen3-32b-fp8`
- `qwen3-32b`

系统默认使用 `qwen-3-32b`，如果API需要不同的模型名称，可以在 `.env` 文件中修改 `DASHSCOPE_MODEL`。

## 使用OpenAI兼容接口

如果您的API是OpenAI兼容格式，需要配置 `DASHSCOPE_API_BASE`：

```env
DASHSCOPE_API_KEY=sk-f72852ce679f42019f669589a51e2639
DASHSCOPE_MODEL=qwen-3-32b
DASHSCOPE_API_BASE=https://api.example.com  # 替换为实际的API基础URL
```

## 验证配置

### 1. 检查配置是否生效

```bash
# 进入后端容器
docker-compose exec backend python

# 测试配置
from app.core.config import settings
print(f"API Key: {settings.DASHSCOPE_API_KEY[:10]}...")
print(f"Model: {settings.DASHSCOPE_MODEL}")
print(f"API Base: {settings.DASHSCOPE_API_BASE}")
```

### 2. 测试API调用

```bash
# 运行测试脚本
docker-compose exec backend python scripts/test_bailian.py
```

## 常见问题

### 问题1: API调用失败，返回401错误

**原因**: API密钥无效或已过期

**解决方法**:
1. 检查API密钥是否正确
2. 确认API密钥是否已激活
3. 检查账户余额

### 问题2: 模型名称不匹配

**错误信息**: `model not found` 或类似错误

**解决方法**:
1. 查看API文档，确认正确的模型名称
2. 在 `.env` 文件中修改 `DASHSCOPE_MODEL` 为正确的模型名称
3. 重启后端服务

### 问题3: API格式不匹配

**错误信息**: API返回格式错误

**解决方法**:
1. 如果使用OpenAI兼容接口，配置 `DASHSCOPE_API_BASE`
2. 查看API文档，确认正确的API端点
3. 检查日志中的详细错误信息

## 重启服务

配置完成后，需要重启后端服务：

```bash
docker-compose restart backend
```

## 查看日志

如果遇到问题，可以查看后端日志：

```bash
docker-compose logs backend --tail 100 -f
```

## 注意事项

1. **API密钥安全**：
   - 不要在代码中硬编码API密钥
   - 使用环境变量管理密钥
   - 不要将 `.env` 文件提交到版本控制系统

2. **成本控制**：
   - Qwen-3 32B是大型模型，调用成本较高
   - 建议监控API调用次数和Token消耗
   - 数据样本限制在前100行，避免Token过多

3. **性能优化**：
   - 32B模型响应时间可能较长
   - API调用超时设置为120秒
   - 如果响应慢，可以考虑使用更小的模型

---

**配置完成时间**: 2025-12-04  
**API类型**: Qwen-3 32B


