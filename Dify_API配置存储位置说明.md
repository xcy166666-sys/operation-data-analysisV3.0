# Dify API 配置存储位置说明

## 一、主要存储位置

### 1. 数据库表：`workflows`

**表结构**：
- `id`: 工作流ID（主键）
- `name`: 工作流名称
- `platform`: 平台类型（'dify' / 'langchain' / 'ragflow'）
- `config`: **JSONB类型字段，存储Dify API配置信息**
- `category`: 分类（如 'operation'）
- `is_active`: 是否激活
- `created_by`: 创建者ID
- `created_at`: 创建时间
- `updated_at`: 更新时间

**配置内容（config字段）**：
```json
{
  "api_url": "http://118.89.16.95/v1",
  "api_key": "app-xxx",
  "url_file": "http://118.89.16.95/v1/files/upload",
  "url_work": "http://118.89.16.95/v1/chat-messages",
  "workflow_id": "1",
  "workflow_type": "chatflow",
  "file_param": "excell",
  "query_param": "sys.query",
  "input_field": "excell,sys.query"
}
```

### 2. 数据库表：`workflow_bindings`

**表结构**：
- `id`: 绑定ID（主键）
- `workflow_id`: 工作流ID（外键，关联到 `workflows.id`）
- `function_key`: 功能键（如 'operation_data_analysis'）
- `user_id`: 用户ID（NULL表示全局配置，非NULL表示用户级配置）
- `sheet_index`: Sheet索引（用于定制化批量分析，0-5对应6个工作流）
- `created_at`: 创建时间
- `updated_at`: 更新时间

**作用**：将工作流配置绑定到具体的功能模块，支持全局配置和用户级配置。

---

## 二、配置查询方式

### 1. 通过功能键查询（推荐）

**代码位置**：`backend/app/services/workflow_service.py`

```python
# 获取功能绑定的工作流（优先返回用户配置，如果没有则返回全局配置）
binding = WorkflowService.get_function_workflow(
    db=db,
    function_key="operation_data_analysis",
    user_id=current_user.id  # 可选，如果提供则优先返回用户配置
)

if binding:
    workflow = binding.workflow
    config = workflow.config  # 获取Dify API配置
    api_key = config.get("api_key")
    api_url = config.get("api_url")
    url_file = config.get("url_file")
    url_work = config.get("url_work")
```

### 2. 直接查询数据库

**SQL查询示例**：

```sql
-- 查询所有Dify工作流配置
SELECT 
    w.id,
    w.name,
    w.platform,
    w.config->>'api_key' as api_key,
    w.config->>'api_url' as api_url,
    w.config->>'url_file' as url_file,
    w.config->>'url_work' as url_work,
    w.is_active
FROM workflows w
WHERE w.platform = 'dify';

-- 查询特定功能的Dify配置（全局配置）
SELECT 
    w.id,
    w.name,
    w.config
FROM workflows w
JOIN workflow_bindings wb ON w.id = wb.workflow_id
WHERE wb.function_key = 'operation_data_analysis'
  AND wb.user_id IS NULL
  AND w.platform = 'dify';

-- 查询用户级配置
SELECT 
    w.id,
    w.name,
    w.config
FROM workflows w
JOIN workflow_bindings wb ON w.id = wb.workflow_id
WHERE wb.function_key = 'operation_data_analysis'
  AND wb.user_id = 1  -- 特定用户ID
  AND w.platform = 'dify';
```

---

## 三、配置优先级

1. **用户级配置**（`workflow_bindings.user_id != NULL`）
   - 优先级最高
   - 用户可以在功能页面自行配置
   - 仅对当前用户生效

2. **全局配置**（`workflow_bindings.user_id = NULL`）
   - 优先级较低
   - 由超级管理员在功能管理页面配置
   - 对所有用户生效（如果用户没有配置）

**查询逻辑**：
- 先查找用户级配置
- 如果不存在，再查找全局配置
- 如果都不存在，返回 `None`

---

## 四、配置文件位置（可选）

### 环境变量配置

**文件位置**：`backend/app/core/config.py`

```python
# AI工作流配置（可选，可通过管理界面配置）
DIFY_API_KEY: Optional[str] = Field(default=None, env="DIFY_API_KEY")
DIFY_API_URL: Optional[str] = Field(default=None, env="DIFY_API_URL")
```

**说明**：
- 这些环境变量是**可选的**
- 主要用于系统初始化或默认配置
- **实际使用的配置来自数据库**（`workflows.config` 字段）

---

## 五、配置修改方式

### 1. 通过前端管理界面（推荐）

**路径**：超级管理员 → 功能管理 → 配置API

**操作流程**：
1. 登录超级管理员账号
2. 进入"功能管理"页面
3. 点击对应功能的"配置API"按钮
4. 填写Dify API配置信息
5. 点击"保存配置"

**后端API**：
- `POST /api/v1/admin/functions/{function_key}/config` - 创建/更新配置
- `PUT /api/v1/admin/functions/{function_key}/config` - 更新配置
- `DELETE /api/v1/admin/functions/{function_key}/config` - 删除配置

### 2. 通过数据库直接修改

```sql
-- 更新工作流的Dify配置
UPDATE workflows
SET config = jsonb_set(
    config,
    '{api_key}',
    '"新的API Key"'
)
WHERE id = 1;

-- 或者完全替换配置
UPDATE workflows
SET config = '{
  "api_url": "http://118.89.16.95/v1",
  "api_key": "app-新的Key",
  "url_file": "http://118.89.16.95/v1/files/upload",
  "url_work": "http://118.89.16.95/v1/chat-messages",
  "workflow_id": "1",
  "workflow_type": "chatflow",
  "file_param": "excell",
  "query_param": "sys.query",
  "input_field": "excell,sys.query"
}'::jsonb
WHERE id = 1;
```

### 3. 通过Python脚本修改

**脚本位置**：`backend/scripts/update_workflow_config.py`

```python
from app.core.database import SessionLocal
from app.models.workflow import Workflow
from sqlalchemy.orm.attributes import flag_modified

db = SessionLocal()
workflow = db.query(Workflow).filter(Workflow.id == 1).first()

# 更新配置
new_config = dict(workflow.config) if workflow.config else {}
new_config.update({
    "api_key": "新的API Key",
    "url_file": "新的文件上传URL",
    "url_work": "新的工作流URL"
})

workflow.config = new_config
flag_modified(workflow, "config")
db.commit()
```

---

## 六、配置使用位置

### 1. 单文件数据分析

**文件**：`backend/app/api/v1/operation.py`

```python
# 获取绑定的Dify工作流
binding = WorkflowService.get_function_workflow(
    db, 
    "operation_data_analysis", 
    user_id
)
workflow = binding.workflow
config = workflow.config  # 使用配置
```

### 2. 批量数据分析

**文件**：`backend/app/api/v1/operation_batch.py`

```python
# 获取绑定的Dify工作流
binding = WorkflowService.get_function_workflow(
    db, 
    "operation_batch_analysis", 
    user_id
)
workflow = binding.workflow
config = workflow.config  # 使用配置
```

### 3. 定制化批量分析

**文件**：`backend/app/api/v1/operation_custom_batch.py`

```python
# 获取特定Sheet的工作流配置
binding = db.query(WorkflowBinding).filter(
    WorkflowBinding.function_key == "custom_operation_data_analysis",
    WorkflowBinding.sheet_index == sheet_index,
    WorkflowBinding.user_id == (user_id if user_id else None)
).first()
workflow = binding.workflow
config = workflow.config  # 使用配置
```

### 4. Dify服务调用

**文件**：`backend/app/services/dify_service.py`

```python
# 使用配置调用Dify API
result = await DifyService.run_workflow(
    api_url=config.get("api_url"),
    api_key=config.get("api_key"),
    workflow_id=config.get("workflow_id"),
    workflow_type=config.get("workflow_type"),
    inputs=inputs,
    user_id=dify_user
)
```

---

## 七、配置字段说明

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `api_url` | string | Dify API基础地址 | `http://118.89.16.95/v1` |
| `api_key` | string | Dify API密钥 | `app-xxx` |
| `url_file` | string | 文件上传URL | `http://118.89.16.95/v1/files/upload` |
| `url_work` | string | 工作流执行URL | `http://118.89.16.95/v1/chat-messages` |
| `workflow_id` | string | 工作流ID | `"1"` |
| `workflow_type` | string | 工作流类型 | `"chatflow"` 或 `"workflow"` |
| `file_param` | string | 文件参数名 | `"excell"` |
| `query_param` | string | 查询参数名 | `"sys.query"` 或 `"query"` |
| `input_field` | string | 输入字段名（逗号分隔） | `"excell,sys.query"` |

---

## 八、快速查看当前配置

### 方法1：通过数据库查询

```bash
# 进入PostgreSQL容器
docker-compose exec postgres psql -U postgres -d operation_analysis

# 查询所有Dify配置
SELECT 
    w.id,
    w.name,
    wb.function_key,
    w.config->>'api_key' as api_key,
    w.config->>'url_file' as url_file,
    w.config->>'url_work' as url_work,
    w.is_active
FROM workflows w
LEFT JOIN workflow_bindings wb ON w.id = wb.workflow_id
WHERE w.platform = 'dify'
ORDER BY w.id;
```

### 方法2：使用Python脚本

**脚本位置**：`backend/scripts/verify_workflows.py`

```bash
cd backend
python scripts/verify_workflows.py
```

### 方法3：通过前端界面

1. 登录超级管理员账号
2. 进入"功能管理"页面
3. 查看各功能的"工作流名称"列
4. 点击"配置API"查看详细配置

---

## 九、注意事项

1. **配置存储在数据库中**，不是文件系统
2. **JSONB字段**支持高效的JSON查询和更新
3. **用户级配置优先于全局配置**
4. **修改配置后需要重启服务**（如果使用了缓存）
5. **API Key是敏感信息**，注意保护数据库安全
6. **定制化批量分析**需要配置6个工作流（sheet_index: 0-5）

---

## 十、相关文件列表

### 数据库模型
- `backend/app/models/workflow.py` - 工作流模型定义

### 服务层
- `backend/app/services/workflow_service.py` - 工作流服务（查询、创建、更新）
- `backend/app/services/dify_service.py` - Dify API调用服务

### API接口
- `backend/app/api/v1/admin.py` - 超级管理员API（配置管理）
- `backend/app/api/v1/operation.py` - 单文件分析API
- `backend/app/api/v1/operation_batch.py` - 批量分析API
- `backend/app/api/v1/operation_custom_batch.py` - 定制化批量分析API

### 前端组件
- `frontend/src/views/Admin/FunctionManagement.vue` - 功能管理页面
- `frontend/src/views/Admin/components/FunctionConfigDialog.vue` - API配置对话框

### 脚本工具
- `backend/scripts/verify_workflows.py` - 验证工作流配置
- `backend/scripts/update_workflow_config.py` - 更新工作流配置
- `backend/scripts/setup_all_workflows.py` - 初始化所有工作流

---

**文档生成时间**: 2025-12-02
**项目名称**: 运营数据分析系统
**版本**: 1.0

