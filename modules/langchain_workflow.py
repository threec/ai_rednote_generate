"""
小红书内容自动化管线 - LangChain 8引擎工作流系统
RedCube AI 工作流深度复刻版本

基于LangChain框架实现的专业级内容生成工作流，包含8个核心引擎：
1. 人格核心引擎 - 建立统一的内容人格
2. 策略罗盘引擎 - 内容战略规划
3. 真理探机引擎 - 权威事实验证
4. 洞察提炼器引擎 - 核心价值挖掘  
5. 叙事棱镜引擎 - 故事架构设计
6. 原子设计师引擎 - 页面布局设计
7. 视觉编码器引擎 - HTML/CSS代码生成
8. 高保真成像仪引擎 - 图片生成优化

采用"系统思维"而非"指令思维"，让AI扮演"架构师"而非"命令者"
"""

import os
import json
import asyncio
import sys
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
import importlib

# LangChain核心组件
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnableSequence

# 项目内部导入
from config import (
    GEMINI_API_KEY, MODEL_FOR_EXECUTION, 
    CACHE_DIR, OUTPUT_DIR, DEFAULT_TEMPERATURE
)
from modules.utils import get_logger, save_json, load_json
from modules.models import get_langchain_model
from modules.git_automation import get_git_automation, auto_commit_if_needed, commit_checkpoint

# ===================================
# 核心配置
# ===================================

logger = get_logger(__name__)

class RedCubeWorkflowConfig:
    """RedCube AI 工作流配置类"""
    
    # 引擎配置
    ENGINES = {
        "persona_core": "人格核心",
        "strategy_compass": "策略罗盘", 
        "truth_detector": "真理探机",
        "insight_distiller": "洞察提炼器",
        "narrative_prism": "叙事棱镜",
        "atomic_designer": "原子设计师",
        "visual_encoder": "视觉编码器",
        "hifi_imager": "高保真成像仪"
    }
    
    # 工作流阶段
    PHASES = {
        "strategic_thinking": "第一认知象限：战略构想",
        "narrative_expression": "第二认知象限：叙事表达"
    }

# ===================================
# 基础工作流引擎类
# ===================================

class FlexibleOutput:
    """灵活的输出格式管理"""
    
    def __init__(self, engine_name: str, topic: str):
        self.engine_name = engine_name
        self.topic = topic
        self.metadata = {}
        self.content = ""
        self.format_type = "json"  # json, text, hybrid
    
    def set_metadata(self, **kwargs):
        """设置元数据"""
        self.metadata.update(kwargs)
    
    def set_content(self, content: str, format_type: str = "text"):
        """设置内容"""
        self.content = content
        self.format_type = format_type
    
    def to_result(self) -> Dict[str, Any]:
        """转换为标准结果格式"""
        result = {
            "engine": self.engine_name,
            "version": "1.0.0",
            "topic": self.topic,
            "format_type": self.format_type,
            "metadata": self.metadata,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if self.format_type == "json":
            # 传统JSON模式
            result["data"] = json.loads(self.content) if isinstance(self.content, str) else self.content
        elif self.format_type == "text":
            # 纯文本模式
            result["content"] = self.content
        elif self.format_type == "hybrid":
            # 混合模式：结构化数据 + 文本报告
            result["content"] = self.content
            result["structured_data"] = self.metadata.get("structured_data", {})
        
        return result
    
    def save(self, cache_dir: str):
        """保存到缓存"""
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        
        # 保存元数据
        metadata_file = cache_path / f"{self.engine_name}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        
        # 保存内容
        if self.format_type in ["text", "hybrid"]:
            content_file = cache_path / f"{self.engine_name}_content.txt"
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(self.content)
        
        # 保存完整结果
        result_file = cache_path / f"{self.engine_name}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_result(), f, ensure_ascii=False, indent=2)

class BaseWorkflowEngine:
    """工作流引擎基类"""
    
    def __init__(self, llm, logger=None):
        self.llm = llm
        self.logger = logger or get_logger()
        self.cache_dir = "cache"
        self.engine_name = self.__class__.__name__.lower().replace("engine", "")
        self.git_auto = get_git_automation()
    
    def create_output(self, topic: str) -> FlexibleOutput:
        """创建灵活的输出对象"""
        return FlexibleOutput(self.engine_name, topic)
    
    def load_cache(self, topic: str, filename: str) -> Optional[Dict[str, Any]]:
        """加载缓存文件"""
        cache_path = Path(self.cache_dir) / f"engine_{self.engine_name}" / filename
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"加载缓存失败: {e}")
        return None
    
    def save_cache(self, topic: str, data: Dict[str, Any], filename: str):
        """保存缓存文件"""
        cache_dir = Path(self.cache_dir) / f"engine_{self.engine_name}"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_path = cache_dir / filename
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_flexible_cache(self, topic: str) -> Optional[Dict[str, Any]]:
        """加载灵活格式的缓存"""
        cache_dir = Path(self.cache_dir) / f"engine_{self.engine_name}"
        result_file = cache_dir / f"{self.engine_name}.json"
        
        if result_file.exists():
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"加载灵活缓存失败: {e}")
        return None
    
    async def execute_with_git(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """带Git自动提交的执行"""
        topic = inputs.get("topic", "")
        
        # 执行引擎逻辑
        result = await self.execute(inputs)
        
        # 检查是否成功并自动提交
        if result.get("execution_status") == "success":
            commit_result = self.git_auto.commit_on_engine_complete(
                self.engine_name, topic
            )
            if commit_result["success"]:
                self.logger.info(f"✅ {self.engine_name}引擎完成，已自动提交Git")
                result["git_commit"] = commit_result["commit_hash"]
            else:
                self.logger.warning(f"Git自动提交失败: {commit_result['message']}")
        
        return result
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行引擎逻辑"""
        raise NotImplementedError("子类必须实现execute方法")

# ===================================
# RedCube AI 主工作流类
# ===================================

class RedCubeWorkflow:
    """RedCube AI 8引擎工作流主类"""
    
    def __init__(self, api_key: str = GEMINI_API_KEY):
        """初始化工作流"""
        self.api_key = api_key
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=MODEL_FOR_EXECUTION,
            temperature=DEFAULT_TEMPERATURE
        )
        
        # 工作流状态
        self.current_topic = None
        self.workflow_state = {}
        
        # 初始化logger（必须在_initialize_engines之前）
        self.logger = get_logger(__name__)
        
        # 初始化8个引擎
        self.engines = {}
        self._initialize_engines()
    
    def _initialize_engines(self):
        """初始化8个引擎"""
        self.logger.info("开始初始化RedCube AI 8个引擎...")
        
        engine_classes = [
            ("persona_core", "PersonaCoreEngine"),
            ("strategy_compass", "StrategyCompassEngine"),
            ("truth_detector", "TruthDetectorEngine"),
            ("insight_distiller", "InsightDistillerEngine"),
            ("narrative_prism", "NarrativePrismEngine"),
            ("atomic_designer", "AtomicDesignerEngine"),
            ("visual_encoder", "VisualEncoderEngine"),
            ("hifi_imager", "HiFiImagerEngine")
        ]
        
        for engine_name, engine_class_name in engine_classes:
            try:
                # 使用绝对导入路径
                module_path = f"modules.engines.{engine_name}"
                engine_module = __import__(module_path, fromlist=[engine_class_name])
                engine_class = getattr(engine_module, engine_class_name)
                
                # 初始化引擎实例
                self.engines[engine_name] = engine_class(self.llm)
                self.logger.info(f"✓ 引擎 {engine_name} 初始化成功")
            except ImportError as e:
                self.logger.warning(f"⚠️ 引擎 {engine_name} 导入失败: {e}")
                self.engines[engine_name] = None
            except Exception as e:
                self.logger.error(f"❌ 引擎 {engine_name} 初始化失败: {e}")
                self.engines[engine_name] = None
        
        successful_engines = [name for name, engine in self.engines.items() if engine is not None]
        failed_engines = [name for name, engine in self.engines.items() if engine is None]
        
        self.logger.info(f"引擎初始化完成: 成功 {len(successful_engines)}/{len(engine_classes)}")
        if successful_engines:
            self.logger.info(f"成功初始化的引擎: {', '.join(successful_engines)}")
        if failed_engines:
            self.logger.warning(f"初始化失败的引擎: {', '.join(failed_engines)}")
    
    async def run_complete_workflow(self, topic: str, force_regenerate: bool = False) -> Dict[str, Any]:
        """运行完整的8引擎工作流"""
        self.current_topic = topic
        self.logger.info(f"开始执行RedCube AI 8引擎工作流，主题：{topic}")
        
        try:
            # 第一认知象限：战略构想
            strategic_results = await self._run_strategic_phase(topic, force_regenerate)
            
            # 第二认知象限：叙事表达  
            narrative_results = await self._run_narrative_phase(strategic_results, force_regenerate)
            
            # 整合最终结果
            final_result = {
                "topic": topic,
                "timestamp": datetime.now().isoformat(),
                "workflow_version": "RedCube_AI_v1.0",
                "strategic_phase": strategic_results,
                "narrative_phase": narrative_results,
                "final_outputs": {
                    "html_content": narrative_results.get("visual_encoder", {}).get("html_code", ""),
                    "image_specs": narrative_results.get("hifi_imager", {}).get("image_specifications", []),
                    "content_summary": strategic_results.get("insight_distiller", {}).get("core_insights", {}),
                    "design_blueprint": narrative_results.get("atomic_designer", {}).get("design_specs", {})
                }
            }
            
            # 保存最终结果
            output_path = os.path.join(OUTPUT_DIR, f"redcube_workflow_{topic[:20]}.json")
            save_json(output_path, final_result)
            
            self.logger.info(f"✓ RedCube AI 工作流执行完成，结果保存至：{output_path}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"工作流执行失败：{str(e)}")
            raise
    
    async def _run_strategic_phase(self, topic: str, force_regenerate: bool) -> Dict[str, Any]:
        """执行第一认知象限：战略构想"""
        self.logger.info("开始执行第一认知象限：战略构想")
        
        results = {}
        
        # 1. 人格核心 - 建立统一的内容人格
        if self.engines["persona_core"]:
            persona_result = await self.engines["persona_core"].execute({
                "topic": topic,
                "force_regenerate": force_regenerate
            })
            results["persona_core"] = persona_result
            self.workflow_state["persona"] = persona_result
        
        # 2. 策略罗盘 - 内容战略规划
        if self.engines["strategy_compass"]:
            strategy_inputs = {
                "topic": topic,
                "persona": self.workflow_state.get("persona", {}),
                "force_regenerate": force_regenerate
            }
            strategy_result = await self.engines["strategy_compass"].execute(strategy_inputs)
            results["strategy_compass"] = strategy_result
            self.workflow_state["strategy"] = strategy_result
        
        # 3. 真理探机 - 权威事实验证
        if self.engines["truth_detector"]:
            truth_inputs = {
                "topic": topic,
                "strategy": self.workflow_state.get("strategy", {}),
                "force_regenerate": force_regenerate
            }
            truth_result = await self.engines["truth_detector"].execute(truth_inputs)
            results["truth_detector"] = truth_result
            self.workflow_state["facts"] = truth_result
        
        # 4. 洞察提炼器 - 核心价值挖掘
        if self.engines["insight_distiller"]:
            insight_inputs = {
                "topic": topic,
                "persona": self.workflow_state.get("persona", {}),
                "strategy": self.workflow_state.get("strategy", {}),
                "facts": self.workflow_state.get("facts", {}),
                "force_regenerate": force_regenerate
            }
            insight_result = await self.engines["insight_distiller"].execute(insight_inputs)
            results["insight_distiller"] = insight_result
            self.workflow_state["insights"] = insight_result
        
        return results
    
    async def _run_narrative_phase(self, strategic_results: Dict[str, Any], force_regenerate: bool) -> Dict[str, Any]:
        """执行第二认知象限：叙事表达"""
        self.logger.info("开始执行第二认知象限：叙事表达")
        
        results = {}
        
        # 5. 叙事棱镜 - 故事架构设计
        if self.engines["narrative_prism"]:
            narrative_inputs = {
                "topic": self.current_topic,
                "strategic_results": strategic_results,
                "workflow_state": self.workflow_state,
                "force_regenerate": force_regenerate
            }
            narrative_result = await self.engines["narrative_prism"].execute(narrative_inputs)
            results["narrative_prism"] = narrative_result
            self.workflow_state["narrative"] = narrative_result
        
        # 6. 原子设计师 - 页面布局设计
        if self.engines["atomic_designer"]:
            design_inputs = {
                "topic": self.current_topic,
                "narrative": self.workflow_state.get("narrative", {}),
                "insights": self.workflow_state.get("insights", {}),
                "force_regenerate": force_regenerate
            }
            design_result = await self.engines["atomic_designer"].execute(design_inputs)
            results["atomic_designer"] = design_result
            self.workflow_state["design"] = design_result
        
        # 7. 视觉编码器 - HTML/CSS代码生成
        if self.engines["visual_encoder"]:
            encoder_inputs = {
                "topic": self.current_topic,
                "design": self.workflow_state.get("design", {}),
                "narrative": self.workflow_state.get("narrative", {}),
                "force_regenerate": force_regenerate
            }
            encoder_result = await self.engines["visual_encoder"].execute(encoder_inputs)
            results["visual_encoder"] = encoder_result
            self.workflow_state["html_code"] = encoder_result
        
        # 8. 高保真成像仪 - 图片生成优化
        if self.engines["hifi_imager"]:
            imager_inputs = {
                "topic": self.current_topic,
                "html_code": self.workflow_state.get("html_code", {}),
                "design": self.workflow_state.get("design", {}),
                "force_regenerate": force_regenerate
            }
            imager_result = await self.engines["hifi_imager"].execute(imager_inputs)
            results["hifi_imager"] = imager_result
        
        return results

# ===================================
# 工作流入口函数
# ===================================

async def run_redcube_workflow(topic: str, force_regenerate: bool = False) -> Dict[str, Any]:
    """运行RedCube AI工作流的主入口函数"""
    workflow = RedCubeWorkflow()
    return await workflow.run_complete_workflow(topic, force_regenerate)

def run_redcube_workflow_sync(topic: str, force_regenerate: bool = False) -> Dict[str, Any]:
    """同步版本的工作流入口函数"""
    return asyncio.run(run_redcube_workflow(topic, force_regenerate))

if __name__ == "__main__":
    # 测试代码
    test_topic = "科学育儿的睡眠训练方法"
    result = run_redcube_workflow_sync(test_topic)
    print(f"工作流测试完成，主题：{test_topic}") 