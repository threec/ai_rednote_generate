"""
RedCube AI 工作流系统 - 重构版
集成新的核心组件：配置管理、异常处理、依赖注入、输出管理

核心改进：
1. 使用统一配置管理
2. 集成异常处理框架
3. 采用依赖注入模式
4. 使用混合数据流架构
5. 改进错误恢复机制
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# 核心组件导入
from modules.core.config import get_config, get_config_value
from modules.core.exceptions import (
    WorkflowException, EngineException, SystemException,
    ErrorCode, get_exception_handler
)
from modules.core.container import get_engine_container, EngineContainer
from modules.core.output import (
    get_output_manager, UnifiedOutput, ContentType, OutputFormat
)

# 传统组件导入
from modules.utils import get_logger
from modules.models import get_langchain_model
from modules.git_automation import get_git_automation, commit_checkpoint

class BaseWorkflowEngine:
    """重构后的工作流引擎基类"""
    
    def __init__(self, llm=None, **kwargs):
        # 获取核心服务
        self.config = get_config()
        self.logger = get_logger(self.__class__.__name__)
        self.exception_handler = get_exception_handler()
        self.output_manager = get_output_manager()
        self.git_auto = get_git_automation() if get_config_value("git.auto_commit", True) else None
        
        # 引擎配置
        self.engine_name = self.__class__.__name__.lower().replace("engine", "")
        self.llm = llm
        self.cache_enabled = get_config_value("workflow.enable_cache", True)
        self.cache_dir = Path(get_config_value("paths.cache_dir", "cache"))
        
        # 初始化引擎
        self._initialize_engine()
    
    def _initialize_engine(self):
        """初始化引擎"""
        try:
            # 检查引擎是否启用
            engine_enabled = get_config_value(f"engines.{self.engine_name}.enabled", True)
            if not engine_enabled:
                self.logger.warning(f"引擎 {self.engine_name} 已禁用")
                return
            
            # 创建缓存目录
            engine_cache_dir = self.cache_dir / f"engine_{self.engine_name}"
            engine_cache_dir.mkdir(parents=True, exist_ok=True)
            
            # 调用子类初始化
            self._setup_engine()
            
            self.logger.info(f"✓ {self.engine_name} 引擎初始化成功")
            
        except Exception as e:
            error_msg = f"引擎 {self.engine_name} 初始化失败"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise EngineException(
                self.engine_name, 
                error_msg, 
                ErrorCode.ENGINE_INIT_FAILED,
                context={"initialization_error": str(e)},
                cause=e
            )
    
    def _setup_engine(self):
        """子类应重写此方法进行具体初始化"""
        pass
    
    def create_output(self, topic: str, content_type: ContentType = ContentType.REPORT) -> UnifiedOutput:
        """创建统一输出对象"""
        return self.output_manager.create_output(self.engine_name, topic, content_type)
    
    def load_cache(self, topic: str) -> Optional[UnifiedOutput]:
        """加载缓存"""
        if not self.cache_enabled:
            return None
        
        try:
            return self.output_manager.load_output(
                self.engine_name, 
                topic, 
                subdirectory=f"engine_{self.engine_name}"
            )
        except Exception as e:
            self.logger.warning(f"缓存加载失败: {str(e)}")
            return None
    
    def save_cache(self, output: UnifiedOutput):
        """保存缓存"""
        if not self.cache_enabled:
            return
        
        try:
            self.output_manager.save_output(
                output, 
                subdirectory=f"engine_{self.engine_name}"
            )
        except Exception as e:
            self.logger.warning(f"缓存保存失败: {str(e)}")
    
    async def execute_with_recovery(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """带异常恢复的执行"""
        topic = inputs.get("topic", "")
        max_retries = get_config_value("error_handling.max_retries", 3)
        retry_delay = get_config_value("error_handling.retry_delay", 1.0)
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"🔄 {self.engine_name} 引擎执行 (尝试 {attempt + 1}/{max_retries + 1})")
                
                # 执行核心逻辑
                result = await self.execute(inputs)
                
                # 检查执行结果
                if result.get("success", True):
                    # 自动提交Git（如果启用）
                    if self.git_auto and get_config_value("git.commit_on_engine_complete", True):
                        commit_result = self.git_auto.commit_on_engine_complete(
                            self.engine_name, topic
                        )
                        if commit_result["success"]:
                            result["git_commit"] = commit_result["commit_hash"]
                
                return result
                
            except Exception as e:
                self.logger.error(f"引擎执行失败 (尝试 {attempt + 1}): {str(e)}")
                
                # 使用异常处理器
                error_result = self.exception_handler.handle_exception(e)
                
                # 检查是否应该重试
                if attempt < max_retries and error_result.get("should_retry", False):
                    retry_delay_actual = error_result.get("retry_delay", retry_delay)
                    self.logger.info(f"⏳ {retry_delay_actual}秒后重试...")
                    await asyncio.sleep(retry_delay_actual)
                    continue
                else:
                    # 返回错误结果
                    return self._create_error_result(e, error_result)
        
        # 如果所有重试都失败了
        return self._create_error_result(
            Exception(f"引擎 {self.engine_name} 在 {max_retries} 次重试后仍然失败"),
            {"success": False, "error": "max_retries_exceeded"}
        )
    
    def _create_error_result(self, exception: Exception, error_result: Dict[str, Any]) -> Dict[str, Any]:
        """创建错误结果"""
        topic = "unknown"
        
        # 创建错误输出
        error_output = self.create_output(topic, ContentType.REPORT)
        error_output.set_content(
            f"# {self.engine_name} 引擎执行失败\n\n## 错误信息\n{str(exception)}\n\n## 错误详情\n{error_result}",
            OutputFormat.TEXT
        )
        error_output.set_metadata(
            execution_status="failed",
            error_type=type(exception).__name__,
            error_message=str(exception),
            recovery_attempted=True
        )
        
        return error_output.to_dict()
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行引擎逻辑 - 子类必须实现"""
        raise NotImplementedError("子类必须实现execute方法")

class RedCubeWorkflow:
    """重构后的RedCube AI工作流系统"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        # 获取核心服务
        self.config = get_config()
        self.logger = get_logger("RedCubeWorkflow")
        self.exception_handler = get_exception_handler()
        self.container = get_engine_container()
        self.output_manager = get_output_manager()
        self.git_auto = get_git_automation() if get_config_value("git.auto_commit", True) else None
        
        # 初始化AI模型
        self.llm = self._initialize_llm(api_key, model_name)
        
        # 初始化引擎
        self.engines = {}
        self._initialize_engines()
        
        self.logger.info("🚀 RedCube AI 工作流系统初始化完成")
    
    def _initialize_llm(self, api_key: Optional[str], model_name: Optional[str]):
        """初始化语言模型"""
        try:
            # 使用配置或参数
            final_api_key = api_key or self.config.get("ai.api_key")
            final_model_name = model_name or get_config_value("ai.model_name", "gemini-pro")
            
            if not final_api_key:
                import os
                final_api_key = os.environ.get("GOOGLE_API_KEY")
            
            if not final_api_key:
                raise SystemException(
                    "API密钥未配置",
                    ErrorCode.API_KEY_MISSING,
                    context={"required_env_var": "GOOGLE_API_KEY"}
                )
            
            return get_langchain_model(final_api_key, final_model_name)
            
        except Exception as e:
            raise SystemException(
                f"语言模型初始化失败: {str(e)}",
                ErrorCode.SYSTEM_INIT_FAILED,
                cause=e
            )
    
    def _initialize_engines(self):
        """初始化8个引擎"""
        self.logger.info("开始初始化RedCube AI 8个引擎...")
        
        engine_configs = [
            ("persona_core_v2", "PersonaCoreEngineV2"),
            ("strategy_compass_v2", "StrategyCompassEngineV2"),
            ("truth_detector_v2", "TruthDetectorEngineV2"),
            ("insight_distiller_v2", "InsightDistillerEngineV2"),
            ("narrative_prism_v2", "NarrativePrismEngineV2"),
            ("atomic_designer_v2", "AtomicDesignerEngineV2"),
            ("visual_encoder_v2", "VisualEncoderEngineV2"),
            ("hifi_imager_v2", "HiFiImagerEngineV2")
        ]
        
        success_count = 0
        
        for engine_name, engine_class_name in engine_configs:
            try:
                # 基础引擎名（去掉_v2后缀）
                base_engine_name = engine_name.replace("_v2", "")
                
                # 检查引擎是否启用
                if not get_config_value(f"engines.{base_engine_name}.enabled", True):
                    self.logger.info(f"⏭️ {base_engine_name} 引擎已禁用，跳过")
                    continue
                
                # 动态导入引擎
                module_path = f"modules.engines.{engine_name}"
                engine_module = __import__(module_path, fromlist=[engine_class_name])
                engine_class = getattr(engine_module, engine_class_name)
                
                # 实例化引擎
                self.engines[base_engine_name] = engine_class(self.llm)
                success_count += 1
                
                self.logger.info(f"✓ {base_engine_name} 引擎V2初始化成功")
                
            except Exception as e:
                self.logger.error(f"✗ {engine_name} 引擎初始化失败: {str(e)}")
                
                # 根据配置决定是否继续
                fail_fast = get_config_value("error_handling.fail_fast", False)
                if fail_fast:
                    raise WorkflowException(
                        f"引擎初始化失败: {engine_name}",
                        ErrorCode.ENGINE_INIT_FAILED,
                        context={"failed_engine": engine_name, "error": str(e)},
                        cause=e
                    )
        
        self.logger.info(f"🎯 引擎初始化完成: {success_count}/8 个引擎加载成功")
        
        if success_count == 0:
            raise SystemException(
                "没有任何引擎初始化成功",
                ErrorCode.SYSTEM_INIT_FAILED
            )
    
    async def execute_workflow(self, topic: str, **kwargs) -> Dict[str, Any]:
        """执行完整工作流"""
        self.logger.info(f"🎬 开始执行RedCube AI工作流 - 主题: {topic}")
        
        # 创建执行上下文
        context = {
            "topic": topic,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "force_regenerate": kwargs.get("force_regenerate", False),
            "enable_git": kwargs.get("enable_git", get_config_value("git.auto_commit", True)),
            "parallel_execution": kwargs.get("parallel_execution", get_config_value("workflow.parallel_engines", False))
        }
        
        try:
            # 工作流开始检查点
            if context["enable_git"]:
                commit_checkpoint(f"开始工作流 - {topic}")
            
            # 执行引擎阶段
            if context["parallel_execution"]:
                results = await self._execute_parallel_workflow(context)
            else:
                results = await self._execute_sequential_workflow(context)
            
            # 构建最终结果
            final_result = self._build_final_result(topic, context, results)
            
            # 保存工作流结果
            self._save_workflow_result(topic, final_result)
            
            # 最终提交
            if context["enable_git"]:
                final_commit = self.git_auto.auto_commit(
                    f"完成完整工作流 - {topic}", "feat"
                )
                if final_commit["success"]:
                    final_result["final_commit"] = final_commit["commit_hash"]
            
            self.logger.info("🎉 RedCube AI工作流执行完成")
            return final_result
            
        except Exception as e:
            self.logger.error(f"工作流执行失败: {str(e)}")
            error_result = self.exception_handler.handle_exception(e)
            
            # 返回错误结果
            return {
                "success": False,
                "topic": topic,
                "error": error_result,
                "partial_results": context.get("partial_results", {})
            }
    
    async def _execute_sequential_workflow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """串行执行工作流"""
        topic = context["topic"]
        results = {}
        
        # 第一认知象限：战略构想
        self.logger.info("🧠 第一认知象限：战略构想阶段")
        
        # 按依赖顺序执行
        execution_order = [
            ("persona_core", "人格核心"),
            ("strategy_compass", "策略罗盘"),
            ("truth_detector", "真理探机"),
            ("insight_distiller", "洞察提炼器")
        ]
        
        for engine_name, engine_desc in execution_order:
            if engine_name in self.engines:
                results[engine_name] = await self._execute_single_engine(
                    engine_name, engine_desc, context, results
                )
        
        # 战略阶段检查点
        if context["enable_git"]:
            commit_checkpoint(f"完成战略构想阶段 - {topic}")
        
        # 第二认知象限：叙事表达
        self.logger.info("🎨 第二认知象限：叙事表达阶段")
        
        execution_order = [
            ("narrative_prism", "叙事棱镜"),
            ("atomic_designer", "原子设计师"),
            ("visual_encoder", "视觉编码器"),
            ("hifi_imager", "高保真成像仪")
        ]
        
        for engine_name, engine_desc in execution_order:
            if engine_name in self.engines:
                results[engine_name] = await self._execute_single_engine(
                    engine_name, engine_desc, context, results
                )
        
        return results
    
    async def _execute_parallel_workflow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """并行执行工作流（未来实现）"""
        # 目前回退到串行执行
        self.logger.info("并行执行模式尚未实现，回退到串行模式")
        return await self._execute_sequential_workflow(context)
    
    async def _execute_single_engine(self, engine_name: str, engine_desc: str,
                                   context: Dict[str, Any], 
                                   previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个引擎"""
        self.logger.info(f"🔧 执行{engine_desc}引擎...")
        
        engine = self.engines[engine_name]
        
        # 准备引擎输入
        engine_context = context.copy()
        engine_context.update(previous_results)
        
        # 执行引擎
        result = await engine.execute_with_recovery(engine_context)
        
        return result
    
    def _build_final_result(self, topic: str, context: Dict[str, Any], 
                           results: Dict[str, Any]) -> Dict[str, Any]:
        """构建最终结果"""
        successful_engines = sum(1 for result in results.values() 
                               if result.get("success", True))
        
        return {
            "workflow": "redcube_ai_v2",
            "version": "2.0.0",
            "topic": topic,
            "timestamp": context["timestamp"],
            "execution_summary": {
                "total_engines": len(self.engines),
                "successful_engines": successful_engines,
                "success_rate": successful_engines / len(self.engines) if self.engines else 0,
                "enable_git": context["enable_git"],
                "parallel_execution": context["parallel_execution"]
            },
            "results": results,
            "success": successful_engines > 0
        }
    
    def _save_workflow_result(self, topic: str, result: Dict[str, Any]):
        """保存工作流结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(get_config_value("paths.output_dir", "output"))
        workflow_dir = output_dir / f"redcube_{topic}_{timestamp}"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        result_file = workflow_dir / "redcube_workflow_result.json"
        import json
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"📁 工作流结果已保存: {result_file}")

# 便捷函数
def create_redcube_workflow(api_key: Optional[str] = None, 
                           model_name: Optional[str] = None) -> RedCubeWorkflow:
    """创建RedCube工作流实例"""
    return RedCubeWorkflow(api_key, model_name) 