"""
阿里百炼对话服务
支持与AI进行多轮对话，实时修改图表内容
"""
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from app.core.config import settings
from app.services.bailian_service import BailianService


class BailianDialogService:
    """阿里百炼对话服务 - 支持实时图表修改"""

    def __init__(self):
        self.bailian_service = BailianService()

    async def process_dialog_message(
        self,
        session_id: str,
        user_message: str,
        current_charts: List[Dict[str, Any]],
        conversation_id: Optional[str] = None,
        file_path: Optional[str] = None,
        current_report_text: str = "",
        current_html_charts: str = "",
        selected_text: Optional[str] = None,
        selected_text_context: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        处理用户对话消息

        Args:
            session_id: 会话ID
            user_message: 用户消息
            current_charts: 当前图表配置
            conversation_id: 对话ID（可选）
            file_path: 文件路径（可选）
            current_report_text: 当前报告文字
            current_html_charts: 当前HTML图表
            selected_text: 选中的文字（可选）
            selected_text_context: 选中文字的上下文（可选）

        Returns:
            {
                "response": str,  # AI回复
                "modified_charts": List[Dict],  # 修改后的图表
                "conversation_id": str,  # 对话ID
                "action_type": str,  # "modify_chart" | "chat" | "analysis" | "modify_text" | "regenerate_report"
                "new_report_text": str,  # 修改后的报告文字（可选）
            }
        """
        try:
            logger.info(f"[BailianDialogService] 处理对话消息: session_id={session_id}, message_length={len(user_message)}")
            
            # 检查是否是文字修改请求
            if selected_text:
                logger.info(f"[BailianDialogService] 检测到选中文字修改请求 - 选中长度: {len(selected_text)}")
                return await self._process_text_modification(
                    session_id=session_id,
                    user_message=user_message,
                    selected_text=selected_text,
                    selected_text_context=selected_text_context,
                    current_report_text=current_report_text,
                    conversation_id=conversation_id
                )

            # 1. 构建对话上下文
            context = await self._build_dialog_context(
                user_message=user_message,
                current_charts=current_charts,
                session_id=session_id
            )

            # 2. 调用阿里百炼API
            api_response = await self._call_bailian_dialog_api(
                context=context,
                conversation_id=conversation_id
            )

            # 3. 解析AI回复
            parsed_response = await self._parse_dialog_response(api_response)

            # 4. 处理图表修改
            modified_charts = current_charts or []
            if parsed_response.get("action_type") == "modify_chart":
                modified_charts = await self._apply_chart_modifications(
                    current_charts or [],
                    parsed_response.get("modifications", []),
                    file_path
                )

            # 5. 返回结果
            result = {
                "response": parsed_response["response"],
                "modified_charts": modified_charts,
                "conversation_id": api_response.get("conversation_id", conversation_id),
                "action_type": parsed_response.get("action_type", "chat")
            }

            logger.info(f"[BailianDialogService] 对话处理完成: action_type={result['action_type']}")
            return result

        except Exception as e:
            logger.error(f"[BailianDialogService] 处理对话失败: {str(e)}")
            return {
                "response": "抱歉，处理您的请求时出现了错误，请重试。",
                "modified_charts": current_charts or [],
                "conversation_id": conversation_id,
                "action_type": "error"
            }

    async def _process_text_modification(
        self,
        session_id: str,
        user_message: str,
        selected_text: str,
        selected_text_context: Optional[Dict[str, str]],
        current_report_text: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理选中文字的修改请求
        """
        try:
            logger.info(f"[BailianDialogService] 处理文字修改 - 选中: {selected_text[:50]}..., 指令: {user_message}")
            
            # 构建修改提示词
            prompt = f"""你是一个专业的文字编辑助手。用户选中了报告中的一段文字，希望你根据指令进行修改。

**选中的文字**：
{selected_text}

**用户的修改指令**：
{user_message}

**要求**：
1. 只修改选中的文字，保持原有的语气和风格
2. 直接输出修改后的文字，不要添加任何解释或标记
3. 不要输出"修改后的文字："等前缀
4. 保持专业、准确的表达

请直接输出修改后的文字："""

            # 调用API
            response = await self.bailian_service._call_dashscope_api(
                prompt=prompt,
                file_base64="",
                file_name=""
            )
            
            # 提取修改后的文字
            if self.bailian_service.use_openai_format:
                modified_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                output = response.get("output", {})
                choices = output.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    modified_text = message.get("content", "") or message.get("text", "")
                else:
                    modified_text = output.get("text", "")
            
            modified_text = modified_text.strip()
            logger.info(f"[BailianDialogService] 文字修改完成 - 原长度: {len(selected_text)}, 新长度: {len(modified_text)}")
            
            # 在原报告中替换选中的文字
            new_report_text = current_report_text
            if selected_text in current_report_text:
                new_report_text = current_report_text.replace(selected_text, modified_text, 1)
                logger.info(f"[BailianDialogService] 报告文字已更新 - 原长度: {len(current_report_text)}, 新长度: {len(new_report_text)}")
            else:
                logger.warning(f"[BailianDialogService] 无法在报告中找到选中的文字，返回修改后的文字供用户手动替换")
            
            return {
                "response": f"已根据您的指令修改了选中的文字。",
                "modified_charts": [],
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "action_type": "modify_text",
                "new_report_text": new_report_text,
                "modified_text": modified_text
            }
            
        except Exception as e:
            logger.error(f"[BailianDialogService] 文字修改失败: {str(e)}")
            return {
                "response": f"抱歉，修改文字时出现了错误：{str(e)}",
                "modified_charts": [],
                "conversation_id": conversation_id,
                "action_type": "error"
            }

    async def _build_dialog_context(
        self,
        user_message: str,
        current_charts: List[Dict[str, Any]],
        session_id: str
    ) -> Dict[str, Any]:
        """构建对话上下文"""

        # 系统提示词
        system_prompt = """你是一个专业的数据分析师助手，可以帮助用户分析数据和修改图表。

你的能力：
1. 理解Excel数据结构和内容
2. 分析数据特征、趋势和异常
3. 根据用户需求修改图表样式、类型、数据范围等
4. 生成新的图表配置（使用JSON格式）
5. 提供数据分析建议和洞察

回复格式：
- 普通对话：直接用自然语言回复
- 图表修改：先说明修改内容，然后用以下JSON格式返回修改配置：

```json
{
  "action_type": "modify_chart",
  "modifications": [
    {
      "chart_index": 0,
      "modification_type": "change_color",
      "config": {
        "color": "#FF6B6B"
      }
    }
  ],
  "response": "已将图表颜色改为红色"
}
```

支持的修改类型：
- change_color: 修改颜色
- change_type: 修改图表类型 (line/bar/pie/scatter)
- add_filter: 添加数据筛选
- modify_style: 修改样式
- update_data_range: 更新数据范围

请始终保持专业、友好的态度，用中文回复。"""

        # 当前图表状态描述
        chart_description = self._describe_current_charts(current_charts)

        # 用户消息上下文
        context_message = f"""当前图表状态：{chart_description}

用户需求：{user_message}

请根据以上信息回复，并判断是否需要修改图表。"""

        return {
            "system_prompt": system_prompt,
            "user_message": context_message,
            "chart_description": chart_description
        }

    def _describe_current_charts(self, charts: List[Dict[str, Any]]) -> str:
        """描述当前图表状态"""
        if not charts:
            return "暂无图表"

        descriptions = []
        for i, chart in enumerate(charts):
            chart_type = chart.get('type', '未知类型')
            title = chart.get('title', f'图表{i+1}')
            desc = f"{title}（{chart_type}图）"
            descriptions.append(desc)

        return "，".join(descriptions)

    async def _call_bailian_dialog_api(
        self,
        context: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """调用阿里百炼对话API"""

        # 构建消息
        messages = [
            {
                "role": "system",
                "content": context["system_prompt"]
            },
            {
                "role": "user",
                "content": context["user_message"]
            }
        ]

        # 如果有conversation_id，添加到请求中（阿里百炼API的对话延续方式）
        request_params = {
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 2000
        }

        if conversation_id:
            # 阿里百炼API的对话延续参数（根据实际API文档调整）
            request_params["conversation_id"] = conversation_id

        try:
            # 调用阿里百炼API（复用现有的BailianService）
            response = await self.bailian_service._call_dashscope_api(
                prompt=context["user_message"],  # 这里传入系统提示+用户消息
                file_base64="",  # 对话阶段不需要重新上传文件
                file_name=""
            )

            # 阿里百炼API响应格式处理
            if self.bailian_service.use_openai_format:
                # OpenAI格式
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                # DashScope格式
                output = response.get("output", {})
                choices = output.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    content = message.get("content", "") or message.get("text", "")
                else:
                    content = output.get("text", "")

            # 生成或返回conversation_id
            response_conversation_id = response.get("conversation_id") or conversation_id or str(uuid.uuid4())

            return {
                "content": content,
                "conversation_id": response_conversation_id,
                "raw_response": response
            }

        except Exception as e:
            logger.error(f"[BailianDialogService] API调用失败: {str(e)}")
            raise

    async def _parse_dialog_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """解析AI对话回复"""

        content = api_response.get("content", "")

        # 检查是否包含JSON配置
        if "```json" in content:
            try:
                # 提取JSON部分
                json_part = content.split("```json")[1].split("```")[0].strip()
                config = json.loads(json_part)

                # 提取文本回复
                text_part = content.split("```json")[0].strip()

                return {
                    "response": text_part,
                    "action_type": config.get("action_type", "chat"),
                    "modifications": config.get("modifications", [])
                }
            except json.JSONDecodeError as e:
                logger.warning(f"[BailianDialogService] JSON解析失败: {str(e)}")
                # JSON解析失败，当作普通对话处理

        # 检查是否包含其他代码块
        elif "```" in content:
            # 尝试提取第一个代码块
            parts = content.split("```")
            if len(parts) >= 3:
                code_content = parts[1].strip()
                text_part = parts[0].strip()

                # 如果是JSON格式
                if code_content.startswith("{") or code_content.startswith("["):
                    try:
                        config = json.loads(code_content)
                        return {
                            "response": text_part,
                            "action_type": config.get("action_type", "chat"),
                            "modifications": config.get("modifications", [])
                        }
                    except:
                        pass

        # 普通文本回复
        return {
            "response": content,
            "action_type": "chat",
            "modifications": []
        }

    async def _apply_chart_modifications(
        self,
        current_charts: List[Dict[str, Any]],
        modifications: List[Dict[str, Any]],
        file_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """应用图表修改"""

        from app.services.chart_modifier import ChartModifier

        modifier = ChartModifier()
        return await modifier.apply_modifications(
            current_charts=current_charts,
            modifications=modifications,
            file_path=file_path
        )
