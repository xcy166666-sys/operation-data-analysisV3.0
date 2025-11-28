# 运营数据分析系统

独立的运营数据分析工具，支持Excel数据上传、AI分析和报告生成。

## 功能特性

- 📊 **单文件分析**：上传Excel/CSV文件，输入分析需求，生成包含图表的分析报告
- 📈 **批量分析**：支持多Sheet Excel文件，自动拆分并对每个Sheet生成独立报告
- 🤖 **AI驱动**：集成Dify工作流，支持多种AI平台（Dify、Langchain、Ragflow）
- 📄 **报告导出**：支持PDF和PNG格式报告下载，包含图表和文本
- 💾 **会话管理**：保存历史分析会话，支持回溯和复用

## 技术栈

### 后端
- **框架**：FastAPI 0.109.0
- **数据库**：PostgreSQL 15
- **缓存**：Redis 7
- **ORM**：SQLAlchemy 2.0
- **认证**：JWT + Session

### 前端
- **框架**：Vue 3 + TypeScript
- **UI库**：Element Plus
- **图表**：ECharts
- **构建工具**：Vite

### 部署
- **容器化**：Docker + Docker Compose
- **反向代理**：Nginx

## 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

### 1. 克隆项目

```bash
git clone <repository-url>
cd operation-data-analysis
```

### 2. 配置环境变量

复制环境变量模板并修改：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置以下关键配置：

```env
# 数据库配置
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=operation_analysis

# JWT密钥（生产环境必须修改）
JWT_SECRET=your_jwt_secret_key_here

# Dify配置
DIFY_API_KEY=your_dify_api_key
DIFY_API_URL=https://api.dify.ai/v1
```

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 初始化数据库

```bash
# 进入后端容器
docker-compose exec backend bash

# 运行数据库迁移
alembic upgrade head

# 创建初始管理员用户（可选）
python scripts/create_admin.py
```

### 5. 访问系统

- **前端**：http://localhost:80
- **后端API**：http://localhost:8000
- **API文档**：http://localhost:8000/docs

## 项目结构

```
operation-data-analysis/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/            # 核心配置
│   │   ├── models/          # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── utils/           # 工具类
│   ├── main.py             # 应用入口
│   ├── requirements.txt    # Python依赖
│   └── Dockerfile          # 后端Dockerfile
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── api/            # API接口
│   │   ├── views/          # 页面组件
│   │   └── stores/         # 状态管理
│   ├── package.json        # 前端依赖
│   ├── Dockerfile          # 前端Dockerfile
│   └── nginx.conf          # Nginx配置
├── nginx/                  # Nginx配置
│   ├── nginx.conf          # 主配置
│   └── conf.d/             # 站点配置
├── docker-compose.yml      # Docker Compose配置
├── .env.example            # 环境变量模板
└── README.md               # 项目文档
```

## 开发指南

### 后端开发

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev
```

## 配置工作流

1. 登录系统后，点击右上角的"配置工作流"按钮
2. 选择AI平台（推荐Dify）
3. 填写配置信息：
   - **Dify API地址**：例如 `https://api.dify.ai/v1`
   - **API Key**：您的Dify API密钥
   - **工作流ID**：Dify工作流的ID
   - **工作流类型**：Workflow 或 Chatflow
4. 保存配置

## API文档

启动服务后，访问以下地址查看API文档：

- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc

## 常见问题

### 1. 数据库连接失败

检查 `.env` 文件中的数据库配置是否正确，确保PostgreSQL容器已启动。

### 2. Dify工作流执行失败

- 检查Dify API地址和API Key是否正确
- 确认工作流ID是否存在
- 查看后端日志获取详细错误信息

### 3. 文件上传失败

- 检查文件大小是否超过限制（默认20MB）
- 确认文件格式是否为 `.xlsx` 或 `.csv`
- 检查上传目录权限

## 生产环境部署

### 1. 修改环境变量

确保 `.env` 文件中的敏感信息已修改为生产环境值。

### 2. 使用Nginx反向代理

项目已包含Nginx配置，生产环境建议使用Nginx作为反向代理。

### 3. 配置HTTPS

在 `nginx/conf.d/default.conf` 中添加SSL配置。

### 4. 数据备份

定期备份PostgreSQL数据：

```bash
docker-compose exec postgres pg_dump -U postgres operation_analysis > backup.sql
```

## 许可证

[添加许可证信息]

## 贡献

欢迎提交Issue和Pull Request！
