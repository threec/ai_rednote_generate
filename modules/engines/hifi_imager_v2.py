"""
高保真成像仪引擎 V2.0 - 重构版
基于新核心架构，提供HTML页面截图和图像生成功能

目标：将HTML代码渲染为高质量图片，生成最终的可发布内容
"""

from typing import Dict, Any
from modules.engines.base_engine_v2 import TechnicalEngine
from modules.core.output import ContentType, OutputFormat

class HiFiImagerEngineV2(TechnicalEngine):
    """高保真成像仪引擎 V2.0"""
    
    def __init__(self, llm, **kwargs):
        super().__init__(llm, **kwargs)
        self.engine_name = "hifi_imager"
        self.screenshot_config = {
            "width": 750,  # 小红书推荐宽度
            "height": 1334,  # 根据内容自适应
            "device_scale_factor": 2,  # 高清显示
            "format": "png",
            "quality": 95,
            "full_page": True
        }
    
    def get_content_type(self) -> ContentType:
        return ContentType.TECHNICAL
    
    def get_expected_output_format(self) -> OutputFormat:
        return OutputFormat.HYBRID
    
    def _setup_processing_chain(self):
        """设置成像处理链"""
        
        system_prompt = """你是一个专业的图像生成和页面渲染专家。

你的任务是分析HTML代码的结构和内容，生成详细的截图配置和图像处理指导。

**核心能力**：
1. HTML页面结构分析和渲染参数优化
2. 图像质量控制和输出格式选择
3. 响应式设计适配和多尺寸生成
4. 性能优化和渲染效率提升
5. 图像后处理和质量增强
6. 平台适配和格式转换

**技术要求**：
- 分析HTML内容和结构特点
- 确定最佳的截图参数配置
- 提供详细的渲染指导
- 考虑不同设备和平台需求
- 确保图像质量和文件大小平衡

**输出要求**：
- 生成完整的截图配置方案
- 提供渲染过程指导
- 包含质量控制建议
- 确保输出的专业性和可用性

你需要基于HTML代码分析，输出详细的截图和图像生成指导。
"""

        user_template = """
请分析以下HTML代码，生成详细的截图配置和图像处理方案：

**主题**: {topic}

**HTML代码**: {html_code}

**生成要求**:
1. 分析HTML页面的内容结构和布局特点
2. 确定最佳的截图参数（尺寸、质量、格式等）
3. 提供分页截图的策略（如果内容过长）
4. 生成图像后处理的建议
5. 确保适配小红书平台的图片规范

**技术规范**:
- 推荐宽度：750px（小红书标准）
- 高度：根据内容自适应，单张图片不超过4000px
- 格式：PNG（保证质量）或JPEG（压缩大小）
- 设备像素比：2x（高清显示）
- 内容分页：超长内容自动分页

**特别关注**:
- 文字清晰度和可读性
- 图片和视觉元素的完整性
- 页面加载完成度检测
- 响应式布局的正确渲染
- 交互元素的最佳状态展示

请输出：
1. 截图配置参数
2. 渲染过程指导
3. 分页策略（如需要）
4. 质量控制建议
5. 文件命名和组织方案
"""

        prompt_template = self._create_prompt_template(system_prompt, user_template)
        self.processing_chain = self._create_processing_chain(prompt_template)
    
    async def _process_content(self, inputs: Dict[str, Any]) -> str:
        """处理内容 - 生成截图配置和指导"""
        topic = inputs.get("topic", "")
        
        # 获取HTML代码
        html_code = self._extract_html_code(inputs)
        
        # 准备链输入
        chain_inputs = {
            "topic": topic,
            "html_code": html_code
        }
        
        # 执行AI处理
        result = await self._invoke_chain_with_timeout(chain_inputs)
        
        return result
    
    def _extract_html_code(self, inputs: Dict[str, Any]) -> str:
        """提取HTML代码"""
        if "visual_encoder" in inputs:
            data = inputs["visual_encoder"]
            if isinstance(data, dict):
                # 尝试从结构化数据中获取
                if "structured_data" in data and data["structured_data"]:
                    html_code = data["structured_data"].get("html_code", "")
                    if html_code:
                        return html_code
                
                # 从内容中获取
                if "content" in data:
                    return data["content"][:2000] + "..." if len(data["content"]) > 2000 else data["content"]
        
        return "未提供HTML代码"
    
    async def _post_process(self, output, inputs: Dict[str, Any]):
        """后处理 - 生成截图配置数据"""
        content = output.content or ""
        
        # 分析和提取截图配置
        screenshot_config = self._extract_screenshot_config(content)
        rendering_guide = self._extract_rendering_guide(content)
        
        # 设置结构化数据
        structured_data = {
            "screenshot_config": screenshot_config,
            "rendering_guide": rendering_guide,
            "image_specifications": self._generate_image_specs(),
            "generated_at": self._get_timestamp()
        }
        output.set_structured_data(structured_data)
        
        # 添加成像相关元数据
        output.set_metadata(
            imaging_config_generated=True,
            has_screenshot_config=bool(screenshot_config),
            has_rendering_guide=bool(rendering_guide),
            supports_multi_page=screenshot_config.get("multi_page", False),
            image_quality=screenshot_config.get("quality", "high"),
            output_format=screenshot_config.get("format", "png")
        )
    
    def _extract_screenshot_config(self, content: str) -> Dict[str, Any]:
        """提取截图配置"""
        import re
        
        config = self.screenshot_config.copy()
        
        # 提取宽度设置
        width_match = re.search(r'宽度.*?(\d+)', content)
        if width_match:
            config["width"] = int(width_match.group(1))
        
        # 提取高度设置
        height_match = re.search(r'高度.*?(\d+)', content)
        if height_match:
            config["height"] = int(height_match.group(1))
        
        # 检查是否需要分页
        if "分页" in content or "多页" in content:
            config["multi_page"] = True
            config["max_height"] = 4000  # 单页最大高度
        
        # 提取质量设置
        if "高质量" in content or "95" in content:
            config["quality"] = 95
        elif "中等质量" in content or "85" in content:
            config["quality"] = 85
        elif "压缩" in content or "75" in content:
            config["quality"] = 75
        
        # 提取格式设置
        if "JPEG" in content or "jpg" in content:
            config["format"] = "jpeg"
        elif "PNG" in content or "png" in content:
            config["format"] = "png"
        
        # 设备像素比
        if "高清" in content or "2x" in content:
            config["device_scale_factor"] = 2
        elif "超高清" in content or "3x" in content:
            config["device_scale_factor"] = 3
        
        return config
    
    def _extract_rendering_guide(self, content: str) -> Dict[str, Any]:
        """提取渲染指导"""
        guide = {
            "wait_for_load": True,
            "wait_for_images": True,
            "wait_for_fonts": True,
            "scroll_behavior": "smooth",
            "capture_mode": "full_page"
        }
        
        # 分析内容中的指导信息
        if "等待加载" in content:
            guide["wait_for_load"] = True
        if "图片加载" in content:
            guide["wait_for_images"] = True
        if "字体加载" in content:
            guide["wait_for_fonts"] = True
        
        # 滚动行为
        if "无滚动" in content:
            guide["scroll_behavior"] = "none"
        elif "快速滚动" in content:
            guide["scroll_behavior"] = "fast"
        
        # 捕获模式
        if "可视区域" in content:
            guide["capture_mode"] = "viewport"
        elif "全页面" in content:
            guide["capture_mode"] = "full_page"
        
        return guide
    
    def _generate_image_specs(self) -> Dict[str, Any]:
        """生成图像规格说明"""
        return {
            "recommended_formats": ["png", "jpeg"],
            "quality_levels": {
                "high": {"quality": 95, "format": "png"},
                "medium": {"quality": 85, "format": "jpeg"},
                "compressed": {"quality": 75, "format": "jpeg"}
            },
            "size_limits": {
                "max_width": 1125,  # 小红书最大宽度
                "max_height": 4000,  # 单图最大高度
                "min_width": 375,   # 最小宽度
                "min_height": 200   # 最小高度
            },
            "xiaohongshu_specs": {
                "recommended_width": 750,
                "recommended_ratio": "3:4",
                "max_file_size": "20MB",
                "supported_formats": ["jpg", "png", "gif"]
            }
        }
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def generate_screenshots(self, topic: str, html_code: str = None) -> Dict[str, Any]:
        """生成截图（主要功能方法）"""
        # 如果没有提供HTML代码，尝试从缓存获取
        if not html_code:
            cached_output = self.load_cache(topic)
            if cached_output and cached_output.structured_data:
                html_code = cached_output.structured_data.get("html_code", "")
        
        if not html_code:
            return {"success": False, "error": "未找到HTML代码"}
        
        try:
            # 这里应该调用实际的截图功能
            # 由于这是V2重构版，我们先返回配置信息
            cached_output = self.load_cache(topic)
            if cached_output and cached_output.structured_data:
                config = cached_output.structured_data.get("screenshot_config", {})
                guide = cached_output.structured_data.get("rendering_guide", {})
                
                return {
                    "success": True,
                    "config_ready": True,
                    "screenshot_config": config,
                    "rendering_guide": guide,
                    "note": "截图配置已生成，需要集成实际的截图引擎"
                }
            
            return {"success": False, "error": "未找到截图配置"}
            
        except Exception as e:
            return {"success": False, "error": f"生成截图失败: {str(e)}"}
    
    def get_imaging_summary(self, topic: str) -> Dict[str, Any]:
        """获取成像摘要信息"""
        cached_output = self.load_cache(topic)
        if not cached_output:
            return {"error": "未找到成像配置"}
        
        structured_data = cached_output.structured_data or {}
        config = structured_data.get("screenshot_config", {})
        
        summary = {
            "topic": topic,
            "config_ready": bool(config),
            "image_width": config.get("width", 750),
            "image_height": config.get("height", "auto"),
            "image_format": config.get("format", "png"),
            "image_quality": config.get("quality", 95),
            "multi_page_support": config.get("multi_page", False),
            "device_scale_factor": config.get("device_scale_factor", 2),
            "generated_at": structured_data.get("generated_at", "")
        }
        
        return summary
    
    def update_screenshot_config(self, **kwargs):
        """更新截图配置"""
        self.screenshot_config.update(kwargs)
        self.logger.info(f"截图配置已更新: {kwargs}")

# 向后兼容
HiFiImagerEngine = HiFiImagerEngineV2 