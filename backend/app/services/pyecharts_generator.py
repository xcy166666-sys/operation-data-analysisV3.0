"""
Pyecharts图表生成引擎
"""
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
                
                if not x_column or not y_columns:
                    logger.warning(f"[PyechartsGenerator] 配置缺少必要字段: x_column={x_column}, y_columns={y_columns}")
                    continue
                
                # 检查列是否存在
                if x_column not in df.columns:
                    logger.warning(f"[PyechartsGenerator] X轴列不存在: {x_column}")
                    continue
                
                for y_col in y_columns:
                    if y_col not in df.columns:
                        logger.warning(f"[PyechartsGenerator] Y轴列不存在: {y_col}")
                        continue
                
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
                logger.error(f"[PyechartsGenerator] 生成图表失败: {str(e)}, config: {config}")
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

