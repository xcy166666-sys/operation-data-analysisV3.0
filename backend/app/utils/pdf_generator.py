"""
PDF生成工具
"""
import io
import base64
from typing import Dict, List, Any, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from loguru import logger


# 全局变量：存储已注册的中文字体名称
CHINESE_FONT_NAME = None

# 注册中文字体（优先使用项目字体，然后尝试系统字体）
def register_chinese_font():
    """注册中文字体，返回字体名称"""
    global CHINESE_FONT_NAME
    
    if CHINESE_FONT_NAME:
        return CHINESE_FONT_NAME
    
    import platform
    import os
    from pathlib import Path
    
    # 获取backend目录的绝对路径
    backend_dir = Path(__file__).parent.parent.parent
    
    # 优先使用项目内的字体文件（按优先级排序）
    project_fonts = [
        ("fonts/SourceHanSansCN-Regular.otf", "SourceHanSans-CN"),
        ("fonts/SourceHanSansSC-Regular.otf", "SourceHanSans-SC"),
        ("fonts/NotoSansSC-Regular.otf", "NotoSans-SC"),
        ("fonts/wqy-microhei.ttc", "WQYMicroHei"),
        ("fonts/simhei.ttf", "SimHei"),
    ]
    
    logger.info(f"[PDF生成] Backend目录: {backend_dir}")
    logger.info(f"[PDF生成] 开始尝试注册项目字体...")
    
    for font_file, font_name in project_fonts:
        font_path = backend_dir / font_file
        try:
            if font_path.exists():
                logger.info(f"[PDF生成] 找到字体文件: {font_path}")
                # 对于 .ttc 文件，尝试指定索引
                if font_path.suffix.lower() == '.ttc':
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', str(font_path), subfontIndex=0))
                        CHINESE_FONT_NAME = 'ChineseFont'
                        logger.info(f"[PDF生成] ✓ 成功注册项目中文字体: {font_name} ({font_path})")
                        return CHINESE_FONT_NAME
                    except Exception as e1:
                        # 如果指定索引失败，尝试不指定索引
                        try:
                            pdfmetrics.registerFont(TTFont('ChineseFont', str(font_path)))
                            CHINESE_FONT_NAME = 'ChineseFont'
                            logger.info(f"[PDF生成] ✓ 成功注册项目中文字体: {font_name} ({font_path})")
                            return CHINESE_FONT_NAME
                        except Exception as e2:
                            logger.warning(f"[PDF生成] 注册项目字体失败 {font_path}: {str(e2)}")
                            continue
                else:
                    # .ttf 或 .otf 文件直接注册
                    pdfmetrics.registerFont(TTFont('ChineseFont', str(font_path)))
                    CHINESE_FONT_NAME = 'ChineseFont'
                    logger.info(f"[PDF生成] ✓ 成功注册项目中文字体: {font_name} ({font_path})")
                    return CHINESE_FONT_NAME
            else:
                logger.debug(f"[PDF生成] 项目字体文件不存在: {font_path}")
        except Exception as e:
            logger.warning(f"[PDF生成] 注册项目字体失败 {font_path}: {str(e)}")
            continue
    
    logger.info(f"[PDF生成] 项目字体未找到，尝试使用系统字体...")
    
    # 如果项目字体不存在，尝试系统字体
    if platform.system() == "Windows":
        # Windows系统字体路径（按优先级排序）
        font_paths = [
            ("C:/Windows/Fonts/simhei.ttf", "SimHei"),         # 黑体（最稳定）
            ("C:/Windows/Fonts/msyh.ttc", "Microsoft YaHei"),  # 微软雅黑
            ("C:/Windows/Fonts/simsun.ttc", "SimSun"),         # 宋体
        ]
        
        for font_path, font_display_name in font_paths:
            try:
                if os.path.exists(font_path):
                    logger.info(f"[PDF生成] 找到系统字体: {font_path}")
                    # 对于 .ttc 文件，尝试指定索引
                    if font_path.endswith('.ttc'):
                        try:
                            pdfmetrics.registerFont(TTFont('ChineseFont', font_path, subfontIndex=0))
                            CHINESE_FONT_NAME = 'ChineseFont'
                            logger.info(f"[PDF生成] ✓ 成功注册系统中文字体: {font_display_name} ({font_path})")
                            return CHINESE_FONT_NAME
                        except Exception as e1:
                            try:
                                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                                CHINESE_FONT_NAME = 'ChineseFont'
                                logger.info(f"[PDF生成] ✓ 成功注册系统中文字体: {font_display_name} ({font_path})")
                                return CHINESE_FONT_NAME
                            except Exception as e2:
                                logger.warning(f"[PDF生成] 注册系统字体失败 {font_path}: {str(e2)}")
                                continue
                    else:
                        # .ttf 文件直接注册
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        CHINESE_FONT_NAME = 'ChineseFont'
                        logger.info(f"[PDF生成] ✓ 成功注册系统中文字体: {font_display_name} ({font_path})")
                        return CHINESE_FONT_NAME
                else:
                    logger.debug(f"[PDF生成] 系统字体文件不存在: {font_path}")
            except Exception as e:
                logger.warning(f"[PDF生成] 注册系统字体失败 {font_path}: {str(e)}")
                continue
    else:
        # Linux/Mac系统，尝试常见的中文字体路径
        linux_font_paths = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "/System/Library/Fonts/STHeiti Light.ttc",  # macOS
        ]
        for font_path in linux_font_paths:
            try:
                if os.path.exists(font_path):
                    logger.info(f"[PDF生成] 找到系统字体: {font_path}")
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    CHINESE_FONT_NAME = 'ChineseFont'
                    logger.info(f"[PDF生成] ✓ 成功注册系统中文字体: {font_path}")
                    return CHINESE_FONT_NAME
            except Exception as e:
                logger.debug(f"[PDF生成] 注册系统字体失败 {font_path}: {str(e)}")
                continue
    
    logger.error("[PDF生成] ✗ 未能注册中文字体，PDF中的中文将显示为乱码")
    logger.error("[PDF生成] 请按照文档说明添加字体文件到 backend/fonts/ 目录")
    return None

# 在模块加载时尝试注册字体
try:
    register_chinese_font()
except Exception as e:
    logger.error(f"[PDF生成] 字体注册过程出错: {str(e)}")


def markdown_to_paragraphs(text: str, styles_dict: Dict) -> List:
    """将Markdown文本转换为ReportLab段落"""
    paragraphs = []
    
    if not text:
        return paragraphs
    
    # 简单的Markdown解析
    lines = text.split('\n')
    current_paragraph = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_paragraph:
                try:
                    para_text = ' '.join(current_paragraph).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    paragraphs.append(Paragraph(para_text, styles_dict.get('Normal')))
                    paragraphs.append(Spacer(1, 0.2*inch))
                except Exception as e:
                    logger.warning(f"[PDF生成] 创建段落失败: {str(e)}")
                current_paragraph = []
            continue
        
        # 处理标题
        if line.startswith('# '):
            if current_paragraph:
                try:
                    para_text = ' '.join(current_paragraph).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    paragraphs.append(Paragraph(para_text, styles_dict.get('Normal')))
                except Exception as e:
                    logger.warning(f"[PDF生成] 创建段落失败: {str(e)}")
                current_paragraph = []
            try:
                title_text = line[2:].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                paragraphs.append(Paragraph(title_text, styles_dict.get('Heading1')))
                paragraphs.append(Spacer(1, 0.2*inch))
            except Exception as e:
                logger.warning(f"[PDF生成] 创建标题失败: {str(e)}")
        elif line.startswith('## '):
            if current_paragraph:
                try:
                    para_text = ' '.join(current_paragraph).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    paragraphs.append(Paragraph(para_text, styles_dict.get('Normal')))
                except Exception as e:
                    logger.warning(f"[PDF生成] 创建段落失败: {str(e)}")
                current_paragraph = []
            try:
                title_text = line[3:].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                paragraphs.append(Paragraph(title_text, styles_dict.get('Heading2')))
                paragraphs.append(Spacer(1, 0.15*inch))
            except Exception as e:
                logger.warning(f"[PDF生成] 创建标题失败: {str(e)}")
        elif line.startswith('### '):
            if current_paragraph:
                try:
                    para_text = ' '.join(current_paragraph).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    paragraphs.append(Paragraph(para_text, styles_dict.get('Normal')))
                except Exception as e:
                    logger.warning(f"[PDF生成] 创建段落失败: {str(e)}")
                current_paragraph = []
            try:
                title_text = line[4:].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                heading3_style = styles_dict.get('Heading3', styles_dict.get('Heading2'))
                paragraphs.append(Paragraph(title_text, heading3_style))
                paragraphs.append(Spacer(1, 0.1*inch))
            except Exception as e:
                logger.warning(f"[PDF生成] 创建标题失败: {str(e)}")
        else:
            # 普通文本，先不转义（在创建Paragraph时转义）
            current_paragraph.append(line)
    
    if current_paragraph:
        try:
            para_text = ' '.join(current_paragraph).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            paragraphs.append(Paragraph(para_text, styles_dict.get('Normal')))
            paragraphs.append(Spacer(1, 0.2*inch))
        except Exception as e:
            logger.warning(f"[PDF生成] 创建段落失败: {str(e)}")
    
    return paragraphs


def create_chart_image(chart_data: Dict[str, Any], width: float = 6*inch, height: float = 4*inch):
    """将ECharts配置转换为图片（简化版：显示为文本说明）"""
    # 注意：完整的图表渲染需要headless browser或图表服务
    # 这里先返回None，在PDF中显示文本说明
    return None


def create_chart_image_from_base64(
    image_base64: str, 
    width: float = 5.5*inch, 
    height: float = 3.5*inch
):
    """
    从Base64字符串创建ReportLab图片对象
    
    Args:
        image_base64: Base64编码的图片数据
        width: 图片宽度
        height: 图片高度
    
    Returns:
        ReportLab Image对象
    """
    try:
        # 解码Base64
        image_data = base64.b64decode(image_base64)
        
        # 创建BytesIO对象
        image_buffer = io.BytesIO(image_data)
        
        # 创建ReportLab Image对象
        from reportlab.platypus import Image as RLImage
        img = RLImage(image_buffer, width=width, height=height)
        
        logger.info(f"[PDF生成] 成功创建图片对象 - size={len(image_data)} bytes")
        return img
    except Exception as e:
        logger.error(f"[PDF生成] 创建图片失败: {str(e)}")
        return None


def generate_report_pdf(
    title: str,
    report_content: Dict[str, Any],
    session_id: int,
    chart_images: Optional[List[Dict[str, Any]]] = None
) -> bytes:
    """
    生成报告PDF
    
    Args:
        title: 报告标题
        report_content: 报告内容，包含text, charts, tables, metrics
        session_id: 会话ID
        chart_images: 图表图片数据列表 [{'index': 0, 'title': '图表1', 'image_data': 'base64...'}]
    
    Returns:
        PDF文件的字节数据
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # 创建样式
    styles = getSampleStyleSheet()
    
    # 添加中文字体支持
    chinese_font = register_chinese_font()  # 确保字体已注册
    
    if not chinese_font:
        # 如果中文字体注册失败，尝试使用系统默认字体
        try:
            registered_fonts = pdfmetrics.getRegisteredFontNames()
            if 'ChineseFont' in registered_fonts:
                chinese_font = 'ChineseFont'
            else:
                # 使用 Helvetica（不支持中文，会显示为方块）
                chinese_font = 'Helvetica'
                logger.error("[PDF生成] 中文字体未注册，使用Helvetica，中文将显示为乱码！")
        except Exception as e:
            chinese_font = 'Helvetica'
            logger.error(f"[PDF生成] 获取字体列表失败: {str(e)}，使用Helvetica，中文将显示为乱码！")
    else:
        # 验证字体是否真的已注册
        try:
            available_fonts = pdfmetrics.getRegisteredFontNames()
            if chinese_font not in available_fonts:
                logger.error(f"[PDF生成] 字体 {chinese_font} 未在注册列表中，尝试重新注册")
                chinese_font = register_chinese_font() or 'Helvetica'
        except Exception as e:
            logger.error(f"[PDF生成] 验证字体失败: {str(e)}")
    
    logger.info(f"[PDF生成] 使用的字体: {chinese_font}")
    
    # 自定义样式
    try:
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=chinese_font
        )
        
        heading1_style = ParagraphStyle(
            'CustomHeading1',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12,
            fontName=chinese_font
        )
        
        heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=10,
            spaceBefore=10,
            fontName=chinese_font
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            leading=16,
            fontName=chinese_font
        )
        
        heading3_style = ParagraphStyle(
            'CustomHeading3',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=8,
            spaceBefore=8,
            fontName=chinese_font
        )
    except Exception as e:
        logger.error(f"[PDF生成] 创建样式失败: {str(e)}，使用默认样式")
        # 使用默认样式
        title_style = styles['Heading1']
        heading1_style = styles['Heading1']
        heading2_style = styles['Heading2']
        heading3_style = styles['Heading2']
        normal_style = styles['Normal']
    
    # 构建PDF内容
    story = []
    
    # 标题（转义HTML特殊字符）
    try:
        title_escaped = str(title).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(title_escaped, title_style))
        story.append(Spacer(1, 0.3*inch))
    except Exception as e:
        logger.error(f"[PDF生成] 添加标题失败: {str(e)}")
        # 使用简单文本作为标题
        story.append(Paragraph(str(title)[:50], normal_style))
        story.append(Spacer(1, 0.3*inch))
    
    # 报告文本内容
    text_content = report_content.get("text", "")
    if text_content:
        # 将Markdown转换为段落
        try:
            text_paragraphs = markdown_to_paragraphs(text_content, {
                'Normal': normal_style,
                'Heading1': heading1_style,
                'Heading2': heading2_style,
                'Heading3': heading3_style
            })
            story.extend(text_paragraphs)
        except Exception as e:
            logger.error(f"[PDF生成] 处理文本内容失败: {str(e)}", exc_info=True)
            # 如果Markdown解析失败，直接使用纯文本
            text_escaped = str(text_content)[:500].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(text_escaped, normal_style))
            story.append(Spacer(1, 0.2*inch))
    
    # 图表
    charts = report_content.get("charts", [])
    if charts:
        try:
            story.append(Paragraph("图表", heading1_style))
            story.append(Spacer(1, 0.2*inch))
        except Exception as e:
            logger.warning(f"[PDF生成] 添加图表标题失败: {str(e)}")
        
        # 创建图片索引映射
        chart_image_map = {}
        if chart_images:
            for img_data in chart_images:
                chart_image_map[img_data['index']] = img_data
            logger.info(f"[PDF生成] 收到 {len(chart_images)} 个图表图片")
        
        for i, chart in enumerate(charts):
            try:
                # 优先使用传入的图片
                if i in chart_image_map:
                    img_data = chart_image_map[i]
                    logger.info(f"[PDF生成] 处理图表 {i}: {img_data.get('title', '')}")
                    
                    chart_img = create_chart_image_from_base64(
                        img_data['image_data'],
                        width=5.5*inch,
                        height=3.5*inch
                    )
                    
                    if chart_img:
                        # 添加图表标题
                        chart_title = str(img_data.get('title', chart.get('title', f'图表{i+1}')))
                        chart_title_escaped = chart_title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        story.append(Paragraph(f"<b>{chart_title_escaped}</b>", normal_style))
                        story.append(Spacer(1, 0.1*inch))
                        
                        # 添加图片
                        story.append(chart_img)
                        story.append(Spacer(1, 0.3*inch))
                        logger.info(f"[PDF生成] ✓ 成功添加图表图片 - index={i}, title={chart_title}")
                    else:
                        # 图片创建失败，显示文本说明
                        chart_title = str(chart.get('title', '未命名图表')).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        story.append(Paragraph(f"图表 {i+1}: {chart_title} (图片加载失败)", normal_style))
                        story.append(Spacer(1, 0.1*inch))
                        logger.warning(f"[PDF生成] ✗ 图表图片创建失败 - index={i}")
                else:
                    # 没有传入图片，显示文本说明
                    chart_title = str(chart.get('title', '未命名图表')).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(f"图表 {i+1}: {chart_title}", normal_style))
                    story.append(Spacer(1, 0.1*inch))
                    logger.info(f"[PDF生成] 图表 {i} 无图片数据，显示文本说明")
            except Exception as e:
                logger.warning(f"[PDF生成] 处理图表失败: {str(e)}")
                try:
                    story.append(Paragraph(f"图表 {i+1} 渲染失败", normal_style))
                    story.append(Spacer(1, 0.1*inch))
                except:
                    pass
    
    # 表格
    tables = report_content.get("tables", [])
    if tables:
        try:
            story.append(Paragraph("数据表格", heading1_style))
            story.append(Spacer(1, 0.2*inch))
        except Exception as e:
            logger.warning(f"[PDF生成] 添加表格标题失败: {str(e)}")
        
        for table_data in tables:
            try:
                columns = table_data.get("columns", [])
                data = table_data.get("data", [])
                
                if columns and data:
                    # 构建表格数据
                    table_rows = []
                    # 表头
                    header_row = [col.get("label", col.get("prop", "")) for col in columns]
                    table_rows.append(header_row)
                    
                    # 数据行
                    for row in data[:20]:  # 限制最多20行
                        row_data = [str(row.get(col.get("prop", ""), "")) for col in columns]
                        table_rows.append(row_data)
                    
                    # 创建表格
                    table = Table(table_rows, repeatRows=1)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
                    ]))
                    
                    story.append(table)
                    story.append(Spacer(1, 0.3*inch))
            except Exception as e:
                logger.warning(f"[PDF生成] 处理表格失败: {str(e)}")
                story.append(Paragraph("表格渲染失败", normal_style))
                story.append(Spacer(1, 0.1*inch))
    
    # 指标
    metrics = report_content.get("metrics", {})
    if metrics:
        try:
            story.append(Paragraph("关键指标", heading1_style))
            story.append(Spacer(1, 0.2*inch))
        except Exception as e:
            logger.warning(f"[PDF生成] 添加指标标题失败: {str(e)}")
        
        for key, value in metrics.items():
            try:
                key_escaped = str(key).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                value_escaped = str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                metric_text = f"<b>{key_escaped}:</b> {value_escaped}"
                story.append(Paragraph(metric_text, normal_style))
                story.append(Spacer(1, 0.1*inch))
            except Exception as e:
                logger.warning(f"[PDF生成] 添加指标失败: {str(e)}")
    
    # 生成PDF
    try:
        if not story:
            # 如果没有内容，至少添加一个标题
            title_text = str(title)[:50].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(title_text, normal_style))
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("报告内容为空", normal_style))
        
        logger.info(f"[PDF生成] ====== 开始构建PDF ======")
        logger.info(f"[PDF生成] 内容项数: {len(story)}")
        logger.info(f"[PDF生成] 标题: {title}")
        logger.info(f"[PDF生成] 文本长度: {len(text_content) if text_content else 0}")
        logger.info(f"[PDF生成] 图表数量: {len(charts)}")
        logger.info(f"[PDF生成] 表格数量: {len(tables)}")
        
        doc.build(story)
        buffer.seek(0)
        pdf_bytes = buffer.read()
        buffer.close()
        
        logger.info(f"[PDF生成] PDF生成成功 - 大小: {len(pdf_bytes)} bytes")
        logger.info(f"[PDF生成] ====== PDF生成完成 ======")
        return pdf_bytes
    except Exception as e:
        import traceback
        try:
            buffer.close()
        except:
            pass
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        logger.error(f"[PDF生成] ====== PDF生成失败 ======")
        logger.error(f"[PDF生成] 错误类型: {type(e).__name__}")
        logger.error(f"[PDF生成] 错误消息: {error_msg}")
        logger.error(f"[PDF生成] 完整堆栈:\n{error_traceback}")
        logger.error(f"[PDF生成] ====== 错误结束 ======")
        raise Exception(f"PDF生成失败: {error_msg}")

