"""
阿里百炼API服务（直接调用DashScope API）
"""
import httpx
import base64
import json
from typing import Dict, Any, Optional, List
from loguru import logger
from app.core.config import settings
import pandas as pd
from datetime import datetime

# 固定prompt模板（用于批量分析文字报告生成）
FIXED_TEXT_REPORT_PROMPT = """你是一个洞察能力极强的游戏公司的数据分析专家善于结合用户的问题以及用户提供的运营数据，透过数据去给出有价值的分析建议运营方面的建议，分析与统计流失用户的VIP等级与流失等级分布，并给出你的意见，形成完整的运营分析报告"""

# 定制化批量分析的固定prompt模板（根据Sheet索引选择）
CUSTOM_BATCH_PROMPTS = [
    # Sheet 0: 最后操作分布
    """你是一个洞察能力极强的游戏公司的数据分析专家善于结合用户的问题以及用户提供的留存率运营数据，透过数据去给出有价值的分析建议运营方面的建议，分析流失用户离开前的最后游戏行为，就TOP10高频率行为，并给出你的意见形成完整的运营分析报告。

【重要】必须生成至少一个可视化图表（如柱状图、折线图、饼图等）来展示关键数据趋势或分布，图表必须使用完整的HTML格式（包含echarts库的完整代码）。""",
    # Sheet 1: 新手漏斗
    """你是一个洞察能力极强的游戏公司的数据分析专家善于结合用户的问题以及用户提供的运营数据，透过数据去给出有价值的分析建议运营方面的建议，分析新手前期环节的留存与转化表现，可以体现数据奇点，并给出你的结论形成完整的运营分析报告。

【重要】必须生成至少一个可视化图表（如漏斗图、折线图、柱状图等）来展示新手转化流程或留存趋势，图表必须使用完整的HTML格式（包含echarts库的完整代码）。""",
    # Sheet 2: 回流用户
    """你是一个洞察能力极强的游戏公司的数据分析专家善于结合用户的问题以及用户提供的运营数据，透过数据去给出有价值的分析建议运营方面的建议，分析回流用户的数量与留存质量变化，并给出你的意见，形成完整的运营分析报告。

【重要】必须生成至少一个可视化图表（如折线图、柱状图、面积图等）来展示回流用户的数量变化趋势或留存质量对比，图表必须使用完整的HTML格式（包含echarts库的完整代码）。""",
    # Sheet 3: 流失用户属性
    """你是一个洞察能力极强的游戏公司的数据分析专家善于结合用户的问题以及用户提供的运营数据，透过数据去给出有价值的分析建议运营方面的建议，分析与统计流失用户的VIP等级与流失等级分布，并给出你的意见，形成完整的运营分析报告。

【重要】必须生成至少一个可视化图表（如饼图、柱状图、堆叠柱状图等）来展示流失用户的VIP等级分布或流失等级分布，图表必须使用完整的HTML格式（包含echarts库的完整代码）。""",
    # Sheet 4: 留存率
    """你是一个洞察能力极强的游戏公司的数据分析专家善于结合用户的问题以及用户提供的留存率运营数据，透过数据去给出有价值的分析建议运营方面的建议，分析全新用户（new)与滚服新增用户(roll）的留存差异，并给出你的意见，形成完整的运营分析报告。

【重要】必须生成至少一个可视化图表（如折线图、对比柱状图等）来展示new用户和roll用户的留存率对比趋势，图表必须使用完整的HTML格式（包含echarts库的完整代码）。""",
    # Sheet 5: LTV
    """你是一个洞察能力极强的游戏公司的数据分析专家善于结合用户的问题以及用户提供的LTV运营数据，透过数据去给出有价值的分析建议运营方面的建议，分析全新用户（new)与滚服新增用户(roll）的LTV差异，并给出你的意见，形成完整的运营分析报告。

【重要】必须生成至少一个可视化图表（如折线图、对比柱状图、面积图等）来展示new用户和roll用户的LTV对比趋势，图表必须使用完整的HTML格式（包含echarts库的完整代码）。"""
]

def get_custom_batch_prompt(sheet_index: int) -> str:
    """
    根据Sheet索引获取对应的固定prompt模板
    
    Args:
        sheet_index: Sheet索引（0-5）
    
    Returns:
        对应的固定prompt模板，如果索引超出范围，返回默认模板
    """
    if 0 <= sheet_index < len(CUSTOM_BATCH_PROMPTS):
        return CUSTOM_BATCH_PROMPTS[sheet_index]
    else:
        # 如果索引超出范围，使用Sheet 0的模板作为默认
        logger.warning(f"[BailianService] Sheet索引 {sheet_index} 超出范围，使用Sheet 0的模板")
        return CUSTOM_BATCH_PROMPTS[0]


class BailianService:
    """阿里百炼API服务（直接调用DashScope API）"""
    
    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        # API基础URL，如果配置了自定义URL则使用，否则使用DashScope默认URL
        api_base = settings.DASHSCOPE_API_BASE
        if api_base:
            # 如果提供了自定义API基础URL（如OpenAI兼容接口）
            self.api_url = api_base.rstrip('/')
            if not self.api_url.endswith('/v1/chat/completions'):
                # 如果是OpenAI兼容接口，使用chat/completions端点
                if '/v1/' in self.api_url:
                    self.api_url = f"{self.api_url.rstrip('/v1')}/v1/chat/completions"
                else:
                    self.api_url = f"{self.api_url}/v1/chat/completions"
            self.use_openai_format = True
        else:
            # 使用DashScope原生API
            self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
            self.use_openai_format = False
        
        self.model = settings.DASHSCOPE_MODEL or "qwen-3-32b"
        
        if not self.api_key:
            logger.warning("[BailianService] DASHSCOPE_API_KEY未配置，图表生成功能将不可用")
        else:
            logger.info(f"[BailianService] 初始化完成 - model={self.model}, api_url={self.api_url}, use_openai_format={self.use_openai_format}")
    
    async def analyze_excel_and_generate_html(
        self,
        file_path: str,
        analysis_request: str,
        chart_customization: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析Excel并生成HTML代码
        
        Args:
            file_path: Excel文件路径
            analysis_request: 分析需求
            chart_customization: 用户自定义的图表定制prompt（完全决定HTML内容）
        
        Returns:
            {
                "success": bool,
                "html_content": str,  # HTML代码内容
                "error": str
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "html_content": None,
                "error": "DASHSCOPE_API_KEY未配置"
            }
        
        try:
            # 1. 读取Excel文件并转换为base64
            with open(file_path, "rb") as f:
                file_content = f.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # 2. 读取文件内容作为文本（用于发送给API）
            # 只发送数据样本，避免Token过多
            df = pd.read_excel(file_path)
            data_sample = df.head(100).to_string()  # 只取前100行作为样本
            
            # 3. 构建HTML生成Prompt（用户prompt为主，代码只做基础格式要求）
            prompt = self._build_html_generation_prompt(
                data_sample=data_sample,
                analysis_request=analysis_request,
                chart_customization=chart_customization
            )
            
            # 4. 调用阿里百炼API
            response = await self._call_dashscope_api(prompt, file_base64, file_path)
            
            # 5. 提取HTML代码
            html_content = self._extract_html_from_response(response)
            
            return {
                "success": True,
                "html_content": html_content,
                "error": None
            }
        
        except Exception as e:
            logger.error(f"[BailianService] 生成HTML失败: {str(e)}")
            return {
                "success": False,
                "html_content": None,
                "error": str(e)
            }
    
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
        if not self.api_key:
            return {
                "success": False,
                "config": None,
                "data_info": None,
                "error": "DASHSCOPE_API_KEY未配置"
            }
        
        try:
            # 1. 读取Excel文件并转换为base64
            with open(file_path, "rb") as f:
                file_content = f.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # 2. 读取文件内容作为文本（用于发送给API）
            # 只发送数据样本，避免Token过多
            df = pd.read_excel(file_path)
            data_sample = df.head(200).to_string()  # 只取前200行作为样本
            
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
        """调用阿里百炼API（支持DashScope原生API和OpenAI兼容接口）"""
        if not self.api_key:
            raise Exception("DASHSCOPE_API_KEY未配置")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "enable"  # 启用流式输出
        }
        
        # 根据API类型构建不同的请求体
        if self.use_openai_format:
            # OpenAI兼容接口格式
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 8000  # 增加到8000，支持更长的HTML代码
            }
        else:
            # DashScope原生API格式（匹配官方API格式）
            payload = {
                "model": self.model,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                "parameters": {
                    "temperature": 0.1,
                    "max_tokens": 8000,  # 增加到8000，支持更长的HTML代码
                    "result_format": "message",
                    "incremental_output": True,  # 启用流式输出（DashScope支持此参数）
                    "enable_search": False  # 禁用搜索功能，可能会减少推理模式的触发
                }
            }
        
        # 增加超时时间到300秒（5分钟），避免长文本生成时连接断开
        # 配置连接超时和读取超时
        timeout_config = httpx.Timeout(
            timeout=300.0,  # 总超时
            connect=60.0,   # 连接超时60秒
            read=300.0,     # 读取超时300秒
            write=60.0      # 写入超时60秒
        )
        
        # 配置连接池限制
        limits = httpx.Limits(
            max_keepalive_connections=5,
            max_connections=10,
            keepalive_expiry=30.0
        )
        
        async with httpx.AsyncClient(
            timeout=timeout_config,
            limits=limits,
            follow_redirects=True
        ) as client:
            logger.info(f"[BailianService] 调用API - model={self.model}, format={'OpenAI' if self.use_openai_format else 'DashScope'}, prompt_length={len(prompt)}, stream=True")
            try:
                # 使用流式请求
                full_content = ""
                logger.debug(f"[BailianService] 开始发送流式请求...")
                async with client.stream('POST', self.api_url, json=payload, headers=headers) as response:
                    logger.debug(f"[BailianService] 收到响应，状态码: {response.status_code}")
                    response.raise_for_status()
                    logger.debug(f"[BailianService] 状态码检查通过，开始读取流式数据...")
                    
                    # 逐字节读取流式响应
                    buffer = ""
                    chunk_count = 0
                    async for chunk in response.aiter_bytes():
                        chunk_count += 1
                        # 将字节转换为字符串
                        buffer += chunk.decode('utf-8', errors='ignore')
                        
                        # 按行分割
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            
                            if not line or line.startswith(':'):
                                continue
                            
                            if line.startswith('data:'):
                                line = line[5:].strip()
                            
                            if line == '[DONE]':
                                break
                            
                            try:
                                chunk_data = json.loads(line)
                                
                                # 第一次收到数据时，打印完整结构用于调试
                                if chunk_count == 1:
                                    logger.debug(f"[BailianService] 第一个数据块结构: {json.dumps(chunk_data, ensure_ascii=False)[:500]}")
                                
                                # 提取内容
                                if not self.use_openai_format:
                                    # DashScope格式
                                    if 'output' in chunk_data and 'choices' in chunk_data['output']:
                                        choices = chunk_data['output']['choices']
                                        if choices and 'message' in choices[0]:
                                            message = choices[0]['message']
                                            
                                            # qwen3-32b推理模式：
                                            # - reasoning_content: 思考过程+最终答案（增量输出）
                                            # - content: 通常为空
                                            # 需要累加reasoning_content
                                            
                                            content_text = message.get('content', '')
                                            reasoning_text = message.get('reasoning_content', '')
                                            
                                            # 优先累加content，如果content为空则累加reasoning_content
                                            if content_text:
                                                full_content += content_text
                                            elif reasoning_text:
                                                full_content += reasoning_text
                                            
                                            # 记录日志
                                            if chunk_count <= 5:
                                                logger.debug(f"[BailianService] 数据块{chunk_count} - content长度: {len(content_text)}, reasoning_content长度: {len(reasoning_text)}, 累积长度: {len(full_content)}")
                                            # 每50个数据块记录一次进度
                                            if chunk_count % 50 == 0:
                                                logger.debug(f"[BailianService] 进度: 数据块{chunk_count}, 累积长度: {len(full_content)}")
                                else:
                                    # OpenAI格式
                                    if 'choices' in chunk_data and chunk_data['choices']:
                                        delta = chunk_data['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            full_content += delta['content']
                            except json.JSONDecodeError as e:
                                if chunk_count <= 3:
                                    logger.debug(f"[BailianService] JSON解析失败: {line[:100]}")
                                continue
                    
                    logger.debug(f"[BailianService] 流式数据读取完成，共收到 {chunk_count} 个数据块")
                
                logger.info(f"[BailianService] 流式响应完成，总长度: {len(full_content)} 字符")
                
                # 构造完整响应
                result = {
                    "output": {
                        "choices": [{
                            "message": {
                                "content": full_content
                            }
                        }]
                    }
                }
                
                # 检查API返回的错误（DashScope格式）
                if not self.use_openai_format and "code" in result and result["code"] != "Success":
                    error_msg = result.get("message", "API调用失败")
                    logger.error(f"[BailianService] API返回错误: {error_msg}")
                    raise Exception(f"API错误: {error_msg}")
                
                # 检查OpenAI格式的错误
                if self.use_openai_format and "error" in result:
                    error_msg = result["error"].get("message", "API调用失败")
                    logger.error(f"[BailianService] API返回错误: {error_msg}")
                    raise Exception(f"API错误: {error_msg}")
                
                return result
            except httpx.HTTPStatusError as e:
                error_detail = ""
                try:
                    error_detail = e.response.json()
                except:
                    error_detail = e.response.text
                logger.error(f"[BailianService] HTTP错误: {e.response.status_code}, {error_detail}")
                raise Exception(f"API调用失败: HTTP {e.response.status_code}")
            except Exception as e:
                logger.error(f"[BailianService] API调用异常: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(f"[BailianService] 异常堆栈: {traceback.format_exc()}")
                raise
    
    def _extract_json_from_response(self, response: Dict[str, Any]) -> list:
        """从API响应中提取JSON配置（支持DashScope和OpenAI格式）"""
        content = ""
        try:
            if self.use_openai_format:
                # OpenAI兼容接口响应格式：choices[0].message.content
                choices = response.get("choices", [])
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", "") or message.get("reasoning_content", "")
            else:
                # DashScope API响应格式：output.choices[0].message.content
                output = response.get("output", {})
                choices = output.get("choices", [])
                
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", "") or message.get("reasoning_content", "") or message.get("text", "")
                else:
                    # 尝试其他可能的响应格式
                    content = output.get("text", "") or response.get("text", "")
            
            if not content:
                logger.error(f"[BailianService] API响应格式异常: {response}")
                raise Exception("API响应中未找到内容")
            
            logger.debug(f"[BailianService] 提取的原始内容长度: {len(content)}")
            
            # 移除markdown代码块标记
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                # 尝试提取第一个代码块
                parts = content.split("```")
                if len(parts) >= 3:
                    content = parts[1].strip()
                    # 如果第一个代码块不是json，尝试找json代码块
                    if not content.startswith("json") and "json" in content.lower():
                        for i in range(1, len(parts), 2):
                            if "json" in parts[i].lower() or parts[i].strip().startswith("["):
                                content = parts[i].strip()
                                break
            
            # 解析JSON
            config = json.loads(content)
            if not isinstance(config, list):
                config = [config]
            
            logger.info(f"[BailianService] 提取JSON配置成功，共 {len(config)} 个图表配置")
            return config
        
        except json.JSONDecodeError as e:
            logger.error(f"[BailianService] JSON解析失败: {str(e)}")
            logger.error(f"[BailianService] 内容预览: {content[:500] if content else 'empty'}")
            raise Exception(f"无法从API响应中提取JSON配置: {str(e)}")
        except Exception as e:
            logger.error(f"[BailianService] 提取JSON配置失败: {str(e)}")
            raise Exception(f"无法从API响应中提取JSON配置: {str(e)}")
    
    def _build_html_generation_prompt(
        self,
        data_sample: str,
        analysis_request: str,
        chart_customization: Optional[str] = None
    ) -> str:
        """
        构建HTML代码生成提示词
        
        注意：chart_customization是用户自定义的prompt，代码只做基础格式要求
        """
        # 最基础的HTML格式要求（不规定任何功能内容）
        base_instruction = """你是一个前端开发专家。请根据用户提供的Excel数据样本和用户的定制要求，生成一个完整的、可运行的HTML网页。

**格式要求**（必须遵守）：
1. 必须返回完整的HTML5文档（<!DOCTYPE html>开头）
2. 包含<head>和<body>标签
3. 使用UTF-8编码（<meta charset="UTF-8">）
4. 所有代码必须内嵌在HTML中，可以直接在浏览器中运行
5. 不要包含markdown代码块标记（```html等），只返回纯HTML代码

**图表尺寸要求**（必须严格遵守）：
1. **容器尺寸**：
   - body 必须设置：margin: 0; padding: 20px; box-sizing: border-box;
   - 主容器 div 必须设置：width: 100%; max-width: 100%; margin: 0 auto;
   
2. **图表尺寸**（非常重要）：
   - 如果使用 ECharts：
     * 容器 div 必须设置：style="width: 100%; height: 600px; min-height: 600px;"
     * 初始化时使用：echarts.init(document.getElementById('chart'))
   
   - 如果使用 Chart.js：
     * canvas 必须包裹在 div 中：<div style="width: 100%; height: 600px;"><canvas id="chart"></canvas></div>
     * canvas 必须设置：style="width: 100% !important; height: 100% !important;"
   
   - 如果使用其他图表库：
     * 容器必须设置明确的高度（至少 500px）
     * 宽度使用 100% 或 max-width: 100%

3. **响应式设计**：
   - 不要使用固定像素宽度（如 width: 1200px）
   - 使用相对单位（%、vw）或 max-width
   - 确保在 iframe 中能正常显示

4. **示例代码结构**：
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据分析图表</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
            font-family: Arial, sans-serif;
        }}
        .container {{
            width: 100%;
            max-width: 100%;
            margin: 0 auto;
        }}
        .chart-container {{
            width: 100%;
            height: 600px;
            min-height: 600px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>图表标题</h2>
        <div id="chart" class="chart-container"></div>
    </div>
    <script>
        var chart = echarts.init(document.getElementById('chart'));
        var option = {{
            // 图表配置
        }};
        chart.setOption(option);
        
        // 响应式调整
        window.addEventListener('resize', function() {{
            chart.resize();
        }});
    </script>
</body>
</html>
```

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
        
        prompt = base_instruction.format(
            data_sample=data_sample,
            analysis_request=analysis_request
        ) + user_prompt
        
        return prompt
    
    def _extract_html_from_response(self, response: Dict[str, Any]) -> str:
        """从API响应中提取HTML代码（支持DashScope和OpenAI格式）"""
        try:
            if self.use_openai_format:
                # OpenAI兼容接口响应格式：choices[0].message.content
                choices = response.get("choices", [])
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", "") or message.get("reasoning_content", "")
                else:
                    content = ""
            else:
                # DashScope API响应格式：output.choices[0].message.content
                output = response.get("output", {})
                choices = output.get("choices", [])
                
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", "") or message.get("reasoning_content", "") or message.get("text", "")
                else:
                    content = output.get("text", "") or response.get("text", "")
            
            if not content:
                logger.error(f"[BailianService] API响应格式异常: {response}")
                raise Exception("API响应中未找到内容")
            
            # 移除markdown代码块标记
            if "```html" in content:
                html = content.split("```html")[1].split("```")[0].strip()
            elif "```" in content:
                # 尝试提取第一个代码块
                parts = content.split("```")
                if len(parts) >= 3:
                    html = parts[1].strip()
                    # 如果第一个代码块不是html，尝试找html代码块或直接使用
                    if not html.startswith("html") and not html.startswith("<!DOCTYPE"):
                        for i in range(1, len(parts), 2):
                            if "html" in parts[i].lower() or parts[i].strip().startswith("<!DOCTYPE"):
                                html = parts[i].strip()
                                # 移除语言标识
                                if html.startswith("html"):
                                    html = html[4:].strip()
                                break
                else:
                    html = content.strip()
            else:
                html = content.strip()
            
            # 确保以<!DOCTYPE开头（如果没有，可能是被截断了）
            if not html.startswith("<!DOCTYPE") and not html.startswith("<html"):
                # 尝试查找HTML开始位置
                doctype_pos = html.find("<!DOCTYPE")
                if doctype_pos > 0:
                    html = html[doctype_pos:]
                elif html.find("<html") > 0:
                    html_pos = html.find("<html")
                    html = html[html_pos:]
            
            logger.info(f"[BailianService] 提取HTML成功，长度: {len(html)} 字符")
            return html
        
        except Exception as e:
            logger.error(f"[BailianService] 提取HTML失败: {str(e)}")
            raise Exception(f"无法从API响应中提取HTML代码: {str(e)}")
    
    def _extract_code_from_response(self, response: Dict[str, Any]) -> str:
        """从API响应中提取代码（支持DashScope和OpenAI格式）"""
        try:
            if self.use_openai_format:
                # OpenAI兼容接口响应格式：choices[0].message.content
                choices = response.get("choices", [])
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", "") or message.get("reasoning_content", "")
                else:
                    content = ""
            else:
                # DashScope API响应格式：output.choices[0].message.content
                output = response.get("output", {})
                choices = output.get("choices", [])
                
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", "") or message.get("reasoning_content", "") or message.get("text", "")
                else:
                    content = output.get("text", "") or response.get("text", "")
            
            if not content:
                logger.error(f"[BailianService] API响应格式异常: {response}")
                raise Exception("API响应中未找到内容")
            
            # 移除markdown代码块标记
            if "```python" in content:
                code = content.split("```python")[1].split("```")[0].strip()
            elif "```" in content:
                # 尝试提取第一个代码块
                parts = content.split("```")
                if len(parts) >= 3:
                    code = parts[1].strip()
                    # 如果第一个代码块不是python，尝试找python代码块
                    if not code.startswith("python"):
                        for i in range(1, len(parts), 2):
                            if "python" in parts[i].lower() or parts[i].strip().startswith("def"):
                                code = parts[i].strip()
                                break
                else:
                    code = content.strip()
            else:
                code = content.strip()
            
            logger.info(f"[BailianService] 提取代码成功，长度: {len(code)} 字符")
            return code
        
        except Exception as e:
            logger.error(f"[BailianService] 提取代码失败: {str(e)}")
            raise Exception(f"无法从API响应中提取代码: {str(e)}")
    
    async def analyze_excel_and_generate_text_report(
        self,
        file_path: str,
        user_prompt: str,
        fixed_prompt_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析Excel并生成文字报告
        
        Args:
            file_path: Excel文件路径
            user_prompt: 用户输入的分析需求prompt
            fixed_prompt_template: 固定的prompt模板（如果为None，使用默认模板）
        
        Returns:
            {
                "success": bool,
                "text_content": str,  # 生成的文字报告内容
                "error": str
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "text_content": None,
                "error": "DASHSCOPE_API_KEY未配置"
            }
        
        try:
            # 1. 读取Excel文件并转换为base64（可选，用于文件上传）
            with open(file_path, "rb") as f:
                file_content = f.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # 2. 读取文件内容作为文本（用于发送给API）
            # 只发送数据样本，避免Token过多
            df = pd.read_excel(file_path)
            data_sample = df.head(100).to_string()  # 只取前100行作为样本
            
            logger.info(f"[BailianService] Excel文件读取成功 - 总行数: {len(df)}, 列数: {len(df.columns)}")
            logger.info(f"[BailianService] 数据样本长度: {len(data_sample)} 字符")
            logger.info(f"[BailianService] 数据样本预览(前500字符): {data_sample[:500]}")
            
            # 3. 构建文字报告生成Prompt
            # 使用固定prompt模板 + 用户prompt + 数据样本
            fixed_template = fixed_prompt_template or FIXED_TEXT_REPORT_PROMPT
            
            prompt = self._build_text_report_prompt(
                data_sample=data_sample,
                fixed_template=fixed_template,
                user_prompt=user_prompt
            )
            
            logger.info(f"[BailianService] 构建的完整prompt长度: {len(prompt)} 字符")
            logger.info(f"[BailianService] Prompt预览(前1000字符): {prompt[:1000]}")
            
            # 4. 调用阿里百炼API
            response = await self._call_dashscope_api(prompt, file_base64, file_path)
            
            # 5. 提取文字报告内容
            text_content = self._extract_text_from_response(response)
            
            return {
                "success": True,
                "text_content": text_content,
                "error": None
            }
        
        except Exception as e:
            logger.error(f"[BailianService] 生成文字报告失败: {str(e)}")
            return {
                "success": False,
                "text_content": None,
                "error": str(e)
            }
    
    def _build_text_report_prompt(
        self,
        data_sample: str,
        fixed_template: str,
        user_prompt: str
    ) -> str:
        """
        构建文字报告生成提示词
        
        格式：
        1. 固定prompt模板（角色定义和基础要求）
        2. 数据样本
        3. 用户prompt（具体分析需求）
        """
        prompt = f"""{fixed_template}

**数据样本**：
{data_sample}

**用户分析需求**：
{user_prompt}

请根据以上数据样本和用户的分析需求，生成一份完整的运营分析报告。报告应该包括：
1. 数据概览和关键指标
2. 深度分析和洞察
3. 问题识别和建议
4. 运营优化建议

请以结构化的方式输出报告，使用Markdown格式。"""
        
        return prompt
    
    def _extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """从API响应中提取文字内容（支持DashScope和OpenAI格式）"""
        try:
            if self.use_openai_format:
                # OpenAI兼容接口响应格式：choices[0].message.content
                choices = response.get("choices", [])
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", "") or message.get("reasoning_content", "")
                else:
                    content = ""
            else:
                # DashScope API响应格式：output.choices[0].message.content
                output = response.get("output", {})
                choices = output.get("choices", [])
                
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", "") or message.get("reasoning_content", "")  or message.get("text", "")
                else:
                    content = output.get("text", "") or response.get("text", "")
            
            if not content:
                logger.error(f"[BailianService] API响应格式异常: {response}")
                raise Exception("API响应中未找到内容")
            
            # 移除thinking标签及其内容（AI的思考过程）
            import re
            # 匹配 <think>...</think> 或 <thinking>...</thinking> 标签
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
            # 清理多余的空行
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            content = content.strip()
            
            # 移除可能的markdown代码块标记
            if "```" in content:
                # 尝试提取markdown内容
                parts = content.split("```")
                if len(parts) >= 3:
                    # 如果有代码块，尝试提取markdown部分
                    for i in range(0, len(parts), 2):
                        if parts[i].strip() and not parts[i].strip().startswith("markdown"):
                            content = parts[i].strip()
                            break
                else:
                    content = content.replace("```", "").strip()
            
            logger.info(f"[BailianService] 提取文字报告成功，长度: {len(content)} 字符")
            return content
        
        except Exception as e:
            logger.error(f"[BailianService] 提取文字报告失败: {str(e)}")
            raise Exception(f"无法从API响应中提取文字报告: {str(e)}")

