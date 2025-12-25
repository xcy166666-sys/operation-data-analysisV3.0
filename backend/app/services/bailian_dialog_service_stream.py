"""
阿里百炼对话服务（流式版本）
支持思考过程可视化
"""
import json
import re
import uuid
import httpx
from typing import Dict, Any, List, Optional, AsyncGenerator
from loguru import logger
from app.core.config import settings


class BailianDialogServiceStream:
    """阿里百炼对话服务 - 流式版本，支持思考过程可视化和多轮对话"""

    # 增强版系统提示词
    ENHANCED_SYSTEM_PROMPT = """你是一个专业的游戏运营数据分析专家，具备以下能力：

1. **数据理解**：能够深入理解Excel数据中的业务含义，识别关键指标（如留存率、转化率、活跃度等）
2. **趋势分析**：分析数据趋势、识别异常点、预测未来走向
3. **洞察生成**：从数据中发现业务洞察，提出可执行的运营建议
4. **图表修改**：根据用户需求调整图表样式、类型、数据范围
5. **报告优化**：改进报告的结构、表达和专业性

当用户询问数据相关问题时，请：
1. 结合报告内容给出具体的数据支持
2. 指出数据中的关键发现
3. 提供可操作的建议
4. 如果需要，引用报告中的具体段落

请用中文回复，保持专业、友好的态度。"""

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        api_base = settings.DASHSCOPE_API_BASE
        if api_base:
            self.api_url = api_base.rstrip('/')
            if not self.api_url.endswith('/v1/chat/completions'):
                if '/v1/' in self.api_url:
                    self.api_url = f"{self.api_url.rstrip('/v1')}/v1/chat/completions"
                else:
                    self.api_url = f"{self.api_url}/v1/chat/completions"
            self.use_openai_format = True
        else:
            self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
            self.use_openai_format = False

        self.model = settings.DASHSCOPE_MODEL or "qwen-3-32b"

    def _build_messages_with_history(
        self,
        current_prompt: str,
        dialog_history: List[Dict[str, str]],
        current_report_text: str = "",
        current_charts: List[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        构建包含对话历史的消息列表

        Args:
            current_prompt: 当前用户消息（已经格式化好的prompt）
            dialog_history: 对话历史列表 [{"role": "user/assistant", "content": "..."}]
            current_report_text: 当前报告文本（用于构建上下文）
            current_charts: 当前图表列表

        Returns:
            格式化的消息列表，用于传递给AI模型
        """
        messages = []

        # 1. 系统提示词 + 报告上下文
        system_content = self.ENHANCED_SYSTEM_PROMPT
        if current_report_text:
            # 提取报告摘要（开头和结尾）
            if len(current_report_text) > 2000:
                report_summary = f"\n\n当前报告摘要：\n{current_report_text[:800]}...\n...\n{current_report_text[-800:]}"
            else:
                report_summary = f"\n\n当前报告内容：\n{current_report_text}"
            system_content += report_summary

        if current_charts:
            chart_desc = self._describe_charts(current_charts)
            system_content += f"\n\n当前图表：{chart_desc}"

        messages.append({
            "role": "system",
            "content": system_content
        })

        # 2. 添加对话历史（最多保留最近20条消息，避免上下文过长）
        max_history = 20
        history_to_use = dialog_history[-max_history:] if len(dialog_history) > max_history else dialog_history

        for msg in history_to_use:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # 3. 添加当前用户消息
        messages.append({
            "role": "user",
            "content": current_prompt
        })

        logger.debug(f"[BailianDialogServiceStream] 构建消息 - 历史消息数: {len(history_to_use)}, 总消息数: {len(messages)}")
        return messages

    def _detect_intent(self, user_message: str, has_selected_text: bool = False) -> str:
        """
        检测用户意图
        返回: 'add_content' | 'modify_text' | 'delete_content' | 'chat'
        """
        # 删除内容的关键词
        delete_keywords = ['删除', '删掉', '去掉', '移除', '删了', '不要', '去除', '清除']
        # 添加内容的关键词
        add_keywords = ['加一个', '添加', '新增', '补充', '再加', '增加', '写一个', '生成一个', '加个', '加上', '后面加', '下面加', '接着写']
        # 章节相关关键词
        section_keywords = ['章节', '部分', '段落', '小节', '4.4', '4.5', '5.1', '标题', '长期', '短期', '策略', '计划', '方案']
        # 位置相关关键词（表示在某处添加）
        position_keywords = ['后面', '下面', '之后', '接着', '继续']
        
        message_lower = user_message.lower()
        
        # 优先检测删除意图（当有选中文字时）
        has_delete_keyword = any(kw in message_lower for kw in delete_keywords)
        if has_selected_text and has_delete_keyword:
            return 'delete_content'
        
        # 检测是否是添加内容的请求
        has_add_keyword = any(kw in message_lower for kw in add_keywords)
        has_section_keyword = any(kw in message_lower for kw in section_keywords)
        has_position_keyword = any(kw in message_lower for kw in position_keywords)
        
        # 检测章节编号模式，如 "4.4", "5.1" 等
        has_section_number = bool(re.search(r'\d+\.\d+', user_message))
        
        # 优先检测添加内容的意图（即使有选中文字）
        if has_add_keyword and (has_section_keyword or has_section_number):
            return 'add_content'
        elif has_add_keyword and ('内容' in message_lower or '报告' in message_lower):
            return 'add_content'
        elif has_add_keyword and has_position_keyword:
            # "在后面加"、"下面加" 等表达
            return 'add_content'
        elif has_selected_text:
            # 有选中文字但不是添加/删除内容，则是修改文字
            return 'modify_text'
        
        return 'chat'

    async def process_dialog_message_stream(
        self,
        session_id: str,
        user_message: str,
        current_charts: List[Dict[str, Any]],
        conversation_id: Optional[str] = None,
        current_report_text: str = "",
        current_html_charts: str = "",
        selected_text: Optional[str] = None,
        selected_text_context: Optional[Dict[str, str]] = None,
        dialog_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式处理用户对话消息（支持多轮对话上下文）

        Args:
            session_id: 会话ID
            user_message: 用户消息
            current_charts: 当前图表列表
            conversation_id: 对话ID
            current_report_text: 当前报告文本
            current_html_charts: 当前HTML图表
            selected_text: 选中的文字
            selected_text_context: 选中文字的上下文
            dialog_history: 对话历史列表 [{"role": "user/assistant", "content": "..."}]

        Yields:
            {
                "type": "thinking" | "content" | "done" | "error",
                "content": str,
                "data": dict  # 仅在done时包含完整结果
            }
        """
        if dialog_history is None:
            dialog_history = []

        try:
            logger.info(f"[BailianDialogServiceStream] 开始流式处理 - session_id={session_id}, 历史消息数={len(dialog_history)}")
            
            # 检测用户意图（传入是否有选中文字）
            intent = self._detect_intent(user_message, has_selected_text=bool(selected_text))
            logger.info(f"[BailianDialogServiceStream] 检测到意图: {intent}, 用户消息: {user_message[:50]}...")
            
            # 删除操作不需要调用AI，直接处理
            if intent == 'delete_content' and selected_text and current_report_text:
                # 记录调试信息
                logger.info(f"[BailianDialogServiceStream] 尝试删除内容 - 选中文字长度: {len(selected_text)}")
                logger.debug(f"[BailianDialogServiceStream] 选中文字前50字符: {repr(selected_text[:50])}")
                
                # 尝试直接匹配
                if selected_text in current_report_text:
                    # 删除选中的文字
                    new_report_text = current_report_text.replace(selected_text, '', 1)
                    # 清理多余的空行
                    new_report_text = re.sub(r'\n{3,}', '\n\n', new_report_text)
                    new_report_text = new_report_text.strip()
                    
                    result = {
                        "response": "已删除选中的内容。",
                        "modified_charts": [],
                        "conversation_id": conversation_id or str(uuid.uuid4()),
                        "action_type": "delete_content",
                        "new_report_text": new_report_text
                    }
                    
                    logger.info(f"[BailianDialogServiceStream] 删除内容完成 - 删除长度: {len(selected_text)}")
                    
                    yield {
                        "type": "done",
                        "content": "",
                        "data": result
                    }
                    return
                else:
                    # 尝试规范化后匹配（处理空格和换行差异）
                    normalized_selected = self._normalize_text(selected_text)
                    normalized_report = self._normalize_text(current_report_text)
                    
                    if normalized_selected in normalized_report:
                        # 找到规范化后的位置，然后在原文中找到对应的实际文本
                        new_report_text = self._delete_normalized_text(current_report_text, selected_text)
                        if new_report_text:
                            # 清理多余的空行
                            new_report_text = re.sub(r'\n{3,}', '\n\n', new_report_text)
                            new_report_text = new_report_text.strip()
                            
                            result = {
                                "response": "已删除选中的内容。",
                                "modified_charts": [],
                                "conversation_id": conversation_id or str(uuid.uuid4()),
                                "action_type": "delete_content",
                                "new_report_text": new_report_text
                            }
                            
                            logger.info(f"[BailianDialogServiceStream] 删除内容完成（规范化匹配）- 删除长度: {len(selected_text)}")
                            
                            yield {
                                "type": "done",
                                "content": "",
                                "data": result
                            }
                            return
                    
                    # 都没找到，返回错误
                    logger.warning(f"[BailianDialogServiceStream] 未找到要删除的内容")
                    logger.debug(f"[BailianDialogServiceStream] 报告文字前100字符: {repr(current_report_text[:100])}")
                    yield {
                        "type": "error",
                        "content": "未找到要删除的内容，可能是文字格式有差异，请尝试重新选择"
                    }
                    return
            
            # 根据意图构建不同的prompt和消息
            use_history = False  # 是否使用对话历史

            if intent == 'modify_text' and selected_text:
                prompt = self._build_text_modification_prompt(user_message, selected_text)
            elif intent == 'add_content':
                # 添加内容时，如果有选中文字，将其作为上下文
                prompt = self._build_add_content_prompt(user_message, current_report_text, selected_text)
            else:
                # 普通对话：使用对话历史进行多轮对话
                prompt = user_message  # 直接使用用户消息，上下文由_build_messages_with_history处理
                use_history = True

            # 流式调用API
            full_content = ""
            full_reasoning = ""

            if use_history and dialog_history:
                # 使用多轮对话模式
                messages = self._build_messages_with_history(
                    prompt, dialog_history, current_report_text, current_charts
                )
                api_generator = self._call_api_stream_with_messages(messages)
            else:
                # 单轮对话模式
                api_generator = self._call_api_stream(prompt)

            async for chunk in api_generator:
                chunk_type = chunk.get("type")
                chunk_content = chunk.get("content", "")
                
                if chunk_type == "thinking":
                    full_reasoning += chunk_content
                    yield chunk
                elif chunk_type == "content":
                    full_content += chunk_content
                    yield chunk
                elif chunk_type == "error":
                    yield chunk
                    return
            
            # 处理最终结果
            final_content = full_content if full_content else full_reasoning
            
            # 构建返回结果
            result = {
                "response": final_content,
                "modified_charts": [],
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "action_type": intent
            }
            
            # 根据意图处理结果
            if intent == 'add_content' and current_report_text:
                # 添加内容模式
                new_content = final_content.strip()
                
                if selected_text and selected_text in current_report_text:
                    # 如果有选中文字，智能找到插入位置
                    insert_pos = self._find_smart_insert_position(current_report_text, selected_text)
                    new_report_text = (
                        current_report_text[:insert_pos].rstrip() + 
                        "\n\n" + new_content + "\n\n" +
                        current_report_text[insert_pos:].lstrip()
                    )
                    result["response"] = f"已在合适位置添加了新内容。"
                    logger.info(f"[BailianDialogServiceStream] 智能插入内容 - 插入位置: {insert_pos}, 新增长度: {len(new_content)}")
                else:
                    # 没有选中文字，在报告末尾添加
                    new_report_text = current_report_text.rstrip() + "\n\n" + new_content
                    result["response"] = "已将新内容添加到报告末尾。"
                    logger.info(f"[BailianDialogServiceStream] 在报告末尾添加内容 - 新增长度: {len(new_content)}")
                
                result["new_report_text"] = new_report_text
                result["action_type"] = "add_content"
                
            elif intent == 'modify_text' and selected_text and current_report_text:
                # 文字修改：替换选中的文字
                modified_text = final_content.strip()
                if selected_text in current_report_text:
                    new_report_text = current_report_text.replace(selected_text, modified_text, 1)
                    result["new_report_text"] = new_report_text
                    result["modified_text"] = modified_text
                    result["response"] = "已根据您的指令修改了选中的文字。"
                    result["action_type"] = "modify_text"
            
            yield {
                "type": "done",
                "content": "",
                "data": result
            }
            
            logger.info(f"[BailianDialogServiceStream] 流式处理完成 - session_id={session_id}, action_type={result['action_type']}")
            
        except Exception as e:
            logger.error(f"[BailianDialogServiceStream] 流式处理失败: {str(e)}")
            yield {
                "type": "error",
                "content": f"处理失败: {str(e)}"
            }

    def _build_text_modification_prompt(self, user_message: str, selected_text: str) -> str:
        """构建文字修改提示词"""
        return f"""你是一个专业的文字编辑助手。用户选中了报告中的一段文字，希望你根据指令进行修改。

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

    def _build_add_content_prompt(self, user_message: str, current_report_text: str, selected_text: Optional[str] = None) -> str:
        """构建添加内容的提示词"""
        # 如果有选中文字，使用选中文字作为上下文
        if selected_text:
            context_info = f"""**用户选中的文字（新内容将添加在此之后）**：
{selected_text}"""
        else:
            # 截取报告的最后部分作为上下文（避免太长）
            report_context = current_report_text[-2000:] if len(current_report_text) > 2000 else current_report_text
            context_info = f"""**当前报告内容（末尾部分）**：
{report_context}"""
        
        return f"""你是一个专业的数据分析报告撰写助手。用户希望在现有报告中添加新的内容。

{context_info}

**用户的需求**：
{user_message}

**要求**：
1. 根据用户需求生成新的章节/段落内容
2. 保持与现有报告一致的格式和风格
3. 如果用户指定了章节编号（如4.4），请使用该编号
4. 内容要专业、有深度，与报告主题相关
5. 直接输出新内容，不要添加"以下是新内容"等前缀
6. 使用Markdown格式，包含适当的标题层级

请直接输出要添加的新内容："""

    def _build_dialog_prompt(self, user_message: str, current_charts: List[Dict[str, Any]], current_report_text: str = "") -> str:
        """构建对话提示词"""
        chart_desc = self._describe_charts(current_charts)
        
        # 如果有报告内容，提供简要上下文
        report_context = ""
        if current_report_text:
            # 只取报告的开头和结尾作为上下文
            if len(current_report_text) > 1000:
                report_context = f"\n\n当前报告概要：\n{current_report_text[:500]}...\n...\n{current_report_text[-500:]}"
            else:
                report_context = f"\n\n当前报告内容：\n{current_report_text}"
        
        return f"""你是一个专业的数据分析师助手，可以帮助用户分析数据和修改图表。

当前图表状态：{chart_desc}{report_context}

用户需求：{user_message}

请根据以上信息回复用户。用中文回复，保持专业、友好的态度。"""

    def _describe_charts(self, charts: List[Dict[str, Any]]) -> str:
        """描述当前图表状态"""
        if not charts:
            return "暂无图表"
        descriptions = []
        for i, chart in enumerate(charts):
            chart_type = chart.get('type', '未知类型')
            title = chart.get('title', f'图表{i+1}')
            descriptions.append(f"{title}（{chart_type}图）")
        return "，".join(descriptions)

    def _find_smart_insert_position(self, report_text: str, selected_text: str) -> int:
        """
        智能查找插入位置
        策略：找到选中文字所在章节的结束位置（下一个同级或更高级标题之前）
        """
        # 找到选中文字的位置
        selected_start = report_text.find(selected_text)
        if selected_start == -1:
            return len(report_text)
        
        selected_end = selected_start + len(selected_text)
        
        # 从选中文字结束位置开始，查找下一个大章节的开始位置
        text_after = report_text[selected_end:]
        
        # 查找下一个大章节的开始位置
        # 匹配一级标题：## 标题、一、标题、1. 标题（但不是1.1这种二级标题）
        next_major_section_patterns = [
            r'\n#{1,2}\s+[^#]',  # Markdown一级或二级标题
            r'\n[一二三四五六七八九十]+[、\.]\s*\S',  # 中文一级标题（如：五、后续行动计划）
            r'\n(\d+)\.\s+(?!\d)',  # 数字一级标题（后面不是数字，避免匹配1.1）
        ]
        
        earliest_pos = len(text_after)
        matched_pattern = None
        for pattern in next_major_section_patterns:
            match = re.search(pattern, text_after)
            if match:
                # +1 是因为我们要保留换行符在前面的内容中
                pos = match.start() + 1
                if pos < earliest_pos:
                    earliest_pos = pos
                    matched_pattern = pattern
                    logger.debug(f"[BailianDialogServiceStream] 找到下一个大章节，模式: {pattern}, 位置: {pos}")
        
        # 计算最终插入位置
        if earliest_pos < len(text_after):
            insert_pos = selected_end + earliest_pos
            logger.info(f"[BailianDialogServiceStream] 智能插入 - 在下一个大章节前插入，模式: {matched_pattern}")
        else:
            # 如果没找到下一个大章节，就在选中文字后面插入
            insert_pos = selected_end
            logger.info(f"[BailianDialogServiceStream] 智能插入 - 未找到下一个大章节，在选中文字末尾插入")
        
        logger.info(f"[BailianDialogServiceStream] 插入位置: selected_end={selected_end}, offset={earliest_pos}, final={insert_pos}")
        
        return insert_pos

    def _normalize_text(self, text: str) -> str:
        """规范化文本，用于宽松匹配"""
        # 将多个空白字符替换为单个空格
        normalized = re.sub(r'\s+', ' ', text)
        # 去除首尾空白
        normalized = normalized.strip()
        return normalized

    def _delete_normalized_text(self, report_text: str, selected_text: str) -> Optional[str]:
        """
        使用规范化匹配删除文本
        尝试找到与选中文字最相似的部分并删除
        """
        # 规范化选中的文字
        normalized_selected = self._normalize_text(selected_text)
        
        # 策略1：尝试找到最长的匹配子串并删除
        # 将选中文字分成多个句子/片段
        selected_sentences = re.split(r'[。！？\n]', selected_text)
        selected_sentences = [s.strip() for s in selected_sentences if s.strip()]
        
        if selected_sentences:
            # 找到第一个句子在报告中的位置
            first_sentence = selected_sentences[0]
            if len(first_sentence) > 10:  # 确保句子足够长以避免误匹配
                # 在报告中查找这个句子
                pos = report_text.find(first_sentence)
                if pos != -1:
                    # 找到了，尝试找到最后一个句子的结束位置
                    last_sentence = selected_sentences[-1] if len(selected_sentences) > 1 else first_sentence
                    end_pos = report_text.find(last_sentence, pos)
                    if end_pos != -1:
                        end_pos += len(last_sentence)
                        # 扩展到句子结束符
                        while end_pos < len(report_text) and report_text[end_pos] in '。！？\n':
                            end_pos += 1
                        # 删除这部分内容
                        new_report_text = report_text[:pos] + report_text[end_pos:]
                        logger.info(f"[BailianDialogServiceStream] 使用句子匹配删除 - 起始:{pos}, 结束:{end_pos}")
                        return new_report_text
        
        # 策略2：尝试在报告中找到匹配的部分（按段落）
        paragraphs = report_text.split('\n\n')
        
        for i, para in enumerate(paragraphs):
            normalized_para = self._normalize_text(para)
            # 检查这个段落是否包含选中的文字（规范化后）
            if normalized_selected in normalized_para or normalized_para in normalized_selected:
                # 找到了，删除这个段落
                new_paragraphs = paragraphs[:i] + paragraphs[i+1:]
                logger.info(f"[BailianDialogServiceStream] 使用段落匹配删除 - 段落索引:{i}")
                return '\n\n'.join(new_paragraphs)
        
        # 策略3：如果按段落没找到，尝试按行匹配
        lines = report_text.split('\n')
        selected_lines = selected_text.split('\n')
        
        # 找到第一行在报告中的位置
        first_line_normalized = self._normalize_text(selected_lines[0]) if selected_lines else ''
        
        for i, line in enumerate(lines):
            line_normalized = self._normalize_text(line)
            if line_normalized == first_line_normalized or (len(first_line_normalized) > 10 and first_line_normalized in line_normalized):
                # 找到起始位置，删除相应数量的行
                end_idx = min(i + len(selected_lines), len(lines))
                new_lines = lines[:i] + lines[end_idx:]
                logger.info(f"[BailianDialogServiceStream] 使用行匹配删除 - 起始行:{i}, 结束行:{end_idx}")
                return '\n'.join(new_lines)
        
        return None

    async def _call_api_stream(self, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用阿里百炼API"""
        if not self.api_key:
            yield {"type": "error", "content": "API密钥未配置"}
            return
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "enable"
        }
        
        if self.use_openai_format:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 4000,
                "stream": True
            }
        else:
            payload = {
                "model": self.model,
                "input": {
                    "messages": [{"role": "user", "content": prompt}]
                },
                "parameters": {
                    "temperature": 0.1,
                    "max_tokens": 4000,
                    "result_format": "message",
                    "incremental_output": True
                }
            }
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream('POST', self.api_url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    
                    buffer = ""
                    async for chunk in response.aiter_bytes():
                        buffer += chunk.decode('utf-8', errors='ignore')
                        
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            
                            if not line or line.startswith(':'):
                                continue
                            
                            if line.startswith('data:'):
                                line = line[5:].strip()
                            
                            if line == '[DONE]':
                                return
                            
                            try:
                                chunk_data = json.loads(line)
                                
                                # 提取内容
                                if not self.use_openai_format:
                                    # DashScope格式
                                    if 'output' in chunk_data and 'choices' in chunk_data['output']:
                                        choices = chunk_data['output']['choices']
                                        if choices and 'message' in choices[0]:
                                            message = choices[0]['message']
                                            content_text = message.get('content', '')
                                            reasoning_text = message.get('reasoning_content', '')
                                            
                                            # 优先输出思考过程
                                            if reasoning_text:
                                                yield {
                                                    "type": "thinking",
                                                    "content": reasoning_text
                                                }
                                            elif content_text:
                                                yield {
                                                    "type": "content",
                                                    "content": content_text
                                                }
                                else:
                                    # OpenAI格式
                                    if 'choices' in chunk_data and chunk_data['choices']:
                                        delta = chunk_data['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            yield {
                                                "type": "content",
                                                "content": delta['content']
                                            }
                            except json.JSONDecodeError:
                                continue
                                
        except httpx.HTTPStatusError as e:
            logger.error(f"[BailianDialogServiceStream] HTTP错误: {e.response.status_code}")
            yield {"type": "error", "content": f"API调用失败: HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error(f"[BailianDialogServiceStream] API调用异常: {str(e)}")
            yield {"type": "error", "content": f"API调用异常: {str(e)}"}

    async def _call_api_stream_with_messages(
        self,
        messages: List[Dict[str, str]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        使用多条消息流式调用API（支持多轮对话）

        Args:
            messages: 消息列表 [{"role": "system/user/assistant", "content": "..."}]

        Yields:
            {"type": "thinking" | "content" | "error", "content": str}
        """
        if not self.api_key:
            yield {"type": "error", "content": "API密钥未配置"}
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "enable"
        }

        if self.use_openai_format:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 4000,
                "stream": True
            }
        else:
            # DashScope原生格式
            payload = {
                "model": self.model,
                "input": {
                    "messages": messages
                },
                "parameters": {
                    "temperature": 0.1,
                    "max_tokens": 4000,
                    "result_format": "message",
                    "incremental_output": True
                }
            }

        logger.debug(f"[BailianDialogServiceStream] 多轮对话调用 - 消息数: {len(messages)}")

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream('POST', self.api_url, json=payload, headers=headers) as response:
                    response.raise_for_status()

                    buffer = ""
                    async for chunk in response.aiter_bytes():
                        buffer += chunk.decode('utf-8', errors='ignore')

                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()

                            if not line or line.startswith(':'):
                                continue

                            if line.startswith('data:'):
                                line = line[5:].strip()

                            if line == '[DONE]':
                                return

                            try:
                                chunk_data = json.loads(line)

                                # 提取内容
                                if not self.use_openai_format:
                                    # DashScope格式
                                    if 'output' in chunk_data and 'choices' in chunk_data['output']:
                                        choices = chunk_data['output']['choices']
                                        if choices and 'message' in choices[0]:
                                            message = choices[0]['message']
                                            content_text = message.get('content', '')
                                            reasoning_text = message.get('reasoning_content', '')

                                            # 优先输出思考过程
                                            if reasoning_text:
                                                yield {
                                                    "type": "thinking",
                                                    "content": reasoning_text
                                                }
                                            elif content_text:
                                                yield {
                                                    "type": "content",
                                                    "content": content_text
                                                }
                                else:
                                    # OpenAI格式
                                    if 'choices' in chunk_data and chunk_data['choices']:
                                        delta = chunk_data['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            yield {
                                                "type": "content",
                                                "content": delta['content']
                                            }
                            except json.JSONDecodeError:
                                continue

        except httpx.HTTPStatusError as e:
            logger.error(f"[BailianDialogServiceStream] HTTP错误: {e.response.status_code}")
            yield {"type": "error", "content": f"API调用失败: HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error(f"[BailianDialogServiceStream] API调用异常: {str(e)}")
            yield {"type": "error", "content": f"API调用异常: {str(e)}"}
