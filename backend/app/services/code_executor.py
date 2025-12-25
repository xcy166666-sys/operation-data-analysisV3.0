"""
代码执行引擎（安全沙箱）
"""
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

