# 前端项目 - 本地运行指南

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:5173` 启动

### 3. 访问应用

打开浏览器访问：`http://localhost:5173`

## ⚙️ 配置说明

### API代理配置

前端通过Vite的proxy功能代理API请求到后端：

- **后端地址**：`http://localhost:21810`（Docker中的后端服务）
- **代理路径**：`/api` → `http://localhost:21810/api`

### 环境变量（可选）

如果需要自定义后端地址，可以在 `frontend` 目录下创建 `.env` 文件：

```env
VITE_API_URL=http://localhost:21810
VITE_API_BASE_URL=/api/v1
```

## 📝 开发命令

```bash
# 启动开发服务器（热重载）
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 代码检查
npm run lint
```

## ⚠️ 重要提示

1. **后端服务必须运行**：确保Docker中的后端服务（端口21810）正在运行
   ```bash
   docker-compose ps backend
   ```

2. **CORS配置**：如果遇到CORS问题，检查后端CORS配置是否允许 `http://localhost:5173`

3. **端口冲突**：如果5173端口被占用，Vite会自动使用下一个可用端口

## 🐛 常见问题

### 问题1：无法连接到后端API

**检查步骤**：
1. 确认后端服务运行：`docker-compose ps backend`
2. 测试后端API：访问 `http://localhost:21810/api/v1/health`（如果有健康检查接口）
3. 检查浏览器控制台的网络请求，查看具体错误

### 问题2：端口被占用

**解决方案**：
- 修改 `vite.config.ts` 中的 `port` 配置
- 或使用 `npm run dev -- --port 3000` 指定端口

### 问题3：热重载不工作

**解决方案**：
- 检查文件是否在 `node_modules` 或 `.gitignore` 中
- 重启开发服务器

---

**最后更新**：2025-12-05

