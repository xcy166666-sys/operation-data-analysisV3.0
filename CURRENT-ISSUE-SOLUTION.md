# 当前问题：加载会话列表失败 500错误

## 📊 问题状态

✅ **已解决**：前端端口问题（现在运行在正确的5173端口）  
❌ **待解决**：后端API返回500错误

## 🔍 错误信息

```
GET /api/v1/operation/sessions 500 (Internal Server Error)
加载会话列表失败: AxiosError
```

## 🎯 可能的原因

1. **数据库未初始化**：表不存在或数据不完整
2. **数据库连接失败**：PostgreSQL容器未运行或连接配置错误
3. **后端代码错误**：Python异常或逻辑错误
4. **认证问题**：用户未正确登录或session失效

## 🔧 诊断步骤

### 步骤1：运行完整诊断

**双击运行：`full-diagnosis.bat`**

这会检查：
- Docker服务状态
- 后端容器健康
- 数据库连接
- 数据库表
- 用户数据
- 错误日志

### 步骤2：查看详细错误

**双击运行：`show-backend-error.bat`**

查找关键错误信息：
- `relation "xxx" does not exist` → 数据库表未创建
- `could not connect to server` → 数据库连接失败
- `Python traceback` → 代码错误

### 步骤3：根据错误类型修复

#### 情况A：数据库表不存在

**双击运行：`init-database.bat`**

这会：
1. 运行数据库迁移（创建表）
2. 初始化功能模块和工作流
3. 验证表创建成功

#### 情况B：数据库连接失败

```bash
# 检查postgres容器
docker ps | findstr postgres

# 如果未运行，启动它
docker start operation-analysis-v2-postgres

# 重启后端
docker restart operation-analysis-v2-backend
```

#### 情况C：后端代码错误

```bash
# 查看完整错误堆栈
docker logs operation-analysis-v2-backend --tail 200

# 重启后端
docker restart operation-analysis-v2-backend
```

#### 情况D：认证问题

1. 清除浏览器Cookie
2. 重新登录
3. 如果没有用户，先注册

## 🚀 快速修复（推荐）

如果不确定问题，按顺序执行：

### 1. 修复后端和数据库
```
双击运行：fix-500-error.bat
```

### 2. 查看诊断结果
```
双击运行：full-diagnosis.bat
```

### 3. 如果还有问题，查看详细日志
```
双击运行：show-backend-error.bat
```

### 4. 测试API
```
双击运行：test-backend-api.bat
```

## 📋 验证清单

修复后，检查以下内容：

### 后端
- [ ] 容器运行中：`docker ps | findstr backend`
- [ ] 健康检查通过：访问 http://localhost:21810/health
- [ ] API文档可访问：访问 http://localhost:21810/docs
- [ ] 日志无错误：`docker logs operation-analysis-v2-backend --tail 50`

### 数据库
- [ ] PostgreSQL运行中：`docker ps | findstr postgres`
- [ ] 可以连接：运行 `full-diagnosis.bat` 步骤4
- [ ] 表已创建：运行 `full-diagnosis.bat` 步骤5
- [ ] 有用户数据：运行 `full-diagnosis.bat` 步骤6

### 前端
- [ ] 运行在5173端口：http://localhost:5173
- [ ] 可以访问登录页面
- [ ] 可以注册/登录

### 功能
- [ ] 登录成功
- [ ] 可以看到会话列表（或空列表）
- [ ] 可以上传文件
- [ ] 可以生成报告

## 🐛 常见错误及解决方案

### 错误1：`relation "users" does not exist`
**原因**：数据库表未创建  
**解决**：运行 `init-database.bat`

### 错误2：`could not connect to server`
**原因**：PostgreSQL未运行  
**解决**：`docker start operation-analysis-v2-postgres`

### 错误3：`401 Unauthorized`
**原因**：未登录或session过期  
**解决**：清除Cookie，重新登录

### 错误4：`500 Internal Server Error`
**原因**：后端代码错误  
**解决**：查看 `show-backend-error.bat` 的详细日志

### 错误5：`CORS policy`
**原因**：CORS配置问题  
**解决**：已在.env中配置，运行 `restart-backend.bat`

## 📞 获取帮助

如果以上步骤都无法解决问题，请提供：

1. **诊断输出**：`full-diagnosis.bat` 的完整输出
2. **错误日志**：`show-backend-error.bat` 的输出
3. **浏览器控制台**：完整的错误信息
4. **操作步骤**：你做了什么导致错误

## 🎯 下一步

1. **运行诊断**：`full-diagnosis.bat`
2. **根据结果修复**：参考上面的"情况A/B/C/D"
3. **验证修复**：检查验证清单
4. **测试功能**：尝试登录和使用系统

---

**提示**：大多数500错误是因为数据库未初始化。运行 `fix-500-error.bat` 通常可以解决。
