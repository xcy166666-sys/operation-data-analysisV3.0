# Python Excel 数据提取与图表生成技术方案

## 📋 目录

1. [技术选型](#技术选型)
2. [Excel 数据提取](#excel-数据提取)
3. [数据处理与分析](#数据处理与分析)
4. [图表生成方案](#图表生成方案)
5. [完整实现示例](#完整实现示例)
6. [最佳实践](#最佳实践)

---

## 1. 技术选型

### 1.1 Excel 读取库对比

| 库名 | 优势 | 劣势 | 适用场景 |
|------|------|------|----------|
| **pandas** | 功能强大，数据分析友好，支持多种格式 | 内存占用较大 | **推荐**：数据分析、统计计算 |
| **openpyxl** | 精确控制，支持样式和格式 | 性能较慢，API复杂 | 需要保留格式的场景 |
| **xlrd** | 轻量级，读取速度快 | 不支持 .xlsx，只支持旧格式 | 旧版Excel文件 |

### 1.2 图表生成库对比

| 库名 | 优势 | 劣势 | 适用场景 |
|------|------|------|----------|
| **matplotlib** | 功能全面，可导出多种格式 | 样式较老，配置复杂 | 科学计算、静态图表 |
| **plotly** | 交互式图表，样式现代 | 文件较大，依赖多 | 交互式Web应用 |
| **ECharts配置** | 前端渲染，样式精美 | 需要前端支持 | **推荐**：Web应用 |

### 1.3 推荐技术栈

```python
# 数据提取
pandas >= 2.0.0        # 主要使用
openpyxl >= 3.1.0      # 备用（pandas依赖）

# 数据分析
numpy >= 1.24.0        # 数值计算（pandas依赖）

# 图表生成（选择其一）
# 方案A：生成ECharts配置（推荐，用于Web）
# 方案B：matplotlib（用于静态图片）
# 方案C：plotly（用于交互式图表）
```

---

## 2. Excel 数据提取

### 2.1 基础读取（pandas）

```python
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

class ExcelDataExtractor:
    """Excel数据提取器"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.df = None
    
    def read_excel(self, sheet_name: str = None, header: int = 0) -> pd.DataFrame:
        """
        读取Excel文件
        
        Args:
            sheet_name: Sheet名称，None表示读取第一个Sheet
            header: 表头行号，0表示第一行
            
        Returns:
            DataFrame对象
        """
        try:
            if sheet_name:
                self.df = pd.read_excel(
                    self.file_path, 
                    sheet_name=sheet_name,
                    header=header
                )
            else:
                # 读取第一个Sheet
                self.df = pd.read_excel(self.file_path, header=header)
            
            return self.df
        except Exception as e:
            raise Exception(f"读取Excel失败: {str(e)}")
    
    def read_all_sheets(self) -> Dict[str, pd.DataFrame]:
        """读取所有Sheet"""
        try:
            # 读取所有Sheet
            excel_file = pd.ExcelFile(self.file_path)
            sheets = {}
            
            for sheet_name in excel_file.sheet_names:
                sheets[sheet_name] = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            return sheets
        except Exception as e:
            raise Exception(f"读取所有Sheet失败: {str(e)}")
    
    def get_basic_info(self) -> Dict[str, Any]:
        """获取基本信息"""
        if self.df is None:
            raise Exception("请先读取Excel文件")
        
        return {
            "row_count": len(self.df),
            "column_count": len(self.df.columns),
            "columns": self.df.columns.tolist(),
            "data_types": self.df.dtypes.astype(str).to_dict(),
            "memory_usage": self.df.memory_usage(deep=True).sum(),
            "has_null": self.df.isnull().any().any(),
            "null_counts": self.df.isnull().sum().to_dict()
        }
    
    def get_numeric_columns(self) -> List[str]:
        """获取数值列"""
        if self.df is None:
            raise Exception("请先读取Excel文件")
        
        return self.df.select_dtypes(include=[np.number]).columns.tolist()
    
    def get_categorical_columns(self) -> List[str]:
        """获取分类列"""
        if self.df is None:
            raise Exception("请先读取Excel文件")
        
        return self.df.select_dtypes(include=['object']).columns.tolist()
    
    def get_date_columns(self) -> List[str]:
        """获取日期列"""
        if self.df is None:
            raise Exception("请先读取Excel文件")
        
        return self.df.select_dtypes(include=['datetime64']).columns.tolist()
```

### 2.2 数据清洗

```python
class DataCleaner:
    """数据清洗器"""
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗数据
        
        1. 删除空行
        2. 删除重复行
        3. 处理缺失值
        4. 数据类型转换
        """
        # 复制数据，避免修改原数据
        cleaned_df = df.copy()
        
        # 1. 删除完全空白的行
        cleaned_df = cleaned_df.dropna(how='all')
        
        # 2. 删除重复行
        cleaned_df = cleaned_df.drop_duplicates()
        
        # 3. 处理缺失值（数值列用0填充，文本列用空字符串）
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype in ['int64', 'float64']:
                cleaned_df[col] = cleaned_df[col].fillna(0)
            else:
                cleaned_df[col] = cleaned_df[col].fillna('')
        
        # 4. 尝试转换日期列
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype == 'object':
                try:
                    cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='ignore')
                except:
                    pass
        
        return cleaned_df
    
    @staticmethod
    def remove_outliers(df: pd.DataFrame, column: str, method: str = 'iqr') -> pd.DataFrame:
        """
        移除异常值
        
        Args:
            df: DataFrame
            column: 列名
            method: 方法 ('iqr' 或 'zscore')
        """
        if method == 'iqr':
            # IQR方法
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
        
        elif method == 'zscore':
            # Z-score方法
            z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
            return df[z_scores < 3]
        
        return df
```

### 2.3 数据统计

```python
class DataAnalyzer:
    """数据分析器"""
    
    @staticmethod
    def get_statistics(df: pd.DataFrame) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {}
        
        # 数值列统计
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            stats['numeric'] = {
                col: {
                    'mean': float(df[col].mean()),
                    'median': float(df[col].median()),
                    'std': float(df[col].std()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'sum': float(df[col].sum()),
                    'count': int(df[col].count())
                }
                for col in numeric_cols
            }
        
        # 分类列统计
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            stats['categorical'] = {
                col: {
                    'unique_count': int(df[col].nunique()),
                    'value_counts': df[col].value_counts().head(10).to_dict(),
                    'most_frequent': df[col].mode().iloc[0] if len(df[col].mode()) > 0 else None
                }
                for col in categorical_cols
            }
        
        return stats
    
    @staticmethod
    def detect_trends(df: pd.DataFrame, date_column: str, value_column: str) -> Dict[str, Any]:
        """
        检测趋势
        
        Args:
            df: DataFrame
            date_column: 日期列名
            value_column: 数值列名
        """
        # 确保日期列是datetime类型
        df[date_column] = pd.to_datetime(df[date_column])
        
        # 按日期排序
        df_sorted = df.sort_values(date_column)
        
        # 计算趋势
        values = df_sorted[value_column].values
        dates = df_sorted[date_column].values
        
        # 简单线性回归计算趋势
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        return {
            'trend': 'increasing' if slope > 0 else 'decreasing',
            'slope': float(slope),
            'first_value': float(values[0]),
            'last_value': float(values[-1]),
            'change_rate': float((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
        }
```

---

## 3. 数据处理与分析

### 3.1 数据聚合

```python
class DataAggregator:
    """数据聚合器"""
    
    @staticmethod
    def group_by(df: pd.DataFrame, group_column: str, agg_columns: Dict[str, List[str]]) -> pd.DataFrame:
        """
        分组聚合
        
        Args:
            df: DataFrame
            group_column: 分组列
            agg_columns: 聚合列和函数，如 {'sales': ['sum', 'mean'], 'quantity': ['sum']}
        """
        return df.groupby(group_column).agg(agg_columns).reset_index()
    
    @staticmethod
    def pivot_table(df: pd.DataFrame, index: str, columns: str, values: str, aggfunc: str = 'sum') -> pd.DataFrame:
        """透视表"""
        return pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=aggfunc)
    
    @staticmethod
    def time_series_aggregate(df: pd.DataFrame, date_column: str, value_column: str, freq: str = 'D') -> pd.DataFrame:
        """
        时间序列聚合
        
        Args:
            df: DataFrame
            date_column: 日期列
            value_column: 数值列
            freq: 频率 ('D'=日, 'W'=周, 'M'=月, 'Y'=年)
        """
        df[date_column] = pd.to_datetime(df[date_column])
        df = df.set_index(date_column)
        return df[value_column].resample(freq).sum().reset_index()
```

### 3.2 数据筛选

```python
class DataFilter:
    """数据筛选器"""
    
    @staticmethod
    def filter_by_condition(df: pd.DataFrame, condition: str) -> pd.DataFrame:
        """
        按条件筛选
        
        Args:
            df: DataFrame
            condition: 条件表达式，如 "sales > 1000 and category == 'A'"
        """
        return df.query(condition)
    
    @staticmethod
    def filter_by_date_range(df: pd.DataFrame, date_column: str, start_date: str, end_date: str) -> pd.DataFrame:
        """按日期范围筛选"""
        df[date_column] = pd.to_datetime(df[date_column])
        return df[(df[date_column] >= start_date) & (df[date_column] <= end_date)]
    
    @staticmethod
    def filter_top_n(df: pd.DataFrame, column: str, n: int, ascending: bool = False) -> pd.DataFrame:
        """筛选Top N"""
        return df.nlargest(n, column) if not ascending else df.nsmallest(n, column)
```

---

## 4. 图表生成方案

### 4.1 方案A：生成 ECharts 配置（推荐用于Web）

```python
from typing import Dict, List, Any
import json

class EChartsGenerator:
    """ECharts图表配置生成器"""
    
    @staticmethod
    def generate_line_chart(
        df: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        title: str = "折线图"
    ) -> Dict[str, Any]:
        """
        生成折线图配置
        
        Args:
            df: DataFrame
            x_column: X轴列名
            y_columns: Y轴列名列表（支持多条线）
            title: 图表标题
        """
        # 准备数据
        x_data = df[x_column].tolist()
        
        series = []
        for y_col in y_columns:
            series.append({
                "name": y_col,
                "type": "line",
                "data": df[y_col].tolist(),
                "smooth": True
            })
        
        return {
            "type": "line",
            "title": title,
            "config": {
                "title": {
                    "text": title,
                    "left": "center"
                },
                "tooltip": {
                    "trigger": "axis"
                },
                "legend": {
                    "data": y_columns,
                    "top": "10%"
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": True
                },
                "xAxis": {
                    "type": "category",
                    "boundaryGap": False,
                    "data": x_data
                },
                "yAxis": {
                    "type": "value"
                },
                "series": series
            }
        }
    
    @staticmethod
    def generate_bar_chart(
        df: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str = "柱状图",
        horizontal: bool = False
    ) -> Dict[str, Any]:
        """生成柱状图配置"""
        x_data = df[x_column].tolist()
        y_data = df[y_column].tolist()
        
        return {
            "type": "bar",
            "title": title,
            "config": {
                "title": {
                    "text": title,
                    "left": "center"
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "type": "shadow"
                    }
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": True
                },
                "xAxis": {
                    "type": "category" if not horizontal else "value",
                    "data": x_data if not horizontal else None
                },
                "yAxis": {
                    "type": "value" if not horizontal else "category",
                    "data": x_data if horizontal else None
                },
                "series": [{
                    "name": y_column,
                    "type": "bar",
                    "data": y_data,
                    "itemStyle": {
                        "color": "#5470c6"
                    }
                }]
            }
        }
    
    @staticmethod
    def generate_pie_chart(
        df: pd.DataFrame,
        name_column: str,
        value_column: str,
        title: str = "饼图"
    ) -> Dict[str, Any]:
        """生成饼图配置"""
        data = [
            {"name": row[name_column], "value": row[value_column]}
            for _, row in df.iterrows()
        ]
        
        return {
            "type": "pie",
            "title": title,
            "config": {
                "title": {
                    "text": title,
                    "left": "center"
                },
                "tooltip": {
                    "trigger": "item",
                    "formatter": "{a} <br/>{b}: {c} ({d}%)"
                },
                "legend": {
                    "orient": "vertical",
                    "left": "left"
                },
                "series": [{
                    "name": title,
                    "type": "pie",
                    "radius": "50%",
                    "data": data,
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowOffsetX": 0,
                            "shadowColor": "rgba(0, 0, 0, 0.5)"
                        }
                    }
                }]
            }
        }
    
    @staticmethod
    def generate_scatter_chart(
        df: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str = "散点图"
    ) -> Dict[str, Any]:
        """生成散点图配置"""
        data = [
            [row[x_column], row[y_column]]
            for _, row in df.iterrows()
        ]
        
        return {
            "type": "scatter",
            "title": title,
            "config": {
                "title": {
                    "text": title,
                    "left": "center"
                },
                "tooltip": {
                    "trigger": "item"
                },
                "xAxis": {
                    "type": "value",
                    "name": x_column
                },
                "yAxis": {
                    "type": "value",
                    "name": y_column
                },
                "series": [{
                    "name": title,
                    "type": "scatter",
                    "data": data
                }]
            }
        }
```

### 4.2 方案B：使用 matplotlib 生成图片

```python
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
from io import BytesIO
import base64

class MatplotlibChartGenerator:
    """Matplotlib图表生成器"""
    
    @staticmethod
    def generate_line_chart_image(
        df: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        title: str = "折线图"
    ) -> str:
        """
        生成折线图并返回base64图片
        
        Returns:
            base64编码的图片字符串
        """
        plt.figure(figsize=(10, 6))
        
        for y_col in y_columns:
            plt.plot(df[x_column], df[y_col], label=y_col, marker='o')
        
        plt.title(title, fontsize=14, fontweight='bold')
        plt.xlabel(x_column)
        plt.ylabel('Value')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # 转换为base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    @staticmethod
    def generate_bar_chart_image(
        df: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str = "柱状图"
    ) -> str:
        """生成柱状图并返回base64图片"""
        plt.figure(figsize=(10, 6))
        plt.bar(df[x_column], df[y_column], color='#5470c6')
        plt.title(title, fontsize=14, fontweight='bold')
        plt.xlabel(x_column)
        plt.ylabel(y_column)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
```

### 4.3 智能图表选择

```python
class SmartChartSelector:
    """智能图表选择器"""
    
    @staticmethod
    def select_chart_type(
        df: pd.DataFrame,
        analysis_request: str,
        numeric_cols: List[str],
        categorical_cols: List[str]
    ) -> List[Dict[str, Any]]:
        """
        根据数据特征和分析需求智能选择图表类型
        
        Returns:
            图表配置列表
        """
        charts = []
        request_lower = analysis_request.lower()
        
        # 趋势分析 -> 折线图
        if any(keyword in request_lower for keyword in ['趋势', '变化', 'trend', 'change']):
            if len(numeric_cols) >= 1:
                # 如果有日期列，用日期作为X轴
                date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
                if date_cols:
                    charts.append({
                        "type": "line",
                        "x_column": date_cols[0],
                        "y_columns": numeric_cols[:3]  # 最多3条线
                    })
                else:
                    charts.append({
                        "type": "line",
                        "x_column": df.index.name or "index",
                        "y_columns": numeric_cols[:3]
                    })
        
        # 对比分析 -> 柱状图
        elif any(keyword in request_lower for keyword in ['对比', '比较', 'compare', 'comparison']):
            if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
                charts.append({
                    "type": "bar",
                    "x_column": categorical_cols[0],
                    "y_column": numeric_cols[0]
                })
        
        # 占比分析 -> 饼图
        elif any(keyword in request_lower for keyword in ['占比', '比例', '分布', 'proportion', 'distribution']):
            if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                charts.append({
                    "type": "pie",
                    "name_column": categorical_cols[0],
                    "value_column": numeric_cols[0]
                })
        
        # 相关性分析 -> 散点图
        elif any(keyword in request_lower for keyword in ['相关', '关系', 'correlation', 'relationship']):
            if len(numeric_cols) >= 2:
                charts.append({
                    "type": "scatter",
                    "x_column": numeric_cols[0],
                    "y_column": numeric_cols[1]
                })
        
        # 默认：如果有数值列，生成折线图
        if not charts and len(numeric_cols) >= 1:
            charts.append({
                "type": "line",
                "x_column": df.index.name or "index",
                "y_columns": numeric_cols[:1]
            })
        
        return charts
```

---

## 5. 完整实现示例

### 5.1 完整的数据提取和图表生成流程

```python
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import numpy as np

class ExcelChartService:
    """Excel数据提取和图表生成服务"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.extractor = ExcelDataExtractor(str(file_path))
        self.cleaner = DataCleaner()
        self.analyzer = DataAnalyzer()
        self.chart_generator = EChartsGenerator()
        self.selector = SmartChartSelector()
    
    def process_and_generate_charts(
        self,
        analysis_request: str = "数据分析",
        sheet_name: str = None
    ) -> Dict[str, Any]:
        """
        完整流程：提取数据 -> 清洗 -> 分析 -> 生成图表
        
        Returns:
            {
                "data_info": {...},
                "statistics": {...},
                "charts": [...]
            }
        """
        # 1. 读取数据
        df = self.extractor.read_excel(sheet_name=sheet_name)
        
        # 2. 清洗数据
        df_cleaned = self.cleaner.clean_dataframe(df)
        
        # 3. 获取基本信息
        data_info = self.extractor.get_basic_info()
        
        # 4. 获取统计信息
        statistics = self.analyzer.get_statistics(df_cleaned)
        
        # 5. 识别列类型
        numeric_cols = self.extractor.get_numeric_columns()
        categorical_cols = self.extractor.get_categorical_columns()
        
        # 6. 智能选择图表类型
        chart_configs = self.selector.select_chart_type(
            df_cleaned,
            analysis_request,
            numeric_cols,
            categorical_cols
        )
        
        # 7. 生成图表配置
        charts = []
        for chart_config in chart_configs:
            chart_type = chart_config["type"]
            
            if chart_type == "line":
                chart = self.chart_generator.generate_line_chart(
                    df_cleaned,
                    chart_config["x_column"],
                    chart_config["y_columns"],
                    title=f"{chart_config['y_columns'][0]} 趋势分析"
                )
            elif chart_type == "bar":
                chart = self.chart_generator.generate_bar_chart(
                    df_cleaned,
                    chart_config["x_column"],
                    chart_config["y_column"],
                    title=f"{chart_config['y_column']} 对比分析"
                )
            elif chart_type == "pie":
                chart = self.chart_generator.generate_pie_chart(
                    df_cleaned,
                    chart_config["name_column"],
                    chart_config["value_column"],
                    title="占比分析"
                )
            elif chart_type == "scatter":
                chart = self.chart_generator.generate_scatter_chart(
                    df_cleaned,
                    chart_config["x_column"],
                    chart_config["y_column"],
                    title="相关性分析"
                )
            else:
                continue
            
            charts.append(chart)
        
        return {
            "data_info": data_info,
            "statistics": statistics,
            "charts": charts,
            "raw_data_sample": df_cleaned.head(10).to_dict('records')  # 前10行作为样本
        }
```

### 5.2 使用示例

```python
# 使用示例
if __name__ == "__main__":
    # 初始化服务
    service = ExcelChartService("data.xlsx")
    
    # 处理并生成图表
    result = service.process_and_generate_charts(
        analysis_request="分析销售趋势和产品分布",
        sheet_name="Sheet1"
    )
    
    # 输出结果
    print(f"数据行数: {result['data_info']['row_count']}")
    print(f"数据列数: {result['data_info']['column_count']}")
    print(f"生成图表数: {len(result['charts'])}")
    
    # 图表配置可以直接用于前端ECharts渲染
    for i, chart in enumerate(result['charts']):
        print(f"\n图表 {i+1}: {chart['title']}")
        print(f"类型: {chart['type']}")
        # chart['config'] 就是ECharts配置，可以直接传给前端
```

---

## 6. 最佳实践

### 6.1 性能优化

```python
# 1. 大文件处理：使用chunksize
def read_large_excel(file_path: str, chunk_size: int = 10000):
    """分块读取大文件"""
    chunks = []
    for chunk in pd.read_excel(file_path, chunksize=chunk_size):
        chunks.append(chunk)
    return pd.concat(chunks, ignore_index=True)

# 2. 只读取需要的列
df = pd.read_excel(file_path, usecols=['column1', 'column2'])

# 3. 使用read_only模式（openpyxl）
workbook = openpyxl.load_workbook(file_path, read_only=True)
```

### 6.2 错误处理

```python
def safe_read_excel(file_path: str) -> pd.DataFrame:
    """安全的Excel读取，包含错误处理"""
    try:
        # 尝试读取
        df = pd.read_excel(file_path)
        return df
    except FileNotFoundError:
        raise Exception(f"文件不存在: {file_path}")
    except PermissionError:
        raise Exception(f"文件被占用，无法读取: {file_path}")
    except Exception as e:
        raise Exception(f"读取Excel失败: {str(e)}")
```

### 6.3 内存管理

```python
# 及时释放内存
def process_excel_with_cleanup(file_path: str):
    df = pd.read_excel(file_path)
    # 处理数据
    result = process_data(df)
    # 删除DataFrame释放内存
    del df
    import gc
    gc.collect()
    return result
```

### 6.4 数据验证

```python
def validate_data(df: pd.DataFrame) -> Dict[str, bool]:
    """验证数据质量"""
    return {
        "has_data": len(df) > 0,
        "has_columns": len(df.columns) > 0,
        "has_numeric": len(df.select_dtypes(include=[np.number]).columns) > 0,
        "no_all_null": not df.isnull().all().any()
    }
```

---

## 7. 依赖安装

### 7.1 requirements.txt 添加

```txt
# Excel处理
pandas>=2.0.0
openpyxl>=3.1.2
xlrd>=2.0.1  # 可选，用于旧版Excel

# 数据分析
numpy>=1.24.0

# 图表生成（选择其一）
# 方案A：ECharts配置（无需额外库，直接生成JSON）
# 方案B：matplotlib（用于生成图片）
matplotlib>=3.7.0
# 方案C：plotly（用于交互式图表）
plotly>=5.14.0
```

### 7.2 安装命令

```bash
pip install pandas openpyxl numpy
# 如果使用matplotlib
pip install matplotlib
# 如果使用plotly
pip install plotly
```

---

## 8. 总结

### 8.1 推荐方案

1. **数据提取**：使用 `pandas` 读取Excel
2. **数据处理**：使用 `pandas` 和 `numpy` 进行数据清洗和分析
3. **图表生成**：生成 ECharts 配置（JSON格式），由前端渲染

### 8.2 优势

- ✅ **灵活性高**：可以根据数据特征动态生成图表
- ✅ **性能好**：后端处理数据，前端渲染图表
- ✅ **样式统一**：ECharts配置可以标准化
- ✅ **易于维护**：代码集中管理

### 8.3 注意事项

- ⚠️ 大文件需要分块处理
- ⚠️ 注意内存使用，及时释放DataFrame
- ⚠️ 数据验证很重要，避免空数据导致错误
- ⚠️ 图表类型选择需要根据实际数据特征

---

**文档版本**：v1.0  
**创建日期**：2025-12-03

