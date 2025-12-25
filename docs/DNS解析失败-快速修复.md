# DNS解析失败 - 快速修复指南

## 错误信息

```
[Errno -3] Temporary failure in name resolution
httpx.ConnectError: [Errno -3] Temporary failure in name resolution
```

## 问题原因

Docker容器中的 httpx 异步客户端无法解析 `dashscope.aliyuncs.com` 域名。

虽然：
- Python 的 `socket.gethostbyname()` 可以正常解析
- Docker DNS 配置正确（8.8.8.8, 223.5.5.5, 114.114.114.114）

但 httpx 的异步DNS解析仍然失败。

## 可能的原因

1. **httpx 异步DNS解析问题**：httpx 使用的异步DNS解析器与系统DNS不同
2. **trust_env=False 副作用**：禁用环境变量可能影响DNS解析
3. **Docker网络隔离**：容器网络与主机网络隔离导致DNS问题
4. **防火墙或网络策略**：阻止了异步连接

## 解决方案

### 方案1：使用IP地址（最快）

直接使用阿里云的IP地址，绕过DNS解析。

**步骤**：

1. 获取IP地址：
```bash
docker exec operation-analysis-v2-backend python -c "import socket; print(socket.gethostbyname('dashscope.aliyuncs.com'))"
```

输出：`39.105.164.144`

2. 修改 `.env` 文件：
```bash
# 使用IP地址代替域名
DASHSCOPE_API_BASE=http://39.105.164.144/api/v1/services/aigc/text-generation/generation
```

**注意**：IP地址可能会变化，这只是临时方案。

### 方案2：修改 httpx 客户端配置（推荐）

修改 `backend/app/services/bailian_service.py`：

```python
# 原代码
async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:

# 修改为（移除 trust_env=False）
async with httpx.AsyncClient(
    timeout=300.0,
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
) as client:
```

或者使用自定义传输：

```python
import httpx

# 创建自定义传输，使用系统DNS
transport = httpx.AsyncHTTPTransport(
    retries=3,  # 重试3次
)

async with httpx.AsyncClient(
    timeout=300.0,
    transport=transport
) as client:
```

### 方案3：添加 hosts 映射

在 `docker-compose.yml` 中添加：

```yaml
backend:
  extra_hosts:
    - "host.docker.internal:host-gateway"
    - "dashscope.aliyuncs.com:39.105.164.144"  # 添加这行
```

然后重启：
```bash
docker-compose down
docker-compose up -d
```

### 方案4：使用同步请求（备选）

如果异步请求一直有问题，可以改用同步请求：

```python
import requests

# 替换 httpx 为 requests
response = requests.post(
    self.api_url,
    json=payload,
    headers=headers,
    timeout=300,
    stream=True
)
```

### 方案5：检查系统代理设置

检查是否有系统代理影响：

```bash
# 在容器中检查
docker exec operation-analysis-v2-backend env | grep -i proxy

# 如果有输出，需要清除
docker exec operation-analysis-v2-backend unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
```

## 推荐修复步骤

### 步骤1：快速测试（方案2）

修改 `backend/app/services/bailian_service.py` 第348行：

```python
# 移除 trust_env=False，添加重试
async with httpx.AsyncClient(
    timeout=httpx.Timeout(300.0, connect=60.0),  # 连接超时60秒
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
    follow_redirects=True
) as client:
```

### 步骤2：重启后端

```bash
docker-compose restart backend
```

### 步骤3：测试

重新生成报告，查看是否还有DNS错误。

### 步骤4：如果仍然失败，使用方案3

在 `docker-compose.yml` 中添加 hosts 映射。

## 验证修复

### 1. 测试DNS解析

```bash
docker exec operation-analysis-v2-backend python -c "
import asyncio
import httpx

async def test():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get('https://dashscope.aliyuncs.com')
            print(f'Success: {response.status_code}')
    except Exception as e:
        print(f'Error: {e}')

asyncio.run(test())
"
```

### 2. 测试API调用

```bash
docker exec operation-analysis-v2-backend python -c "
import asyncio
from app.services.bailian_service import BailianService

async def test():
    service = BailianService()
    # 测试简单的API调用
    print('Testing API connection...')

asyncio.run(test())
"
```

### 3. 查看日志

```bash
docker logs operation-analysis-v2-backend --tail 50 | grep -i "dns\|resolution\|connect"
```

## 长期解决方案

1. **使用阿里云内网**：如果部署在阿里云，使用内网域名
2. **配置DNS缓存**：在容器中运行 dnsmasq
3. **使用服务网格**：如 Istio，统一管理服务间通信
4. **监控DNS健康**：定期检查DNS解析是否正常

## 相关文件

- `backend/app/services/bailian_service.py` - API调用逻辑
- `docker-compose.yml` - Docker网络配置
- `.env` - 环境变量配置
