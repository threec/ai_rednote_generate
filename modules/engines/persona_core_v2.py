"""
人格核心引擎 V2.0 - 完全重构版
基于新的核心架构，提供更好的错误处理、配置管理和输出格式

目标：为内容注入统一的灵魂，定义人格(Persona)、声音(Voice)和基调(Tone)
"""

from typing import Dict, Any
from modules.engines.base_engine_v2 import AnalysisEngine
from modules.core.output import ContentType, OutputFormat

class PersonaCoreEngineV2(AnalysisEngine):
    """人格核心引擎 V2.0"""
    
    def __init__(self, llm, **kwargs):
        super().__init__(llm, **kwargs)
        self.engine_name = "persona_core"
    
    def _setup_processing_chain(self):
        """设置人格分析处理链"""
        
        system_prompt = """你是一个专业的内容人格分析师和品牌策略专家。

你的任务是为给定主题构建一个专业、鲜明、统一的内容人格档案。

**核心能力**：
1. 深度分析主题特征和受众需求
2. 设计独特而吸引人的内容人格
3. 确保人格设定的一致性和可操作性
4. 提供具体的表达指导和风格规范

**输出要求**：
- 以专业的分析报告形式输出
- 结构清晰，逻辑严谨
- 包含具体的人格设定和使用指导
- 确保后续引擎能够基于此人格创作内容

**报告结构**：
# 内容人格档案分析报告

## 1. 主题与受众分析
- 主题领域特征
- 目标受众画像
- 内容消费场景

## 2. 人格核心设定
### 2.1 身份定位
- 署名/昵称建议
- 职业身份标签
- 专业背景描述
- 独特标识语

### 2.2 性格特征
- 核心性格关键词
- 价值观导向
- 沟通风格特点

### 2.3 声音与基调
- 语言风格定义
- 情感基调设定
- 表达习惯特点

## 3. 内容策略指导
- 专业角度选择
- 论证方式偏好
- 与读者互动模式

## 4. 风格规范指南
### 4.1 应该做的
- 具体的表达建议
- 推荐的用词习惯
- 句式风格指导

### 4.2 应该避免的
- 不适合的表达方式
- 需要规避的用词
- 风格禁忌事项

## 5. 一致性维护
- 核心理念关键词
- 内容主题方向
- 品牌差异化要点

请确保人格设定专业、有辨识度，能够支撑长期的内容创作需求。
"""

        user_template = """
请为以下主题构建完整的内容人格档案：

**主题**: {topic}

**分析要求**:
1. 深入分析该主题的内容创作特点和受众需求
2. 设计最适合的人格设定和声音调性
3. 建立清晰的风格指南和一致性标准
4. 确保人格设定能够支撑长期内容创作
5. 提供具体可操作的执行指导

请输出完整的人格档案分析报告。
"""

        prompt_template = self._create_prompt_template(system_prompt, user_template)
        self.processing_chain = self._create_processing_chain(prompt_template)
    
    async def _process_content(self, inputs: Dict[str, Any]) -> str:
        """处理内容 - 生成人格档案分析"""
        topic = inputs.get("topic", "")
        
        # 准备链输入
        chain_inputs = {"topic": topic}
        
        # 执行AI处理
        result = await self._invoke_chain_with_timeout(chain_inputs)
        
        return result
    
    async def _post_process(self, output, inputs: Dict[str, Any]):
        """后处理 - 提取关键人格信息到结构化数据"""
        content = output.content
        
        # 从报告中提取关键信息到结构化数据
        structured_data = self._extract_persona_data(content)
        output.set_structured_data(structured_data)
        
        # 添加额外元数据
        output.set_metadata(
            persona_extracted=True,
            key_elements=list(structured_data.keys()),
            content_length=len(content),
            structure_quality="high" if len(structured_data) > 5 else "medium"
        )
    
    def _extract_persona_data(self, content: str) -> Dict[str, Any]:
        """从分析报告中提取结构化的人格数据"""
        
        # 这里可以使用更复杂的NLP技术来提取信息
        # 目前使用简单的文本分析
        
        structured_data = {
            "extracted_at": self.created_at.isoformat(),
            "extraction_method": "text_analysis"
        }
        
        # 提取身份信息
        if "身份定位" in content or "署名" in content:
            structured_data["identity_section_found"] = True
        
        # 提取性格特征
        if "性格特征" in content or "关键词" in content:
            structured_data["personality_section_found"] = True
        
        # 提取声音基调
        if "声音与基调" in content or "语言风格" in content:
            structured_data["voice_tone_section_found"] = True
        
        # 提取风格指南
        if "风格规范" in content or "应该做的" in content:
            structured_data["style_guide_found"] = True
        
        # 提取关键词（简单实现）
        keywords = []
        for line in content.split('\n'):
            if '关键词' in line or '特征' in line:
                # 简单提取，实际可以用更复杂的方法
                keywords.append(line.strip())
        
        if keywords:
            structured_data["extracted_keywords"] = keywords[:5]  # 限制数量
        
        return structured_data
    
    def get_persona_summary(self, topic: str) -> Dict[str, str]:
        """获取人格摘要信息"""
        cached_output = self.load_cache(topic)
        if not cached_output:
            return {"error": "未找到人格档案"}
        
        content = cached_output.content
        structured_data = cached_output.structured_data
        
        # 从内容中提取摘要信息
        summary = {
            "topic": topic,
            "has_identity": structured_data.get("identity_section_found", False),
            "has_personality": structured_data.get("personality_section_found", False),
            "has_voice_tone": structured_data.get("voice_tone_section_found", False),
            "has_style_guide": structured_data.get("style_guide_found", False),
            "content_preview": content[:200] + "..." if len(content) > 200 else content
        }
        
        return summary

# 为了保持向后兼容，创建一个别名
PersonaCoreEngine = PersonaCoreEngineV2 