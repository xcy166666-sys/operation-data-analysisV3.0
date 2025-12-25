# HTML图表生成方案（替代JSON配置）

## 📋 需求分析

用户希望通过**自定义prompt提示词**，让阿里百炼大模型（qwen3）读取Excel数据后，直接生成**可运行的HTML代码**。代码层面只做最基础的HTML格式要求，**不规定具体功能**，完全由用户的prompt决定HTML内容。

**核心原则**：
- ✅ **用户自定义prompt**：用户通过"图表定制Prompt"输入框编写自己的提示词，**完全决定HTML内容**（图表类型、筛选器、下载功能、样式等）
- ✅ **代码最小化设定**：后端代码只做最基础的HTML格式要求（确保是HTML5文档），**不写死任何功能要求**
- ✅ **前端纯执行**：前端只负责执行运行发过来的HTML代码（通过iframe渲染），不做任何内容判断
- ✅ **库资源准备**：前端需要提前准备好常用图表库的CDN资源，确保HTML代码中的库引用可以正常加载

## 🎯 方案设计

### 当前架构 vs 新架构

#### 当前架构（JSON配置方式）

```
Excel数据
    ↓
阿里百炼API → 生成JSON配置
    ↓
Pyecharts → 转换为ECharts配置
    ↓
前端ECharts → 渲染图表
```

#### 新架构（HTML代码方式）

```
Excel数据
    ↓
阿里百炼API → 生成完整HTML代码（包含图表、交互、样式）
    ↓
后端验证和存储HTML
    ↓
前端直接渲染HTML（iframe或v-html）
```

## 🏗️ 架构设计

### 1. 数据流设计

```
用户上传Excel
    ↓
用户在"图表定制Prompt"输入框中编写自定义prompt
    ↓
后端调用阿里百炼API
    ├─ 发送Excel数据样本（自动提取）
    ├─ 发送用户自定义的图表定制Prompt（用户编写）
    └─ 添加基础辅助设定（确保生成HTML格式）
    ↓
阿里百炼根据用户prompt生成HTML代码
    ↓
后端验证和清理HTML（安全处理）
    ↓
存储HTML到报告内容
    ↓
前端接收HTML代码
    ↓
前端将图表显示区域改为HTML渲染区域（iframe）
```

### 2. HTML代码格式要求（仅格式，不规定内容）

**重要**：以下只是HTML代码的**格式要求**，具体包含什么内容（图表、筛选器、下载功能等）**完全由用户的prompt决定**，代码不做任何规定。

**代码层面的格式要求**（最小化）：
- 必须是完整的HTML5文档（`<!DOCTYPE html>`开头）
- 包含`<head>`和`<body>`标签
- 使用UTF-8编码
- 所有代码内嵌在HTML中，可以直接在浏览器中运行
- 不要包含markdown代码块标记

**示例格式**（内容由用户prompt决定）：
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>用户prompt决定的标题</title>
    
    <!-- 用户prompt决定使用什么库 -->
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    
    <style>
        /* 用户prompt决定的样式 */
    </style>
</head>
<body>
    <!-- 用户prompt决定包含什么内容 -->
    <!-- 可能是图表、筛选器、下载按钮、分析文字等，完全由用户prompt决定 -->
    <div class="container">
        <!-- 内容由用户prompt决定 -->
    </div>
    
    <script>
        // 用户prompt决定的JavaScript逻辑
    </script>
</body>
</html>
```

**注意**：代码不会要求必须包含图表、筛选器、下载功能等，这些完全由用户的prompt决定。

## 🔧 实现方案

### 方案A：前端直接渲染HTML（推荐）

**优点**：
- ✅ 实现简单，前端改动小
- ✅ 性能好，不需要iframe
- ✅ 可以自定义样式和交互

**缺点**：
- ⚠️ 需要严格的安全验证（XSS防护）
- ⚠️ 需要处理HTML中的外部资源加载

**实现方式**：
- 使用 `v-html` 渲染HTML
- 使用 `sandbox` 属性限制执行
- 使用 CSP（Content Security Policy）限制资源加载

### 方案B：使用iframe渲染HTML

**优点**：
- ✅ 安全性高，完全隔离
- ✅ 不会影响主页面样式
- ✅ 可以加载外部资源（CDN）

**缺点**：
- ⚠️ 需要处理iframe通信
- ⚠️ 样式可能不一致
- ⚠️ 响应式布局需要额外处理

**实现方式**：
- 创建iframe元素
- 将HTML代码写入iframe的srcdoc
- 设置iframe的样式和尺寸

### 方案C：混合方案（推荐用于生产环境）

**优点**：
- ✅ 结合两种方案的优点
- ✅ 可以根据内容类型选择渲染方式
- ✅ 更灵活和安全

**实现方式**：
- 简单HTML使用v-html渲染
- 复杂HTML（包含外部资源）使用iframe渲染
- 根据HTML内容自动选择

## 📝 详细实现步骤

### 阶段1：后端修改

#### 1.1 修改 BailianService

**核心思路**：用户自定义prompt为主，代码只做基础辅助设定

```python
# backend/app/services/bailian_service.py

def _build_html_generation_prompt(
    self,
    data_sample: str,
    analysis_request: str,
    chart_customization: Optional[str] = None
) -> str:
    """
    构建HTML代码生成提示词
    
    注意：chart_customization是用户自定义的prompt，代码只做基础框架设定
    """
    
    # 最基础的HTML格式要求（不规定任何功能内容）
    base_instruction = """你是一个前端开发专家。请根据用户提供的Excel数据样本和用户的定制要求，生成一个完整的、可运行的HTML网页。

**格式要求**（必须遵守）：
1. 必须返回完整的HTML5文档（<!DOCTYPE html>开头）
2. 包含<head>和<body>标签
3. 使用UTF-8编码（<meta charset="UTF-8">）
4. 所有代码必须内嵌在HTML中，可以直接在浏览器中运行
5. 不要包含markdown代码块标记（```html等），只返回纯HTML代码

**数据样本**：
{data_sample}

**基础分析需求**：
{analysis_request}
"""
    
    # 用户自定义prompt（核心内容，完全决定HTML内容）
    if chart_customization and chart_customization.strip():
        # 用户自己写的prompt，直接使用，不做任何修改
        user_prompt = f"""

**用户的定制要求**（请严格按照以下要求生成HTML内容，包括图表类型、功能、样式等）：
{chart_customization}
"""
    else:
        # 如果没有用户自定义prompt，只提示生成HTML，不规定具体内容
        user_prompt = """

**要求**：
请根据数据样本和分析需求，生成一个包含数据可视化的HTML网页。
"""
    
    # 不添加任何技术建议或默认要求，完全由用户prompt决定
    
    prompt = base_instruction.format(
        data_sample=data_sample,
        analysis_request=analysis_request
    ) + user_prompt
    
    return prompt
```

#### 1.2 修改 ChartGenerator

```python
# backend/app/services/chart_generator.py

async def generate_charts_from_excel(
    self,
    file_path: str,
    analysis_request: str,
    generate_type: str = "html",  # 新增：支持 "html" 类型
    chart_customization: Optional[str] = None
) -> Dict[str, Any]:
    """
    从Excel生成图表（支持HTML代码生成）
    
    Args:
        file_path: Excel文件路径
        analysis_request: 分析需求
        generate_type: 生成类型 "html"（新）或 "json"（旧）或 "code"
        chart_customization: 图表定制化 prompt
    
    Returns:
        {
            "success": bool,
            "html_content": str,  # HTML代码内容
            "charts": [],  # 保持兼容性，可以为空
            "data_summary": dict,
            "error": str
        }
    """
    try:
        if generate_type == "html":
            # 新方式：生成HTML代码
            logger.info(f"[ChartGenerator] 调用阿里百炼API生成HTML代码")
            html_result = await self.bailian_service.analyze_excel_and_generate_html(
                file_path=file_path,
                analysis_request=analysis_request,
                chart_customization=chart_customization
            )
            
            if not html_result["success"]:
                return {
                    "success": False,
                    "html_content": None,
                    "charts": [],
                    "data_summary": {},
                    "error": f"HTML生成失败: {html_result['error']}"
                }
            
            html_content = html_result["html_content"]
            
            # 验证和清理HTML（安全处理）
            cleaned_html = self._sanitize_html(html_content)
            
            # 读取数据摘要
            df = pd.read_excel(file_path)
            data_summary = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": df.columns.tolist(),
                "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
                "categorical_columns": df.select_dtypes(include=['object']).columns.tolist()
            }
            
            return {
                "success": True,
                "html_content": cleaned_html,
                "charts": [],  # HTML模式下，charts为空
                "data_summary": data_summary,
                "error": None
            }
        else:
            # 旧方式：生成JSON配置（保持向后兼容）
            # ... 原有逻辑 ...
            pass
    
    except Exception as e:
        logger.error(f"[ChartGenerator] 生成图表失败: {str(e)}")
        return {
            "success": False,
            "html_content": None,
            "charts": [],
            "data_summary": {},
            "error": str(e)
        }

def _sanitize_html(self, html_content: str) -> str:
    """清理和验证HTML内容（安全处理）"""
    # 1. 移除潜在的恶意脚本
    # 2. 验证外部资源URL
    # 3. 限制允许的标签和属性
    # 可以使用 bleach 或类似的库
    import bleach
    from bleach.css_sanitizer import CSSSanitizer
    
    # 允许的标签
    allowed_tags = [
        'html', 'head', 'body', 'title', 'meta', 'link', 'script',
        'style', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'p', 'button', 'select', 'option', 'input', 'canvas', 'svg'
    ]
    
    # 允许的属性
    allowed_attrs = {
        '*': ['class', 'id', 'style'],
        'script': ['src'],
        'link': ['href', 'rel'],
        'meta': ['charset', 'name', 'content'],
        'canvas': ['width', 'height'],
        'button': ['onclick'],
        'select': ['id', 'onchange'],
        'input': ['type', 'id', 'value']
    }
    
    # 允许的CSS属性
    css_sanitizer = CSSSanitizer(
        allowed_css_properties=['width', 'height', 'margin', 'padding', 
                              'color', 'background-color', 'border', 
                              'border-radius', 'font-size', 'font-family']
    )
    
    cleaned_html = bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attrs,
        css_sanitizer=css_sanitizer,
        strip=False
    )
    
    return cleaned_html
```

#### 1.3 修改 ReportMerger

```python
# backend/app/services/report_merger.py

@staticmethod
def merge_report(
    text_content: str,
    charts: List[Dict[str, Any]],
    data_summary: Dict[str, Any] = None,
    html_charts: Optional[str] = None  # 新增：HTML图表内容
) -> Dict[str, Any]:
    """
    合并文字和图表生成最终报告
    
    Args:
        text_content: Dify生成的文字内容
        charts: 图表配置列表（JSON方式，可选）
        data_summary: 数据摘要
        html_charts: HTML图表内容（新方式，可选）
    
    Returns:
        完整的报告内容
    """
    report_content = {
        "text": text_content,
        "charts": charts,  # JSON方式的图表（向后兼容）
        "html_charts": html_charts,  # HTML方式的图表（新）
        "tables": [],
        "metrics": {}
    }
    
    # ... 其他逻辑 ...
    
    return report_content
```

### 阶段2：前端修改（重点改动）

**核心改动**：将原来的ECharts图表显示区域（`<div class="report-charts">`）完全替换为HTML显示区域（使用iframe）

#### 2.1 修改数据接口定义

```typescript
// frontend/src/api/operation.ts

export interface ReportContent {
  text: string
  charts?: Array<{
    type: string
    data: any
    config?: any
  }>
  html_charts?: string  // 新增：HTML图表内容（优先使用）
  tables?: Array<{
    columns: Array<{ prop: string; label: string }>
    data: any[]
  }>
  metrics?: Record<string, number>
}
```

#### 2.2 修改报告显示组件（重点：替换图表显示区域）

**当前代码结构**（需要修改的部分）：
```vue
<!-- 当前：使用ECharts渲染 -->
<div class="report-charts" v-if="reportContent && reportContent.charts && reportContent.charts.length > 0">
  <div v-for="(_chart, index) in reportContent.charts" :key="index" class="chart-container">
    <div :id="`chart-${index}`" class="chart"></div>  <!-- 这里是canvas元素 -->
  </div>
</div>
```

**修改后**（替换为HTML显示区域）：
```vue
<!-- frontend/src/views/Operation/DataAnalysis.vue -->

<template>
  <div class="message-content">
    <!-- 报告文字内容 -->
    <div class="report-text" v-if="reportContent && reportContent.text">
      <!-- ... 文字显示逻辑保持不变 ... -->
    </div>
    
    <!-- HTML图表显示区域（替换原来的ECharts区域） -->
    <div class="html-charts-container" v-if="reportContent && reportContent.html_charts">
      <!-- 使用iframe渲染HTML（推荐，安全隔离） -->
      <iframe
        :srcdoc="reportContent.html_charts"
        class="html-charts-iframe"
        frameborder="0"
        sandbox="allow-scripts allow-same-origin allow-forms"
        @load="handleHtmlChartLoad"
      ></iframe>
    </div>
    
    <!-- JSON图表显示（向后兼容，如果没有html_charts则使用旧方式） -->
    <div class="report-charts" v-else-if="reportContent && reportContent.charts && reportContent.charts.length > 0">
      <!-- 保留原有ECharts渲染逻辑作为降级方案 -->
      <div 
        v-for="(_chart, index) in reportContent.charts" 
        :key="index"
        class="chart-container"
      >
        <div :id="`chart-${index}`" class="chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'

const reportContent = computed(() => operationStore.reportContent)

// iframe加载完成处理
const handleHtmlChartLoad = (event: Event) => {
  const iframe = event.target as HTMLIFrameElement
  console.log('[HTML图表] iframe加载完成')
  
  // 尝试自动调整iframe高度（如果同源）
  try {
    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document
    if (iframeDoc && iframeDoc.body) {
      // 等待内容渲染完成
      setTimeout(() => {
        const height = Math.max(
          iframeDoc.body.scrollHeight,
          iframeDoc.documentElement.scrollHeight,
          600 // 最小高度
        )
        iframe.style.height = `${height}px`
        console.log('[HTML图表] iframe高度已调整:', height)
      }, 100)
    }
  } catch (e) {
    // 跨域限制，使用固定高度
    console.warn('[HTML图表] 无法访问iframe内容，使用固定高度')
    iframe.style.height = '600px'
  }
}

// 监听html_charts变化，确保iframe正确渲染
watch(() => reportContent.value?.html_charts, (newHtml) => {
  if (newHtml) {
    console.log('[HTML图表] 检测到新的HTML内容，长度:', newHtml.length)
    nextTick(() => {
      // iframe会自动通过:srcdoc绑定更新
    })
  }
}, { immediate: true })
</script>

<style scoped>
/* HTML图表容器样式 */
.html-charts-container {
  margin-top: 20px;
  margin-bottom: 20px;
  border: 1px solid var(--apple-border-light);
  border-radius: var(--apple-radius-lg);
  overflow: hidden;
  background: var(--apple-bg-primary);
  box-shadow: var(--apple-shadow-sm);
}

.html-charts-iframe {
  width: 100%;
  min-height: 600px;
  border: none;
  display: block;
  background: white;
}

/* 保留原有图表样式（向后兼容） */
.report-charts {
  margin-top: 20px;
}

.chart-container {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-lg);
  border: 1px solid var(--apple-border-light);
}

.chart {
  width: 100%;
  height: 400px;
}
</style>
```

#### 2.3 前端库资源准备（重要）

**核心要求**：前端需要提前准备好常用图表库的CDN资源，确保HTML代码中的库引用可以正常加载。

**实现方式**：在`index.html`中预加载常用库的CDN资源

```html
<!-- frontend/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>运营数据分析</title>
  
  <!-- 预加载常用图表库CDN资源（确保HTML代码中的引用可以正常加载） -->
  <!-- ECharts -->
  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js" crossorigin="anonymous"></script>
  
  <!-- Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.js" crossorigin="anonymous"></script>
  
  <!-- D3.js -->
  <script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js" crossorigin="anonymous"></script>
  
  <!-- 其他常用库（根据实际需求添加） -->
</head>
<body>
  <div id="app"></div>
</body>
</html>
```

**或者**：在iframe的sandbox中允许加载外部资源（推荐，更灵活）

```vue
<!-- 前端iframe配置 -->
<iframe
  :srcdoc="reportContent.html_charts"
  class="html-charts-iframe"
  frameborder="0"
  sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
  allow="fullscreen"
></iframe>
```

**注意**：
- 前端**只负责执行**HTML代码，不做任何内容判断
- HTML代码中引用的CDN资源需要能够正常访问
- 如果使用iframe，确保sandbox配置允许加载外部资源

#### 2.4 移除或注释原有的ECharts渲染逻辑

**需要修改的函数**：
```typescript
// frontend/src/views/Operation/DataAnalysis.vue

// 原有的renderCharts函数可以保留作为降级方案，但优先使用HTML渲染
const renderCharts = async (charts: any[]) => {
  // 如果已经有html_charts，不渲染ECharts（前端只执行HTML）
  if (reportContent.value?.html_charts) {
    console.log('[图表渲染] 使用HTML模式，跳过ECharts渲染')
    return
  }
  
  // 降级方案：如果没有html_charts，使用原有ECharts渲染
  if (!charts || charts.length === 0) return
  
  await nextTick()
  
  // ... 原有ECharts渲染逻辑 ...
}
```

#### 2.3 添加HTML清理库（如果使用v-html方式）

```bash
# frontend/package.json
{
  "dependencies": {
    "dompurify": "^3.0.6",
    "@types/dompurify": "^3.0.5"
  }
}
```

### 阶段3：后端API修改

#### 3.1 修改报告生成接口

```python
# backend/app/api/v1/operation.py

@router.post("/generate", response_model=SuccessResponse)
async def generate_report(
    session_id: int = Form(...),
    file_id: int = Form(...),
    analysis_request: str = Form(...),
    chart_customization_prompt: Optional[str] = Form(None),
    chart_generation_mode: str = Form("html"),  # 新增：图表生成模式 "html" 或 "json"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """生成报告（支持HTML图表生成）"""
    
    # ... 前面的验证代码 ...
    
    # 构建图表生成任务
    async def generate_charts():
        chart_prompt = analysis_request
        if chart_customization_prompt:
            chart_prompt = f"{analysis_request}\n\n图表定制要求：\n{chart_customization_prompt}"
        
        return await chart_generator.generate_charts_from_excel(
            file_path=str(file_path),
            analysis_request=chart_prompt,
            generate_type=chart_generation_mode,  # 使用用户选择的模式
            chart_customization=chart_customization_prompt if chart_customization_prompt else None
        )
    
    # ... 其他逻辑 ...
    
    # 合并报告
    report_content = report_merger.merge_report(
        text_content=final_text,
        charts=charts if chart_generation_mode == "json" else [],  # JSON模式才填充charts
        data_summary=data_summary,
        html_charts=charts_result.get("html_content") if chart_generation_mode == "html" else None  # HTML模式填充html_charts
    )
    
    # ... 返回报告 ...
```

## 🔒 安全考虑

### 1. HTML内容安全

**风险**：
- XSS攻击（恶意脚本注入）
- 外部资源加载（可能泄露数据）
- 不安全的交互（如eval、Function等）

**防护措施**：

1. **使用iframe + sandbox**（推荐）：
   ```html
   <iframe
     :srcdoc="htmlContent"
     sandbox="allow-scripts allow-same-origin"
   ></iframe>
   ```
   - `allow-scripts`: 允许执行脚本（图表需要）
   - `allow-same-origin`: 允许同源访问（某些图表库需要）
   - 限制其他危险操作

2. **HTML清理**（如果使用v-html）：
   - 使用 `DOMPurify` 或 `bleach` 清理HTML
   - 白名单机制（只允许特定标签和属性）
   - 移除危险脚本和事件处理器

3. **CSP（Content Security Policy）**：
   ```html
   <meta http-equiv="Content-Security-Policy" 
         content="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline';">
   ```

4. **资源URL验证**：
   - 只允许特定的CDN域名（如cdn.jsdelivr.net）
   - 禁止加载外部数据源
   - 禁止内联危险脚本

### 2. 数据安全

- 确保HTML中的真实数据来自Excel，不是AI生成的虚假数据
- 验证数据格式和范围
- 防止数据泄露

## 📊 数据流对比

### 当前方式（JSON配置）

```
Excel → 阿里百炼 → JSON配置 → Pyecharts → ECharts配置 → 前端渲染
```

### 新方式（HTML代码）

```
Excel → 阿里百炼 → 完整HTML代码 → 后端验证 → 前端直接渲染
```

## 🎨 前端配置修改清单

### 必须修改（重点）

1. ✅ **ReportContent接口**：添加 `html_charts?: string` 字段
2. ✅ **替换图表显示区域**：
   - 将 `<div class="report-charts">` 中的ECharts渲染逻辑
   - 替换为 `<div class="html-charts-container">` 中的iframe渲染
   - 原来的 `<div :id="chart-${index}" class="chart">` 改为 `<iframe :srcdoc="html_charts">`
3. ✅ **渲染优先级**：优先使用 `html_charts`，如果没有则降级到 `charts`（ECharts）
4. ✅ **移除或注释ECharts初始化**：`renderCharts` 函数中，如果存在 `html_charts` 则跳过ECharts渲染

### 可选修改

1. ⚠️ **iframe高度自适应**：根据内容自动调整iframe高度（已实现）
2. ⚠️ **样式隔离**：确保HTML图表样式不影响主页面（iframe天然隔离）
3. ⚠️ **加载状态**：添加HTML加载中的提示
4. ⚠️ **错误处理**：如果HTML渲染失败，显示错误提示并降级到ECharts

### 前端改动对比

**改动前**（ECharts方式）：
```vue
<div class="report-charts">
  <div v-for="chart in charts" class="chart-container">
    <div :id="`chart-${index}`" class="chart"></div>  <!-- canvas元素 -->
  </div>
</div>
```

**改动后**（HTML iframe方式）：
```vue
<div class="html-charts-container" v-if="html_charts">
  <iframe :srcdoc="html_charts" class="html-charts-iframe"></iframe>
</div>
<div class="report-charts" v-else-if="charts">
  <!-- 降级方案：保留原有ECharts渲染 -->
</div>
```

## 🔄 向后兼容性

### 兼容策略

1. **双模式支持**：
   - 保留JSON模式（向后兼容）
   - 新增HTML模式（新功能）
   - 用户可以选择使用哪种模式

2. **数据格式**：
   ```typescript
   interface ReportContent {
     text: string
     charts?: Array<...>      // JSON模式
     html_charts?: string     // HTML模式
     // 两种模式可以共存，前端根据优先级选择
   }
   ```

3. **前端渲染逻辑**：
   ```typescript
   // 优先使用HTML模式，如果没有则使用JSON模式
   if (reportContent.html_charts) {
     // 渲染HTML图表
   } else if (reportContent.charts && reportContent.charts.length > 0) {
     // 渲染JSON图表（旧方式）
   }
   ```

## 📝 实现优先级

### 阶段1：基础实现（1-2天）

1. ✅ **后端修改**：
   - 修改BailianService，支持HTML生成（用户prompt为主，代码辅助设定）
   - 修改ChartGenerator，支持HTML模式
   - 修改ReportMerger，支持html_charts字段

2. ✅ **前端修改（重点）**：
   - 修改ReportContent接口，添加html_charts字段
   - **替换图表显示区域**：将ECharts渲染区域改为iframe HTML渲染区域
   - 修改renderCharts函数，优先使用HTML渲染
   - 添加iframe加载处理逻辑

### 阶段2：安全增强（1天）

1. ✅ 实现HTML清理和验证（后端）
2. ✅ iframe sandbox属性配置（前端）
3. ✅ 资源URL白名单验证（后端）

### 阶段3：用户体验优化（1天）

1. ✅ iframe高度自适应（已实现）
2. ✅ 加载状态提示
3. ✅ 错误处理和降级方案（HTML失败时回退到ECharts）

### 阶段4：功能增强（可选）

1. ⚠️ 支持多HTML图表（多个iframe）
2. ⚠️ HTML预览和编辑
3. ⚠️ 图表缓存和复用

## 🚧 注意事项

1. **HTML大小限制**：
   - 大模型生成的HTML可能很大
   - 需要控制HTML大小（如限制在50KB以内）
   - 如果过大，考虑压缩或拆分

2. **外部资源加载**：
   - HTML中可能包含CDN资源（如ECharts）
   - 需要确保CDN资源可访问
   - 考虑使用本地资源或代理

3. **浏览器兼容性**：
   - iframe的srcdoc属性需要现代浏览器
   - 需要测试不同浏览器的兼容性

4. **性能考虑**：
   - 大量HTML内容可能影响页面性能
   - 考虑懒加载或虚拟滚动

5. **调试和错误处理**：
   - HTML代码可能有语法错误
   - 需要完善的错误处理和日志
   - 提供降级方案（如果HTML生成失败，回退到JSON模式）

## 📋 Prompt设计建议

### 用户自定义Prompt示例

**重要**：用户通过"图表定制Prompt"输入框编写自己的prompt，代码只做基础辅助设定。

#### 示例1：基础图表生成
```
请根据Excel数据生成一个折线图，展示新用户增长趋势。
使用ECharts库，蓝色主题（#3498db），添加数据标签。
图表标题：新用户增长趋势分析
```

#### 示例2：复杂交互式图表
```
请生成一个包含以下功能的HTML页面：
1. 使用ECharts创建一个多系列折线图，展示不同渠道的用户增长
2. 添加日期筛选器，可以按周/月/季度筛选
3. 添加用户类型筛选器（新用户/老用户）
4. 提供下载PNG图片功能
5. 提供下载CSV数据功能
6. 在图表下方添加数据洞察文字，分析增长趋势
7. 使用现代化UI设计，响应式布局
```

#### 示例3：多图表组合
```
请生成一个包含多个图表的HTML页面：
1. 顶部：折线图展示用户增长趋势（蓝色主题）
2. 中间：柱状图展示留存率对比（绿色主题）
3. 底部：饼图展示用户流失原因分布
每个图表都要有独立的标题和说明
```

#### 示例4：自定义样式和交互
```
请生成一个数据可视化页面，要求：
- 使用深色主题（背景色：#1e1e1e，文字：#ffffff）
- 图表使用渐变色填充
- 添加动画效果（图表加载时渐入）
- 支持图表缩放和拖拽
- 鼠标悬停时显示详细数据
- 添加数据刷新按钮（模拟数据更新）
```

### 代码辅助设定（后端自动添加，最小化）

**重要**：代码层面**只添加最基础的HTML格式要求**，**不规定任何功能内容**。

代码会自动添加的基础设定（仅格式要求）：
```
格式要求（必须遵守）：
- 必须返回完整的HTML5文档（<!DOCTYPE html>开头）
- 包含<head>和<body>标签
- 使用UTF-8编码
- 所有代码内嵌在HTML中，可以直接在浏览器中运行
- 不要包含markdown代码块标记（```html等）
```

**不添加的内容**（完全由用户prompt决定）：
- ❌ 不要求必须包含图表
- ❌ 不要求必须包含筛选器
- ❌ 不要求必须包含下载功能
- ❌ 不要求必须使用特定图表库
- ❌ 不要求特定的样式或布局
- ❌ 不提供任何技术建议或默认要求

**用户prompt优先级**：用户自定义的prompt完全决定HTML内容，代码只确保格式正确。

## ✅ 优势总结

1. **灵活性高**：大模型可以生成任意复杂的HTML界面
2. **功能丰富**：可以包含筛选器、下载、交互等功能
3. **用户体验好**：完整的交互式界面
4. **实现简单**：前端只需要渲染HTML，不需要复杂的图表配置

## ⚠️ 风险提示

1. **安全风险**：HTML代码需要严格的安全验证
2. **质量风险**：大模型生成的HTML可能有错误
3. **性能风险**：大量HTML内容可能影响性能
4. **维护风险**：HTML代码难以调试和维护

## 🔑 关键实现要点总结

### 1. 用户自定义Prompt（核心）
- ✅ 用户通过"图表定制Prompt"输入框编写自己的提示词
- ✅ **完全决定HTML内容**：图表类型、筛选器、下载功能、样式等，完全由用户prompt决定
- ✅ 代码层面**只做最基础的HTML格式要求**（确保是HTML5文档），**不写死任何功能要求**

### 2. 前端纯执行（重点）
- ✅ **只负责执行**：前端收到HTML代码后，直接通过iframe渲染，不做任何内容判断
- ✅ **替换图表显示区域**：将原来的 `<div class="report-charts">` 中的ECharts渲染（canvas元素）
- ✅ **改为HTML显示区域**：使用 `<iframe :srcdoc="html_charts">` 渲染HTML内容
- ✅ **库资源准备**：前端需要提前准备好常用图表库的CDN资源（在index.html中预加载）
- ✅ **保留降级方案**：如果没有html_charts，则使用原有的ECharts渲染

### 3. 后端最小化设定
- ✅ 自动提取Excel数据样本
- ✅ **只添加最基础的HTML格式要求**（确保生成HTML5文档、UTF-8编码、内嵌代码等）
- ✅ **不规定任何功能内容**（不要求必须包含图表、筛选器、下载功能等）
- ✅ 安全验证和清理HTML内容

### 4. 数据流
```
用户输入自定义prompt（决定HTML内容）
    ↓
后端只添加基础HTML格式要求（不规定功能）
    ↓
阿里百炼根据用户prompt生成HTML代码
    ↓
后端验证HTML格式和安全性
    ↓
前端直接执行HTML代码（iframe渲染）
```

### 5. 核心原则对比

| 方面 | 代码层面 | 用户prompt |
|------|---------|-----------|
| HTML格式 | ✅ 规定（HTML5、UTF-8等） | ❌ 不涉及 |
| 图表类型 | ❌ 不规定 | ✅ 完全由用户决定 |
| 筛选器 | ❌ 不规定 | ✅ 完全由用户决定 |
| 下载功能 | ❌ 不规定 | ✅ 完全由用户决定 |
| 样式设计 | ❌ 不规定 | ✅ 完全由用户决定 |
| 交互逻辑 | ❌ 不规定 | ✅ 完全由用户决定 |

---

**文档版本**：v2.1  
**创建日期**：2025-12-04  
**更新日期**：2025-12-04  
**状态**：方案设计阶段，待实现  
**核心变更**：
- ✅ 强调用户自定义prompt完全决定HTML内容
- ✅ 代码层面只做最基础的HTML格式要求，不写死任何功能要求
- ✅ 前端只负责执行HTML代码，不做任何内容判断
- ✅ 前端需要提前准备好常用图表库的CDN资源


