# 图表定制化 Prompt 实现方案

## 📋 需求分析

用户希望通过输入框输入 prompt，同时传给：
1. **阿里百炼 qwen3 模型** - 用于定制化生成图表
2. **Dify 工作流** - 用于生成文字报告

## 🎯 方案设计

### 方案A：双输入框设计（推荐）

**优点**：
- ✅ 职责清晰，用户明确知道哪个输入框控制什么
- ✅ 实现简单，不需要智能分割
- ✅ 用户体验好，可以分别控制图表和文字

**缺点**：
- ⚠️ 需要两个输入框，界面稍复杂

#### 界面设计

```
┌─────────────────────────────────────────┐
│ 分析需求（文字报告）                    │
│ ┌───────────────────────────────────┐ │
│ │ 生成一份关注新手留存的周度报告      │ │
│ └───────────────────────────────────┘ │
│                                         │
│ 图表定制 Prompt（可选，用于图表生成）   │
│ ┌───────────────────────────────────┐ │
│ │ 请生成折线图，展示新用户增长趋势   │ │
│ │ 使用蓝色主题，添加数据标签         │ │
│ └───────────────────────────────────┘ │
│                                         │
│ [生成报告]                              │
└─────────────────────────────────────────┘
```

#### 数据流

```
用户输入
├─ 分析需求 → Dify工作流 → 文字报告
└─ 图表定制Prompt → 阿里百炼API → 图表配置
```

### 方案B：单输入框 + 智能分割

**优点**：
- ✅ 界面简洁，只有一个输入框
- ✅ 用户输入自然，不需要区分

**缺点**：
- ⚠️ 需要智能识别，可能不够准确
- ⚠️ 实现复杂，需要额外的分割逻辑

#### 实现方式

1. **前端智能分割**：
   - 使用关键词识别（如"图表"、"折线图"、"柱状图"等）
   - 提取图表相关需求，剩余部分作为文字需求

2. **后端智能分割**：
   - 使用 LLM 进行需求分割
   - 更准确，但增加一次 API 调用

### 方案C：单输入框 + 特殊标记

**优点**：
- ✅ 界面简洁
- ✅ 用户控制明确

**缺点**：
- ⚠️ 需要用户学习特殊标记语法
- ⚠️ 不够自然

#### 语法示例

```
生成一份关注新手留存的周度报告

[图表]
请生成折线图，展示新用户增长趋势
使用蓝色主题，添加数据标签
[/图表]

[文字]
详细分析新手留存情况，包括：
1. 留存率趋势
2. 流失原因分析
3. 优化建议
[/文字]
```

## 🚀 推荐实现：方案A（双输入框）

### 1. 前端实现

#### 1.1 修改输入框组件

```vue
<template>
  <div class="analysis-input-section">
    <!-- 主分析需求输入框 -->
    <div class="input-group">
      <label>分析需求（文字报告）</label>
      <el-input
        v-model="analysisRequest"
        type="textarea"
        :rows="3"
        placeholder="请输入分析需求，将用于生成文字报告..."
      />
    </div>
    
    <!-- 图表定制 Prompt 输入框（可选） -->
    <div class="input-group">
      <div class="input-header">
        <label>图表定制 Prompt（可选）</label>
        <el-switch
          v-model="enableChartCustomization"
          size="small"
          @change="handleChartCustomizationToggle"
        />
      </div>
      <el-input
        v-if="enableChartCustomization"
        v-model="chartCustomizationPrompt"
        type="textarea"
        :rows="3"
        placeholder="请输入图表定制需求，例如：&#10;- 请生成折线图，展示新用户增长趋势&#10;- 使用蓝色主题，添加数据标签&#10;- 图表标题：新用户增长趋势分析"
      />
      <div v-else class="hint-text">
        开启后可以定制图表样式和类型
      </div>
    </div>
    
    <!-- 生成按钮 -->
    <el-button
      type="primary"
      :loading="isGenerating"
      :disabled="!canSubmit"
      @click="submitAnalysis"
    >
      生成报告
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const analysisRequest = ref('')
const chartCustomizationPrompt = ref('')
const enableChartCustomization = ref(false)

const canSubmit = computed(() => {
  return analysisRequest.value.trim().length > 0
})

const handleChartCustomizationToggle = (value: boolean) => {
  if (!value) {
    chartCustomizationPrompt.value = ''
  }
}
</script>
```

#### 1.2 修改 API 调用

```typescript
// frontend/src/api/operation.ts

export interface GenerateReportRequest {
  session_id: number
  file_id: number
  analysis_request: string
  chart_customization_prompt?: string  // 新增字段
}

export function generateReport(data: GenerateReportRequest) {
  return request.post<ApiResponse<ReportResponse>>(
    '/operation/generate',
    data,
    {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      transformRequest: [
        (data) => {
          const formData = new URLSearchParams()
          formData.append('session_id', String(data.session_id))
          formData.append('file_id', String(data.file_id))
          formData.append('analysis_request', data.analysis_request)
          if (data.chart_customization_prompt) {
            formData.append('chart_customization_prompt', data.chart_customization_prompt)
          }
          return formData.toString()
        }
      ]
    }
  )
}
```

### 2. 后端实现

#### 2.1 修改 API 接口

```python
# backend/app/api/v1/operation.py

@router.post("/generate", response_model=SuccessResponse)
async def generate_report(
    session_id: int = Form(...),
    file_id: int = Form(...),
    analysis_request: str = Form(...),
    chart_customization_prompt: Optional[str] = Form(None),  # 新增参数
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """生成报告（支持图表定制化）"""
    
    # ... 前面的验证代码 ...
    
    # 构建图表生成任务
    async def generate_charts():
        # 合并分析需求和图表定制 prompt
        chart_prompt = analysis_request
        if chart_customization_prompt:
            chart_prompt = f"{analysis_request}\n\n图表定制要求：\n{chart_customization_prompt}"
        
        return await chart_generator.generate_charts_from_excel(
            file_path=str(file_path),
            analysis_request=chart_prompt,  # 使用合并后的 prompt
            generate_type="json"
        )
    
    # 文字生成任务（只使用分析需求）
    async def generate_text():
        # ... 使用 analysis_request，不包含图表定制 prompt ...
        pass
    
    # 并行执行
    charts_result, report_text = await asyncio.gather(
        charts_task,
        text_task,
        return_exceptions=True
    )
    
    # ... 后续处理 ...
```

#### 2.2 修改 BailianService

```python
# backend/app/services/bailian_service.py

def _build_json_config_prompt(
    self, 
    data_sample: str, 
    analysis_request: str,
    chart_customization: Optional[str] = None  # 新增参数
) -> str:
    """构建JSON配置生成提示词（支持定制化）"""
    
    base_prompt = f"""你是一个数据分析专家。用户提供了Excel数据样本和分析需求，请生成图表配置JSON。

数据样本：
{data_sample}

分析需求：{analysis_request}
"""
    
    # 如果有图表定制要求，添加到 prompt 中
    if chart_customization:
        base_prompt += f"""

图表定制要求：
{chart_customization}

请根据以上定制要求生成图表配置，包括：
- 图表类型（line/bar/pie/scatter）
- 图表样式（颜色、主题等）
- 图表标题
- 数据标签
- 其他定制化选项
"""
    else:
        base_prompt += """

请根据分析需求生成合适的图表配置JSON。
"""
    
    base_prompt += """

格式如下：
[
  {
    "chart_type": "line|bar|pie|scatter",
    "title": "图表标题",
    "x_column": "X轴列名",
    "y_columns": ["Y轴列名1", "Y轴列名2"],
    "description": "图表说明",
    "style": {
      "color": "#3498db",  // 可选：自定义颜色
      "theme": "light",     // 可选：主题
      "show_label": true   // 可选：显示数据标签
    }
  }
]

请只返回JSON数组，不要包含markdown代码块标记。"""
    
    return base_prompt
```

### 3. 数据流设计

```
用户输入
├─ analysis_request: "生成一份关注新手留存的周度报告"
└─ chart_customization_prompt: "请生成折线图，展示新用户增长趋势，使用蓝色主题"
    ↓
后端接收
├─ 图表生成路径
│   ├─ 合并 prompt: "生成一份关注新手留存的周度报告\n\n图表定制要求：\n请生成折线图..."
│   ├─ 调用阿里百炼API
│   └─ 生成图表配置
│
└─ 文字生成路径
    ├─ 使用 analysis_request
    ├─ 调用 Dify 工作流
    └─ 生成文字报告
    ↓
合并报告
└─ 返回前端
```

## 📝 实现步骤

### 阶段1：前端界面改造（1-2小时）

1. ✅ 添加图表定制输入框
2. ✅ 添加开关控制显示/隐藏
3. ✅ 修改表单提交逻辑
4. ✅ 更新 API 调用

### 阶段2：后端接口改造（1-2小时）

1. ✅ 修改 API 接口，接收 `chart_customization_prompt` 参数
2. ✅ 修改 `generate_charts` 函数，合并 prompt
3. ✅ 修改 `BailianService`，支持定制化 prompt
4. ✅ 添加日志记录

### 阶段3：测试验证（1小时）

1. ✅ 测试无图表定制的情况（向后兼容）
2. ✅ 测试有图表定制的情况
3. ✅ 测试各种图表类型和样式定制
4. ✅ 验证文字报告不受影响

## 🎨 界面设计建议

### 布局方案1：上下布局

```
┌─────────────────────────────────────┐
│ 分析需求（文字报告）                 │
│ [输入框 - 3行]                      │
│                                     │
│ 图表定制 Prompt（可选）             │
│ [开关] 启用图表定制                 │
│ [输入框 - 3行]                      │
│                                     │
│ [生成报告按钮]                      │
└─────────────────────────────────────┘
```

### 布局方案2：左右布局

```
┌──────────────────┬──────────────────┐
│ 分析需求          │ 图表定制          │
│ （文字报告）      │ （可选）          │
│                  │                  │
│ [输入框 - 6行]   │ [开关]           │
│                  │ [输入框 - 6行]   │
│                  │                  │
└──────────────────┴──────────────────┘
│ [生成报告按钮]                      │
└─────────────────────────────────────┘
```

## 🔧 技术细节

### 1. Prompt 合并策略

```python
def merge_prompts(
    analysis_request: str,
    chart_customization: Optional[str] = None
) -> str:
    """合并分析需求和图表定制 prompt"""
    if not chart_customization:
        return analysis_request
    
    return f"""{analysis_request}

图表定制要求：
{chart_customization}

请根据以上要求生成图表配置。"""
```

### 2. 图表定制 Prompt 模板

```python
CHART_CUSTOMIZATION_TEMPLATE = """
图表定制要求：
1. 图表类型：{chart_type}
2. 颜色主题：{color_theme}
3. 数据标签：{show_labels}
4. 图表标题：{title}
5. 其他要求：{other_requirements}
"""
```

### 3. 错误处理

```python
# 如果图表定制 prompt 过长，截断或提示
if chart_customization_prompt and len(chart_customization_prompt) > 500:
    logger.warning("图表定制 prompt 过长，将截断")
    chart_customization_prompt = chart_customization_prompt[:500]
```

## 📊 示例场景

### 场景1：基础使用（无图表定制）

```
分析需求：生成一份关注新手留存的周度报告
图表定制：关闭

结果：
- 文字报告：正常生成
- 图表：使用默认配置生成
```

### 场景2：图表定制

```
分析需求：生成一份关注新手留存的周度报告
图表定制：开启
定制内容：
  请生成折线图，展示新用户增长趋势
  使用蓝色主题（#3498db）
  添加数据标签
  图表标题：新用户增长趋势分析

结果：
- 文字报告：正常生成
- 图表：按照定制要求生成折线图
```

### 场景3：多图表定制

```
分析需求：生成一份关注新手留存的周度报告
图表定制：开启
定制内容：
  请生成以下图表：
  1. 折线图：新用户增长趋势（蓝色主题）
  2. 柱状图：留存率对比（绿色主题）
  3. 饼图：用户流失原因分布

结果：
- 文字报告：正常生成
- 图表：生成3个定制化的图表
```

## ✅ 优势总结

1. **灵活性高**：用户可以精确控制图表样式
2. **向后兼容**：不开启图表定制时，行为与之前一致
3. **职责清晰**：分析需求和图表定制分离
4. **易于扩展**：后续可以添加更多定制选项

## 🚧 注意事项

1. **Prompt 长度限制**：需要控制图表定制 prompt 的长度，避免超过 API 限制
2. **错误处理**：如果图表定制 prompt 导致生成失败，应该有降级方案
3. **用户引导**：需要提供示例和提示，帮助用户编写有效的图表定制 prompt
4. **性能影响**：图表定制可能会增加 API 调用时间，需要优化

---

**文档版本**：v1.0  
**创建日期**：2025-12-04

