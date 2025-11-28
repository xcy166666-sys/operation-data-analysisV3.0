"""
报告图片生成工具
将报告内容渲染为PNG图片，避免PDF中文乱码问题
"""
import io
from typing import Dict, List, Any, Optional
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
import re
from pathlib import Path


def get_chinese_font(size: int = 20):
    """获取中文字体，支持Windows和Linux"""
    import platform
    import os
    
    font_paths = []
    
    if platform.system() == "Windows":
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",     # 黑体
            "C:/Windows/Fonts/simsun.ttc",     # 宋体
        ]
    else:
        # Linux/Mac
        font_paths = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/System/Library/Fonts/PingFang.ttc",  # macOS
        ]
    
    # 尝试项目字体目录
    backend_dir = Path(__file__).parent.parent.parent
    project_fonts = [
        backend_dir / "fonts" / "SourceHanSansCN-Regular.otf",
        backend_dir / "fonts" / "wqy-microhei.ttc",
        backend_dir / "fonts" / "simhei.ttf",
    ]
    
    for font_path in project_fonts + [Path(p) for p in font_paths]:
        try:
            if font_path.exists():
                font = ImageFont.truetype(str(font_path), size)
                logger.info(f"[图片生成] 使用字体: {font_path}")
                return font
        except Exception as e:
            logger.debug(f"[图片生成] 字体加载失败 {font_path}: {str(e)}")
            continue
    
    # 使用默认字体（可能不支持中文）
    try:
        return ImageFont.load_default()
    except:
        return None


def parse_markdown_to_lines(text: str) -> List[Dict[str, Any]]:
    """将Markdown文本解析为结构化行"""
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            lines.append({"type": "blank", "content": ""})
            continue
        
        if line.startswith('# '):
            lines.append({"type": "h1", "content": line[2:].strip()})
        elif line.startswith('## '):
            lines.append({"type": "h2", "content": line[3:].strip()})
        elif line.startswith('### '):
            lines.append({"type": "h3", "content": line[4:].strip()})
        elif line.startswith('- ') or line.startswith('* '):
            lines.append({"type": "list", "content": line[2:].strip()})
        else:
            lines.append({"type": "text", "content": line})
    
    return lines


def wrap_text(text: str, font, max_width: int) -> List[str]:
    """将文本按最大宽度换行"""
    if not font:
        # 简单估算：每个字符约10像素
        chars_per_line = max_width // 10
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > chars_per_line and current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length
            else:
                current_line.append(word)
                current_length += word_length
        
        if current_line:
            lines.append(' '.join(current_line))
        return lines
    
    lines = []
    words = text.split()
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word]) if current_line else word
        try:
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]
            if width > max_width and current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                current_line.append(word)
        except:
            # 如果字体不支持，使用简单估算
            if len(test_line) > max_width // 10 and current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                current_line.append(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines if lines else [text]


def generate_report_image(
    title: str,
    report_content: Dict[str, Any],
    session_id: int,
    width: int = 1200,
    padding: int = 40,
    line_spacing: int = 8,
    page_margin: int = 60
) -> bytes:
    """
    生成报告图片
    
    Args:
        title: 报告标题
        report_content: 报告内容，包含text, charts, tables, metrics
        session_id: 会话ID
        width: 图片宽度（像素）
        padding: 内边距
        line_spacing: 行间距
        page_margin: 页面边距
    
    Returns:
        PNG图片的字节数据
    """
    logger.info(f"[图片生成] ====== 开始生成报告图片 ======")
    logger.info(f"[图片生成] 标题: {title}, session_id={session_id}")
    
    try:
        # 获取字体
        title_font = get_chinese_font(36)
        h1_font = get_chinese_font(28)
        h2_font = get_chinese_font(24)
        h3_font = get_chinese_font(20)
        text_font = get_chinese_font(18)
        small_font = get_chinese_font(14)
        
        # 计算内容区域宽度
        content_width = width - 2 * padding
        
        # 解析文本内容
        text_content = report_content.get("text", "")
        lines = parse_markdown_to_lines(text_content) if text_content else []
        
        # 计算所需高度
        y = padding
        y += 60  # 标题高度
        y += 30  # 标题后间距
        
        for line in lines:
            if line["type"] == "blank":
                y += line_spacing * 2
            elif line["type"] == "h1":
                y += 40
            elif line["type"] == "h2":
                y += 35
            elif line["type"] == "h3":
                y += 30
            else:
                wrapped = wrap_text(line["content"], text_font, content_width)
                y += len(wrapped) * (24 + line_spacing)
        
        # 添加图表和表格的高度估算
        charts = report_content.get("charts", [])
        tables = report_content.get("tables", [])
        y += len(charts) * 300  # 每个图表约300像素高
        y += len(tables) * 200  # 每个表格约200像素高
        
        # 添加底部边距
        y += page_margin
        
        # 确保最小高度
        height = max(y, 800)
        
        logger.info(f"[图片生成] 图片尺寸: {width}x{height}")
        
        # 创建图片
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # 绘制标题
        y = padding
        title_lines = wrap_text(title, title_font, content_width)
        for line in title_lines:
            try:
                draw.text((padding, y), line, fill='#1a1a1a', font=title_font)
                bbox = title_font.getbbox(line) if title_font else (0, 0, len(line) * 20, 30)
                y += (bbox[3] - bbox[1]) + line_spacing
            except Exception as e:
                logger.warning(f"[图片生成] 绘制标题行失败: {str(e)}")
                y += 40
        
        y += 20  # 标题后间距
        
        # 绘制分隔线
        draw.line([(padding, y), (width - padding, y)], fill='#e0e0e0', width=2)
        y += 30
        
        # 绘制文本内容
        for line in lines:
            if line["type"] == "blank":
                y += line_spacing * 2
                continue
            
            content = line["content"]
            wrapped = wrap_text(content, text_font, content_width)
            
            if line["type"] == "h1":
                font = h1_font
                color = '#2c3e50'
                spacing = 15
            elif line["type"] == "h2":
                font = h2_font
                color = '#34495e'
                spacing = 12
            elif line["type"] == "h3":
                font = h3_font
                color = '#34495e'
                spacing = 10
            elif line["type"] == "list":
                font = text_font
                color = '#333333'
                spacing = 8
                wrapped = [f"• {w}" for w in wrapped]
            else:
                font = text_font
                color = '#333333'
                spacing = 8
            
            for text_line in wrapped:
                try:
                    draw.text((padding, y), text_line, fill=color, font=font)
                    bbox = font.getbbox(text_line) if font else (0, 0, len(text_line) * 12, 20)
                    y += (bbox[3] - bbox[1]) + spacing
                except Exception as e:
                    logger.warning(f"[图片生成] 绘制文本行失败: {str(e)}")
                    y += 24
        
        # 绘制图表说明
        if charts:
            y += 20
            try:
                draw.text((padding, y), "图表", fill='#2c3e50', font=h1_font)
                y += 40
            except:
                y += 40
            
            for i, chart in enumerate(charts):
                chart_title = str(chart.get('title', f'图表 {i+1}'))
                chart_text = f"图表 {i+1}: {chart_title}"
                wrapped = wrap_text(chart_text, text_font, content_width)
                for line in wrapped:
                    try:
                        draw.text((padding, y), line, fill='#333333', font=text_font)
                        y += 28
                    except:
                        y += 28
                y += 20
        
        # 绘制表格
        if tables:
            y += 20
            try:
                draw.text((padding, y), "数据表格", fill='#2c3e50', font=h1_font)
                y += 40
            except:
                y += 40
            
            for table_data in tables:
                try:
                    columns = table_data.get("columns", [])
                    data = table_data.get("data", [])
                    
                    if columns and data:
                        # 绘制表头
                        header_bg_color = '#3498db'
                        header_text_color = '#ffffff'
                        cell_height = 35
                        col_width = content_width // len(columns)
                        
                        x = padding
                        for col in columns:
                            col_label = str(col.get("label", col.get("prop", "")))
                            # 绘制表头背景
                            draw.rectangle(
                                [x, y, x + col_width, y + cell_height],
                                fill=header_bg_color
                            )
                            # 绘制表头文本
                            draw.text(
                                (x + 10, y + 8),
                                col_label[:15],  # 限制长度
                                fill=header_text_color,
                                font=small_font
                            )
                            x += col_width
                        
                        y += cell_height
                        
                        # 绘制数据行（最多10行）
                        for row_idx, row in enumerate(data[:10]):
                            x = padding
                            bg_color = '#f8f9fa' if row_idx % 2 == 0 else '#ffffff'
                            
                            for col_idx, col in enumerate(columns):
                                cell_value = str(row.get(col.get("prop", ""), ""))
                                # 绘制单元格背景
                                draw.rectangle(
                                    [x, y, x + col_width, y + cell_height],
                                    fill=bg_color,
                                    outline='#e0e0e0'
                                )
                                # 绘制单元格文本
                                draw.text(
                                    (x + 10, y + 8),
                                    cell_value[:15],  # 限制长度
                                    fill='#333333',
                                    font=small_font
                                )
                                x += col_width
                            
                            y += cell_height
                        
                        y += 20
                except Exception as e:
                    logger.warning(f"[图片生成] 绘制表格失败: {str(e)}")
                    y += 50
        
        # 绘制指标
        metrics = report_content.get("metrics", {})
        if metrics:
            y += 20
            try:
                draw.text((padding, y), "关键指标", fill='#2c3e50', font=h1_font)
                y += 40
            except:
                y += 40
            
            for key, value in metrics.items():
                metric_text = f"{key}: {value}"
                wrapped = wrap_text(metric_text, text_font, content_width)
                for line in wrapped:
                    try:
                        draw.text((padding, y), line, fill='#333333', font=text_font)
                        y += 28
                    except:
                        y += 28
                y += 10
        
        # 转换为字节
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        image_bytes = buffer.read()
        buffer.close()
        
        logger.info(f"[图片生成] 图片生成成功 - 大小: {len(image_bytes)} bytes")
        logger.info(f"[图片生成] ====== 图片生成完成 ======")
        
        return image_bytes
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"[图片生成] ====== 图片生成失败 ======")
        logger.error(f"[图片生成] 错误类型: {type(e).__name__}")
        logger.error(f"[图片生成] 错误消息: {str(e)}")
        logger.error(f"[图片生成] 完整堆栈:\n{error_traceback}")
        logger.error(f"[图片生成] ====== 错误结束 ======")
        raise Exception(f"图片生成失败: {str(e)}")

