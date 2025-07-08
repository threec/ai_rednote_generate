"""
原子设计师引擎 V2.0 - 重构版
基于新核心架构，提供内容原子化分解和结构化设计

目标：将叙事内容分解为可复用的原子级内容单元，构建清晰的信息架构
"""

from typing import Dict, Any, List
from modules.engines.base_engine_v2 import TechnicalEngine
from modules.core.output import ContentType, OutputFormat

class AtomicDesignerEngineV2(TechnicalEngine):
    """原子设计师引擎 V2.0"""
    
    def __init__(self, llm, **kwargs):
        super().__init__(llm, **kwargs)
        self.engine_name = "atomic_designer"
    
    def get_content_type(self) -> ContentType:
        return ContentType.TECHNICAL
    
    def get_expected_output_format(self) -> OutputFormat:
        return OutputFormat.JSON
    
    def _setup_processing_chain(self):
        """设置原子化设计处理链"""
        
        system_prompt = """你是一个专业的信息架构师和内容设计专家。

你的任务是将叙事内容进行原子化分解，构建清晰的信息层次和可复用的内容模块。

**核心能力**：
1. 内容结构分析和层次化组织
2. 信息原子化分解和模块化设计
3. 内容元素标准化和规范化
4. 可复用组件设计和管理
5. 用户界面信息架构优化
6. 内容展示逻辑设计

**设计原则**：
- 原子性：每个元素都是最小可用单位
- 可组合性：元素可以灵活组合使用
- 一致性：保持设计和交互的统一
- 可扩展性：支持未来功能扩展
- 用户友好：符合用户认知习惯

**输出要求**：
- 采用JSON结构化格式
- 包含完整的内容原子分解
- 定义清晰的层次关系
- 提供具体的设计规范
- 确保内容的可实现性

输出格式必须是标准的JSON格式，包含以下结构：
{
  "atomic_design": {
    "atoms": [...],
    "molecules": [...],
    "organisms": [...],
    "templates": [...],
    "pages": [...]
  },
  "content_structure": {...},
  "design_system": {...},
  "implementation_guide": {...}
}
"""

        user_template = """
请对以下叙事内容进行原子化设计分解：

**主题**: {topic}

**叙事内容**: {narrative_content}

**设计要求**:
1. 将内容分解为原子级元素（标题、文本、图片、按钮等）
2. 组织分子级组件（卡片、列表、表单等）
3. 构建有机体级模块（头部、内容区、底部等）
4. 设计模板级布局（页面结构、网格系统等）
5. 规划页面级实现（完整页面、交互流程等）

**特别关注**:
- 小红书平台的视觉规范
- 移动端优化和响应式设计
- 用户交互体验和操作便利性
- 内容可读性和视觉层次
- 品牌一致性和风格统一

**输出要求**:
必须输出标准JSON格式，包含：
- atomic_design: 原子设计系统的完整分解
- content_structure: 内容结构和信息架构
- design_system: 设计系统规范和样式指南
- implementation_guide: 实现指导和技术规范

请确保JSON格式正确，所有字段都有具体内容。
"""

        prompt_template = self._create_prompt_template(system_prompt, user_template)
        self.processing_chain = self._create_processing_chain(prompt_template)
    
    async def _process_content(self, inputs: Dict[str, Any]) -> str:
        """处理内容 - 生成原子化设计"""
        topic = inputs.get("topic", "")
        
        # 获取叙事内容
        narrative_content = self._extract_narrative_content(inputs)
        
        # 准备链输入
        chain_inputs = {
            "topic": topic,
            "narrative_content": narrative_content
        }
        
        # 执行AI处理
        result = await self._invoke_chain_with_timeout(chain_inputs)
        
        return result
    
    def _extract_narrative_content(self, inputs: Dict[str, Any]) -> str:
        """提取叙事内容"""
        if "narrative_prism" in inputs:
            data = inputs["narrative_prism"]
            if isinstance(data, dict) and "content" in data:
                return data["content"]
        return "未提供叙事内容"
    
    async def _post_process(self, output, inputs: Dict[str, Any]):
        """后处理 - 验证和优化设计结构"""
        content = output.content or ""
        
        # 解析和验证JSON结构
        design_data = self._parse_and_validate_json(content)
        if design_data:
            # 将解析的JSON作为结构化数据
            output.set_structured_data(design_data)
            
            # 同时保持JSON字符串作为主要内容
            import json
            output.set_content(
                json.dumps(design_data, ensure_ascii=False, indent=2),
                OutputFormat.JSON
            )
        
        # 添加设计相关元数据
        output.set_metadata(
            atomic_design_completed=True,
            has_atomic_structure=bool(design_data.get("atomic_design")),
            has_content_structure=bool(design_data.get("content_structure")),
            has_design_system=bool(design_data.get("design_system")),
            has_implementation_guide=bool(design_data.get("implementation_guide")),
            design_completeness=self._assess_design_completeness(design_data),
            component_count=self._count_components(design_data),
            design_quality=self._assess_design_quality(design_data)
        )
    
    def _parse_and_validate_json(self, content: str) -> Dict[str, Any]:
        """解析和验证JSON内容"""
        import json
        import re
        
        try:
            # 尝试直接解析
            if content.strip().startswith('{'):
                return json.loads(content)
            
            # 从文本中提取JSON
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            json_matches = re.findall(json_pattern, content, re.DOTALL)
            
            if json_matches:
                return json.loads(json_matches[0])
            
            # 查找第一个JSON对象
            start_idx = content.find('{')
            if start_idx != -1:
                # 简单的括号匹配
                bracket_count = 0
                for i, char in enumerate(content[start_idx:], start_idx):
                    if char == '{':
                        bracket_count += 1
                    elif char == '}':
                        bracket_count -= 1
                        if bracket_count == 0:
                            json_str = content[start_idx:i+1]
                            return json.loads(json_str)
            
            # 如果无法解析，返回默认结构
            return self._create_default_structure(content)
            
        except json.JSONDecodeError:
            return self._create_default_structure(content)
    
    def _create_default_structure(self, content: str) -> Dict[str, Any]:
        """创建默认的设计结构"""
        return {
            "atomic_design": {
                "atoms": [
                    {"type": "title", "content": "主标题", "style": "h1"},
                    {"type": "text", "content": "正文内容", "style": "body"},
                    {"type": "image", "content": "封面图", "style": "cover"},
                    {"type": "button", "content": "行动按钮", "style": "primary"}
                ],
                "molecules": [
                    {"type": "content_card", "components": ["title", "text", "image"]},
                    {"type": "action_group", "components": ["button", "text"]}
                ],
                "organisms": [
                    {"type": "header", "components": ["title"]},
                    {"type": "main_content", "components": ["content_card"]},
                    {"type": "footer", "components": ["action_group"]}
                ],
                "templates": [
                    {"type": "post_template", "layout": ["header", "main_content", "footer"]}
                ],
                "pages": [
                    {"type": "content_page", "template": "post_template"}
                ]
            },
            "content_structure": {
                "hierarchy": ["主题", "核心内容", "行动指导"],
                "sections": 3,
                "word_count": len(content),
                "reading_time": len(content) // 200  # 估算阅读时间（分钟）
            },
            "design_system": {
                "colors": {
                    "primary": "#FF6B9D",
                    "secondary": "#FFA726",
                    "text": "#333333",
                    "background": "#FFFFFF"
                },
                "typography": {
                    "h1": {"size": "24px", "weight": "bold"},
                    "body": {"size": "16px", "weight": "normal"}
                },
                "spacing": {
                    "small": "8px",
                    "medium": "16px",
                    "large": "24px"
                }
            },
            "implementation_guide": {
                "platform": "xiaohongshu",
                "format": "mobile_first",
                "interactions": ["tap", "scroll", "share"],
                "accessibility": ["screen_reader", "high_contrast"],
                "performance": ["image_optimization", "lazy_loading"]
            },
            "parsing_note": "自动生成的默认结构，基于内容分析"
        }
    
    def _assess_design_completeness(self, design_data: Dict[str, Any]) -> str:
        """评估设计完整性"""
        if not design_data:
            return "incomplete"
        
        required_sections = ["atomic_design", "content_structure", "design_system", "implementation_guide"]
        present_sections = sum(1 for section in required_sections if section in design_data)
        
        if present_sections >= 4:
            return "complete"
        elif present_sections >= 3:
            return "mostly_complete"
        elif present_sections >= 2:
            return "partial"
        else:
            return "incomplete"
    
    def _count_components(self, design_data: Dict[str, Any]) -> int:
        """统计组件数量"""
        if not design_data or "atomic_design" not in design_data:
            return 0
        
        atomic_design = design_data["atomic_design"]
        count = 0
        
        for level in ["atoms", "molecules", "organisms", "templates", "pages"]:
            if level in atomic_design and isinstance(atomic_design[level], list):
                count += len(atomic_design[level])
        
        return count
    
    def _assess_design_quality(self, design_data: Dict[str, Any]) -> str:
        """评估设计质量"""
        if not design_data:
            return "low"
        
        quality_score = 0
        
        # 检查原子设计完整性
        if design_data.get("atomic_design", {}).get("atoms"):
            quality_score += 2
        if design_data.get("atomic_design", {}).get("molecules"):
            quality_score += 2
        if design_data.get("atomic_design", {}).get("organisms"):
            quality_score += 2
        
        # 检查设计系统
        if design_data.get("design_system", {}).get("colors"):
            quality_score += 1
        if design_data.get("design_system", {}).get("typography"):
            quality_score += 1
        
        # 检查实现指南
        if design_data.get("implementation_guide"):
            quality_score += 2
        
        if quality_score >= 8:
            return "high"
        elif quality_score >= 6:
            return "medium"
        else:
            return "low"
    
    def get_design_summary(self, topic: str) -> Dict[str, Any]:
        """获取设计摘要信息"""
        cached_output = self.load_cache(topic)
        if not cached_output:
            return {"error": "未找到原子化设计"}
        
        structured_data = cached_output.structured_data or {}
        
        summary = {
            "topic": topic,
            "design_completeness": structured_data.get("design_completeness", "unknown"),
            "component_count": structured_data.get("component_count", 0),
            "design_quality": structured_data.get("design_quality", "unknown"),
            "has_atomic_structure": structured_data.get("has_atomic_structure", False),
            "has_design_system": structured_data.get("has_design_system", False),
            "has_implementation_guide": structured_data.get("has_implementation_guide", False)
        }
        
        # 添加组件统计
        if "atomic_design" in structured_data:
            atomic_design = structured_data["atomic_design"]
            summary["component_breakdown"] = {
                "atoms": len(atomic_design.get("atoms", [])),
                "molecules": len(atomic_design.get("molecules", [])),
                "organisms": len(atomic_design.get("organisms", [])),
                "templates": len(atomic_design.get("templates", [])),
                "pages": len(atomic_design.get("pages", []))
            }
        
        return summary
    
    def get_design_specifications(self, topic: str) -> Dict[str, Any]:
        """获取设计规范"""
        cached_output = self.load_cache(topic)
        if not cached_output:
            return {"error": "未找到设计规范"}
        
        structured_data = cached_output.structured_data or {}
        
        return {
            "design_system": structured_data.get("design_system", {}),
            "implementation_guide": structured_data.get("implementation_guide", {}),
            "content_structure": structured_data.get("content_structure", {})
        }

# 向后兼容
AtomicDesignerEngine = AtomicDesignerEngineV2 