"""
图表修改服务 - 使用AI理解用户指令并修改图表
"""
from typing import Optional, Dict, Any
from loguru import logger
import httpx
from app.core.config import settings


class ChartModificationService:
    """图表修改服务"""
    
    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model = "qwen-plus"
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    async def modify_chart(
        self,
        current_html: str,
        color: Optional[str] = None,
        chart_type: Optional[str] = None,
        ai_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        修改图表
        
        Args:
            current_html: 当前图表的HTML代码
            color: 颜色修改（如 #409eff）
            chart_type: 图表类型（bar/line/pie）
            ai_instruction: AI自由修改指令
        
        Returns:
            {
                "success": bool,
                "html": str,  # 新的HTML代码
                "error": str  # 错误信息（如果失败）
            }
        """
        try:
            # 构建修改指令
            instruction = self._build_instruction(color, chart_type, ai_instruction)
            
            if not instruction:
                return {
                    "success": False,
                    "error": "没有提供任何修改指令"
                }
            
            logger.info(f"[图表修改] 修改指令: {instruction}")
            
            # 构建Prompt
            prompt = self._build_prompt(current_html, instruction)
            
            # 调用AI
            new_html = await self._call_ai(prompt)
            
            if not new_html:
                return {
                    "success": False,
                    "error": "AI生成失败"
                }
            
            logger.info(f"[图表修改] 修改成功，新HTML长度: {len(new_html)}")
            
            return {
                "success": True,
                "html": new_html
            }
            
        except Exception as e:
            logger.error(f"[图表修改] 修改失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_instruction(
        self,
        color: Optional[str],
        chart_type: Optional[str],
        ai_instruction: Optional[str]
    ) -> str:
        """构建修改指令"""
        instructions = []
        
        if color:
            instructions.append(f"将图表的主色调改为 {color}")
        
        if chart_type:
            type_map = {
                "bar": "柱状图",
                "line": "折线图",
                "pie": "饼图"
            }
            chart_name = type_map.get(chart_type, chart_type)
            instructions.append(f"将图表类型改为{chart_name}")
        
        if ai_instruction:
            instructions.append(ai_instruction)
        
        return "；".join(instructions)
    
    def _build_prompt(self, current_html: str, instruction: str) -> str:
        """构建AI Prompt"""
        return f"""你是一个图表修改专家。用户想要修改现有的图表，请根据用户的指令重新生成HTML代码。

当前图表HTML代码：
```html
{current_html}
```

用户修改指令：
{instruction}

请生成修改后的完整HTML代码，要求：
1. **保持图表的数据不变**，只修改样式和类型
2. 应用用户要求的所有修改
3. 确保HTML代码完整可运行，包含所有必要的标签
4. 使用ECharts图表库（通过CDN引入）
5. 包含必要的CSS样式和JavaScript代码
6. 图表容器设置合适的尺寸（width: 100%; height: 600px; min-height: 600px;）
7. 确保图表在iframe中能正常显示

**重要**：直接返回完整的HTML代码，不要有任何其他说明文字，不要使用markdown代码块标记。

HTML代码："""
    
    async def _call_ai(self, prompt: str) -> Optional[str]:
        """调用AI API"""
        try:
            async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 4000
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"[图表修改] AI调用失败: {response.status_code} - {response.text}")
                    return None
                
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # 清理可能的markdown标记
                content = content.strip()
                if content.startswith("```html"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                return content
                
        except Exception as e:
            logger.error(f"[图表修改] AI调用异常: {str(e)}")
            return None
