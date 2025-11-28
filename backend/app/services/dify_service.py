"""
Dify AI工作流服务
"""
import httpx
import json
from typing import Dict, Any, Optional, AsyncGenerator
from loguru import logger


class DifyService:
    """Dify API服务"""
    
    @staticmethod
    async def upload_file(
        api_url: str,
        api_key: str,
        file_path: str,
        file_name: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        上传文件到 Dify
        
        Args:
            api_url: Dify API地址，如 https://api.dify.ai/v1
            api_key: Dify API密钥
            file_path: 本地文件路径
            file_name: 文件名
            user_id: Dify用户ID
        
        Returns:
            Dict包含文件信息（id, name, size等）
        """
        # 构建文件上传URL：如果api_url已经包含完整路径，直接使用；否则拼接 /files/upload
        if '/files/upload' in api_url:
            url = api_url
        else:
            base_url = api_url.rstrip('/')
            url = f"{base_url}/files/upload"
        
        logger.info(f"[DifyService] 上传文件到Dify")
        logger.info(f"[DifyService] API地址: {api_url}")
        logger.info(f"[DifyService] 构建的URL: {url}")
        logger.info(f"[DifyService] 文件名: {file_name}")
        
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        try:
            # 读取文件内容
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # 根据文件扩展名确定 MIME 类型和文件类型
            file_ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
            mime_type_map = {
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'xls': 'application/vnd.ms-excel',
                'csv': 'text/csv',
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
                'webp': 'image/webp'
            }
            mime_type = mime_type_map.get(file_ext, 'application/octet-stream')
            
            # 文件类型（用于 Dify API 的 type 字段）
            # 图片类型统一使用 "image/png" 格式
            if file_ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                file_type = 'image/png'
            else:
                file_type_map = {
                    'xlsx': 'XLSX',
                    'xls': 'XLS',
                    'csv': 'CSV'
                }
                file_type = file_type_map.get(file_ext.upper(), 'XLSX')
            
            # 准备 multipart/form-data
            files = {
                "file": (file_name, file_content, mime_type)
            }
            data = {
                "user": user_id,
                "type": file_type  # 添加 type 字段，如 "XLSX"
            }
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                logger.info(f"[DifyService] 开始上传文件 - file_name={file_name}, type={file_type}, size={len(file_content)} bytes")
                response = await client.post(url, files=files, data=data, headers=headers)
                logger.info(f"[DifyService] 文件上传响应 - status_code={response.status_code}")
                
                # Dify 文件上传成功返回 201，不是 200
                if response.status_code != 201:
                    error_text = response.text
                    logger.error(f"[DifyService] 文件上传失败 - status={response.status_code}, response={error_text[:500]}")
                    response.raise_for_status()
                
                result = response.json()
                file_id = result.get('id')
                logger.info(f"[DifyService] 文件上传成功 - file_id={file_id}, name={result.get('name')}")
                
                if not file_id:
                    logger.error(f"[DifyService] 文件上传响应中缺少 id 字段 - response={result}")
                    return {
                        "success": False,
                        "error": "Dify文件上传响应中缺少文件ID",
                        "detail": str(result)
                    }
                
                return {
                    "success": True,
                    "data": result
                }
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            try:
                error_json = e.response.json()
                error_message = error_json.get("message", error_json.get("error", error_detail))
            except:
                error_message = error_detail
            
            logger.error(f"[DifyService] 文件上传失败 - Status: {e.response.status_code}")
            logger.error(f"[DifyService] 错误详情: {error_message}")
            logger.error(f"[DifyService] 完整响应: {error_detail[:1000]}")
            logger.error(f"[DifyService] 请求URL: {url}")
            logger.error(f"[DifyService] 文件大小: {len(file_content)} bytes")
            logger.error(f"[DifyService] 文件类型: {file_type}")
            logger.error(f"[DifyService] MIME类型: {mime_type}")
            return {
                "success": False,
                "error": f"Dify文件上传失败: {e.response.status_code}",
                "detail": error_message
            }
        except Exception as e:
            logger.error(f"[DifyService] 文件上传异常 - Error: {str(e)}")
            return {
                "success": False,
                "error": f"文件上传失败: {str(e)}"
            }
    
    @staticmethod
    def generate_user_id(
        user_id: int, 
        function_key: str, 
        conversation_id: Optional[int] = None
    ) -> str:
        """
        生成Dify用户标识（简化版，移除project_id依赖）
        
        格式: user_{user_id}_func_{function_key}_conv_{conversation_id}
        
        Args:
            user_id: 系统用户ID
            function_key: 功能键（如 operation_data_analysis）
            conversation_id: 对话ID（可选，首次发送时为None，创建对话后传入）
        
        Returns:
            Dify用户标识字符串
        """
        if conversation_id:
            # 完整格式：包含对话ID（有上下文关联）
            return f"user_{user_id}_func_{function_key}_conv_{conversation_id}"
        else:
            # 临时格式：不包含对话ID（首次发送，尚未创建对话）
            # 使用时间戳确保唯一性
            import time
            timestamp = int(time.time() * 1000)
            return f"user_{user_id}_func_{function_key}_temp_{timestamp}"
    
    @staticmethod
    async def run_workflow(
        api_url: str,
        api_key: str,
        workflow_id: str,
        user_id: int,
        function_key: str,
        inputs: Dict[str, Any],
        conversation_id: Optional[int] = None,
        response_mode: str = "blocking",
        workflow_type: str = "workflow"  # "workflow" 或 "chatflow"
    ) -> Dict[str, Any]:
        """
        执行Dify工作流或Chatflow
        
        Args:
            api_url: Dify API地址，如 https://api.dify.ai/v1
            api_key: Dify API密钥
            workflow_id: Dify工作流ID或Chatflow ID
            user_id: 系统用户ID
            function_key: 功能键（如 operation_data_analysis）
            inputs: 输入参数字典
            conversation_id: 对话ID（可选）
            response_mode: 响应模式 - blocking(阻塞) 或 streaming(流式)
            workflow_type: 工作流类型 - "workflow" 或 "chatflow"
        
        Returns:
            Dict包含执行结果
        """
        # 生成唯一的Dify用户标识
        dify_user = DifyService.generate_user_id(
            user_id=user_id,
            function_key=function_key,
            conversation_id=conversation_id
        )
        
        # 构建请求URL（去除尾部斜杠）
        # 如果api_url已经包含完整路径，直接使用；否则拼接相应端点
        base_url = api_url.rstrip('/')
        
        # 根据工作流类型选择不同的端点
        if workflow_type == "chatflow":
            # Chatflow 使用 /chat-messages 端点
            if '/chat-messages' in api_url:
                url = api_url
                logger.info(f"[DifyService] 检测到完整Chatflow端点URL，直接使用: {url}")
            else:
                url = f"{base_url}/chat-messages"
                logger.info(f"[DifyService] 构建Chatflow URL: {url}")
        else:
            # Workflow 使用 /workflows/run 端点
            if base_url.endswith('/workflows/run'):
                url = base_url
                logger.info(f"检测到完整Workflow端点URL，直接使用: {url}")
            else:
                url = f"{base_url}/workflows/run"
        
        # 构建请求体
        if workflow_type == "chatflow":
            # Chatflow 的请求格式：根据用户提供的测试脚本，文件应该放在 inputs.excell 对象中
            # 将 inputs 中的变量转换为 query 和 inputs
            # 优先使用query，如果没有则使用sys.query
            query = inputs.get("query") or inputs.get("sys.query", "")
            if not query:
                logger.warning(f"[DifyService] Chatflow query 为空，可能导致错误")
            
            # 提取文件ID（支持upload_file_id或excell作为键名）
            upload_file_id = inputs.get("upload_file_id") or inputs.get("excell")
            
            # 构建 chat_inputs，将文件放在 excell 对象中（根据测试脚本格式）
            chat_inputs = {}
            if upload_file_id:
                # 根据测试脚本，文件应该放在 inputs.excell 对象中
                chat_inputs["excell"] = {
                    "transfer_method": "local_file",
                    "upload_file_id": upload_file_id,
                    "type": "document"
                }
                logger.info(f"[DifyService] 添加文件到 inputs.excell - file_id: {upload_file_id}")
            
            # 保留其他输入变量（排除已处理的）
            for k, v in inputs.items():
                if k not in ["sys.query", "query", "upload_file_id", "excell"]:
                    chat_inputs[k] = v
            
            payload = {
                "inputs": chat_inputs,
                "query": query,
                "response_mode": response_mode,
                "user": dify_user
            }
            
            # 添加 conversation_id（如果提供且是有效的UUID格式）
            # Dify要求conversation_id必须是有效的UUID，如果不是则让Dify自动创建新对话
            if conversation_id:
                import re
                # 检查是否是有效的UUID格式
                uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                conversation_id_str = str(conversation_id)
                if re.match(uuid_pattern, conversation_id_str, re.IGNORECASE):
                    payload["conversation_id"] = conversation_id_str
                    logger.info(f"[DifyService] 使用conversation_id: {conversation_id_str}")
                else:
                    logger.info(f"[DifyService] conversation_id不是有效的UUID格式，不传递此参数，让Dify自动创建新对话")
            
            logger.debug(f"[DifyService] Chatflow payload: query={query[:50]}..., inputs_keys={list(chat_inputs.keys())}, has_excell={upload_file_id is not None}")
        else:
            # Workflow 的请求格式
            payload = {
                "inputs": inputs,
                "response_mode": response_mode,
                "user": dify_user
            }
        
        logger.info(f"准备调用Dify API ({workflow_type}) - URL: {url}, User: {dify_user}")
        logger.debug(f"请求payload: {payload}")
        logger.info(f"[DifyService] 发送Dify请求 - URL: {url}")
        logger.info(f"[DifyService] 请求参数 - inputs_keys: {list(inputs.keys())}")
        
        # 请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # 增加超时时间到300秒（5分钟），因为复杂的Dify工作流可能需要较长时间执行
            logger.info(f"[DifyService] 开始发送HTTP POST请求到: {url}")
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                logger.info(f"[DifyService] 收到HTTP响应 - status_code={response.status_code}")
                logger.info(f"[DifyService] 响应内容长度: {len(response.text)} 字符")
                response.raise_for_status()
                
                result = response.json()
                
                logger.info(f"Dify {workflow_type}执行成功 - User: {dify_user}, ID: {workflow_id}")
                logger.debug(f"Dify响应详情: {result}")
                logger.info(f"[DifyService] 解析JSON成功 - data_keys: {list(result.keys())}")
                
                return {
                    "success": True,
                    "data": result,
                    "dify_user": dify_user
                }
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            try:
                error_json = e.response.json()
                error_message = error_json.get("message", error_json.get("error", error_detail))
                # 尝试获取更详细的错误信息
                if "detail" in error_json:
                    error_message = error_json["detail"]
            except:
                error_message = error_detail
            
            logger.error(f"Dify API请求失败 - Status: {e.response.status_code}, User: {dify_user}, Error: {error_message}")
            logger.error(f"[DifyService] HTTP错误 - URL: {url}, Response: {error_detail[:500]}")
            return {
                "success": False,
                "error": f"Dify API返回错误: {e.response.status_code}",
                "detail": error_message
            }
        except httpx.TimeoutException:
            logger.error(f"Dify API请求超时 - User: {dify_user}, URL: {url}")
            logger.error(f"[DifyService] 请求超时 - 超过300秒")
            return {
                "success": False,
                "error": "Dify API请求超时，请稍后重试"
            }
        except Exception as e:
            logger.error(f"调用Dify API异常 - User: {dify_user}, Error: {str(e)}")
            logger.error(f"[DifyService] 异常详情: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "error": f"调用Dify失败: {str(e)}"
            }
    
    @staticmethod
    async def test_connection(
        api_url: str,
        api_key: str
    ) -> Dict[str, Any]:
        """
        测试Dify API连接（用于验证配置）
        
        Args:
            api_url: Dify API地址
            api_key: Dify API密钥
        
        Returns:
            Dict包含测试结果
        """
        base_url = api_url.rstrip('/')
        # 使用parameters端点测试连接（该端点通常用于获取应用参数）
        url = f"{base_url}/parameters"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                logger.info(f"Dify连接测试成功 - URL: {api_url}")
                
                return {
                    "success": True,
                    "message": "连接成功",
                    "data": response.json()
                }
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                error_msg = "API密钥无效"
            elif e.response.status_code == 404:
                error_msg = "API地址或工作流ID不正确"
            else:
                error_msg = f"HTTP {e.response.status_code}"
            
            logger.error(f"Dify连接测试失败 - URL: {api_url}, Error: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "detail": e.response.text
            }
        except httpx.TimeoutException:
            logger.error(f"Dify连接超时 - URL: {api_url}")
            return {
                "success": False,
                "error": "连接超时，请检查API地址"
            }
        except Exception as e:
            logger.error(f"Dify连接测试异常 - URL: {api_url}, Error: {str(e)}")
            return {
                "success": False,
                "error": f"连接失败: {str(e)}"
            }

