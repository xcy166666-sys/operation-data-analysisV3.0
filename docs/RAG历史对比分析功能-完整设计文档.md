# RAG 历史对比分析功能 - 完整设计文档

## 📋 文档信息

- **功能名称**：基于 RAG 的 Project 历史对比分析系统
- **创建日期**：2024-12-26
- **版本**：v1.0
- **状态**：设计阶段

---

## 🎯 一、功能概述

### 1.1 核心价值

将现有的数据分析系统从**无状态的分析工具**升级为**智能化的分析平台**，通过 RAG（检索增强生成）技术实现：

- 📊 **历史数据对比**：自动对比当前数据与历史趋势
- 🧠 **知识积累**：从每次分析中学习，积累分析经验
- 🎯 **智能推荐**：基于历史成功案例推荐分析方法
- 🚀 **持续优化**：系统越用越智能，分析质量持续提升

### 1.2 设计理念

**类似 ChatGPT Project 的设计思路**：

- 每个 **Analysis Project**（分析项目）是一个主题化的数据分析空间
- 包含**数据池**（用户上传的数据源）
- 包含**RAG 知识库**（从数据中提取的洞察和模式）
- 用户可以勾选不同数据源进行对比分析

### 1.3 典型使用场景

**场景：留存分析项目**

```
第1个月（11月）：
- 用户创建"留存分析"项目
- 上传 11月留存数据.xlsx
- 生成报告，发现"新手引导影响留存"
- 将数据和洞察存入 RAG 知识库

第2个月（12月）：
- 用户上传 12月留存数据.xlsx
- 勾选 11月和12月数据
- 启用"历史对比"
- 系统自动检索 RAG 知识库
- 生成对比报告："12月留存率提升3%，可能是新手引导优化的结果"

第3个月（1月）：
- 用户上传 1月留存数据.xlsx
- 勾选 11月、12月、1月数据
- 系统生成3个月趋势对比报告
- 自动标注异常点和拐点
```

---

## 🏗️ 二、技术架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    前端（Vue 3）                         │
├─────────────────────────────────────────────────────────┤
│  项目管理页面  │  数据池管理  │  分析配置  │  报告展示  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                 后端 API（FastAPI）                      │
├─────────────────────────────────────────────────────────┤
│  项目管理API  │  数据源API  │  RAG检索API  │  分析API  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────┬──────────────────┬───────────────────┐
│  PostgreSQL      │  pgvector        │  阿里云 DashScope │
│  (关系数据)      │  (向量数据库)    │  (Embedding API)  │
└──────────────────┴──────────────────┴───────────────────┘
```

### 2.2 核心技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端 | Vue 3 + Element Plus | 已有技术栈 |
| 后端 | FastAPI + SQLAlchemy | 已有技术栈 |
| 数据库 | PostgreSQL 14+ | 已有，需安装 pgvector 扩展 |
| 向量数据库 | pgvector | PostgreSQL 扩展，无需额外部署 |
| Embedding API | 阿里云 DashScope text-embedding-v3 | 中文优化，已有 API Key |
| LLM | 阿里云 DashScope qwen-3-32b | 已有，用于生成报告 |



---

## 📊 三、数据库设计

### 3.1 新增表结构

#### 表1：analysis_projects（分析项目表）

```sql
CREATE TABLE analysis_projects (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,              -- 项目名称（如"留存分析"）
    description TEXT,                         -- 项目描述
    project_type VARCHAR(50),                 -- 项目类型（retention/payment/churn等）
    config JSONB DEFAULT '{}',                -- 项目配置（关注指标、分析偏好等）
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_projects_user ON analysis_projects(user_id);
CREATE INDEX idx_projects_type ON analysis_projects(project_type);
```

**字段说明：**
- `name`：项目名称，如"留存分析"、"付费分析"
- `project_type`：项目类型，用于分类和推荐
- `config`：JSON 格式，存储项目配置，如：
  ```json
  {
    "focus_metrics": ["day1_retention", "day7_retention"],
    "comparison_mode": "time_series",
    "auto_add_to_rag": true
  }
  ```

#### 表2：project_data_sources（数据源表）

```sql
CREATE TABLE project_data_sources (
    id SERIAL PRIMARY KEY,
    project_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,          -- 文件名
    file_path VARCHAR(500) NOT NULL,          -- 文件路径
    file_size BIGINT,                         -- 文件大小（字节）
    upload_date DATE,                         -- 数据日期（用户指定或自动识别）
    data_summary JSONB,                       -- 数据摘要（行数、列信息、关键指标）
    is_in_rag BOOLEAN DEFAULT FALSE,          -- 是否已存入RAG
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (project_id) REFERENCES analysis_projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_data_sources_project ON project_data_sources(project_id);
CREATE INDEX idx_data_sources_date ON project_data_sources(upload_date);
CREATE INDEX idx_data_sources_rag ON project_data_sources(is_in_rag);
```

**字段说明：**
- `upload_date`：数据的业务日期（如"2024-11-01"），用于时间序列对比
- `data_summary`：JSON 格式，存储数据摘要，如：
  ```json
  {
    "row_count": 50000,
    "columns": ["user_id", "register_date", "day1_retention"],
    "metrics": {
      "day1_retention": 0.65,
      "day7_retention": 0.42,
      "total_users": 50000
    }
  }
  ```
- `is_in_rag`：标记是否已加入 RAG 知识库

#### 表3：project_rag_vectors（RAG 向量表）

```sql
-- 需要先安装 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE project_rag_vectors (
    id SERIAL PRIMARY KEY,
    project_id INT NOT NULL,
    data_source_id INT,                       -- 关联的数据源（可选）
    session_id INT,                           -- 关联的分析会话（可选）
    
    -- 内容分类（三层结构）
    content_type VARCHAR(50) NOT NULL,        -- data_summary / insight / analysis_pattern
    content_text TEXT NOT NULL,               -- 文本内容（用于生成embedding）
    
    -- 向量
    embedding VECTOR(1536) NOT NULL,          -- 1536维向量（text-embedding-v3）
    
    -- 结构化元数据（用于精确过滤）
    metadata JSONB DEFAULT '{}',
    
    -- 质量指标
    relevance_score FLOAT DEFAULT 0.0,        -- 相关性评分
    reuse_count INT DEFAULT 0,                -- 被复用次数
    user_rating FLOAT DEFAULT 0.0,            -- 用户评分（1-5星）
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (project_id) REFERENCES analysis_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (data_source_id) REFERENCES project_data_sources(id) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(id) ON DELETE SET NULL
);

-- 向量索引（使用 IVFFlat 算法）
CREATE INDEX idx_rag_vectors_embedding ON project_rag_vectors 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 复合索引（加速过滤查询）
CREATE INDEX idx_rag_vectors_project_type ON project_rag_vectors(project_id, content_type);
CREATE INDEX idx_rag_vectors_metadata ON project_rag_vectors USING gin(metadata);
```

**字段说明：**
- `content_type`：内容类型，三层结构：
  - `data_summary`：数据摘要（关键指标、数据特征）
  - `insight`：关键洞察（AI 提取的发现和结论）
  - `analysis_pattern`：分析模式（成功的方法、图表配置）
- `embedding`：1536维向量，由 DashScope text-embedding-v3 生成
- `metadata`：JSON 格式，存储元数据，如：
  ```json
  {
    "date": "2024-11-01",
    "data_type": "retention",
    "metrics": {"day1_retention": 0.65},
    "insight_type": "correlation",
    "confidence": 0.85
  }
  ```

### 3.2 扩展现有表

#### 扩展：analysis_sessions（分析会话表）

```sql
ALTER TABLE analysis_sessions 
    ADD COLUMN project_id INT REFERENCES analysis_projects(id) ON DELETE SET NULL,
    ADD COLUMN selected_data_sources INT[] DEFAULT '{}',  -- 本次分析选中的数据源ID列表
    ADD COLUMN comparison_enabled BOOLEAN DEFAULT FALSE;  -- 是否启用历史对比
```



---

## 🔄 四、RAG 数据流程

### 4.1 RAG 向量数据库存储内容（三层结构）

#### 第1层：数据摘要层（Data Summary Layer）

**存储内容：** 数据源的统计摘要和关键指标

**示例：**
```json
{
  "content_type": "data_summary",
  "content_text": "数据时间：2024年11月\n数据类型：用户留存分析\n总用户数：50,000\n次日留存率：65%\n7日留存率：42%\n30日留存率：28%",
  "metadata": {
    "date": "2024-11-01",
    "data_type": "retention",
    "metrics": {
      "day1_retention": 0.65,
      "day7_retention": 0.42,
      "day30_retention": 0.28,
      "total_users": 50000
    }
  },
  "embedding": [0.123, 0.456, ..., 0.789]  // 1536维向量
}
```

**用途：**
- 快速检索相似时间段的数据
- 对比不同月份的指标变化
- 识别数据结构相似的历史数据

#### 第2层：洞察层（Insight Layer）

**存储内容：** AI 从报告中提取的关键洞察和发现

**示例：**
```json
{
  "content_type": "insight",
  "content_text": "新手引导完成率与7日留存强相关。完成新手引导的用户7日留存率为58%，未完成的用户仅为23%。建议优化新手引导流程。",
  "metadata": {
    "date": "2024-11-01",
    "insight_type": "correlation",
    "confidence": 0.85,
    "impact": "high",
    "actionable": true,
    "related_metrics": ["day7_retention", "tutorial_completion"]
  },
  "embedding": [0.234, 0.567, ..., 0.890]
}
```

**用途：**
- 检索历史上类似的洞察
- 避免重复发现
- 追踪洞察的演变

#### 第3层：知识层（Knowledge Layer）

**存储内容：** 成功的分析方法和最佳实践

**示例：**
```json
{
  "content_type": "analysis_pattern",
  "content_text": "分析方法：留存率漏斗分析\n适用场景：新用户留存分析\n图表类型：漏斗图 + 折线图组合\n用户反馈：5星评价，被复用15次",
  "metadata": {
    "pattern_type": "funnel_analysis",
    "data_type": "retention",
    "success_metrics": {
      "reuse_count": 15,
      "avg_rating": 4.8
    },
    "chart_config": {
      "type": "funnel",
      "color_scheme": "blue_gradient"
    }
  },
  "embedding": [0.345, 0.678, ..., 0.901]
}
```

**用途：**
- 推荐成功的分析方法
- 复用有效的图表配置
- 持续优化分析质量

### 4.2 完整数据流程

#### 流程1：存入数据（第一个月 - 11月）

```
1. 用户创建项目并上传数据
   ↓
2. 生成分析报告（调用 qwen-3-32b）
   ↓
3. 提取关键信息
   - 数据摘要：总用户数、关键指标
   - 关键洞察：AI 提取的发现
   - 分析模式：使用的方法和图表
   ↓
4. 调用 Embedding API（text-embedding-v3）
   - 将每条信息转换为 1536维向量
   - 单次调用成本：约 ¥0.00014
   ↓
5. 存入 PostgreSQL + pgvector
   - 存储文本内容
   - 存储向量
   - 存储元数据
```

**代码示例：**
```python
# 调用 Embedding API
import dashscope

text = "数据时间：2024-11，次日留存率：65%，7日留存率：42%"

response = dashscope.TextEmbedding.call(
    model='text-embedding-v3',
    input=text,
    api_key=settings.DASHSCOPE_API_KEY
)

embedding = response.output['embeddings'][0]['embedding']
# embedding = [0.123, 0.456, ..., 0.789]  # 1536个数字

# 存入数据库
db.execute("""
    INSERT INTO project_rag_vectors 
    (project_id, content_type, content_text, embedding, metadata)
    VALUES (%s, %s, %s, %s, %s)
""", (project_id, 'data_summary', text, embedding, metadata))
```

#### 流程2：检索数据（第二个月 - 12月）

```
1. 用户上传12月数据，勾选11月和12月
   ↓
2. 用户输入分析需求："对比11月和12月的留存率变化"
   ↓
3. 调用 Embedding API
   - 将查询转换为向量
   - 单次调用成本：约 ¥0.00014
   ↓
4. 在向量数据库中搜索（pgvector）
   - 使用余弦相似度计算
   - 返回最相关的前10条
   - 数据库内部计算，不调用 API
   ↓
5. 按类型分组
   - 数据摘要：11月的关键指标
   - 关键洞察：11月发现的规律
   - 分析模式：推荐的分析方法
   ↓
6. 构建增强 Prompt
   - 历史数据 + 历史洞察 + 当前数据 + 用户需求
   ↓
7. 调用 LLM 生成对比报告（qwen-3-32b）
   ↓
8. 将12月的数据和洞察也存入 RAG
```

**代码示例：**
```python
# 1. 生成查询向量
query = "对比11月和12月的留存率变化"
query_embedding = dashscope.TextEmbedding.call(
    model='text-embedding-v3',
    input=query
).output['embeddings'][0]['embedding']

# 2. 向量检索（使用 pgvector 的余弦相似度）
results = db.execute("""
    SELECT 
        content_type,
        content_text,
        metadata,
        1 - (embedding <=> %s::vector) AS similarity
    FROM project_rag_vectors
    WHERE project_id = %s
    ORDER BY embedding <=> %s::vector
    LIMIT 10
""", (query_embedding, project_id, query_embedding)).fetchall()

# 3. 按类型分组
historical_context = {
    "data_summaries": [],
    "insights": [],
    "patterns": []
}

for row in results:
    if row.content_type == 'data_summary':
        historical_context['data_summaries'].append(row.content_text)
    elif row.content_type == 'insight':
        historical_context['insights'].append(row.content_text)
    elif row.content_type == 'analysis_pattern':
        historical_context['patterns'].append(row.content_text)

# 4. 构建增强 Prompt
enhanced_prompt = f"""
【历史数据摘要】
{historical_context['data_summaries'][0]}

【历史关键洞察】
{historical_context['insights'][0]}
{historical_context['insights'][1]}

【推荐分析方法】
{historical_context['patterns'][0]}

【用户需求】
{query}

请生成对比分析报告...
"""

# 5. 调用 LLM 生成报告
report = await bailian_service.generate_report(enhanced_prompt)
```



---

## 🔌 五、后端 API 设计

### 5.1 项目管理 API

#### API 1: 创建项目

```http
POST /api/v1/operation/projects/create
Content-Type: application/json

{
  "name": "留存分析",
  "description": "分析新用户留存趋势",
  "project_type": "retention",
  "config": {
    "focus_metrics": ["day1_retention", "day7_retention"],
    "comparison_mode": "time_series",
    "auto_add_to_rag": true
  }
}
```

**响应：**
```json
{
  "code": 200,
  "message": "项目创建成功",
  "data": {
    "id": 1,
    "name": "留存分析",
    "created_at": "2024-12-26T10:00:00Z"
  }
}
```

#### API 2: 获取项目列表

```http
GET /api/v1/operation/projects/list?page=1&page_size=20
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "留存分析",
        "project_type": "retention",
        "data_source_count": 5,
        "analysis_count": 12,
        "created_at": "2024-12-26T10:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

#### API 3: 获取项目详情

```http
GET /api/v1/operation/projects/{project_id}
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "name": "留存分析",
    "description": "分析新用户留存趋势",
    "project_type": "retention",
    "config": {...},
    "data_sources": [
      {
        "id": 1,
        "file_name": "11月留存数据.xlsx",
        "upload_date": "2024-11-01",
        "is_in_rag": true,
        "data_summary": {...}
      },
      {
        "id": 2,
        "file_name": "12月留存数据.xlsx",
        "upload_date": "2024-12-01",
        "is_in_rag": true,
        "data_summary": {...}
      }
    ],
    "analysis_count": 12,
    "created_at": "2024-12-26T10:00:00Z"
  }
}
```

### 5.2 数据源管理 API

#### API 4: 添加数据源

```http
POST /api/v1/operation/projects/{project_id}/data-sources/add
Content-Type: multipart/form-data

file: [Excel文件]
upload_date: "2024-11-01"
auto_add_to_rag: true
```

**响应：**
```json
{
  "code": 200,
  "message": "数据源添加成功",
  "data": {
    "id": 1,
    "file_name": "11月留存数据.xlsx",
    "upload_date": "2024-11-01",
    "data_summary": {
      "row_count": 50000,
      "metrics": {
        "day1_retention": 0.65,
        "day7_retention": 0.42
      }
    }
  }
}
```

#### API 5: 将数据源加入 RAG

```http
POST /api/v1/operation/projects/{project_id}/data-sources/{source_id}/add-to-rag
```

**响应：**
```json
{
  "code": 200,
  "message": "已成功加入RAG知识库",
  "data": {
    "vectors_created": 4,
    "types": ["data_summary", "insight", "insight", "analysis_pattern"]
  }
}
```

### 5.3 分析 API

#### API 6: 在项目内创建分析

```http
POST /api/v1/operation/projects/{project_id}/analyze
Content-Type: application/json

{
  "selected_data_sources": [1, 2],
  "analysis_request": "对比11月和12月的留存率变化，分析原因",
  "comparison_enabled": true,
  "chart_customization": "生成折线图展示趋势"
}
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "session_id": 123,
    "report": {
      "text": "11月 vs 12月留存率对比分析报告...",
      "html_charts": "<html>...</html>",
      "rag_context_used": true,
      "historical_insights_count": 3
    }
  }
}
```

#### API 7: 获取项目内的分析历史

```http
GET /api/v1/operation/projects/{project_id}/sessions?page=1&page_size=20
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 123,
        "title": "11月 vs 12月留存对比",
        "selected_data_sources": [1, 2],
        "comparison_enabled": true,
        "created_at": "2024-12-26T10:00:00Z"
      }
    ],
    "total": 12
  }
}
```

---

## 🎨 六、前端 UI 设计

### 6.1 项目列表页面

```
┌─────────────────────────────────────────────────────────┐
│  我的分析项目                              [+ 新建项目]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │ 📊 留存分析       │  │ 💰 付费分析       │            │
│  │                  │  │                  │            │
│  │ 5 个数据源       │  │ 3 个数据源       │            │
│  │ 12 次分析        │  │ 8 次分析         │            │
│  │                  │  │                  │            │
│  │ 创建于 11-01     │  │ 创建于 11-15     │            │
│  └──────────────────┘  └──────────────────┘            │
│                                                          │
│  ─────────────────── 或者 ───────────────────           │
│                                                          │
│  [快速分析（不建立项目，单次分析）]                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 6.2 项目详情页面（数据池管理）

```
┌─────────────────────────────────────────────────────────┐
│  📊 留存分析项目                          [项目设置]     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  【数据池】(5个数据源)                  [+ 添加数据源]   │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ☑ 11月留存数据.xlsx  2024-11-01  50,000行  已加入RAG│ │
│  │ ☑ 12月留存数据.xlsx  2024-12-01  55,000行  已加入RAG│ │
│  │ ☑ 1月留存数据.xlsx   2024-01-01  52,000行  已加入RAG│ │
│  │ ☐ 2月留存数据.xlsx   2024-02-01  58,000行  未加入   │ │
│  │ ☐ 3月留存数据.xlsx   2024-03-01  60,000行  未加入   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  【分析配置】                                            │
│  选中的数据源：3个 (11月、12月、1月)                     │
│  对比模式：☑ 启用历史对比（使用RAG）                     │
│  关注指标：次日留存、7日留存、30日留存                   │
│                                                          │
│  分析需求：                                              │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 对比11月、12月、1月的留存趋势，分析哪些因素导致了   │ │
│  │ 留存率的变化                                        │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  [生成对比分析报告]                                      │
│                                                          │
│  【分析历史】                                            │
│  • 11月 vs 12月留存对比 (2024-12-15)                    │
│  • 11月、12月、1月趋势分析 (2024-01-20)                 │
│  • ...                                                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 6.3 报告展示页面（带 RAG 标识）

```
┌─────────────────────────────────────────────────────────┐
│  11月 vs 12月留存率对比分析报告                          │
│  🧠 本报告使用了 RAG 历史对比（检索到 3 条历史洞察）     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  【数据对比】                                            │
│  指标          11月    12月    变化                      │
│  次日留存率    65%     68%     +3% ↑                    │
│  7日留存率     42%     45%     +3% ↑                    │
│  30日留存率    28%     30%     +2% ↑                    │
│                                                          │
│  【变化分析】                                            │
│  1. 留存率全面提升                                       │
│     12月各项留存指标均有提升...                          │
│                                                          │
│  2. 可能原因（💡 结合历史洞察）                          │
│     - 11月分析发现"新手引导影响留存"，12月可能优化了...  │
│     - 11月发现"付费用户留存更高"，12月可能加强了...      │
│                                                          │
│  【建议】                                                │
│  - 继续优化新手引导流程                                  │
│  - 分析具体哪些优化措施最有效                            │
│                                                          │
│  [查看图表详情] [下载报告] [保存到知识库]                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```



---

## 📝 七、核心服务实现

### 7.1 Embedding 服务

```python
# backend/app/services/embedding_service.py

import dashscope
from typing import List
from loguru import logger
from app.core.config import settings

class EmbeddingService:
    """Embedding 服务（封装阿里云 DashScope API）"""
    
    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model = 'text-embedding-v3'
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        将文本转换为向量
        
        Args:
            text: 要转换的文本
        
        Returns:
            1536维的向量（List[float]）
        """
        try:
            response = dashscope.TextEmbedding.call(
                model=self.model,
                input=text,
                api_key=self.api_key
            )
            
            if response.status_code == 200:
                embedding = response.output['embeddings'][0]['embedding']
                logger.info(f"[EmbeddingService] 生成向量成功，维度: {len(embedding)}")
                return embedding
            else:
                raise Exception(f"Embedding API 调用失败: {response.message}")
        
        except Exception as e:
            logger.error(f"[EmbeddingService] 生成向量失败: {str(e)}")
            raise
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量转换文本为向量（提高效率）
        
        Args:
            texts: 要转换的文本列表
        
        Returns:
            向量列表
        """
        try:
            response = dashscope.TextEmbedding.call(
                model=self.model,
                input=texts,  # 支持批量输入
                api_key=self.api_key
            )
            
            if response.status_code == 200:
                embeddings = [
                    item['embedding'] 
                    for item in response.output['embeddings']
                ]
                logger.info(f"[EmbeddingService] 批量生成向量成功，数量: {len(embeddings)}")
                return embeddings
            else:
                raise Exception(f"Embedding API 调用失败: {response.message}")
        
        except Exception as e:
            logger.error(f"[EmbeddingService] 批量生成向量失败: {str(e)}")
            raise
```

### 7.2 RAG 服务

```python
# backend/app/services/project_rag_service.py

import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from app.services.embedding_service import EmbeddingService
from app.models.project import AnalysisProject, ProjectDataSource, ProjectRAGVector
from app.models.session import AnalysisSession

class ProjectRAGService:
    """项目级别的 RAG 服务"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    async def add_session_to_rag(
        self,
        project_id: int,
        session_id: int,
        data_source_id: int,
        db: Session
    ):
        """
        将分析会话加入 RAG 知识库
        
        Args:
            project_id: 项目ID
            session_id: 会话ID
            data_source_id: 数据源ID
            db: 数据库会话
        """
        logger.info(f"[RAG] 开始将会话 {session_id} 加入RAG知识库")
        
        # 1. 获取会话和数据源
        session = db.query(AnalysisSession).get(session_id)
        data_source = db.query(ProjectDataSource).get(data_source_id)
        
        if not session or not data_source:
            raise Exception("会话或数据源不存在")
        
        # 2. 提取报告内容
        report_text = session.messages[-1]['content']  # AI的回复
        
        # ========== 存储第1层：数据摘要 ==========
        
        # 2.1 构建数据摘要文本
        data_summary_text = self._build_data_summary_text(data_source)
        
        # 2.2 生成 embedding
        data_embedding = await self.embedding_service.get_embedding(data_summary_text)
        
        # 2.3 存入向量数据库
        data_vector = ProjectRAGVector(
            project_id=project_id,
            data_source_id=data_source_id,
            session_id=session_id,
            content_type='data_summary',
            content_text=data_summary_text,
            embedding=data_embedding,
            metadata={
                "date": str(data_source.upload_date),
                "data_type": "retention",
                "metrics": data_source.data_summary.get('metrics', {})
            }
        )
        db.add(data_vector)
        
        # ========== 存储第2层：关键洞察 ==========
        
        # 2.4 从报告中提取关键洞察
        insights = self._extract_insights(report_text)
        
        # 2.5 批量生成 embeddings
        insight_embeddings = await self.embedding_service.get_embeddings_batch(insights)
        
        # 2.6 存入向量数据库
        for insight, embedding in zip(insights, insight_embeddings):
            insight_vector = ProjectRAGVector(
                project_id=project_id,
                session_id=session_id,
                content_type='insight',
                content_text=insight,
                embedding=embedding,
                metadata={
                    "date": str(data_source.upload_date),
                    "insight_type": "correlation",
                    "confidence": 0.85
                }
            )
            db.add(insight_vector)
        
        # ========== 存储第3层：分析模式 ==========
        
        # 2.7 记录成功的分析模式
        pattern_text = self._build_pattern_text(session)
        pattern_embedding = await self.embedding_service.get_embedding(pattern_text)
        
        pattern_vector = ProjectRAGVector(
            project_id=project_id,
            session_id=session_id,
            content_type='analysis_pattern',
            content_text=pattern_text,
            embedding=pattern_embedding,
            metadata={
                "pattern_type": "funnel_analysis",
                "data_type": "retention"
            }
        )
        db.add(pattern_vector)
        
        # 3. 标记数据源已加入RAG
        data_source.is_in_rag = True
        
        db.commit()
        
        logger.info(f"[RAG] 成功将会话 {session_id} 加入RAG知识库，共创建 {len(insights) + 2} 个向量")
    
    async def retrieve_relevant_context(
        self,
        project_id: int,
        query: str,
        top_k: int = 10,
        db: Session = None
    ) -> Dict[str, List[str]]:
        """
        检索相关的历史上下文
        
        Args:
            project_id: 项目ID
            query: 查询文本
            top_k: 返回最相关的前K条
            db: 数据库会话
        
        Returns:
            按类型分组的历史上下文
        """
        logger.info(f"[RAG] 开始检索项目 {project_id} 的历史上下文")
        
        # 1. 生成查询向量
        query_embedding = await self.embedding_service.get_embedding(query)
        
        # 2. 在向量数据库中搜索（使用 pgvector 的余弦相似度）
        results = db.execute("""
            SELECT 
                id,
                content_type,
                content_text,
                metadata,
                1 - (embedding <=> :query_embedding::vector) AS similarity
            FROM project_rag_vectors
            WHERE project_id = :project_id
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :top_k
        """, {
            "project_id": project_id,
            "query_embedding": query_embedding,
            "top_k": top_k
        }).fetchall()
        
        # 3. 按类型分组
        context = {
            "data_summaries": [],
            "insights": [],
            "patterns": []
        }
        
        for row in results:
            logger.info(f"[RAG] 检索到: {row.content_type}, 相似度: {row.similarity:.3f}")
            
            if row.content_type == 'data_summary':
                context['data_summaries'].append(row.content_text)
            elif row.content_type == 'insight':
                context['insights'].append(row.content_text)
            elif row.content_type == 'analysis_pattern':
                context['patterns'].append(row.content_text)
        
        logger.info(f"[RAG] 检索完成，共找到 {len(results)} 条相关上下文")
        
        return context
    
    def _build_data_summary_text(self, data_source: ProjectDataSource) -> str:
        """构建数据摘要文本"""
        metrics = data_source.data_summary.get('metrics', {})
        
        text = f"""数据时间：{data_source.upload_date}
数据类型：用户留存分析
总用户数：{metrics.get('total_users', 0)}
次日留存率：{metrics.get('day1_retention', 0) * 100:.1f}%
7日留存率：{metrics.get('day7_retention', 0) * 100:.1f}%
30日留存率：{metrics.get('day30_retention', 0) * 100:.1f}%"""
        
        return text
    
    def _extract_insights(self, report_text: str) -> List[str]:
        """从报告中提取关键洞察（简化版）"""
        insights = []
        lines = report_text.split('\n')
        in_findings = False
        
        for line in lines:
            if '【关键发现】' in line or '关键发现' in line:
                in_findings = True
                continue
            if '【' in line and in_findings:
                break
            if in_findings and line.strip() and (
                line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '-', '•'))
            ):
                # 提取第一行（标题）
                insight = line.strip().lstrip('1234567890.-• ')
                if insight:
                    insights.append(insight)
        
        return insights[:5]  # 最多返回5条洞察
    
    def _build_pattern_text(self, session: AnalysisSession) -> str:
        """构建分析模式文本"""
        text = f"""分析方法：留存率漏斗分析
适用场景：新用户留存分析
分析维度：新手引导完成率、付费状态
图表类型：漏斗图、折线图"""
        
        return text
```



---

## 📅 八、实施计划

### 8.1 分阶段实施（4个阶段）

#### 阶段1：基础设施搭建（1-2周）

**目标：** 搭建 RAG 基础设施，实现基本的存储和检索

**任务清单：**

1. **数据库准备**
   - [ ] 安装 pgvector 扩展
   - [ ] 创建新表：`analysis_projects`, `project_data_sources`, `project_rag_vectors`
   - [ ] 扩展现有表：`analysis_sessions`
   - [ ] 创建索引和约束

2. **Embedding 服务**
   - [ ] 实现 `EmbeddingService` 类
   - [ ] 集成阿里云 DashScope text-embedding-v3 API
   - [ ] 实现单条和批量 embedding 生成
   - [ ] 添加错误处理和重试机制

3. **基础 RAG 服务**
   - [ ] 实现 `ProjectRAGService` 类
   - [ ] 实现数据存入功能（三层结构）
   - [ ] 实现向量检索功能（余弦相似度）
   - [ ] 实现洞察提取功能（规则 based）

4. **测试验证**
   - [ ] 单元测试：Embedding 生成
   - [ ] 单元测试：向量存储和检索
   - [ ] 集成测试：完整的存入和检索流程

**验收标准：**
- ✅ 能够将文本转换为向量并存入数据库
- ✅ 能够根据查询检索相关的历史向量
- ✅ 检索延迟 < 500ms

---

#### 阶段2：项目管理功能（1-2周）

**目标：** 实现项目管理和数据源管理功能

**任务清单：**

1. **后端 API**
   - [ ] 实现项目 CRUD API
   - [ ] 实现数据源上传 API
   - [ ] 实现数据源加入 RAG API
   - [ ] 实现项目详情查询 API

2. **前端页面**
   - [ ] 项目列表页面
   - [ ] 项目创建对话框
   - [ ] 项目详情页面（数据池管理）
   - [ ] 数据源上传组件

3. **数据处理**
   - [ ] Excel 文件解析
   - [ ] 数据摘要提取（行数、列信息、关键指标）
   - [ ] 数据日期识别（自动或手动）

4. **测试验证**
   - [ ] 功能测试：创建项目
   - [ ] 功能测试：上传数据源
   - [ ] 功能测试：查看数据池

**验收标准：**
- ✅ 用户能够创建项目
- ✅ 用户能够上传数据源到项目
- ✅ 用户能够查看项目的数据池

---

#### 阶段3：RAG 对比分析（2-3周）

**目标：** 实现基于 RAG 的历史对比分析功能

**任务清单：**

1. **后端核心功能**
   - [ ] 实现项目内分析 API
   - [ ] 集成 RAG 检索到分析流程
   - [ ] 实现增强 Prompt 构建
   - [ ] 实现分析结果自动存入 RAG

2. **前端分析界面**
   - [ ] 数据源选择组件（多选）
   - [ ] 历史对比开关
   - [ ] 分析需求输入框
   - [ ] 报告展示页面（带 RAG 标识）

3. **Prompt 优化**
   - [ ] 设计对比分析 Prompt 模板
   - [ ] 实现历史上下文注入
   - [ ] 实现洞察引用标注

4. **测试验证**
   - [ ] 功能测试：单数据源分析（不启用 RAG）
   - [ ] 功能测试：多数据源对比（启用 RAG）
   - [ ] 质量测试：对比报告准确性
   - [ ] 性能测试：检索延迟和生成速度

**验收标准：**
- ✅ 用户能够选择多个数据源进行对比
- ✅ 启用 RAG 后，报告包含历史洞察
- ✅ 对比报告质量明显优于不启用 RAG
- ✅ 检索延迟 < 500ms，总生成时间 < 30秒

---

#### 阶段4：优化和完善（1-2周）

**目标：** 优化用户体验和系统性能

**任务清单：**

1. **用户体验优化**
   - [ ] 添加 RAG 检索进度提示
   - [ ] 添加历史洞察来源标注
   - [ ] 添加用户反馈功能（点赞/点踩）
   - [ ] 优化报告展示样式

2. **性能优化**
   - [ ] 实现 Embedding 缓存
   - [ ] 实现批量处理
   - [ ] 优化向量索引参数
   - [ ] 添加异步处理

3. **监控和日志**
   - [ ] 添加 RAG 检索日志
   - [ ] 添加性能监控指标
   - [ ] 添加错误告警

4. **文档和培训**
   - [ ] 编写用户使用手册
   - [ ] 录制功能演示视频
   - [ ] 编写开发文档

**验收标准：**
- ✅ 用户体验流畅，无明显卡顿
- ✅ 有完整的监控和日志
- ✅ 有完整的使用文档

---

### 8.2 里程碑和时间线

```
Week 1-2:  阶段1 - 基础设施搭建
           ├─ 数据库准备
           ├─ Embedding 服务
           └─ 基础 RAG 服务

Week 3-4:  阶段2 - 项目管理功能
           ├─ 后端 API
           ├─ 前端页面
           └─ 数据处理

Week 5-7:  阶段3 - RAG 对比分析
           ├─ 后端核心功能
           ├─ 前端分析界面
           ├─ Prompt 优化
           └─ 测试验证

Week 8-9:  阶段4 - 优化和完善
           ├─ 用户体验优化
           ├─ 性能优化
           ├─ 监控和日志
           └─ 文档和培训

Week 10:   上线和迭代
```

**总计：约 10 周（2.5 个月）**

---

## 💰 九、成本估算

### 9.1 API 调用成本

**阿里云 DashScope 价格：**
- text-embedding-v3: ¥0.0007 / 1000 tokens
- qwen-3-32b: ¥0.012 / 1000 tokens（已有）

**成本估算（每月 100 次分析）：**

```
Embedding API 调用：
- 存入数据：每次分析 4 条向量 × 200 tokens = 800 tokens
- 检索查询：每次分析 1 次 × 200 tokens = 200 tokens
- 总计：1000 tokens/次 × 100次 = 100,000 tokens
- 成本：100 × 0.0007 = ¥0.07（7分钱）

LLM API 调用（已有）：
- 每次分析约 2000 tokens
- 成本：2 × 0.012 × 100 = ¥2.4

总成本：¥0.07 + ¥2.4 = ¥2.47/月
```

**结论：成本极低，可以忽略不计**

### 9.2 存储成本

**向量数据存储：**
```
单个向量大小：1536 × 4 bytes = 6KB
每次分析存储：4 个向量 = 24KB
每月 100 次分析：24KB × 100 = 2.4MB
每年：2.4MB × 12 = 28.8MB

结论：存储成本可忽略
```

### 9.3 开发成本

**人力成本：**
- 后端开发：2 周
- 前端开发：2 周
- 测试和优化：1 周
- 总计：5 周（1.25 个月）

---

## 🎯 十、成功指标

### 10.1 技术指标

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 检索延迟 | < 500ms | 后端日志统计 |
| 检索准确率 | > 70% | 用户反馈统计 |
| 系统可用性 | > 99.5% | 监控系统 |
| API 成本 | < ¥5/月 | 账单统计 |

### 10.2 业务指标

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 用户采用率 | > 50% | 30天内使用 RAG 功能的用户占比 |
| 复用率 | > 2次/周 | 用户平均每周复用历史案例次数 |
| 满意度 | > 4.2/5 | 用户评分统计 |
| 效率提升 | > 40% | 完成分析的平均时间对比 |

### 10.3 质量指标

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 对比报告准确性 | > 85% | 人工评估 |
| 洞察引用相关性 | > 80% | 用户反馈 |
| 图表一致性 | > 50% | 相同数据类型生成相同图表的比例 |

---

## 🔒 十一、风险和应对

### 11.1 技术风险

**风险1：检索不准确**
- **影响：** 检索到不相关的历史数据，影响报告质量
- **应对：**
  - 实现元数据过滤（按时间、数据类型）
  - 调整相似度阈值
  - 加入重排序（Rerank）

**风险2：性能问题**
- **影响：** 检索延迟过高，影响用户体验
- **应对：**
  - 优化向量索引参数
  - 实现缓存机制
  - 限制检索数量（top_k）

**风险3：成本超预期**
- **影响：** API 调用成本过高
- **应对：**
  - 实现 Embedding 缓存
  - 批量处理
  - 设置调用上限

### 11.2 业务风险

**风险1：用户不使用**
- **影响：** 功能开发了但用户不用
- **应对：**
  - 默认启用 RAG（用户可关闭）
  - 在报告中明确标注 RAG 带来的价值
  - 提供使用教程和案例

**风险2：数据质量差**
- **影响：** 存入的数据质量差，影响检索效果
- **应对：**
  - 实现数据清洗
  - 提供数据质量检查
  - 允许用户删除低质量数据

---

## 📚 十二、参考资料

### 12.1 技术文档

- [pgvector 官方文档](https://github.com/pgvector/pgvector)
- [阿里云 DashScope Embedding API](https://help.aliyun.com/zh/dashscope/developer-reference/text-embedding-api-details)
- [RAG 最佳实践](https://www.pinecone.io/learn/retrieval-augmented-generation/)

### 12.2 相关论文

- Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis et al., 2020)
- Dense Passage Retrieval for Open-Domain Question Answering (Karpukhin et al., 2020)

---

## 📞 十三、联系方式

**项目负责人：** [你的名字]
**技术支持：** [技术团队]
**文档更新日期：** 2024-12-26

---

## ✅ 附录：快速开始检查清单

### 开发环境准备

- [ ] PostgreSQL 14+ 已安装
- [ ] pgvector 扩展已安装
- [ ] 阿里云 DashScope API Key 已配置
- [ ] Python 依赖已安装（dashscope, pgvector）

### 数据库初始化

- [ ] 创建 pgvector 扩展
- [ ] 执行数据库迁移脚本
- [ ] 创建向量索引
- [ ] 验证表结构

### 服务部署

- [ ] 部署 Embedding 服务
- [ ] 部署 RAG 服务
- [ ] 配置环境变量
- [ ] 启动后端服务

### 功能测试

- [ ] 创建测试项目
- [ ] 上传测试数据
- [ ] 生成测试报告
- [ ] 验证 RAG 检索
- [ ] 验证对比分析

---

**文档结束**

