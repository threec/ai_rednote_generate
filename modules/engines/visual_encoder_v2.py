"""
视觉编码器引擎 V2.0 - 重构版
基于新核心架构，提供视觉设计规范和HTML代码生成

目标：将原子化设计转化为具体的视觉实现代码，生成可运行的HTML页面
"""

from typing import Dict, Any
from modules.engines.base_engine_v2 import TechnicalEngine
from modules.core.output import ContentType, OutputFormat

class VisualEncoderEngineV2(TechnicalEngine):
    """视觉编码器引擎 V2.0"""
    
    def __init__(self, llm, **kwargs):
        super().__init__(llm, **kwargs)
        self.engine_name = "visual_encoder"
    
    def get_content_type(self) -> ContentType:
        return ContentType.TECHNICAL
    
    def get_expected_output_format(self) -> OutputFormat:
        return OutputFormat.HYBRID
    
    def _setup_processing_chain(self):
        """设置视觉编码处理链"""
        
        system_prompt = """你是一个专业的前端开发工程师和视觉设计师。

你的任务是将原子化设计规范转化为具体的HTML/CSS代码实现，创建美观且功能完整的网页。

**核心能力**：
1. HTML语义化结构编写
2. 现代CSS样式设计和布局
3. 响应式设计和移动端优化
4. 交互效果和动画实现
5. 性能优化和代码质量控制
6. 小红书平台视觉规范应用

**技术要求**：
- 使用语义化HTML5标签
- 采用现代CSS3特性
- 确保移动端优先的响应式设计
- 遵循Web标准和最佳实践
- 优化加载性能和用户体验
- 保持代码简洁和可维护性

**输出要求**：
- 生成完整可运行的HTML页面
- 包含内联CSS样式
- 确保代码结构清晰
- 适配小红书平台风格
- 支持各种屏幕尺寸

输出格式为混合模式：
1. HTML代码（完整页面）
2. 技术说明和使用指南
3. 性能优化建议
"""

        user_template = """
请基于以下原子化设计生成完整的HTML页面代码：

**主题**: {topic}

**叙事内容**: {narrative_content}

**原子化设计**: {atomic_design}

**编码要求**:
1. 生成语义化的HTML5页面结构
2. 使用内联CSS确保样式完整性
3. 实现移动端优先的响应式设计
4. 应用小红书平台的视觉风格
5. 确保代码简洁易读，性能优良

**视觉风格要求**:
- 色彩：温暖友好的配色方案
- 字体：清晰易读的中文字体
- 布局：简洁现代的卡片式设计
- 交互：微妙的悬停和点击效果
- 图片：预留合适的图片展示空间

**技术规范**:
- DOCTYPE html5
- 响应式meta标签
- 合理的语义化标签
- 现代CSS Grid/Flexbox布局
- 优化的字体和间距设计
- 适当的动画和过渡效果

请输出包含以下内容：
1. 完整的HTML页面代码
2. 代码结构说明
3. 使用和定制指南
4. 性能优化建议

确保生成的代码可以直接在浏览器中运行。
"""

        prompt_template = self._create_prompt_template(system_prompt, user_template)
        self.processing_chain = self._create_processing_chain(prompt_template)
    
    async def _process_content(self, inputs: Dict[str, Any]) -> str:
        """处理内容 - 生成HTML代码"""
        topic = inputs.get("topic", "")
        
        # 获取前序内容
        narrative_content = self._extract_content(inputs, "narrative_prism", "创意叙事内容")
        atomic_design = self._extract_content(inputs, "atomic_designer", "原子化设计规范")
        
        # 准备链输入
        chain_inputs = {
            "topic": topic,
            "narrative_content": narrative_content,
            "atomic_design": atomic_design
        }
        
        # 执行AI处理
        result = await self._invoke_chain_with_timeout(chain_inputs)
        
        return result
    
    def _extract_content(self, inputs: Dict[str, Any], key: str, default: str) -> str:
        """提取内容"""
        if key in inputs:
            data = inputs[key]
            if isinstance(data, dict) and "content" in data:
                content = data["content"]
                # 对于长内容进行截取
                return content[:1000] + "..." if len(content) > 1000 else content
        return default
    
    async def _post_process(self, output, inputs: Dict[str, Any]):
        """后处理 - 分析和优化HTML代码"""
        content = output.content or ""
        
        # 分析HTML代码质量
        code_analysis = self._analyze_html_code(content)
        
        # 提取HTML代码和说明文档
        html_code, documentation = self._extract_html_and_docs(content)
        
        # 设置结构化数据
        structured_data = {
            "html_code": html_code,
            "documentation": documentation,
            "code_analysis": code_analysis,
            "generated_at": self._get_timestamp()
        }
        output.set_structured_data(structured_data)
        
        # 添加编码相关元数据
        output.set_metadata(
            html_generated=True,
            code_quality=code_analysis.get("quality_score", "unknown"),
            has_html_structure=code_analysis.get("has_html_structure", False),
            has_css_styles=code_analysis.get("has_css_styles", False),
            is_responsive=code_analysis.get("is_responsive", False),
            is_semantic=code_analysis.get("is_semantic", False),
            performance_optimized=code_analysis.get("performance_optimized", False),
            lines_of_code=code_analysis.get("lines_of_code", 0)
        )
    
    def _analyze_html_code(self, content: str) -> Dict[str, Any]:
        """分析HTML代码质量"""
        analysis = {
            "lines_of_code": len(content.split('\n')),
            "has_html_structure": False,
            "has_css_styles": False,
            "is_responsive": False,
            "is_semantic": False,
            "performance_optimized": False
        }
        
        # 检查HTML结构
        if "<!DOCTYPE html>" in content and "<html" in content:
            analysis["has_html_structure"] = True
        
        # 检查CSS样式
        if "<style>" in content or "style=" in content:
            analysis["has_css_styles"] = True
        
        # 检查响应式设计
        responsive_indicators = ["viewport", "media", "@media", "responsive", "mobile"]
        if any(indicator in content for indicator in responsive_indicators):
            analysis["is_responsive"] = True
        
        # 检查语义化标签
        semantic_tags = ["header", "main", "section", "article", "nav", "footer", "aside"]
        semantic_count = sum(1 for tag in semantic_tags if f"<{tag}" in content)
        analysis["is_semantic"] = semantic_count >= 3
        
        # 检查性能优化
        performance_indicators = ["async", "defer", "preload", "lazy", "optimized"]
        if any(indicator in content for indicator in performance_indicators):
            analysis["performance_optimized"] = True
        
        # 计算质量分数
        quality_factors = [
            analysis["has_html_structure"],
            analysis["has_css_styles"], 
            analysis["is_responsive"],
            analysis["is_semantic"],
            analysis["performance_optimized"]
        ]
        quality_score = sum(quality_factors)
        
        if quality_score >= 4:
            analysis["quality_score"] = "high"
        elif quality_score >= 3:
            analysis["quality_score"] = "medium"
        else:
            analysis["quality_score"] = "low"
        
        return analysis
    
    def _extract_html_and_docs(self, content: str) -> tuple:
        """提取HTML代码和文档说明"""
        import re
        
        # 查找HTML代码块
        html_pattern = r'```html\s*(.*?)\s*```'
        html_matches = re.findall(html_pattern, content, re.DOTALL)
        
        if html_matches:
            html_code = html_matches[0]
        else:
            # 查找完整HTML结构
            if "<!DOCTYPE html>" in content:
                start_idx = content.find("<!DOCTYPE html>")
                end_idx = content.rfind("</html>") + 7
                if start_idx != -1 and end_idx > start_idx:
                    html_code = content[start_idx:end_idx]
                else:
                    html_code = content
            else:
                html_code = content
        
        # 提取文档说明（HTML代码之外的部分）
        documentation = content.replace(html_code, "").strip()
        if not documentation:
            documentation = "自动生成的HTML页面代码"
        
        return html_code, documentation
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_html_code(self, topic: str) -> str:
        """获取生成的HTML代码"""
        cached_output = self.load_cache(topic)
        if not cached_output:
            return ""
        
        structured_data = cached_output.structured_data or {}
        return structured_data.get("html_code", "")
    
    def get_code_summary(self, topic: str) -> Dict[str, Any]:
        """获取代码摘要信息"""
        cached_output = self.load_cache(topic)
        if not cached_output:
            return {"error": "未找到HTML代码"}
        
        structured_data = cached_output.structured_data or {}
        code_analysis = structured_data.get("code_analysis", {})
        
        summary = {
            "topic": topic,
            "quality_score": code_analysis.get("quality_score", "unknown"),
            "lines_of_code": code_analysis.get("lines_of_code", 0),
            "has_html_structure": code_analysis.get("has_html_structure", False),
            "has_css_styles": code_analysis.get("has_css_styles", False),
            "is_responsive": code_analysis.get("is_responsive", False),
            "is_semantic": code_analysis.get("is_semantic", False),
            "performance_optimized": code_analysis.get("performance_optimized", False),
            "generated_at": structured_data.get("generated_at", ""),
            "documentation_available": bool(structured_data.get("documentation"))
        }
        
        return summary
    
    def save_html_file(self, topic: str, output_dir: str = "output") -> Dict[str, Any]:
        """保存HTML文件到磁盘"""
        from pathlib import Path
        
        html_code = self.get_html_code(topic)
        if not html_code:
            return {"success": False, "error": "未找到HTML代码"}
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{topic}_{timestamp}.html"
        file_path = output_path / filename
        
        try:
            # 保存HTML文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_code)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "file_size": len(html_code),
                "lines_count": len(html_code.split('\n'))
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"保存文件失败: {str(e)}"
            }

# 向后兼容
VisualEncoderEngine = VisualEncoderEngineV2 