"""
真理探机引擎 V2.0 - 重构版
基于新核心架构，提供深度事实核查和内容可信度分析

目标：确保内容的准确性、可信度和权威性，防止虚假信息传播
"""

from typing import Dict, Any
from modules.engines.base_engine_v2 import AnalysisEngine
from modules.core.output import ContentType, OutputFormat

class TruthDetectorEngineV2(AnalysisEngine):
    """真理探机引擎 V2.0"""
    
    def __init__(self, llm, **kwargs):
        super().__init__(llm, **kwargs)
        self.engine_name = "truth_detector"
    
    def _setup_processing_chain(self):
        """设置事实核查处理链"""
        
        system_prompt = """你是一个专业的事实核查专家和内容可信度分析师。

你的任务是对给定主题进行深度的事实核查和可信度分析，确保内容创作基于准确、可靠的信息基础。

**核心能力**：
1. 医学健康信息的专业核查
2. 科学数据和研究结果验证
3. 权威信息源识别和评估
4. 潜在风险和误导信息识别
5. 证据等级评估和可信度分析

**分析维度**：
- 事实准确性验证
- 信息源权威性评估
- 科学证据支持度
- 潜在风险识别
- 内容安全性分析
- 伦理合规性检查

**输出要求**：
- 采用分析报告格式
- 包含明确的可信度评级
- 提供权威信息源
- 标识潜在风险点
- 给出具体的修正建议

输出格式：
# 内容真实性分析报告

## 1. 综合可信度评估
- **可信度等级**: [A/B/C/D级]
- **安全性等级**: [高/中/低风险]
- **权威性评分**: [1-10分]

## 2. 事实核查结果
### 2.1 核心事实验证
### 2.2 数据准确性分析
### 2.3 权威信息源对比

## 3. 风险识别与评估
### 3.1 医学健康风险
### 3.2 误导信息风险
### 3.3 法律合规风险

## 4. 权威信息源
### 4.1 官方机构观点
### 4.2 专业研究证据
### 4.3 权威专家意见

## 5. 改进建议
### 5.1 内容修正建议
### 5.2 风险缓解措施
### 5.3 可信度提升方案
"""

        user_template = """
请对以下主题进行全面的事实核查和可信度分析：

**主题**: {topic}

**现有策略背景**: {strategy_info}

**分析要求**:
1. 针对该主题进行深度事实核查，特别关注医学健康相关内容
2. 识别和评估潜在的误导信息或安全风险
3. 验证相关数据、研究和权威信息源
4. 评估内容的科学性、准确性和安全性
5. 提供具体的修正建议和风险缓解措施

**特别关注领域**:
- 婴幼儿健康与安全
- 医学建议和健康指导
- 科学数据和研究引用
- 安全操作指导
- 潜在过敏或危险因素

请输出完整的事实核查分析报告，确保内容的准确性和安全性。
"""

        prompt_template = self._create_prompt_template(system_prompt, user_template)
        self.processing_chain = self._create_processing_chain(prompt_template)
    
    async def _process_content(self, inputs: Dict[str, Any]) -> str:
        """处理内容 - 生成事实核查分析"""
        topic = inputs.get("topic", "")
        
        # 获取策略信息
        strategy_info = "未提供策略信息"
        if "strategy_compass" in inputs:
            strategy_data = inputs["strategy_compass"]
            if isinstance(strategy_data, dict) and "content" in strategy_data:
                strategy_info = strategy_data["content"][:500] + "..."
        
        # 准备链输入
        chain_inputs = {
            "topic": topic,
            "strategy_info": strategy_info
        }
        
        # 执行AI处理
        result = await self._invoke_chain_with_timeout(chain_inputs)
        
        return result
    
    async def _post_process(self, output, inputs: Dict[str, Any]):
        """后处理 - 提取可信度评估数据"""
        content = output.content or ""
        
        # 提取结构化的事实核查数据
        fact_check_data = self._extract_fact_check_data(content)
        if fact_check_data:
            output.set_structured_data(fact_check_data)
        
        # 添加事实核查相关元数据
        output.set_metadata(
            fact_check_completed=True,
            credibility_assessed=bool(fact_check_data.get("credibility_level")),
            safety_evaluated=bool(fact_check_data.get("safety_level")),
            authority_checked=bool(fact_check_data.get("authority_score")),
            has_risks_identified=self._has_section(content, "风险识别"),
            has_authoritative_sources=self._has_section(content, "权威信息源"),
            content_safety_level=self._extract_safety_level(content),
            credibility_grade=self._extract_credibility_grade(content)
        )
    
    def _extract_fact_check_data(self, content: str) -> Dict[str, Any]:
        """从分析报告中提取结构化的事实核查数据"""
        from datetime import datetime
        import re
        
        fact_check_data = {
            "checked_at": datetime.now().isoformat(),
            "check_method": "ai_analysis"
        }
        
        # 提取可信度等级
        credibility_pattern = r'可信度等级.*?([A-D]级)'
        credibility_match = re.search(credibility_pattern, content)
        if credibility_match:
            fact_check_data["credibility_level"] = credibility_match.group(1)
        
        # 提取安全性等级
        safety_pattern = r'安全性等级.*?(高|中|低)风险'
        safety_match = re.search(safety_pattern, content)
        if safety_match:
            fact_check_data["safety_level"] = safety_match.group(1) + "风险"
        
        # 提取权威性评分
        authority_pattern = r'权威性评分.*?(\d+)分'
        authority_match = re.search(authority_pattern, content)
        if authority_match:
            fact_check_data["authority_score"] = int(authority_match.group(1))
        
        # 检查关键章节
        if "事实核查结果" in content:
            fact_check_data["has_fact_verification"] = True
        
        if "风险识别" in content:
            fact_check_data["has_risk_assessment"] = True
        
        if "权威信息源" in content:
            fact_check_data["has_authority_sources"] = True
        
        if "改进建议" in content:
            fact_check_data["has_improvement_suggestions"] = True
        
        # 提取风险关键词
        risk_keywords = []
        risk_indicators = ["风险", "危险", "注意", "禁忌", "避免", "警告"]
        for line in content.split('\n'):
            if any(indicator in line for indicator in risk_indicators):
                risk_keywords.append(line.strip())
        
        if risk_keywords:
            fact_check_data["identified_risks"] = risk_keywords[:5]  # 限制数量
        
        # 提取权威信息源
        authority_sources = []
        for line in content.split('\n'):
            if any(keyword in line for keyword in ["WHO", "CDC", "卫生部", "医学会", "研究", "权威"]):
                authority_sources.append(line.strip())
        
        if authority_sources:
            fact_check_data["authority_sources"] = authority_sources[:3]  # 限制数量
        
        return fact_check_data
    
    def _has_section(self, content: str, section_keyword: str) -> bool:
        """检查内容是否包含特定章节"""
        return section_keyword in content
    
    def _extract_safety_level(self, content: str) -> str:
        """提取安全等级"""
        if "高风险" in content:
            return "high_risk"
        elif "中风险" in content:
            return "medium_risk"
        elif "低风险" in content:
            return "low_risk"
        else:
            return "unknown"
    
    def _extract_credibility_grade(self, content: str) -> str:
        """提取可信度等级"""
        if "A级" in content:
            return "A"
        elif "B级" in content:
            return "B"
        elif "C级" in content:
            return "C"
        elif "D级" in content:
            return "D"
        else:
            return "unknown"
    
    def get_fact_check_summary(self, topic: str) -> Dict[str, Any]:
        """获取事实核查摘要信息"""
        cached_output = self.load_cache(topic)
        if not cached_output:
            return {"error": "未找到事实核查报告"}
        
        structured_data = cached_output.structured_data or {}
        content = cached_output.content
        
        summary = {
            "topic": topic,
            "credibility_level": structured_data.get("credibility_level", "unknown"),
            "safety_level": structured_data.get("safety_level", "unknown"),
            "authority_score": structured_data.get("authority_score", 0),
            "has_fact_verification": structured_data.get("has_fact_verification", False),
            "has_risk_assessment": structured_data.get("has_risk_assessment", False),
            "has_authority_sources": structured_data.get("has_authority_sources", False),
            "identified_risks_count": len(structured_data.get("identified_risks", [])),
            "authority_sources_count": len(structured_data.get("authority_sources", [])),
            "content_preview": content[:300] + "..." if len(content) > 300 else content
        }
        
        # 添加风险警告
        if summary["safety_level"] in ["高风险", "中风险"]:
            summary["safety_warning"] = f"⚠️ 检测到{summary['safety_level']}，需要仔细审查内容"
        
        return summary
    
    def is_content_safe(self, topic: str) -> bool:
        """检查内容是否安全"""
        summary = self.get_fact_check_summary(topic)
        if "error" in summary:
            return False
        
        # 基于可信度和安全性判断
        credibility_ok = summary["credibility_level"] in ["A", "B"]
        safety_ok = summary["safety_level"] != "高风险"
        authority_ok = summary["authority_score"] >= 6
        
        return credibility_ok and safety_ok and authority_ok

# 向后兼容
TruthDetectorEngine = TruthDetectorEngineV2 