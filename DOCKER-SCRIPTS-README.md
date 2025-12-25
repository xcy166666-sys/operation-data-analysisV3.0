# Docker管理脚本使用指南

## 🚨 当前问题：注册失败 500错误

### 快速修复（推荐）

**直接双击运行：`fix-500-error.bat`**

这个脚本会自动完成所有修复步骤：
1. ✅ 重启后端（应用CORS配置）
2. ✅ 初始化数据库
3. ✅ 检查服务状态

运行完成后，刷新浏览器重试注册。

---

## 📋 所有可用脚本

### 1. 修复和诊断

| 脚本 | 用途 | 何时使用 |
|------|------|----------|
| `fix-500-error.bat` | **一键修复500错误** | 遇到注册/登录失败时 |
| `diagnose.bat` | 完整系统诊断 | 需要详细了解系统状态 |
| `check-error.bat` | 查看错误日志 | 快速查看最近的错误 |

### 2. 重启服务

| 脚本 | 用途 | 何时使用 |
|------|------|----------|
| `restart-backend.bat` | 快速重启后端 | 修改了后端代码或.env |
| `rebuild-docker.bat` | 完全重建所有服务 | 需要清空数据重新开始 |
| `rebuild-docker.ps1` | PowerShell版重建 | 同上（PowerShell用户） |

### 3. 日志查看

| 脚本 | 用途 |
|------|------|
| `view-logs.bat` | 查看后端日志 |

### 4. 数据库管理

| 脚本 | 用途 |
|------|------|
| `init-database.bat` | 初始化数据库 |

---

## 🔧 手动修复步骤（如果脚本不工作）

### 步骤1：重启后端
```bash
docker restart operation-analysis-v2-backend
```

### 步骤2：初始化数据库
```bash
# 运行迁移
docker exec operation-analysis-v2-backend alembic upgrade head

# 初始化数据
docker exec operation-analysis-v2-backend python scripts/init_all.py
```

### 步骤3：查看日志
```bash
docker logs operation-analysis-v2-backend --tail 50
```

---

## 📊 服务端口

| 服务 | 端口 | 访问地址 |
|------|------|----------|
| 后端API | 21810 | http://localhost:21810/docs |
| PostgreSQL | 22810 | localhost:22810 |
| Redis | 22811 | localhost:22811 |
| 前端（开发） | 5173 | http://localhost:5173 |
| 前端（生产） | 20810 | http://localhost:20810 |

---

## 🐛 常见问题

### Q1: 脚本运行失败，提示"docker命令不存在"
**A:** 确保Docker Desktop正在运行

### Q2: 数据库连接失败
**A:** 检查postgres容器状态：
```bash
docker ps | findstr postgres
```
如果未运行，启动它：
```bash
docker start operation-analysis-v2-postgres
```

### Q3: 端口被占用
**A:** 检查端口占用：
```bash
netstat -ano | findstr "21810"
```

### Q4: 需要完全重置
**A:** 运行 `rebuild-docker.bat`（会删除所有数据）

---

## 📝 已完成的修复

1. ✅ 更新了CORS配置，添加本地开发地址
   - `http://localhost:5173`
   - `http://localhost:20810`
   - `http://127.0.0.1:5173`
   - `http://127.0.0.1:20810`

2. ✅ 添加了DATABASE_URL环境变量

3. ✅ 创建了自动化修复脚本

---

## 🎯 下一步

1. **运行修复脚本**：双击 `fix-500-error.bat`
2. **刷新浏览器**
3. **尝试注册**

如果还有问题，运行 `check-error.bat` 并将输出发给开发者。
