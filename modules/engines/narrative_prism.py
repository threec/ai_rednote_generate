"""
引擎⑤: 叙事棱镜引擎 (Narrative Prism Engine)
RedCube AI 工作流系统

目标：将"大故事"蓝图解构成逻辑连贯、引人入胜的系列笔记目录

核心功能：
- 封面标题策略：矩阵化、系列化的内容才能构建护城河
- 拒绝平铺直叙："XX介绍"
- 拥抱"钩子"，创造高点击率标题（悬念、冲突、问题、比喻等）

实现方式：
- 基于LangChain构建叙事架构链
- 多页面内容规划设计
- 标题优化和钩子设计
- 输出完整的叙事架构
"""

import json
from typing import Dict, Any, Optional, List
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from ..langchain_workflow import BaseWorkflowEngine
from ..utils import get_logger

class NarrativePrismEngine(BaseWorkflowEngine):
    """叙事棱镜引擎 - 故事架构设计"""
    
    def __init__(self, llm):
        super().__init__("narrative_prism", llm)
        self._initialize_narrative_chain()
    
    def _initialize_narrative_chain(self):
        """初始化叙事架构链"""
        
        system_prompt = """
你是RedCube AI的"叙事棱镜大师"，专门负责将大故事解构为引人入胜的系列内容。

## 核心使命：构建引人入胜的叙事架构

将"大故事"蓝图解构成逻辑连贯、引人入胜的系列笔记目录，确保每一页都有强大的吸引力。

## 叙事设计框架

### 【封面标题策略】
1. **矩阵化思维** 📊
   - 系列化内容规划：多个相关主题形成内容矩阵
   - 主题深度挖掘：单一主题的多维度展开
   - 内容护城河：建立不可替代的内容优势

2. **钩子化表达** 🎣
   - **拒绝平铺直叙**：避免"XX介绍"式的无聊标题
   - **拥抱钩子元素**：悬念、冲突、问题、比喻、数字等
   - **高点击率设计**：创造让人忍不住点击的标题

### 【叙事架构原则】
1. **逻辑连贯性**
   - 故事线索清晰：从问题到解决的完整路径
   - 层次递进：浅入深出的认知升级
   - 情感起伏：保持读者的注意力和兴趣

2. **页面功能分工**
   - **封面页**：吸引注意，建立期待
   - **内容页**：核心价值传递
   - **对比页**：强化认知差异
   - **结尾页**：价值升华，行动引导

3. **互动设计**
   - 参与感营造：让读者有代入感
   - 讨论点设置：引发评论和分享
   - 行动引导：从认知到行为的转化

### 【页面内容规划】
每页内容需要明确：
- **页面目标**：这一页要达成什么目的
- **核心信息**：传递的关键内容点
- **吸引元素**：保持注意力的设计
- **连接逻辑**：与前后页面的关系

### 【输出规范】
必须返回严格的JSON格式：

```json
{
  "narrative_overview": {
    "story_theme": "整体故事主题",
    "narrative_strategy": "叙事策略选择",
    "target_emotion": "目标情感体验",
    "engagement_approach": "互动参与方式"
  },
  "content_series": {
    "series_title": "系列内容标题",
    "total_pages": "总页数",
    "content_flow": "内容流动逻辑",
    "key_differentiators": ["差异化要素1", "差异化要素2"]
  },
  "page_breakdown": [
    {
      "page_number": 1,
      "page_type": "封面页",
      "page_title": "具体页面标题",
      "hook_elements": ["钩子元素1", "钩子元素2"],
      "core_message": "核心信息",
      "visual_concept": "视觉概念",
      "engagement_trigger": "参与触发器",
      "transition_to_next": "与下页的连接"
    }
  ],
  "title_optimization": {
    "headline_strategies": [
      {
        "strategy_name": "策略名称",
        "technique": "技巧说明",
        "example_titles": ["示例标题1", "示例标题2"]
      }
    ],
    "hook_library": {
      "curiosity_gaps": ["好奇缺口1", "好奇缺口2"],
      "conflict_elements": ["冲突元素1", "冲突元素2"],
      "benefit_promises": ["利益承诺1", "利益承诺2"],
      "social_proof": ["社会证明1", "社会证明2"]
    }
  },
  "engagement_design": {
    "interaction_points": [
      {
        "page_location": "页面位置",
        "interaction_type": "互动类型",
        "engagement_goal": "互动目标",
        "implementation": "实现方式"
      }
    ],
    "discussion_starters": ["讨论引发点1", "讨论引发点2"],
    "sharing_hooks": ["分享钩子1", "分享钩子2"]
  },
  "content_continuity": {
    "story_arc": "故事弧线设计",
    "emotional_journey": "情感旅程规划",
    "knowledge_progression": "知识递进路径",
    "action_pathway": "行动引导路径"
  },
  "quality_metrics": {
    "clickability_score": "点击性评分",
    "engagement_potential": "参与潜力",
    "shareability_index": "分享指数",
    "memorability_factor": "记忆度因子"
  }
}
```

### 【质量标准】
- **钩子强度**：每个标题都有强烈的吸引力
- **逻辑清晰**：内容展开有清晰的逻辑线索
- **情感连接**：与读者建立情感共鸣
- **行动导向**：引导读者从认知到行动

现在请根据前期分析，设计引人入胜的叙事架构。
"""

        user_template = """
请为以下内容设计叙事架构：

**主题**: {topic}

**核心洞察**: {insight_summary}

**设计要求**:
1. 设计6-8页的系列内容架构
2. 每页都要有强烈的钩子和吸引力
3. 整体形成完整的故事弧线
4. 拒绝平铺直叙，拥抱钩子化表达
5. 确保逻辑连贯和情感起伏

请严格按照JSON格式输出完整的叙事架构设计。
"""

        self.narrative_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_template)
        ])
        
        self.narrative_chain = (
            self.narrative_prompt
            | self.llm
            | StrOutputParser()
        )
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行叙事架构设计"""
        topic = inputs.get("topic", "")
        strategic_results = inputs.get("strategic_results", {})
        workflow_state = inputs.get("workflow_state", {})
        force_regenerate = inputs.get("force_regenerate", False)
        
        self.logger.info(f"🌈 叙事棱镜引擎启动 - 主题: {topic}")
        
        # 检查缓存
        if not force_regenerate:
            cached_result = self.load_cache(topic, "narrative_prism.json")
            if cached_result:
                self.logger.info("✓ 使用缓存的叙事架构")
                return cached_result
        
        try:
            # 提取洞察摘要
            insight_summary = self._extract_insight_summary(workflow_state.get("insights", {}))
            
            # 执行叙事架构链
            self.logger.info("执行叙事架构设计...")
            result_text = await self.narrative_chain.ainvoke({
                "topic": topic,
                "insight_summary": insight_summary
            })
            
            # 解析JSON结果
            try:
                cleaned_text = result_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                narrative_result = json.loads(cleaned_text)
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {e}")
                narrative_result = self._get_fallback_narrative(topic)
            
            # 添加引擎元数据
            final_result = {
                "engine": "narrative_prism",
                "version": "1.0.0",
                "topic": topic,
                "narrative_data": narrative_result,
                "insight_reference": insight_summary,
                "execution_status": "success"
            }
            
            # 保存缓存
            self.save_cache(topic, final_result, "narrative_prism.json")
            
            self.logger.info("✓ 叙事架构设计完成")
            return final_result
            
        except Exception as e:
            self.logger.error(f"叙事棱镜引擎执行失败: {str(e)}")
            return {
                "engine": "narrative_prism",
                "version": "1.0.0",
                "topic": topic,
                "narrative_data": self._get_fallback_narrative(topic),
                "execution_status": "fallback",
                "error": str(e)
            }
    
    def _extract_insight_summary(self, insights: Dict[str, Any]) -> str:
        """提取洞察摘要"""
        if not insights:
            return "核心价值洞察"
        
        insight_data = insights.get("insight_data", {})
        big_idea = insight_data.get("big_idea", {})
        
        central_concept = big_idea.get("central_concept", "")
        value_prop = big_idea.get("value_proposition", "")
        unique_angle = big_idea.get("unique_angle", "")
        
        return f"{central_concept} | {value_prop} | {unique_angle}"
    
    def _get_fallback_narrative(self, topic: str) -> Dict[str, Any]:
        """获取备用叙事模板"""
        return {
            "narrative_overview": {
                "story_theme": f"关于{topic}的系统性指导故事",
                "narrative_strategy": "问题驱动的解决方案展示",
                "target_emotion": "从困惑到清晰的成就感",
                "engagement_approach": "互动式教学和实践指导"
            },
            "content_series": {
                "series_title": f"{topic}系统指南",
                "total_pages": 6,
                "content_flow": "问题识别 → 方法介绍 → 实践指导 → 进阶优化 → 常见误区 → 总结升华",
                "key_differentiators": ["系统性方法", "实践导向", "专业权威"]
            },
            "page_breakdown": [
                {
                    "page_number": 1,
                    "page_type": "封面页",
                    "page_title": f"你真的了解{topic}吗？这些误区99%的人都踩过",
                    "hook_elements": ["疑问句钩子", "数据化表达", "误区悬念"],
                    "core_message": f"揭示{topic}中的常见认知误区",
                    "visual_concept": "问题与解答的对比设计",
                    "engagement_trigger": "自我检视和好奇心",
                    "transition_to_next": "引出系统性解决方案的必要性"
                },
                {
                    "page_number": 2,
                    "page_type": "内容页",
                    "page_title": f"科学方法：{topic}的3个核心原则",
                    "hook_elements": ["权威性表达", "数字化概括", "核心原则"],
                    "core_message": "介绍科学系统的核心方法",
                    "visual_concept": "原则图解和要点展示",
                    "engagement_trigger": "专业知识的渴望",
                    "transition_to_next": "从理论转向实践应用"
                },
                {
                    "page_number": 3,
                    "page_type": "内容页",
                    "page_title": f"实战攻略：{topic}的具体操作步骤",
                    "hook_elements": ["实战感", "攻略概念", "具体操作"],
                    "core_message": "提供详细的实践操作指导",
                    "visual_concept": "步骤流程图和操作示例",
                    "engagement_trigger": "实用价值和可操作性",
                    "transition_to_next": "进入个性化和进阶内容"
                },
                {
                    "page_number": 4,
                    "page_type": "内容页",
                    "page_title": f"进阶技巧：让{topic}效果翻倍的秘诀",
                    "hook_elements": ["进阶感", "效果量化", "秘诀神秘感"],
                    "core_message": "分享高级技巧和优化方法",
                    "visual_concept": "对比效果和技巧展示",
                    "engagement_trigger": "进阶成长的需求",
                    "transition_to_next": "转向风险规避和误区提醒"
                },
                {
                    "page_number": 5,
                    "page_type": "对比页",
                    "page_title": f"避坑指南：{topic}中最容易犯的5个错误",
                    "hook_elements": ["避坑概念", "具体数量", "错误警示"],
                    "core_message": "指出常见错误和正确做法",
                    "visual_concept": "错误与正确的对比展示",
                    "engagement_trigger": "风险规避的安全感",
                    "transition_to_next": "总结和行动引导"
                },
                {
                    "page_number": 6,
                    "page_type": "结尾页",
                    "page_title": f"掌握{topic}，从今天开始改变",
                    "hook_elements": ["掌握感", "时间紧迫性", "改变承诺"],
                    "core_message": "总结要点并引导行动",
                    "visual_concept": "成长路径和行动计划",
                    "engagement_trigger": "成就感和行动动力",
                    "transition_to_next": "完成内容闭环"
                }
            ],
            "title_optimization": {
                "headline_strategies": [
                    {
                        "strategy_name": "疑问钩子",
                        "technique": "用疑问句引发思考",
                        "example_titles": [f"你真的了解{topic}吗？", f"为什么{topic}总是失败？"]
                    },
                    {
                        "strategy_name": "数字化表达",
                        "technique": "用具体数字增强可信度",
                        "example_titles": [f"{topic}的3个核心原则", f"最容易犯的5个错误"]
                    }
                ],
                "hook_library": {
                    "curiosity_gaps": ["你真的了解吗", "秘诀揭秘", "误区警示"],
                    "conflict_elements": ["常见错误", "避坑指南", "对比分析"],
                    "benefit_promises": ["效果翻倍", "系统掌握", "快速提升"],
                    "social_proof": ["99%的人", "专家建议", "科学方法"]
                }
            },
            "engagement_design": {
                "interaction_points": [
                    {
                        "page_location": "封面页",
                        "interaction_type": "自我检测",
                        "engagement_goal": "建立参与感",
                        "implementation": "误区自查清单"
                    },
                    {
                        "page_location": "实践页",
                        "interaction_type": "操作指导",
                        "engagement_goal": "提升实用性",
                        "implementation": "步骤清单和工具推荐"
                    }
                ],
                "discussion_starters": ["你遇到过哪些误区", "分享你的实践经验"],
                "sharing_hooks": ["干货收藏", "帮助朋友避坑"]
            },
            "content_continuity": {
                "story_arc": "发现问题 → 学习方法 → 实践应用 → 进阶优化 → 风险规避 → 成长总结",
                "emotional_journey": "困惑 → 启发 → 信心 → 进步 → 安全感 → 成就感",
                "knowledge_progression": "认知升级 → 方法掌握 → 技能提升 → 错误避免 → 系统整合",
                "action_pathway": "意识 → 学习 → 实践 → 优化 → 持续改进"
            },
            "quality_metrics": {
                "clickability_score": "高（钩子元素丰富）",
                "engagement_potential": "强（互动设计充分）",
                "shareability_index": "优（实用价值突出）",
                "memorability_factor": "好（结构清晰有序）"
            }
        }
    
    def get_narrative_summary(self, topic: str) -> Optional[Dict[str, Any]]:
        """获取叙事摘要"""
        cached_result = self.load_cache(topic, "narrative_prism.json")
        if not cached_result:
            return None
        
        narrative_data = cached_result.get("narrative_data", {})
        
        return {
            "story_theme": narrative_data.get("narrative_overview", {}).get("story_theme", ""),
            "total_pages": narrative_data.get("content_series", {}).get("total_pages", 6),
            "page_titles": [page.get("page_title", "") for page in narrative_data.get("page_breakdown", [])],
            "content_flow": narrative_data.get("content_series", {}).get("content_flow", "")
        } 