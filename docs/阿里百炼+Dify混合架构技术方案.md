# 阿里百炼API + Dify工作流混合架构技术实现方案

## 📋 目录

1. [方案概述](#方案概述)
2. [技术路线分析](#技术路线分析)
3. [系统架构设计](#系统架构设计)
4. [核心组件实现](#核心组件实现)
5. [数据流设计](#数据流设计)
6. [阿里百炼API集成](#阿里百炼api集成)
7. [Pyecharts图表生成](#pyecharts图表生成)
8. [完整实现示例](#完整实现示例)
9. [安全与性能优化](#安全与性能优化)
10. [实施步骤](#实施步骤)

---

## 1. 方案概述

### 1.1 技术路线

```
用户上传Excel文件
    ↓
后端程序（调度中心与组装器）
    ↓
并行处理
    ├─ 路径一：调用阿里百炼API
    │   ├─ 发送提示词 + Excel数据
    │   ├─ 百炼大模型理解表格
    │   └─ 生成Python绘图代码或JSON配置
    │       ↓
    │   安全执行代码/解析JSON
    │       ↓
    │   生成图表文件（Pyecharts）
    │       ↓
    │   产出物A：可视化图表
    │
    └─ 路径二：调用Dify工作流API
        ├─ Dify工作流处理
        │   ├─ 智能提取与计算核心数据
        │   └─ 大模型生成文字分析报告
        │       ↓
        └─ 产出物B：结构化数据与文字报告
    ↓
后端程序组装最终报告
    ├─ 合并图表、数据与文字
    └─ 生成完整的HTML/PDF报告
```

### 1.2 方案优势

- ✅ **格式适应性强**：阿里百炼大模型理解各种Excel格式，无需固定格式
- ✅ **数据准确性高**：Python执行基于真实数据，避免AI生成错误
- ✅ **职责分离清晰**：
  - 阿里百炼：理解数据，生成画图代码/配置
  - Python：执行画图，保证准确性
  - Dify：生成文字报告（不改动现有逻辑）
- ✅ **灵活可扩展**：AI生成的代码/配置可以处理各种复杂情况
- ✅ **成本可控**：直接调用API，成本可控
- ✅ **Dify部分无需改动**：文字生成部分保持现有实现

### 1.3 技术选型

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| **Excel理解** | 阿里百炼API（DashScope） | 直接调用API，理解Excel结构和数据 |
| **代码/配置生成** | 阿里百炼API | 生成Python画图代码或JSON配置 |
| **代码执行** | Python exec/eval | 安全执行生成的代码（如果生成代码） |
| **图表生成** | Pyecharts | 根据代码/配置生成ECharts图表 |
| **文字生成** | Dify工作流 | 生成文字分析报告（保持现有实现） |

---

## 2. 技术路线分析

### 2.1 可行性分析

#### ✅ 高度可行

1. **阿里百炼API能力**
   - 支持文件上传和解析
   - 支持代码生成和JSON配置生成
   - 支持多模态理解（Excel表格）
   - API调用简单直接

2. **代码/配置执行**
   - 如果生成代码：安全执行（沙箱环境）
   - 如果生成JSON：直接解析，更安全
   - Pyecharts稳定可靠

3. **与现有系统集成**
   - Dify文字生成部分完全不变
   - 只新增阿里百炼API调用
   - 前端无需修改
   - 报告格式保持一致

### 2.2 关键技术点

1. **阿里百炼API调用**
   - 直接调用DashScope API
   - 上传Excel文件或发送base64
   - 设计精确的提示词

2. **生成方式选择**
   - **方案A**：生成Python代码 → 执行代码 → Pyecharts生成图表
   - **方案B**：生成JSON配置 → 解析配置 → Pyecharts根据配置生成图表（推荐，更安全）

3. **Pyecharts集成**
   - 根据代码执行结果或JSON配置生成图表
   - 生成ECharts配置供前端使用

4. **Dify部分保持不变**
   - 文字生成工作流无需修改
   - 保持现有调用方式

---

## 3. 系统架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      Web前端                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  上传Excel   │  │  输入需求     │  │  查看报告     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
└─────────┼─────────────────┼─────────────────┼─────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────┐
│                    FastAPI后端                           │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │           报告生成服务 (ReportGenerator)          │  │
│  │          (调度中心与组装器)                        │  │
│  └──────────────────────────────────────────────────┘  │
│           │                    │                    │   │
│           ▼                    ▼                    ▼   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ 阿里百炼服务  │  │ Pyecharts    │  │ Dify服务     │ │
│  │(BailianAPI)  │  │(图表生成)    │  │(文字生成)    │ │
│  │              │  │              │  │(保持现有)    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘ │
│         │                 │                           │
│         ▼                 ▼                           │
│  ┌──────────────┐  ┌──────────────┐                  │
│  │ 代码执行引擎  │  │ 报告合并服务  │                  │
│  │(可选)       │  │              │                  │
│  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 阿里百炼API   │  │  Python环境   │  │   Dify API   │
│(DashScope)  │  │(Pyecharts)   │  │ (文字生成)   │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 3.2 核心服务模块

```
backend/app/services/
├── bailian_service.py         # 阿里百炼API服务（直接调用）
├── pyecharts_generator.py      # Pyecharts图表生成引擎
├── code_executor.py            # 代码执行引擎（如果生成代码）
├── chart_generator.py          # 图表生成服务（协调层）
├── dify_service.py            # Dify服务（已存在，复用，不改动）
└── report_merger.py            # 报告合并服务
```

---

## 4. 核心组件实现

### 4.1 阿里百炼API服务（直接调用）

```python
# backend/app/services/bailian_service.py
import httpx
import base64
import json
from typing import Dict, Any, Optional
from loguru import logger
from app.core.config import settings


class BailianService:
    """阿里百炼API服务（直接调用DashScope API）"""
    
    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.model = settings.DASHSCOPE_MODEL or "qwen-plus"
    
    async def analyze_excel_and_generate_chart_config(
        self,
        file_path: str,
        analysis_request: str,
        generate_type: str = "json"  # "json" 或 "code"
    ) -> Dict[str, Any]:
        """
        分析Excel并生成图表配置（代码或JSON）
        
        Args:
            file_path: Excel文件路径
            analysis_request: 分析需求
            generate_type: 生成类型 "json"（推荐）或 "code"
        
        Returns:
            {
                "success": bool,
                "config": dict/str,  # JSON配置或Python代码
                "data_info": dict,  # 数据信息
                "error": str
            }
        """
        try:
            # 1. 读取Excel文件并转换为base64
            with open(file_path, "rb") as f:
                file_content = f.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # 2. 读取文件内容作为文本（用于发送给API）
            # 也可以只发送数据样本，避免Token过多
            import pandas as pd
            df = pd.read_excel(file_path)
            data_sample = df.head(100).to_string()  # 只取前100行作为样本
            
            # 3. 构建Prompt
            if generate_type == "json":
                prompt = self._build_json_config_prompt(data_sample, analysis_request)
            else:
                prompt = self._build_code_generation_prompt(data_sample, analysis_request)
            
            # 4. 调用阿里百炼API
            response = await self._call_dashscope_api(prompt, file_base64, file_path)
            
            # 5. 提取生成的内容
            if generate_type == "json":
                config = self._extract_json_from_response(response)
            else:
                config = self._extract_code_from_response(response)
            
            return {
                "success": True,
                "config": config,
                "data_info": {},
                "error": None
            }
        
        except Exception as e:
            logger.error(f"[BailianService] 生成配置失败: {str(e)}")
            return {
                "success": False,
                "config": None,
                "data_info": None,
                "error": str(e)
            }
    
    def _build_json_config_prompt(self, data_sample: str, analysis_request: str) -> str:
        """构建JSON配置生成提示词（推荐方案）"""
        prompt = f"""你是一个数据分析专家。用户提供了Excel数据样本和分析需求，请生成图表配置JSON。

数据样本：
{data_sample}

分析需求：{analysis_request}

请按照以下要求生成图表配置JSON（只输出JSON，不要包含其他文字）：

格式如下：
[
  {{
    "chart_type": "line|bar|pie|scatter",
    "title": "图表标题",
    "x_column": "X轴列名",
    "y_columns": ["Y轴列名1", "Y轴列名2"],  # 对于line/bar可以多条
    "description": "图表说明"
  }}
]

示例：
如果数据有"日期"列和"销售额"列，分析需求是"分析销售趋势"，则生成：
[
  {{
    "chart_type": "line",
    "title": "销售趋势分析",
    "x_column": "日期",
    "y_columns": ["销售额"],
    "description": "展示销售额随时间的变化趋势"
  }}
]

请只返回JSON数组，不要包含markdown代码块标记。"""
        
        return prompt
    
    def _build_code_generation_prompt(self, data_sample: str, analysis_request: str) -> str:
        """构建代码生成提示词（备选方案）"""
        prompt = f"""你是一个数据分析专家。用户提供了Excel数据样本和分析需求，请生成Python代码来绘制图表。

数据样本：
{data_sample}

分析需求：{analysis_request}

请按照以下要求生成Python代码：

1. 使用pandas读取Excel文件（文件路径通过变量file_path传入）
2. 分析数据结构，识别数值列、分类列、日期列
3. 根据分析需求，使用pyecharts生成图表配置（ECharts格式）
4. 代码必须返回一个字典，格式如下：
   {{
       "charts": [
           {{
               "type": "line|bar|pie|scatter",
               "title": "图表标题",
               "config": {{...ECharts配置...}}
           }}
       ],
       "data_summary": {{
           "row_count": int,
           "column_count": int,
           "columns": list,
           "numeric_columns": list,
           "categorical_columns": list
       }}
   }}

5. 代码必须可以直接执行，不要包含示例代码或注释
6. 使用以下库：pandas, numpy, pyecharts
7. 图表配置必须是完整的ECharts配置JSON

请只返回可执行的Python代码，不要包含markdown代码块标记（```python等）。"""
        
        return prompt
    
    async def _call_dashscope_api(
        self,
        prompt: str,
        file_base64: str,
        file_name: str
    ) -> Dict[str, Any]:
        """调用阿里百炼DashScope API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求体
        # 注意：根据阿里百炼API实际文档调整
        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "file",
                                "file": {
                                    "data": file_base64,
                                    "name": file_name,
                                    "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                }
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "temperature": 0.1,  # 降低温度，生成更确定的内容
                "max_tokens": 4000
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            logger.info(f"[BailianService] 调用DashScope API - model={self.model}")
            response = await client.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result
    
    def _extract_json_from_response(self, response: Dict[str, Any]) -> list:
        """从API响应中提取JSON配置"""
        try:
            # 根据DashScope API的实际响应格式提取
            content = response.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 移除markdown代码块标记
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # 解析JSON
            config = json.loads(content)
            if not isinstance(config, list):
                config = [config]
            
            logger.info(f"[BailianService] 提取JSON配置成功，共 {len(config)} 个图表配置")
            return config
        
        except Exception as e:
            logger.error(f"[BailianService] 提取JSON配置失败: {str(e)}")
            raise Exception(f"无法从API响应中提取JSON配置: {str(e)}")
    
    def _extract_code_from_response(self, response: Dict[str, Any]) -> str:
        """从API响应中提取代码"""
        try:
            content = response.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 移除markdown代码块标记
            if "```python" in content:
                code = content.split("```python")[1].split("```")[0].strip()
            elif "```" in content:
                code = content.split("```")[1].split("```")[0].strip()
            else:
                code = content.strip()
            
            logger.info(f"[BailianService] 提取代码成功，长度: {len(code)} 字符")
            return code
        
        except Exception as e:
            logger.error(f"[BailianService] 提取代码失败: {str(e)}")
            raise Exception(f"无法从API响应中提取代码: {str(e)}")
```

### 4.2 代码执行引擎

```python
# backend/app/services/code_executor.py
import sys
import io
import contextlib
from typing import Dict, Any, Optional
from loguru import logger
import pandas as pd
import numpy as np


class CodeExecutor:
    """代码执行引擎（安全沙箱）"""
    
    # 允许使用的模块白名单
    ALLOWED_MODULES = {
        'pandas': pd,
        'numpy': np,
        'json': __import__('json'),
        'math': __import__('math'),
        'datetime': __import__('datetime'),
        'collections': __import__('collections'),
    }
    
    # 允许使用的内置函数
    ALLOWED_BUILTINS = {
        'len', 'range', 'enumerate', 'zip', 'list', 'dict', 'tuple',
        'str', 'int', 'float', 'bool', 'min', 'max', 'sum', 'abs',
        'round', 'sorted', 'reversed', 'any', 'all'
    }
    
    @classmethod
    def execute_chart_code(
        cls,
        code: str,
        file_path: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        执行图表生成代码
        
        Args:
            code: Python代码字符串
            file_path: Excel文件路径
            timeout: 超时时间（秒）
        
        Returns:
            {
                "success": bool,
                "result": dict,  # 执行结果
                "error": str,
                "stdout": str,   # 标准输出
                "stderr": str    # 错误输出
            }
        """
        # 1. 验证代码安全性
        if not cls._validate_code_safety(code):
            return {
                "success": False,
                "result": None,
                "error": "代码包含不安全的操作",
                "stdout": "",
                "stderr": ""
            }
        
        # 2. 准备执行环境
        safe_globals = cls._create_safe_globals()
        safe_globals['file_path'] = file_path
        
        # 3. 执行代码
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(stdout_capture):
                with contextlib.redirect_stderr(stderr_capture):
                    # 执行代码
                    exec(code, safe_globals, {})
                    
                    # 获取结果（假设代码定义了generate_charts函数）
                    if 'generate_charts' in safe_globals:
                        result = safe_globals['generate_charts'](file_path)
                    else:
                        # 尝试直接获取result变量
                        result = safe_globals.get('result', {})
                    
                    return {
                        "success": True,
                        "result": result,
                        "error": None,
                        "stdout": stdout_capture.getvalue(),
                        "stderr": stderr_capture.getvalue()
                    }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[CodeExecutor] 代码执行失败: {error_msg}")
            return {
                "success": False,
                "result": None,
                "error": error_msg,
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue()
            }
    
    @classmethod
    def _validate_code_safety(cls, code: str) -> bool:
        """验证代码安全性"""
        # 禁止的操作
        dangerous_patterns = [
            'import os',
            'import sys',
            'import subprocess',
            '__import__',
            'eval(',
            'exec(',
            'open(',
            'file(',
            'input(',
            'raw_input(',
            'compile(',
            'reload(',
            'exit(',
            'quit(',
        ]
        
        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if pattern in code_lower:
                logger.warning(f"[CodeExecutor] 检测到危险操作: {pattern}")
                return False
        
        return True
    
    @classmethod
    def _create_safe_globals(cls) -> Dict[str, Any]:
        """创建安全的全局环境"""
        safe_globals = {
            '__builtins__': {
                name: getattr(__builtins__, name)
                for name in cls.ALLOWED_BUILTINS
                if hasattr(__builtins__, name)
            }
        }
        
        # 添加允许的模块
        safe_globals.update(cls.ALLOWED_MODULES)
        
        return safe_globals
```

### 4.2 Pyecharts图表生成引擎

```python
# backend/app/services/pyecharts_generator.py
from pyecharts.charts import Line, Bar, Pie, Scatter
from pyecharts import options as opts
from pyecharts.globals import ThemeType
from typing import Dict, Any, List
import pandas as pd
import json
from loguru import logger


class PyechartsGenerator:
    """Pyecharts图表生成引擎"""
    
    @staticmethod
    def generate_charts_from_config(
        df: pd.DataFrame,
        chart_configs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        根据JSON配置生成图表
        
        Args:
            df: DataFrame（真实数据）
            chart_configs: 图表配置列表（来自阿里百炼）
        
        Returns:
            图表配置列表（ECharts格式）
        """
        charts = []
        
        for config in chart_configs:
            try:
                chart_type = config.get("chart_type", "line")
                title = config.get("title", "图表")
                x_column = config.get("x_column")
                y_columns = config.get("y_columns", [])
                
                if chart_type == "line":
                    chart = PyechartsGenerator._generate_line_chart(
                        df, x_column, y_columns, title
                    )
                elif chart_type == "bar":
                    chart = PyechartsGenerator._generate_bar_chart(
                        df, x_column, y_columns, title
                    )
                elif chart_type == "pie":
                    chart = PyechartsGenerator._generate_pie_chart(
                        df, x_column, y_columns[0] if y_columns else None, title
                    )
                elif chart_type == "scatter":
                    chart = PyechartsGenerator._generate_scatter_chart(
                        df, x_column, y_columns[0] if y_columns else None, title
                    )
                else:
                    logger.warning(f"[PyechartsGenerator] 不支持的图表类型: {chart_type}")
                    continue
                
                # 获取ECharts配置
                echarts_config = json.loads(chart.dump_options_with_quotes())
                
                charts.append({
                    "type": chart_type,
                    "title": title,
                    "config": echarts_config
                })
            
            except Exception as e:
                logger.error(f"[PyechartsGenerator] 生成图表失败: {str(e)}")
                continue
        
        return charts
    
    @staticmethod
    def _generate_line_chart(
        df: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        title: str
    ):
        """生成折线图"""
        x_data = df[x_column].tolist()
        
        chart = (
            Line(init_opts=opts.InitOpts(theme=ThemeType.MACARONS))
            .add_xaxis(x_data)
            .set_global_opts(
                title_opts=opts.TitleOpts(title=title),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                legend_opts=opts.LegendOpts(pos_top="10%"),
            )
        )
        
        for y_col in y_columns:
            chart.add_yaxis(
                series_name=y_col,
                y_axis=df[y_col].tolist(),
                is_smooth=True
            )
        
        return chart
    
    @staticmethod
    def _generate_bar_chart(
        df: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        title: str
    ):
        """生成柱状图"""
        x_data = df[x_column].tolist()
        
        chart = (
            Bar(init_opts=opts.InitOpts(theme=ThemeType.MACARONS))
            .add_xaxis(x_data)
            .set_global_opts(
                title_opts=opts.TitleOpts(title=title),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
            )
        )
        
        for y_col in y_columns:
            chart.add_yaxis(
                series_name=y_col,
                y_axis=df[y_col].tolist()
            )
        
        return chart
    
    @staticmethod
    def _generate_pie_chart(
        df: pd.DataFrame,
        name_column: str,
        value_column: str,
        title: str
    ):
        """生成饼图"""
        data = [
            [row[name_column], row[value_column]]
            for _, row in df.iterrows()
        ]
        
        chart = (
            Pie(init_opts=opts.InitOpts(theme=ThemeType.MACARONS))
            .add(
                series_name=title,
                data_pair=data,
                radius=["40%", "70%"]
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title=title),
                legend_opts=opts.LegendOpts(orient="vertical", pos_left="left")
            )
        )
        
        return chart
    
    @staticmethod
    def _generate_scatter_chart(
        df: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str
    ):
        """生成散点图"""
        chart = (
            Scatter(init_opts=opts.InitOpts(theme=ThemeType.MACARONS))
            .add_xaxis(df[x_column].tolist())
            .add_yaxis(
                series_name=title,
                y_axis=df[y_column].tolist()
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title=title),
                xaxis_opts=opts.AxisOpts(name=x_column),
                yaxis_opts=opts.AxisOpts(name=y_column)
            )
        )
        
        return chart
```

### 4.3 图表生成服务（协调层）

```python
# backend/app/services/chart_generator.py
from typing import Dict, Any
from loguru import logger
import pandas as pd
from app.services.bailian_service import BailianService
from app.services.pyecharts_generator import PyechartsGenerator
from app.services.code_executor import CodeExecutor


class ChartGenerator:
    """图表生成服务（协调阿里百炼和Pyecharts）"""
    
    def __init__(self):
        self.bailian_service = BailianService()
        self.pyecharts_generator = PyechartsGenerator()
        self.code_executor = CodeExecutor()
    
    async def generate_charts_from_excel(
        self,
        file_path: str,
        analysis_request: str,
        generate_type: str = "json"  # "json"（推荐）或 "code"
    ) -> Dict[str, Any]:
        """
        从Excel生成图表（完整流程）
        
        Args:
            file_path: Excel文件路径
            analysis_request: 分析需求
            generate_type: 生成类型 "json"（推荐）或 "code"
        
        Returns:
            {
                "success": bool,
                "charts": list,  # 图表配置列表
                "data_summary": dict,  # 数据摘要
                "error": str
            }
        """
        try:
            # 1. 调用阿里百炼API生成配置
            logger.info(f"[ChartGenerator] 调用阿里百炼API生成配置 - type={generate_type}")
            config_result = await self.bailian_service.analyze_excel_and_generate_chart_config(
                file_path=file_path,
                analysis_request=analysis_request,
                generate_type=generate_type
            )
            
            if not config_result["success"]:
                return {
                    "success": False,
                    "charts": [],
                    "data_summary": {},
                    "error": f"配置生成失败: {config_result['error']}"
                }
            
            # 2. 读取真实数据
            df = pd.read_excel(file_path)
            
            # 3. 根据生成类型处理
            if generate_type == "json":
                # 方案A：JSON配置（推荐）
                chart_configs = config_result["config"]
                charts = self.pyecharts_generator.generate_charts_from_config(df, chart_configs)
                
                # 提取数据摘要
                data_summary = {
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": df.columns.tolist(),
                    "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
                    "categorical_columns": df.select_dtypes(include=['object']).columns.tolist()
                }
            
            else:
                # 方案B：Python代码（备选）
                code = config_result["config"]
                logger.info(f"[ChartGenerator] 执行生成的代码")
                exec_result = self.code_executor.execute_chart_code(
                    code=code,
                    file_path=file_path
                )
                
                if not exec_result["success"]:
                    return {
                        "success": False,
                        "charts": [],
                        "data_summary": {},
                        "error": f"代码执行失败: {exec_result['error']}"
                    }
                
                result = exec_result["result"]
                charts = result.get("charts", [])
                data_summary = result.get("data_summary", {})
            
            # 4. 验证图表配置
            validated_charts = []
            for chart in charts:
                if self._validate_chart_config(chart):
                    validated_charts.append(chart)
                else:
                    logger.warning(f"[ChartGenerator] 跳过无效图表配置")
            
            return {
                "success": True,
                "charts": validated_charts,
                "data_summary": data_summary,
                "error": None
            }
        
        except Exception as e:
            logger.error(f"[ChartGenerator] 生成图表失败: {str(e)}")
            return {
                "success": False,
                "charts": [],
                "data_summary": {},
                "error": str(e)
            }
    
    def _validate_chart_config(self, chart: Dict[str, Any]) -> bool:
        """验证图表配置"""
        required_fields = ["type", "config"]
        
        for field in required_fields:
            if field not in chart:
                return False
        
        # 验证类型
        valid_types = ["line", "bar", "pie", "scatter", "area", "radar"]
        if chart["type"] not in valid_types:
            return False
        
        # 验证config是字典
        if not isinstance(chart["config"], dict):
            return False
        
        return True
```

### 4.4 报告合并服务

```python
# backend/app/services/report_merger.py
from typing import Dict, Any, List
from loguru import logger


class ReportMerger:
    """报告合并服务"""
    
    @staticmethod
    def merge_report(
        text_content: str,
        charts: List[Dict[str, Any]],
        data_summary: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        合并文字和图表生成最终报告
        
        Args:
            text_content: Dify生成的文字内容
            charts: 图表配置列表
            data_summary: 数据摘要
        
        Returns:
            完整的报告内容
        """
        report_content = {
            "text": text_content,
            "charts": charts,
            "tables": [],
            "metrics": {}
        }
        
        # 如果有数据摘要，添加到metrics中
        if data_summary:
            report_content["metrics"] = {
                "row_count": data_summary.get("row_count", 0),
                "column_count": data_summary.get("column_count", 0),
                "columns": data_summary.get("columns", []),
                "numeric_columns": data_summary.get("numeric_columns", []),
                "categorical_columns": data_summary.get("categorical_columns", [])
            }
        
        logger.info(f"[ReportMerger] 报告合并完成 - 文字长度: {len(text_content)}, 图表数: {len(charts)}")
        
        return report_content
```

---

## 5. 数据流设计

### 5.1 完整数据流

```
1. 用户上传Excel文件
   └─> 后端保存文件到 uploads/

2. 用户提交分析需求
   └─> 后端接收：session_id, file_id, analysis_request

3. 后端程序（调度中心）并行处理（异步）

   A. 路径一：阿里百炼API流程
      ├─> 读取Excel文件
      ├─> 提取数据样本（避免Token过多）
      ├─> 调用阿里百炼API（DashScope）
      │   ├─> 发送提示词 + 数据样本
      │   ├─> 百炼大模型理解表格
      │   └─> 生成Python绘图代码或JSON配置
      ├─> 解析生成的内容
      │   ├─> 如果生成JSON：直接解析
      │   └─> 如果生成代码：安全执行代码
      ├─> Pyecharts根据配置/结果生成图表
      │   ├─> 读取真实数据（不是样本）
      │   └─> 生成ECharts图表配置
      └─> 产出物A：可视化图表

   B. 路径二：Dify工作流流程（保持现有实现）
      ├─> 上传文件到Dify（或传base64）
      ├─> 调用Dify工作流
      │   ├─> 智能提取与计算核心数据
      │   └─> 大模型生成文字分析报告
      ├─> 接收Dify返回的文字内容
      └─> 产出物B：结构化数据与文字报告

4. 后端程序（组装器）合并
   ├─> 合并图表（来自路径一）
   ├─> 合并文字（来自路径二）
   └─> 生成最终报告结构

5. 保存报告
   └─> 保存到数据库

6. 返回前端
   └─> 前端渲染文字和图表（左图 + 右文）
```

### 5.2 错误处理流程

```
代码生成失败
    ↓
尝试使用备用方案（简单图表生成）
    ↓
如果仍然失败
    ↓
返回错误信息，提示用户
```

---

## 6. 阿里百炼API集成

### 6.1 API配置

```python
# backend/app/core/config.py 添加配置

class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # 阿里百炼DashScope配置
    DASHSCOPE_API_KEY: Optional[str] = Field(default=None, env="DASHSCOPE_API_KEY")
    DASHSCOPE_MODEL: str = Field(
        default="qwen-plus",
        env="DASHSCOPE_MODEL"
    )
```

### 6.2 环境变量配置

```env
# .env 文件添加
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_MODEL=qwen-plus  # 可以改为 qwen-turbo 或其他模型
```

### 6.3 API调用方式

阿里百炼DashScope API支持两种方式：

1. **文件上传方式**（推荐）
   - 先上传文件到DashScope，获取file_id
   - 然后调用API时引用file_id

2. **Base64方式**
   - 直接将文件内容base64编码后传递

### 6.4 生成方式选择

#### 方案A：生成JSON配置（推荐）

**优势**：
- ✅ 更安全：不需要执行代码
- ✅ 容错性强：JSON格式错误容易检测
- ✅ 易于维护：配置格式统一

**实现**：
```python
# AI生成JSON配置
config = [
    {
        "chart_type": "line",
        "x_column": "日期",
        "y_columns": ["销售额"]
    }
]

# Pyecharts根据配置生成图表
charts = pyecharts_generator.generate_charts_from_config(df, config)
```

#### 方案B：生成Python代码（备选）

**优势**：
- ✅ 灵活性高：可以处理复杂逻辑
- ✅ 功能强大：可以自定义数据处理

**劣势**：
- ⚠️ 需要代码执行，安全性要求高
- ⚠️ 容错性较差：代码错误难以修复

**实现**：
```python
# AI生成Python代码
code = "def generate_charts(file_path): ..."

# 安全执行代码
result = code_executor.execute_chart_code(code, file_path)

# Pyecharts根据结果生成图表
charts = result["charts"]
```

### 6.5 推荐方案

**推荐使用方案A（JSON配置）**：
- 更安全
- 更易维护
- 容错性强
- 符合"容错性强"的设计原则

---

## 7. Pyecharts图表生成

### 7.1 Pyecharts简介

Pyecharts是一个用于生成ECharts图表的Python库，可以：
- 生成ECharts配置JSON（供前端使用）
- 生成HTML文件（包含完整图表）
- 生成图片（PNG/JPEG）

### 7.2 安装依赖

```txt
# requirements.txt 添加
pyecharts>=2.0.0
```

### 7.3 使用方式

```python
from pyecharts.charts import Line
from pyecharts import options as opts

# 创建图表
chart = Line()
chart.add_xaxis(["1月", "2月", "3月"])
chart.add_yaxis("销售额", [100, 200, 300])

# 获取ECharts配置（供前端使用）
echarts_config = json.loads(chart.dump_options_with_quotes())

# 或生成HTML
html = chart.render_embed()
```

### 7.4 代码执行引擎（备选方案，如果生成代码）

### 7.1 安全措施

1. **代码验证**
   - 禁止危险操作（文件操作、系统调用等）
   - 白名单机制（只允许特定模块）

2. **沙箱环境**
   - 限制执行时间
   - 限制内存使用
   - 隔离执行环境

3. **错误处理**
   - 捕获所有异常
   - 记录详细日志
   - 提供友好的错误信息

### 7.2 增强版代码执行（可选）

```python
# 使用更安全的执行方式（可选）
import subprocess
import tempfile
import os

class SecureCodeExecutor:
    """更安全的代码执行器（使用子进程）"""
    
    @staticmethod
    def execute_in_subprocess(code: str, file_path: str) -> Dict[str, Any]:
        """在子进程中执行代码"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # 在子进程中执行
            result = subprocess.run(
                ['python', temp_file, file_path],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                # 解析输出（假设输出是JSON）
                import json
                return json.loads(result.stdout)
            else:
                raise Exception(result.stderr)
        
        finally:
            # 清理临时文件
            os.unlink(temp_file)
```

---

## 8. 完整实现示例

### 8.1 修改报告生成接口

```python
# backend/app/api/v1/operation.py 修改 generate_report 函数

from app.services.chart_generator import ChartGenerator
from app.services.report_merger import ReportMerger
from app.services.dify_service import DifyService
import asyncio

@router.post("/generate", response_model=SuccessResponse)
async def generate_report(
    session_id: int = Form(...),
    file_id: int = Form(...),
    analysis_request: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """生成报告（新架构：阿里百炼API + Dify工作流）"""
    
    # ... 前面的验证代码不变（获取文件路径、工作流配置等）...
    
    # 获取文字生成工作流配置（使用现有的工作流配置，不改动）
    text_workflow = get_text_workflow(db, function_key)  # 使用现有的工作流
    text_api_url = text_workflow.config.get("api_url")
    text_api_key = text_workflow.config.get("api_key")
    
    # 并行处理
    chart_generator = ChartGenerator()
    report_merger = ReportMerger()
    
    # 任务1：生成图表（阿里百炼API + Pyecharts）
    async def generate_charts():
        return await chart_generator.generate_charts_from_excel(
            file_path=str(file_path),
            analysis_request=analysis_request,
            generate_type="json"  # 推荐使用JSON配置
        )
    
    # 任务2：生成文字（Dify工作流 - 保持现有实现，不改动）
    async def generate_text():
        # 使用现有的Dify调用逻辑（完全不变）
        if workflow_type == "chatflow":
            # Chatflow: 先上传文件到Dify
            upload_result = await DifyService.upload_file(
                api_url=url_file,
                api_key=api_key,
                file_path=str(file_path),
                file_name=file_path.name,
                user_id=dify_user
            )
            
            if not upload_result.get("success"):
                return "文字生成失败：文件上传失败"
            
            dify_file_id = upload_result.get("data", {}).get("id")
            
            inputs = {
                file_param: dify_file_id,
                query_param: analysis_request,  # 提示词中明确只生成文字分析
            }
        else:
            # Workflow: 读取文件内容并转换为base64
            with open(file_path, "rb") as f:
                file_content = f.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            inputs = {
                file_param: file_base64,
                f"sys.{query_param}": analysis_request,
            }
        
        # 调用Dify工作流（保持现有逻辑）
        result = await DifyService.run_workflow(
            api_url=url_work,
            api_key=api_key,
            workflow_id="1",
            user_id=current_user.id,
            function_key=function_key,
            inputs=inputs,
            conversation_id=session_id,
            response_mode="blocking",
            workflow_type=workflow_type
        )
        
        if not result.get("success"):
            return "文字生成失败"
        
        dify_data = result.get("data", {})
        if workflow_type == "chatflow":
            report_text = dify_data.get("answer", "") or dify_data.get("text", "")
        else:
            workflow_output = dify_data.get("data", {}).get("outputs", {})
            report_text = workflow_output.get("text", "") or dify_data.get("text", "")
        
        return report_text
    
    # 并行执行
    charts_task = generate_charts()
    text_task = generate_text()
    
    charts_result, report_text = await asyncio.gather(
        charts_task,
        text_task,
        return_exceptions=True
    )
    
    # 处理异常
    if isinstance(charts_result, Exception):
        logger.error(f"图表生成异常: {charts_result}")
        charts_result = {"success": False, "charts": [], "data_summary": {}}
    
    if isinstance(report_text, Exception):
        logger.error(f"文字生成异常: {report_text}")
        report_text = "报告生成失败，请重试。"
    
    # 合并报告
    report_content = report_merger.merge_report(
        text_content=report_text if isinstance(report_text, str) else "报告生成失败",
        charts=charts_result.get("charts", []) if isinstance(charts_result, dict) else [],
        data_summary=charts_result.get("data_summary", {}) if isinstance(charts_result, dict) else {}
    )
    
    # ... 后面的保存和返回代码不变 ...
```

---

## 9. 安全与性能优化

### 9.1 安全措施

1. **API密钥管理**
   - 使用环境变量存储
   - 不在代码中硬编码
   - 定期轮换密钥

2. **代码执行安全**
   - 白名单机制
   - 超时控制
   - 资源限制

3. **错误信息处理**
   - 不暴露敏感信息
   - 记录详细日志
   - 用户友好的错误提示

### 9.2 性能优化

1. **并行处理**
   - 图表生成和文字生成并行
   - 使用 asyncio.gather

2. **缓存机制**
   - 相同文件的代码可以缓存
   - 避免重复调用API

3. **超时控制**
   - API调用设置超时
   - 代码执行设置超时

### 9.3 错误回退

```python
# 如果阿里百炼失败，使用备用方案
if not charts_result["success"]:
    # 使用简单的图表生成（基于pandas）
    charts_result = simple_chart_generator.generate(file_path)
```

---

## 10. 实施步骤

### 10.1 第一阶段：基础集成

1. **配置阿里百炼API**
   - [ ] 申请DashScope API密钥
   - [ ] 配置环境变量
   - [ ] 测试API连接

2. **实现基础服务**
   - [ ] 创建 BailianService（阿里百炼API服务）
   - [ ] 创建 PyechartsGenerator（图表生成引擎）
   - [ ] 创建 ChartGenerator（协调层）
   - [ ] 创建 CodeExecutor（可选，如果生成代码）

3. **测试图表生成**
   - [ ] 测试阿里百炼API调用
   - [ ] 测试JSON配置解析
   - [ ] 测试Pyecharts生成图表
   - [ ] 验证结果格式

### 10.2 第二阶段：集成到现有系统

1. **修改报告生成接口**
   - [ ] 修改 generate_report
   - [ ] 实现并行处理
   - [ ] 集成报告合并

2. **修改Dify提示词**
   - [ ] 更新提示词（只生成文字）
   - [ ] 测试文字生成

3. **测试完整流程**
   - [ ] 端到端测试
   - [ ] 错误处理测试
   - [ ] 性能测试

### 10.3 第三阶段：优化和增强

1. **性能优化**
   - [ ] 实现缓存
   - [ ] 优化API调用
   - [ ] 优化代码执行

2. **安全增强**
   - [ ] 加强代码验证
   - [ ] 实现沙箱环境
   - [ ] 添加监控

3. **功能扩展**
   - [ ] 支持更多图表类型
   - [ ] 支持复杂数据分析
   - [ ] 支持自定义代码模板

---

## 11. 依赖安装

### 11.1 requirements.txt 添加

```txt
# 数据处理（已有）
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.2

# HTTP客户端（已有）
httpx>=0.26.0

# 图表生成（新增）
pyecharts>=2.0.0
```

### 11.2 安装命令

```bash
# 只需安装pyecharts
pip install pyecharts

# 其他依赖都已存在
# pandas, numpy, openpyxl, httpx 都已存在
```

---

## 12. 总结

### 12.1 方案优势

- ✅ **格式适应性强**：阿里百炼大模型理解各种Excel格式，无需固定格式
- ✅ **数据准确性高**：Pyecharts基于真实数据生成图表，避免AI生成错误
- ✅ **职责分离清晰**：
  - 阿里百炼：理解数据，生成画图配置
  - Python：执行画图，保证准确性
  - Dify：生成文字报告（不改动）
- ✅ **容错性强**：推荐生成JSON配置，不生成代码，更安全
- ✅ **成本可控**：直接调用API，成本可控
- ✅ **Dify部分无需改动**：文字生成保持现有实现

### 12.2 关键技术点

1. **阿里百炼API集成**：直接调用DashScope API，无需LangChain
2. **Prompt工程**：设计精确的提示词，确保生成正确的JSON配置
3. **Pyecharts集成**：根据JSON配置生成图表，基于真实数据
4. **Dify部分保持不变**：文字生成工作流完全复用现有实现
5. **并行处理**：图表生成和文字生成并行，提高性能

### 12.3 注意事项

- ⚠️ 需要申请阿里百炼DashScope API密钥
- ⚠️ 推荐使用JSON配置方案，更安全
- ⚠️ 如果使用代码生成方案，需要严格把控代码执行安全性
- ⚠️ 需要完善的错误处理和回退机制
- ⚠️ 需要监控API调用成本和性能

---

**文档版本**：v1.0  
**创建日期**：2025-12-03

