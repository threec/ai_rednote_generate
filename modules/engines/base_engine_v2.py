"""
引擎基类 V2.0 - 完全重构版
整合配置管理、异常处理、输出管理等核心组件

这是新引擎的标准模板，所有引擎都应该继承这个基类
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

# 核心组件
from modules.core.config import get_config_value
from modules.core.exceptions import EngineException, ErrorCode
from modules.core.output import UnifiedOutput, ContentType, OutputFormat
from modules.langchain_workflow import BaseWorkflowEngine

class BaseEngineV2(BaseWorkflowEngine):
    """引擎基类 V2.0"""
    
    def __init__(self, llm, **kwargs):
        super().__init__(llm, **kwargs)
        
        # 引擎特定配置
        self.engine_config = self._load_engine_config()
        self.ai_config = self._load_ai_config()
        
        # 初始化AI链
        self.processing_chain = None
        self._setup_processing_chain()
    
    def _load_engine_config(self) -> Dict[str, Any]:
        """加载引擎特定配置"""
        return {
            "enabled": get_config_value(f"engines.{self.engine_name}.enabled", True),
            "cache_ttl": get_config_value(f"engines.{self.engine_name}.cache_ttl", 
                                        get_config_value("workflow.cache_ttl", 3600)),
            "retry_attempts": get_config_value(f"engines.{self.engine_name}.retry_attempts",
                                             get_config_value("error_handling.max_retries", 3)),
            "timeout": get_config_value(f"engines.{self.engine_name}.timeout",
                                      get_config_value("ai.timeout", 30))
        }
    
    def _load_ai_config(self) -> Dict[str, Any]:
        """加载AI模型配置"""
        return {
            "temperature": get_config_value("ai.temperature", 0.7),
            "max_tokens": get_config_value("ai.max_tokens", 2048),
            "timeout": get_config_value("ai.timeout", 30)
        }
    
    @abstractmethod
    def _setup_processing_chain(self):
        """设置处理链 - 子类必须实现"""
        pass
    
    @abstractmethod
    def get_content_type(self) -> ContentType:
        """获取内容类型 - 子类必须实现"""
        pass
    
    @abstractmethod
    def get_expected_output_format(self) -> OutputFormat:
        """获取期望的输出格式 - 子类必须实现"""
        pass
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """统一的执行入口"""
        topic = inputs.get("topic", "")
        force_regenerate = inputs.get("force_regenerate", False)
        
        self.logger.info(f"🎭 {self.engine_name} 引擎启动 - 主题: {topic}")
        
        # 检查缓存
        if not force_regenerate:
            cached_output = self.load_cache(topic)
            if cached_output:
                self.logger.info("✓ 使用缓存结果")
                return cached_output.to_dict()
        
        try:
            # 执行核心处理
            result_content = await self._process_content(inputs)
            
            # 创建统一输出
            output = self.create_output(topic, self.get_content_type())
            output.set_content(result_content, self.get_expected_output_format())
            
            # 设置元数据
            output.set_metadata(
                engine_version="2.0",
                execution_status="success",
                processing_time=None,  # 可以添加实际时间测量
                config_used=self.engine_config
            )
            
            # 后处理
            await self._post_process(output, inputs)
            
            # 验证输出
            output.validate()
            
            # 保存缓存
            self.save_cache(output)
            
            self.logger.info(f"✓ {self.engine_name} 引擎执行成功")
            return output.to_dict()
            
        except Exception as e:
            self.logger.error(f"❌ {self.engine_name} 引擎执行失败: {str(e)}")
            
            # 创建错误输出
            error_output = self._create_error_output(topic, e)
            return error_output.to_dict()
    
    @abstractmethod
    async def _process_content(self, inputs: Dict[str, Any]) -> Any:
        """处理内容 - 子类必须实现"""
        pass
    
    async def _post_process(self, output: UnifiedOutput, inputs: Dict[str, Any]):
        """后处理 - 子类可重写"""
        pass
    
    def _create_error_output(self, topic: str, error: Exception) -> UnifiedOutput:
        """创建错误输出"""
        output = self.create_output(topic, ContentType.REPORT)
        
        error_content = f"""# {self.engine_name} 引擎执行失败

## 错误信息
{str(error)}

## 错误类型
{type(error).__name__}

## 建议
- 检查输入参数是否正确
- 确认网络连接正常
- 查看详细日志获取更多信息
"""
        
        output.set_content(error_content, OutputFormat.MARKDOWN)
        output.set_metadata(
            execution_status="failed",
            error_type=type(error).__name__,
            error_message=str(error)
        )
        
        return output
    
    def _create_prompt_template(self, system_prompt: str, user_template: str) -> ChatPromptTemplate:
        """创建提示词模板的辅助方法"""
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_template)
        ])
    
    def _create_processing_chain(self, prompt_template: ChatPromptTemplate):
        """创建处理链的辅助方法"""
        return (
            prompt_template
            | self.llm
            | StrOutputParser()
        )
    
    async def _invoke_chain_with_timeout(self, chain_inputs: Dict[str, Any]) -> str:
        """带超时的链调用"""
        timeout = self.ai_config["timeout"]
        
        try:
            result = await asyncio.wait_for(
                self.processing_chain.ainvoke(chain_inputs),
                timeout=timeout
            )
            return result
            
        except asyncio.TimeoutError:
            raise EngineException(
                self.engine_name,
                f"AI处理超时（{timeout}秒）",
                ErrorCode.API_REQUEST_FAILED,
                context={"timeout": timeout, "inputs": chain_inputs}
            )
    
    def get_engine_info(self) -> Dict[str, Any]:
        """获取引擎信息"""
        return {
            "name": self.engine_name,
            "version": "2.0",
            "enabled": self.engine_config["enabled"],
            "content_type": self.get_content_type().value,
            "output_format": self.get_expected_output_format().value,
            "config": self.engine_config,
            "cache_enabled": self.cache_enabled
        }

class TextReportEngine(BaseEngineV2):
    """文本报告类引擎基类"""
    
    def get_content_type(self) -> ContentType:
        return ContentType.REPORT
    
    def get_expected_output_format(self) -> OutputFormat:
        return OutputFormat.TEXT

class AnalysisEngine(BaseEngineV2):
    """分析类引擎基类"""
    
    def get_content_type(self) -> ContentType:
        return ContentType.ANALYSIS
    
    def get_expected_output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

class StrategyEngine(BaseEngineV2):
    """策略类引擎基类"""
    
    def get_content_type(self) -> ContentType:
        return ContentType.STRATEGY
    
    def get_expected_output_format(self) -> OutputFormat:
        return OutputFormat.HYBRID

class TechnicalEngine(BaseEngineV2):
    """技术类引擎基类"""
    
    def get_content_type(self) -> ContentType:
        return ContentType.TECHNICAL
    
    def get_expected_output_format(self) -> OutputFormat:
        return OutputFormat.JSON 