"""
引擎⑥: 原子设计师引擎 (Atomic Designer Engine)
RedCube AI 工作流系统

目标：为每一篇笔记生成细化到"逐页"的、包含文案和视觉构思的"施工图"

核心功能：
- 连接"文字内容"和"视觉呈现"的关键桥梁，极大降低最终视觉生成的不确定性
- 为什么重要：连接"文字内容"和"视觉呈现"的关键桥梁，极大降低最终视觉生成的不确定性

最终输出物：
- 一份完整的图文笔记发布方案
1. 小红书标题（3个备选）
2. 小红书正文（带#Tag）
3. 逐页信息图设计大纲（核心）

实现方式：
- 基于LangChain构建原子设计链
- 精确的页面级设计规范
- 文案与视觉的完美结合
- 输出可直接执行的施工图
"""

import json
import os
import sys
from typing import Dict, Any, Optional, List
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 修复导入路径问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.langchain_workflow import BaseWorkflowEngine
from modules.utils import get_logger

class AtomicDesignerEngine(BaseWorkflowEngine):
    """原子设计师引擎 - 页面布局设计"""
    
    def __init__(self, llm):
        super().__init__("atomic_designer", llm)
        self._initialize_design_chain()
    
    def _initialize_design_chain(self):
        """初始化原子设计链"""
        
        system_prompt = """
你是RedCube AI的"原子设计师大师"，专门负责将叙事架构转化为精确的页面设计施工图。

## 核心使命：精确的页面级设计规范

为每一篇笔记生成细化到"逐页"的、包含文案和视觉构思的"施工图"，确保最终视觉效果的精确控制。

## 原子设计原理

### 【设计大纲的技术核心】
"设计大纲"的技术核心：精确、可执行的技术性指令

你输出的不是模糊描述，而是AI可以100%理解并执行的"代码"级别的设计指令：

#### 信息图: 3/9
- **页面类型**: 核心要点对比
- **页面标题**: 两种技术路线的优劣
- **核心内容与视觉构思**:
  - **布局**: 上下对比结构
  - **上半部分**:
    - **构思**: 淡蓝背景卡片(`bg-blue-100`)
    - **标题**: "路线A" + 图标 "⚙️"
  - **下半部分**:
    - **构思**: 淡绿背景卡片(`bg-green-100`)
    - **标题**: "路线B" + 图标 "🚀"

这不是模糊描述，而是AI可以100%理解并执行的"代码"。

### 【页面设计规范】
1. **技术指向性**
   - 具体的CSS类名和颜色代码
   - 明确的布局结构和元素位置
   - 精确的图标和视觉元素选择

2. **完整性保证**
   - 每页都有完整的设计方案
   - 文案与视觉的精确匹配
   - 从标题到细节的全面覆盖

3. **一致性维护**
   - 整体风格的统一协调
   - 品牌色彩的一致应用
   - 设计语言的连贯表达

### 【输出规范】
必须返回严格的JSON格式：

```json
{{
  "publication_package": {{
    "xiaohongshu_titles": [
      "主标题选项1（高点击率导向）",
      "主标题选项2（价值导向）",
      "主标题选项3（话题导向）"
    ],
    "xiaohongshu_content": {{
      "main_text": "小红书正文内容",
      "hashtags": ["#标签1", "#标签2", "#标签3"],
      "call_to_action": "行动引导文案"
    }},
    "content_metadata": {{
      "target_audience": "目标受众",
      "content_category": "内容分类",
      "publishing_timing": "发布时机建议"
    }}
  }},
  "page_design_specs": [
    {{
      "page_number": 1,
      "page_type": "封面页/内容页/对比页/结尾页",
      "page_title": "具体页面标题",
      "layout_structure": {{
        "layout_type": "布局类型（单栏/双栏/上下分割/左右分割）",
        "main_sections": [
          {{
            "section_name": "区域名称",
            "section_purpose": "区域功能",
            "content_elements": ["元素1", "元素2"],
            "visual_treatment": "视觉处理方式"
          }}
        ]
      }},
      "content_specification": {{
        "headline": "页面主标题",
        "subheadline": "副标题（如有）",
        "body_content": [
          {{
            "content_type": "文本/列表/引用/数据",
            "content_text": "具体文字内容",
            "visual_emphasis": "视觉强调方式",
            "formatting": "格式化要求"
          }}
        ],
        "supporting_elements": ["支撑元素1", "支撑元素2"]
      }},
      "visual_design": {{
        "color_scheme": {{
          "primary_color": "主色调（CSS代码）",
          "secondary_color": "辅助色（CSS代码）",
          "background_color": "背景色（CSS代码）",
          "text_color": "文字色（CSS代码）"
        }},
        "typography": {{
          "title_font": "标题字体设置",
          "body_font": "正文字体设置",
          "emphasis_treatment": "强调文字处理"
        }},
        "visual_elements": [
          {{
            "element_type": "图标/插图/图表/装饰",
            "element_description": "元素具体描述",
            "placement": "放置位置",
            "size_specification": "尺寸规格",
            "style_treatment": "样式处理"
          }}
        ]
      }},
      "technical_implementation": {{
        "css_classes": ["css-class-1", "css-class-2"],
        "layout_code": "布局代码指导",
        "responsive_notes": "响应式设计说明",
        "accessibility_considerations": "无障碍访问考虑"
      }}
    }}
  ],
  "design_system": {{
    "brand_guidelines": {{
      "color_palette": ["#颜色1", "#颜色2", "#颜色3"],
      "typography_scale": "字体层级系统",
      "spacing_system": "间距系统",
      "component_library": ["组件1", "组件2"]
    }},
    "visual_consistency": {{
      "design_principles": ["原则1", "原则2"],
      "style_guidelines": "风格指导原则",
      "quality_standards": "质量标准"
    }}
  }},
  "production_notes": {{
    "design_priorities": ["优先级1", "优先级2"],
    "implementation_sequence": "实施顺序",
    "quality_checkpoints": ["检查点1", "检查点2"],
    "revision_guidelines": "修改指导原则"
  }}
}}
```

### 【质量标准】
- **精确性**：每个设计指令都具体明确，可直接执行
- **完整性**：覆盖从标题到细节的所有设计要素
- **一致性**：整体风格协调统一
- **可执行性**：技术实现路径清晰明确

现在请根据叙事架构，设计精确的页面施工图。
"""

        user_template = """
请为以下内容设计精确的页面施工图：

**主题**: {topic}

**叙事架构**: {narrative_summary}

**设计要求**:
1. 为每一页生成精确的设计施工图
2. 确保文案与视觉的完美匹配
3. 提供可直接执行的技术指令
4. 保持整体设计的一致性和专业性
5. 输出完整的小红书发布方案

请严格按照JSON格式输出完整的原子设计规范。
"""

        self.design_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_template)
        ])
        
        self.design_chain = (
            self.design_prompt
            | self.llm
            | StrOutputParser()
        )
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行原子设计"""
        topic = inputs.get("topic", "")
        narrative = inputs.get("narrative", {})
        insights = inputs.get("insights", {})
        force_regenerate = inputs.get("force_regenerate", False)
        
        self.logger.info(f"⚛️ 原子设计师引擎启动 - 主题: {topic}")
        
        # 检查缓存
        if not force_regenerate:
            cached_result = self.load_cache(topic, "atomic_designer.json")
            if cached_result:
                self.logger.info("✓ 使用缓存的原子设计")
                return cached_result
        
        try:
            # 提取叙事摘要
            narrative_summary = self._extract_narrative_summary(narrative)
            
            # 执行原子设计链
            self.logger.info("执行原子设计...")
            result_text = await self.design_chain.ainvoke({
                "topic": topic,
                "narrative_summary": narrative_summary
            })
            
            # 解析JSON结果
            try:
                cleaned_text = result_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                design_result = json.loads(cleaned_text)
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {e}")
                design_result = self._get_fallback_design(topic, narrative)
            
            # 添加引擎元数据
            final_result = {
                "engine": "atomic_designer",
                "version": "1.0.0",
                "topic": topic,
                "design_data": design_result,
                "narrative_reference": narrative_summary,
                "execution_status": "success"
            }
            
            # 保存缓存
            self.save_cache(topic, final_result, "atomic_designer.json")
            
            self.logger.info("✓ 原子设计完成")
            return final_result
            
        except Exception as e:
            self.logger.error(f"原子设计师引擎执行失败: {str(e)}")
            return {
                "engine": "atomic_designer",
                "version": "1.0.0",
                "topic": topic,
                "design_data": self._get_fallback_design(topic, narrative),
                "execution_status": "fallback",
                "error": str(e)
            }
    
    def _extract_narrative_summary(self, narrative: Dict[str, Any]) -> str:
        """提取叙事摘要"""
        if not narrative:
            return "标准内容叙事结构"
        
        narrative_data = narrative.get("narrative_data", {})
        
        story_theme = narrative_data.get("narrative_overview", {}).get("story_theme", "")
        total_pages = narrative_data.get("content_series", {}).get("total_pages", 6)
        content_flow = narrative_data.get("content_series", {}).get("content_flow", "")
        
        page_titles = [page.get("page_title", "") for page in narrative_data.get("page_breakdown", [])]
        
        summary = f"主题: {story_theme} | 页数: {total_pages} | 流程: {content_flow}"
        if page_titles:
            summary += f" | 标题: {' → '.join(page_titles[:3])}..."
        
        return summary
    
    def _get_fallback_design(self, topic: str, narrative: Dict[str, Any]) -> Dict[str, Any]:
        """获取备用设计模板"""
        
        # 尝试从narrative中获取页面信息
        page_breakdown = []
        narrative_data = narrative.get("narrative_data", {}) if narrative else {}
        if narrative_data.get("page_breakdown"):
            page_breakdown = narrative_data["page_breakdown"]
        else:
            # 默认6页结构
            page_breakdown = [
                {"page_number": 1, "page_type": "封面页", "page_title": f"掌握{topic}的关键秘诀"},
                {"page_number": 2, "page_type": "内容页", "page_title": f"{topic}的核心方法"},
                {"page_number": 3, "page_type": "内容页", "page_title": f"实践{topic}的具体步骤"},
                {"page_number": 4, "page_type": "内容页", "page_title": f"{topic}的进阶技巧"},
                {"page_number": 5, "page_type": "对比页", "page_title": f"{topic}的常见误区"},
                {"page_number": 6, "page_type": "结尾页", "page_title": f"开始你的{topic}之旅"}
            ]
        
        return {
            "publication_package": {
                "xiaohongshu_titles": [
                    f"🔥{topic}完全指南！99%的人都不知道的方法",
                    f"💡{topic}系统攻略：从入门到精通的全路径",
                    f"⚡️掌握{topic}，这一篇就够了！"
                ],
                "xiaohongshu_content": {
                    "main_text": f"关于{topic}，很多人都有误解。今天分享系统性的方法，让你快速掌握核心要点。\n\n✅ 科学方法\n✅ 实用技巧\n✅ 避坑指南\n\n收藏起来慢慢看！",
                    "hashtags": [f"#{topic}", "#干货分享", "#实用技巧", "#避坑指南", "#系统学习"],
                    "call_to_action": "有问题评论区见！点赞收藏让更多人看到～"
                },
                "content_metadata": {
                    "target_audience": f"对{topic}感兴趣的学习者",
                    "content_category": "教育干货",
                    "publishing_timing": "工作日晚上8-10点，周末下午2-4点"
                }
            },
            "page_design_specs": [
                self._create_page_spec(page_info, topic) for page_info in page_breakdown
            ],
            "design_system": {
                "brand_guidelines": {
                    "color_palette": ["#2563eb", "#10b981", "#f59e0b", "#ef4444"],
                    "typography_scale": "标题32px/正文16px/说明14px",
                    "spacing_system": "4px基础网格系统",
                    "component_library": ["卡片", "按钮", "图标", "标签"]
                },
                "visual_consistency": {
                    "design_principles": ["清晰易读", "视觉层次", "一致性"],
                    "style_guidelines": "现代简约风格，注重可读性",
                    "quality_standards": "高对比度、合理间距、响应式适配"
                }
            },
            "production_notes": {
                "design_priorities": ["内容可读性", "视觉吸引力", "品牌一致性"],
                "implementation_sequence": "从封面到结尾，逐页完善",
                "quality_checkpoints": ["文字清晰度", "色彩搭配", "布局平衡"],
                "revision_guidelines": "基于用户反馈优化，保持核心设计不变"
            }
        }
    
    def _create_page_spec(self, page_info: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """创建单页设计规格"""
        page_number = page_info.get("page_number", 1)
        page_type = page_info.get("page_type", "内容页")
        page_title = page_info.get("page_title", f"{topic}相关内容")
        
        # 根据页面类型选择不同的设计模板
        if page_type == "封面页":
            return self._create_cover_page_spec(page_number, page_title, topic)
        elif page_type == "对比页":
            return self._create_comparison_page_spec(page_number, page_title, topic)
        elif page_type == "结尾页":
            return self._create_final_page_spec(page_number, page_title, topic)
        else:
            return self._create_content_page_spec(page_number, page_title, topic)
    
    def _create_cover_page_spec(self, page_number: int, page_title: str, topic: str) -> Dict[str, Any]:
        """创建封面页规格"""
        return {
            "page_number": page_number,
            "page_type": "封面页",
            "page_title": page_title,
            "layout_structure": {
                "layout_type": "居中布局",
                "main_sections": [
                    {
                        "section_name": "主标题区",
                        "section_purpose": "吸引注意力",
                        "content_elements": ["大标题", "副标题", "装饰元素"],
                        "visual_treatment": "大字体、高对比度"
                    }
                ]
            },
            "content_specification": {
                "headline": page_title,
                "subheadline": f"关于{topic}的系统性指南",
                "body_content": [
                    {
                        "content_type": "标签",
                        "content_text": "干货分享 | 实用技巧 | 避坑指南",
                        "visual_emphasis": "标签样式",
                        "formatting": "小字体、彩色背景"
                    }
                ],
                "supporting_elements": ["作者信息", "品牌标识"]
            },
            "visual_design": {
                "color_scheme": {
                    "primary_color": "#2563eb",
                    "secondary_color": "#3b82f6",
                    "background_color": "#f8fafc", 
                    "text_color": "#1e293b"
                },
                "typography": {
                    "title_font": "加粗32px",
                    "body_font": "常规16px",
                    "emphasis_treatment": "颜色强调"
                },
                "visual_elements": [
                    {
                        "element_type": "图标",
                        "element_description": "主题相关图标",
                        "placement": "标题旁边",
                        "size_specification": "24px",
                        "style_treatment": "线性图标风格"
                    }
                ]
            },
            "technical_implementation": {
                "css_classes": ["cover-page", "text-center", "bg-blue-50"],
                "layout_code": "flex flex-col items-center justify-center",
                "responsive_notes": "移动端优先设计",
                "accessibility_considerations": "确保文字对比度符合WCAG标准"
            }
        }
    
    def _create_content_page_spec(self, page_number: int, page_title: str, topic: str) -> Dict[str, Any]:
        """创建内容页规格"""
        return {
            "page_number": page_number,
            "page_type": "内容页",
            "page_title": page_title,
            "layout_structure": {
                "layout_type": "单栏布局",
                "main_sections": [
                    {
                        "section_name": "标题区",
                        "section_purpose": "明确页面主题",
                        "content_elements": ["页面标题", "页码"],
                        "visual_treatment": "清晰层次"
                    },
                    {
                        "section_name": "内容区",
                        "section_purpose": "传递核心信息",
                        "content_elements": ["要点列表", "说明文字"],
                        "visual_treatment": "结构化展示"
                    }
                ]
            },
            "content_specification": {
                "headline": page_title,
                "subheadline": None,
                "body_content": [
                    {
                        "content_type": "列表",
                        "content_text": f"{topic}的核心要点列表",
                        "visual_emphasis": "项目符号",
                        "formatting": "间距清晰的列表"
                    }
                ],
                "supporting_elements": ["小贴士", "注意事项"]
            },
            "visual_design": {
                "color_scheme": {
                    "primary_color": "#10b981",
                    "secondary_color": "#34d399", 
                    "background_color": "#ffffff",
                    "text_color": "#374151"
                },
                "typography": {
                    "title_font": "加粗24px",
                    "body_font": "常规16px",
                    "emphasis_treatment": "颜色和字重强调"
                },
                "visual_elements": [
                    {
                        "element_type": "装饰线",
                        "element_description": "分割线装饰",
                        "placement": "标题下方",
                        "size_specification": "2px高度",
                        "style_treatment": "渐变色彩"
                    }
                ]
            },
            "technical_implementation": {
                "css_classes": ["content-page", "bg-white", "text-gray-700"],
                "layout_code": "space-y-4 p-6",
                "responsive_notes": "确保在小屏幕上可读性",
                "accessibility_considerations": "合理的标题层级结构"
            }
        }
    
    def _create_comparison_page_spec(self, page_number: int, page_title: str, topic: str) -> Dict[str, Any]:
        """创建对比页规格"""
        return {
            "page_number": page_number,
            "page_type": "对比页", 
            "page_title": page_title,
            "layout_structure": {
                "layout_type": "上下对比",
                "main_sections": [
                    {
                        "section_name": "错误示例区",
                        "section_purpose": "展示错误做法",
                        "content_elements": ["错误标识", "错误内容"],
                        "visual_treatment": "红色警示风格"
                    },
                    {
                        "section_name": "正确示例区", 
                        "section_purpose": "展示正确做法",
                        "content_elements": ["正确标识", "正确内容"],
                        "visual_treatment": "绿色确认风格"
                    }
                ]
            },
            "content_specification": {
                "headline": page_title,
                "subheadline": "对比学习，避免踩坑",
                "body_content": [
                    {
                        "content_type": "对比项",
                        "content_text": f"{topic}的正确vs错误做法",
                        "visual_emphasis": "对比色彩",
                        "formatting": "卡片式对比布局"
                    }
                ],
                "supporting_elements": ["提示说明", "记忆口诀"]
            },
            "visual_design": {
                "color_scheme": {
                    "primary_color": "#ef4444",
                    "secondary_color": "#10b981",
                    "background_color": "#f9fafb",
                    "text_color": "#111827"
                },
                "typography": {
                    "title_font": "加粗24px",
                    "body_font": "常规16px", 
                    "emphasis_treatment": "背景色块强调"
                },
                "visual_elements": [
                    {
                        "element_type": "对比图标",
                        "element_description": "❌和✅图标",
                        "placement": "每个对比项前",
                        "size_specification": "20px",
                        "style_treatment": "彩色图标"
                    }
                ]
            },
            "technical_implementation": {
                "css_classes": ["comparison-page", "bg-gray-50"],
                "layout_code": "grid grid-cols-1 gap-4",
                "responsive_notes": "确保对比清晰可见",
                "accessibility_considerations": "使用图标和颜色双重指示"
            }
        }
    
    def _create_final_page_spec(self, page_number: int, page_title: str, topic: str) -> Dict[str, Any]:
        """创建结尾页规格"""
        return {
            "page_number": page_number,
            "page_type": "结尾页",
            "page_title": page_title,
            "layout_structure": {
                "layout_type": "居中布局",
                "main_sections": [
                    {
                        "section_name": "总结区",
                        "section_purpose": "内容回顾",
                        "content_elements": ["关键要点", "行动建议"],
                        "visual_treatment": "突出重点"
                    },
                    {
                        "section_name": "互动区",
                        "section_purpose": "引导参与",
                        "content_elements": ["点赞提醒", "评论引导"],
                        "visual_treatment": "友好邀请"
                    }
                ]
            },
            "content_specification": {
                "headline": page_title,
                "subheadline": "感谢阅读，一起成长",
                "body_content": [
                    {
                        "content_type": "总结",
                        "content_text": f"掌握{topic}的关键要点总结",
                        "visual_emphasis": "要点标记",
                        "formatting": "简洁明了的要点列表"
                    },
                    {
                        "content_type": "互动",
                        "content_text": "点赞收藏，评论分享你的经验",
                        "visual_emphasis": "按钮样式",
                        "formatting": "行动按钮设计"
                    }
                ],
                "supporting_elements": ["作者信息", "关注提醒"]
            },
            "visual_design": {
                "color_scheme": {
                    "primary_color": "#8b5cf6",
                    "secondary_color": "#a78bfa",
                    "background_color": "#ffffff",
                    "text_color": "#1f2937"
                },
                "typography": {
                    "title_font": "加粗28px",
                    "body_font": "常规16px",
                    "emphasis_treatment": "渐变色彩"
                },
                "visual_elements": [
                    {
                        "element_type": "装饰元素",
                        "element_description": "庆祝图标或徽章",
                        "placement": "页面中心",
                        "size_specification": "48px",
                        "style_treatment": "彩色渐变"
                    }
                ]
            },
            "technical_implementation": {
                "css_classes": ["final-page", "text-center", "bg-white"],
                "layout_code": "flex flex-col items-center space-y-6",
                "responsive_notes": "确保在所有设备上居中显示",
                "accessibility_considerations": "清晰的行动指引"
            }
        }
    
    def get_design_summary(self, topic: str) -> Optional[Dict[str, Any]]:
        """获取设计摘要"""
        cached_result = self.load_cache(topic, "atomic_designer.json")
        if not cached_result:
            return None
        
        design_data = cached_result.get("design_data", {})
        
        return {
            "xiaohongshu_titles": design_data.get("publication_package", {}).get("xiaohongshu_titles", []),
            "total_pages": len(design_data.get("page_design_specs", [])),
            "design_style": design_data.get("design_system", {}).get("visual_consistency", {}).get("style_guidelines", ""),
            "color_palette": design_data.get("design_system", {}).get("brand_guidelines", {}).get("color_palette", [])
        } 