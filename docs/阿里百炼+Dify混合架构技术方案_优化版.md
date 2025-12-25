# LangChain + Dify 混合架构技术实现方案（优化版）

## 📋 目录

1. [方案概述](#方案概述)
2. [技术路线分析](#技术路线分析)
3. [系统架构设计](#系统架构设计)
4. [核心组件实现](#核心组件实现)
5. [数据流设计](#数据流设计)
6. [LangChain集成方案](#langchain集成方案)
7. [Pyecharts图表引擎](#pyecharts图表引擎)
8. [完整实现示例](#完整实现示例)
9. [方案亮点总结](#方案亮点总结)
10. [安全与性能优化](#安全与性能优化)
11. [实施步骤](#实施步骤)

---

## 1. 方案概述

### 1.1 技术路线（优化版）

```
用户上传Excel
    ↓
1. Pandas读取与清洗
   ├─ 读取Excel文件
   ├─ 数据清洗和预处理
   └─ 提取统计摘要
    ↓
2. 数据采样 + LangChain + 阿里百炼（Qwen-Plus）
   ├─ 截取数据样本（避免Token过多）
   ├─ 通过LangChain调用Qwen-Plus
   └─ 生成绘图配置JSON（不生成代码）
    ↓
3. Pyecharts画图引擎
   ├─ 根据JSON配置读取真实数据
   └─ 生成ECharts图表配置/HTML
    ↓
4. Pandas提取统计摘要 + Dify工作流
   ├─ 只发送统计摘要（不发送原始数据）
   └─ 生成文字分析报告
    ↓
5. 综合拼接
   ├─ 文字内容（Dify）
   └─ 图表配置（Pyecharts生成）
    ↓
6. 生成最终报告（左图 + 右文）
```

### 1.2 方案优势

- ✅ **容错性强**：AI只输出JSON配置，不直接写代码，避免生成不可运行的代码
- ✅ **安全性高**：只发送统计摘要给Dify，原始数据不离开本地，保护隐私并节省Token
- ✅ **可维护性高**：
  - 修改图表样式：只需修改Python函数 `generate_chart_html`
  - 修改报告样式：只需调整Dify的Prompt，无需重启后端
  - 切换大模型：在LangChain初始化时替换模型即可（如qwen-plus → Ollama）
- ✅ **格式适应性强**：Qwen-Plus理解各种Excel格式，无需固定格式
- ✅ **数据准确性高**：Pyecharts基于真实数据生成图表，避免AI生成错误
- ✅ **性能优化**：数据统计本地完成，只发送摘要，减少API调用成本

### 1.3 技术选型

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| **数据处理** | Pandas | 读取、清洗、统计分析Excel数据 |
| **AI理解** | LangChain + 阿里百炼(Qwen-Plus) | 理解数据样本，生成绘图配置JSON |
| **图表生成** | Pyecharts | 根据JSON配置生成ECharts图表 |
| **文字生成** | Dify工作流 | 基于统计摘要生成文字分析报告 |
| **模型切换** | LangChain | 可灵活切换为本地Ollama等模型 |

---

## 2. 技术路线分析

### 2.1 可行性分析

#### ✅ 高度可行

1. **LangChain + Qwen-Plus能力**
   - LangChain提供统一的LLM调用接口
   - Qwen-Plus支持多模态理解（Excel表格）
   - 可以灵活切换模型（Qwen-Plus → Ollama等）
   - 输出JSON配置，容错性强

2. **Pyecharts图表生成**
   - 基于真实数据生成图表，准确性高
   - 可以生成ECharts配置或HTML
   - 样式统一，易于维护

3. **数据安全性**
   - 原始数据不离开本地
   - 只发送统计摘要给Dify
   - 保护用户隐私

4. **与现有系统集成**
   - 复用现有的Dify集成
   - 前端无需修改
   - 报告格式保持一致

### 2.2 关键技术点

1. **数据采样策略**
   - 大文件截取样本（避免Token过多）
   - 保持数据代表性

2. **JSON配置格式**
   - 定义清晰的配置结构
   - 易于解析和验证

3. **Pyecharts集成**
   - 根据JSON配置生成图表
   - 支持多种图表类型

4. **统计摘要提取**
   - 使用Pandas提取关键统计信息
   - 格式化为Dify可理解的文本

---

## 3. 系统架构设计

### 3.1 整体架构（优化版）

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
│  └──────────────────────────────────────────────────┘  │
│           │                    │                    │   │
│           ▼                    ▼                    ▼   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Pandas处理    │  │ LangChain+   │  │ Pyecharts    │ │
│  │(读取/清洗)    │  │ Qwen-Plus    │  │(图表生成)    │ │
│  │              │  │(生成JSON配置)│  │              │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                  │          │
│         ▼                 ▼                  ▼          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ 统计摘要提取  │  │ Dify工作流   │  │ 报告合并服务  │ │
│  │(Pandas)     │  │(文字生成)    │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  本地处理     │  │ 阿里云API    │  │   Dify API   │
│ (Pandas)    │  │(Qwen-Plus)   │  │ (文字生成)   │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 3.2 核心服务模块

```
backend/app/services/
├── data_processor.py          # Pandas数据处理服务
├── langchain_chart_service.py # LangChain + Qwen-Plus图表配置生成
├── pyecharts_generator.py     # Pyecharts图表生成引擎
├── dify_service.py           # Dify服务（已存在，复用）
└── report_merger.py          # 报告合并服务
```

---

## 4. 核心组件实现

### 4.1 Pandas数据处理服务

```python
# backend/app/services/data_processor.py
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from loguru import logger


class DataProcessor:
    """Pandas数据处理服务"""
    
    @staticmethod
    def read_and_clean_excel(file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        读取并清洗Excel文件
        
        Args:
            file_path: Excel文件路径
            sheet_name: Sheet名称（可选）
        
        Returns:
            清洗后的DataFrame
        """
        try:
            # 读取Excel
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
            
            # 数据清洗
            # 1. 删除完全空白的行
            df = df.dropna(how='all')
            
            # 2. 删除重复行
            df = df.drop_duplicates()
            
            # 3. 处理缺失值
            for col in df.columns:
                if df[col].dtype in ['int64', 'float64']:
                    df[col] = df[col].fillna(0)
                else:
                    df[col] = df[col].fillna('')
            
            logger.info(f"[DataProcessor] 数据读取成功 - 行数: {len(df)}, 列数: {len(df.columns)}")
            return df
        
        except Exception as e:
            logger.error(f"[DataProcessor] 读取Excel失败: {str(e)}")
            raise
    
    @staticmethod
    def get_data_sample(df: pd.DataFrame, max_rows: int = 100) -> pd.DataFrame:
        """
        获取数据样本（用于AI分析，避免Token过多）
        
        Args:
            df: DataFrame
            max_rows: 最大行数
        
        Returns:
            数据样本
        """
        if len(df) <= max_rows:
            return df
        
        # 如果数据量大，采样
        # 策略：取前N行 + 后N行 + 中间均匀采样
        if len(df) > max_rows * 2:
            sample_size = max_rows // 3
            head = df.head(sample_size)
            tail = df.tail(sample_size)
            middle = df.iloc[sample_size:-sample_size].sample(n=max_rows - sample_size * 2)
            return pd.concat([head, middle, tail]).reset_index(drop=True)
        else:
            return df.head(max_rows)
    
    @staticmethod
    def extract_statistics_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """
        提取统计摘要（用于发送给Dify，不发送原始数据）
        
        Args:
            df: DataFrame
        
        Returns:
            统计摘要字典
        """
        summary = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "data_types": df.dtypes.astype(str).to_dict(),
        }
        
        # 数值列统计
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            summary["numeric_statistics"] = {}
            for col in numeric_cols:
                summary["numeric_statistics"][col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "sum": float(df[col].sum())
                }
        
        # 分类列统计
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            summary["categorical_statistics"] = {}
            for col in categorical_cols:
                value_counts = df[col].value_counts().head(10).to_dict()
                summary["categorical_statistics"][col] = {
                    "unique_count": int(df[col].nunique()),
                    "top_values": {str(k): int(v) for k, v in value_counts.items()}
                }
        
        return summary
    
    @staticmethod
    def format_summary_for_dify(summary: Dict[str, Any]) -> str:
        """
        将统计摘要格式化为Dify可理解的文本
        
        Args:
            summary: 统计摘要字典
        
        Returns:
            格式化的文本
        """
        text = f"数据概览：\n"
        text += f"- 总行数：{summary['row_count']}\n"
        text += f"- 总列数：{summary['column_count']}\n"
        text += f"- 列名：{', '.join(summary['columns'])}\n\n"
        
        if "numeric_statistics" in summary:
            text += "数值列统计：\n"
            for col, stats in summary["numeric_statistics"].items():
                text += f"- {col}：平均值={stats['mean']:.2f}, 中位数={stats['median']:.2f}, "
                text += f"最小值={stats['min']:.2f}, 最大值={stats['max']:.2f}\n"
            text += "\n"
        
        if "categorical_statistics" in summary:
            text += "分类列统计：\n"
            for col, stats in summary["categorical_statistics"].items():
                text += f"- {col}：唯一值数量={stats['unique_count']}, "
                text += f"主要值={', '.join(list(stats['top_values'].keys())[:5])}\n"
        
        return text
```

### 4.2 LangChain + Qwen-Plus图表配置生成服务

```python
# backend/app/services/langchain_chart_service.py
from langchain.llms import Tongyi  # 阿里百炼
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import Dict, Any, Optional
import json
from loguru import logger
from app.core.config import settings


class LangChainChartService:
    """LangChain + Qwen-Plus图表配置生成服务"""
    
    def __init__(self):
        # 初始化LangChain + 阿里百炼
        # 可以切换为其他模型，如：Ollama
        self.llm = Tongyi(
            model_name="qwen-plus",  # 可以改为 "qwen-turbo" 或其他
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
            temperature=0.1  # 降低温度，生成更确定的配置
        )
    
    def generate_chart_configs(
        self,
        data_sample: str,  # 数据样本（JSON格式或文本格式）
        analysis_request: str
    ) -> Dict[str, Any]:
        """
        生成图表配置JSON（不生成代码）
        
        Args:
            data_sample: 数据样本（格式化的字符串）
            analysis_request: 分析需求
        
        Returns:
            {
                "success": bool,
                "chart_configs": list,  # 图表配置列表
                "error": str
            }
        """
        try:
            # 构建Prompt
            prompt = self._build_chart_config_prompt(data_sample, analysis_request)
            
            # 调用LangChain
            logger.info(f"[LangChainChartService] 调用Qwen-Plus生成图表配置")
            response = self.llm(prompt)
            
            # 解析JSON响应
            chart_configs = self._parse_json_response(response)
            
            return {
                "success": True,
                "chart_configs": chart_configs,
                "error": None
            }
        
        except Exception as e:
            logger.error(f"[LangChainChartService] 生成图表配置失败: {str(e)}")
            return {
                "success": False,
                "chart_configs": [],
                "error": str(e)
            }
    
    def _build_chart_config_prompt(self, data_sample: str, analysis_request: str) -> str:
        """构建图表配置生成提示词"""
        prompt = f"""你是一个数据分析专家。用户提供了Excel数据样本和分析需求，请生成图表配置JSON。

数据样本：
{data_sample}

分析需求：{analysis_request}

请按照以下要求生成图表配置JSON（只输出JSON，不要包含其他文字）：

1. 分析数据特征，选择合适的图表类型（line, bar, pie, scatter等）
2. 根据分析需求确定需要绘制的列
3. 生成JSON配置，格式如下：
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
    
    def _parse_json_response(self, response: str) -> list:
        """解析JSON响应"""
        try:
            # 移除可能的markdown代码块标记
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            # 解析JSON
            configs = json.loads(response)
            
            if not isinstance(configs, list):
                configs = [configs]
            
            logger.info(f"[LangChainChartService] 解析成功，生成 {len(configs)} 个图表配置")
            return configs
        
        except json.JSONDecodeError as e:
            logger.error(f"[LangChainChartService] JSON解析失败: {str(e)}")
            logger.debug(f"[LangChainChartService] 响应内容: {response[:500]}")
            return []
```

### 4.3 Pyecharts图表生成引擎

```python
# backend/app/services/pyecharts_generator.py
from pyecharts.charts import Line, Bar, Pie, Scatter
from pyecharts import options as opts
from pyecharts.globals import ThemeType
from typing import Dict, Any, List
import pandas as pd
from loguru import logger


class PyechartsGenerator:
    """Pyecharts图表生成引擎"""
    
    @staticmethod
    def generate_chart_html(
        df: pd.DataFrame,
        chart_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据配置生成图表HTML/ECharts配置
        
        Args:
            df: DataFrame（真实数据）
            chart_config: 图表配置JSON
        
        Returns:
            {
                "type": str,
                "title": str,
                "config": dict,  # ECharts配置
                "html": str  # HTML字符串（可选）
            }
        """
        chart_type = chart_config.get("chart_type", "line")
        title = chart_config.get("title", "图表")
        x_column = chart_config.get("x_column")
        y_columns = chart_config.get("y_columns", [])
        
        try:
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
                raise ValueError(f"不支持的图表类型: {chart_type}")
            
            # 获取ECharts配置
            echarts_config = chart.dump_options_with_quotes()
            
            return {
                "type": chart_type,
                "title": title,
                "config": json.loads(echarts_config),
                "html": chart.render_embed()  # 可选：生成HTML
            }
        
        except Exception as e:
            logger.error(f"[PyechartsGenerator] 生成图表失败: {str(e)}")
            raise
    
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
        data = [
            [row[x_column], row[y_column]]
            for _, row in df.iterrows()
        ]
        
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

3. Pandas数据处理
   ├─> 读取Excel文件
   ├─> 数据清洗和预处理
   ├─> 提取统计摘要
   └─> 获取数据样本（用于AI分析）

4. 并行处理（异步）

   A. 图表生成流程：
      ├─> 格式化数据样本（转为文本或JSON）
      ├─> 调用LangChain + Qwen-Plus
      │   ├─> 分析数据样本
      │   └─> 生成图表配置JSON（不生成代码）
      ├─> 解析JSON配置
      └─> Pyecharts根据配置生成图表
          ├─> 读取真实数据（不是样本）
          └─> 生成ECharts配置

   B. 文字生成流程：
      ├─> 提取统计摘要（Pandas）
      ├─> 格式化为文本
      ├─> 调用Dify工作流（只发送摘要，不发送原始数据）
      └─> 接收文字分析报告

5. 报告合并
   ├─> 合并文字内容（来自Dify）
   ├─> 合并图表配置（来自Pyecharts）
   └─> 生成最终报告结构

6. 保存报告
   └─> 保存到数据库

7. 返回前端
   └─> 前端渲染文字和图表（左图 + 右文）
```

---

## 6. LangChain集成方案

### 6.1 LangChain配置

```python
# backend/app/core/config.py 添加配置

class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # 阿里百炼配置（用于LangChain）
    DASHSCOPE_API_KEY: Optional[str] = Field(default=None, env="DASHSCOPE_API_KEY")
    LLM_MODEL: str = Field(default="qwen-plus", env="LLM_MODEL")  # 可切换为其他模型
```

### 6.2 环境变量配置

```env
# .env 文件添加
DASHSCOPE_API_KEY=your_dashscope_api_key_here
LLM_MODEL=qwen-plus  # 可以改为 qwen-turbo 或本地模型
```

### 6.3 切换模型示例

```python
# 使用阿里百炼
from langchain.llms import Tongyi
llm = Tongyi(model_name="qwen-plus", dashscope_api_key=api_key)

# 切换为本地Ollama（未来扩展）
from langchain.llms import Ollama
llm = Ollama(model="llama2")
```

---

## 7. Pyecharts图表引擎

### 7.1 安装依赖

```txt
# requirements.txt 添加
pyecharts>=2.0.0
snapshot-selenium>=0.1.0  # 可选，用于生成图片
```

### 7.2 图表配置JSON格式

```json
[
  {
    "chart_type": "line",
    "title": "销售趋势分析",
    "x_column": "日期",
    "y_columns": ["销售额", "利润"],
    "description": "展示销售和利润随时间的变化趋势"
  },
  {
    "chart_type": "bar",
    "title": "产品销量对比",
    "x_column": "产品名称",
    "y_columns": ["销量"],
    "description": "对比不同产品的销量"
  }
]
```

---

## 8. 完整实现示例

### 8.1 修改报告生成接口

```python
# backend/app/api/v1/operation.py 修改 generate_report 函数

from app.services.data_processor import DataProcessor
from app.services.langchain_chart_service import LangChainChartService
from app.services.pyecharts_generator import PyechartsGenerator
from app.services.report_merger import ReportMerger
from app.services.dify_service import DifyService
import asyncio
import json

@router.post("/generate", response_model=SuccessResponse)
async def generate_report(
    session_id: int = Form(...),
    file_id: int = Form(...),
    analysis_request: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """生成报告（新架构：LangChain + Pyecharts + Dify）"""
    
    # ... 前面的验证代码不变 ...
    
    # 初始化服务
    data_processor = DataProcessor()
    langchain_service = LangChainChartService()
    pyecharts_generator = PyechartsGenerator()
    report_merger = ReportMerger()
    
    # 1. Pandas读取和清洗数据
    df = data_processor.read_and_clean_excel(str(file_path))
    
    # 2. 提取统计摘要（用于Dify）
    statistics_summary = data_processor.extract_statistics_summary(df)
    summary_text = data_processor.format_summary_for_dify(statistics_summary)
    
    # 3. 获取数据样本（用于AI分析）
    data_sample_df = data_processor.get_data_sample(df, max_rows=100)
    data_sample_text = data_sample_df.to_string()  # 或转为JSON
    
    # 并行处理
    # 任务1：生成图表配置（LangChain + Qwen-Plus）
    async def generate_charts():
        # 调用LangChain生成图表配置JSON
        chart_result = langchain_service.generate_chart_configs(
            data_sample=data_sample_text,
            analysis_request=analysis_request
        )
        
        if not chart_result["success"]:
            return {"success": False, "charts": [], "error": chart_result["error"]}
        
        # 使用Pyecharts根据配置生成图表
        charts = []
        for config in chart_result["chart_configs"]:
            try:
                chart = pyecharts_generator.generate_chart_html(df, config)
                charts.append({
                    "type": chart["type"],
                    "title": chart["title"],
                    "config": chart["config"]
                })
            except Exception as e:
                logger.error(f"生成图表失败: {str(e)}")
                continue
        
        return {"success": True, "charts": charts, "error": None}
    
    # 任务2：生成文字（Dify工作流）
    async def generate_text():
        # 调用Dify（只发送统计摘要，不发送原始数据）
        # 获取文字生成工作流配置
        text_workflow = get_text_workflow(db, function_key)
        text_api_url = text_workflow.config.get("api_url")
        text_api_key = text_workflow.config.get("api_key")
        
        # 构建提示词（包含统计摘要）
        prompt = f"""基于以下数据统计摘要，生成详细的数据分析报告。

统计摘要：
{summary_text}

分析需求：{analysis_request}

请生成专业的文字分析报告，不要生成图表配置。"""
        
        result = await DifyService.run_workflow(
            api_url=text_api_url,
            api_key=text_api_key,
            workflow_id="1",
            user_id=current_user.id,
            function_key=function_key,
            inputs={"query": prompt},  # 只发送文本，不发送文件
            conversation_id=session_id,
            response_mode="blocking",
            workflow_type="chatflow"
        )
        
        if not result.get("success"):
            return "文字生成失败"
        
        dify_data = result.get("data", {})
        return dify_data.get("answer", "") or dify_data.get("text", "")
    
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
        charts_result = {"success": False, "charts": []}
    if isinstance(report_text, Exception):
        report_text = "报告生成失败，请重试。"
    
    # 合并报告
    report_content = report_merger.merge_report(
        text_content=report_text if isinstance(report_text, str) else "报告生成失败",
        charts=charts_result.get("charts", []) if isinstance(charts_result, dict) else [],
        data_summary=statistics_summary
    )
    
    # ... 后面的保存和返回代码不变 ...
```

---

## 9. 方案亮点总结

### 9.1 容错性强

- **AI只输出JSON配置**：不直接写代码，避免生成不可运行的代码
- **示例**：AI输出 `{"chart_type": "line", "x_column": "A", "y_columns": ["B"]}`
- **优势**：即使AI理解有偏差，JSON格式错误也容易检测和修复
- **实际绘图**：由本地Python（Pyecharts）稳定执行

### 9.2 安全性高

- **数据统计本地完成**：使用Pandas在本地完成所有数据统计
- **只发送摘要**：只发送统计摘要（Summary）给Dify
- **原始数据不离开本地**：数百万条用户数据不需要上传到Dify
- **优势**：
  - 保护用户隐私
  - 节省Token使用量
  - 降低API调用成本

### 9.3 可维护性高

#### 修改图表样式
- **只需修改Python函数**：`generate_chart_html`
- **无需修改AI提示词**
- **无需重启后端**（如果使用热重载）

#### 修改报告样式
- **只需调整Dify的Prompt**
- **无需修改代码**
- **无需重启后端**

#### 切换大模型
- **在LangChain初始化时替换**：`qwen-plus` → `Ollama`（本地模型）
- **代码无需修改**
- **统一接口**

---

## 10. 安全与性能优化

### 10.1 安全措施

1. **数据隐私保护**
   - 原始数据不离开本地
   - 只发送统计摘要

2. **API密钥管理**
   - 使用环境变量存储
   - 不在代码中硬编码

3. **错误处理**
   - 不暴露敏感信息
   - 记录详细日志

### 10.2 性能优化

1. **数据采样**
   - 大文件只采样部分数据给AI
   - 保持数据代表性

2. **并行处理**
   - 图表生成和文字生成并行
   - 使用 asyncio.gather

3. **缓存机制**
   - 相同文件的统计摘要可以缓存
   - 避免重复计算

---

## 11. 实施步骤

### 11.1 第一阶段：基础集成

1. **安装依赖**
   - [ ] 安装 `langchain`
   - [ ] 安装 `dashscope`（阿里百炼SDK）
   - [ ] 安装 `pyecharts`

2. **实现基础服务**
   - [ ] 创建 DataProcessor
   - [ ] 创建 LangChainChartService
   - [ ] 创建 PyechartsGenerator

3. **测试图表生成**
   - [ ] 测试LangChain调用
   - [ ] 测试JSON配置解析
   - [ ] 测试Pyecharts生成图表

### 11.2 第二阶段：集成到现有系统

1. **修改报告生成接口**
   - [ ] 修改 generate_report
   - [ ] 实现并行处理
   - [ ] 集成报告合并

2. **修改Dify提示词**
   - [ ] 更新提示词（只生成文字，不生成图表）
   - [ ] 测试文字生成

3. **测试完整流程**
   - [ ] 端到端测试
   - [ ] 错误处理测试
   - [ ] 性能测试

### 11.3 第三阶段：优化和增强

1. **性能优化**
   - [ ] 实现数据采样策略
   - [ ] 实现缓存机制
   - [ ] 优化API调用

2. **功能扩展**
   - [ ] 支持更多图表类型
   - [ ] 支持自定义图表样式
   - [ ] 支持模型切换（Ollama等）

---

## 12. 依赖安装

### 12.1 requirements.txt 添加

```txt
# LangChain
langchain>=0.1.0
dashscope>=1.10.0  # 阿里百炼SDK

# Pyecharts
pyecharts>=2.0.0

# 数据处理（已有）
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.2
```

### 12.2 安装命令

```bash
pip install langchain dashscope pyecharts
```

---

## 13. 总结

### 13.1 方案优势

- ✅ **容错性强**：AI只输出JSON配置，不生成代码
- ✅ **安全性高**：原始数据不离开本地，只发送摘要
- ✅ **可维护性高**：修改样式只需改Python函数或Prompt
- ✅ **灵活可扩展**：可以切换模型（Qwen-Plus → Ollama）

### 13.2 关键技术点

1. **数据采样**：大文件采样，避免Token过多
2. **JSON配置**：AI生成配置，Python执行绘图
3. **统计摘要**：只发送摘要给Dify，保护隐私
4. **Pyecharts**：基于真实数据生成图表，准确性高

### 13.3 注意事项

- ⚠️ 需要申请阿里百炼API密钥
- ⚠️ 数据采样策略需要优化，保持代表性
- ⚠️ JSON配置格式需要严格验证
- ⚠️ 需要完善的错误处理和回退机制

---

**文档版本**：v2.0（优化版）  
**创建日期**：2025-12-03  
**最后更新**：2025-12-03

