"""
统一异常处理框架
提供系统级的异常分类和处理机制

功能特点：
1. 分层异常体系
2. 错误码和错误消息
3. 异常链追踪
4. 自动错误恢复
5. 详细的错误上下文
"""

from typing import Any, Dict, Optional, List, Union
from enum import Enum
import traceback
import json
from datetime import datetime

class ErrorLevel(Enum):
    """错误级别"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorCode(Enum):
    """错误码"""
    # 系统级错误 (1000-1999)
    SYSTEM_INIT_FAILED = 1001
    CONFIG_LOAD_FAILED = 1002
    DEPENDENCY_MISSING = 1003
    RESOURCE_EXHAUSTED = 1004
    
    # 工作流错误 (2000-2999)
    WORKFLOW_INIT_FAILED = 2001
    WORKFLOW_EXECUTION_FAILED = 2002
    ENGINE_NOT_FOUND = 2003
    ENGINE_INIT_FAILED = 2004
    ENGINE_EXECUTION_FAILED = 2005
    
    # AI模型错误 (3000-3999)
    API_KEY_MISSING = 3001
    API_REQUEST_FAILED = 3002
    MODEL_NOT_SUPPORTED = 3003
    TOKEN_LIMIT_EXCEEDED = 3004
    RATE_LIMIT_EXCEEDED = 3005
    
    # 数据处理错误 (4000-4999)
    DATA_VALIDATION_FAILED = 4001
    DATA_PARSING_FAILED = 4002
    DATA_SERIALIZATION_FAILED = 4003
    CACHE_OPERATION_FAILED = 4004
    
    # 文件操作错误 (5000-5999)
    FILE_NOT_FOUND = 5001
    FILE_PERMISSION_DENIED = 5002
    FILE_CORRUPTED = 5003
    DISK_SPACE_INSUFFICIENT = 5004
    
    # Git操作错误 (6000-6999)
    GIT_REPOSITORY_NOT_FOUND = 6001
    GIT_COMMAND_FAILED = 6002
    GIT_MERGE_CONFLICT = 6003
    GIT_AUTHENTICATION_FAILED = 6004
    
    # 网络错误 (7000-7999)
    NETWORK_TIMEOUT = 7001
    NETWORK_CONNECTION_FAILED = 7002
    NETWORK_AUTHENTICATION_FAILED = 7003
    
    # 业务逻辑错误 (8000-8999)
    INVALID_INPUT = 8001
    BUSINESS_RULE_VIOLATION = 8002
    OPERATION_NOT_ALLOWED = 8003
    
    # 未知错误 (9000-9999)
    UNKNOWN_ERROR = 9000

class BaseWorkflowException(Exception):
    """工作流基础异常类"""
    
    def __init__(self, 
                 message: str,
                 error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
                 level: ErrorLevel = ErrorLevel.ERROR,
                 context: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.level = level
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.now()
        self.traceback_info = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code.value,
            "error_name": self.error_code.name,
            "level": self.level.value,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback_info,
            "cause": str(self.cause) if self.cause else None
        }
    
    def to_json(self) -> str:
        """转换为JSON格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

class SystemException(BaseWorkflowException):
    """系统级异常"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.SYSTEM_INIT_FAILED, **kwargs):
        super().__init__(message, error_code, ErrorLevel.CRITICAL, **kwargs)

class WorkflowException(BaseWorkflowException):
    """工作流异常"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.WORKFLOW_EXECUTION_FAILED, **kwargs):
        super().__init__(message, error_code, ErrorLevel.ERROR, **kwargs)

class EngineException(BaseWorkflowException):
    """引擎异常"""
    
    def __init__(self, engine_name: str, message: str, 
                 error_code: ErrorCode = ErrorCode.ENGINE_EXECUTION_FAILED, **kwargs):
        context = kwargs.get('context', {})
        context['engine_name'] = engine_name
        kwargs['context'] = context
        super().__init__(message, error_code, ErrorLevel.ERROR, **kwargs)

class AIModelException(BaseWorkflowException):
    """AI模型异常"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.API_REQUEST_FAILED, **kwargs):
        super().__init__(message, error_code, ErrorLevel.ERROR, **kwargs)

class DataException(BaseWorkflowException):
    """数据处理异常"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.DATA_VALIDATION_FAILED, **kwargs):
        super().__init__(message, error_code, ErrorLevel.WARNING, **kwargs)

class FileOperationException(BaseWorkflowException):
    """文件操作异常"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.FILE_NOT_FOUND, **kwargs):
        super().__init__(message, error_code, ErrorLevel.ERROR, **kwargs)

class GitException(BaseWorkflowException):
    """Git操作异常"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.GIT_COMMAND_FAILED, **kwargs):
        super().__init__(message, error_code, ErrorLevel.WARNING, **kwargs)

class NetworkException(BaseWorkflowException):
    """网络异常"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.NETWORK_CONNECTION_FAILED, **kwargs):
        super().__init__(message, error_code, ErrorLevel.ERROR, **kwargs)

class BusinessException(BaseWorkflowException):
    """业务逻辑异常"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.BUSINESS_RULE_VIOLATION, **kwargs):
        super().__init__(message, error_code, ErrorLevel.WARNING, **kwargs)

class ExceptionHandler:
    """异常处理器"""
    
    def __init__(self):
        self.handlers = {}
        self.error_logs = []
        self.recovery_strategies = {}
        
        # 注册默认处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认异常处理器"""
        
        # 系统级异常处理
        self.register_handler(SystemException, self._handle_system_exception)
        
        # 工作流异常处理
        self.register_handler(WorkflowException, self._handle_workflow_exception)
        
        # 引擎异常处理
        self.register_handler(EngineException, self._handle_engine_exception)
        
        # AI模型异常处理
        self.register_handler(AIModelException, self._handle_ai_model_exception)
        
        # 数据异常处理
        self.register_handler(DataException, self._handle_data_exception)
    
    def register_handler(self, exception_type: type, handler_func):
        """注册异常处理器"""
        self.handlers[exception_type] = handler_func
    
    def register_recovery_strategy(self, error_code: ErrorCode, strategy_func):
        """注册恢复策略"""
        self.recovery_strategies[error_code] = strategy_func
    
    def handle_exception(self, exception: Exception) -> Dict[str, Any]:
        """处理异常"""
        
        # 记录异常
        self._log_exception(exception)
        
        # 查找处理器
        handler = None
        for exc_type, handler_func in self.handlers.items():
            if isinstance(exception, exc_type):
                handler = handler_func
                break
        
        if handler:
            return handler(exception)
        else:
            return self._handle_unknown_exception(exception)
    
    def _log_exception(self, exception: Exception):
        """记录异常"""
        if isinstance(exception, BaseWorkflowException):
            self.error_logs.append(exception.to_dict())
        else:
            self.error_logs.append({
                "error_code": ErrorCode.UNKNOWN_ERROR.value,
                "level": ErrorLevel.ERROR.value,
                "message": str(exception),
                "timestamp": datetime.now().isoformat(),
                "traceback": traceback.format_exc()
            })
    
    def _handle_system_exception(self, exception: SystemException) -> Dict[str, Any]:
        """处理系统异常"""
        return {
            "success": False,
            "error": exception.to_dict(),
            "recovery_action": "restart_system",
            "should_retry": False
        }
    
    def _handle_workflow_exception(self, exception: WorkflowException) -> Dict[str, Any]:
        """处理工作流异常"""
        return {
            "success": False,
            "error": exception.to_dict(),
            "recovery_action": "skip_failed_engine",
            "should_retry": True,
            "max_retries": 3
        }
    
    def _handle_engine_exception(self, exception: EngineException) -> Dict[str, Any]:
        """处理引擎异常"""
        engine_name = exception.context.get('engine_name', 'unknown')
        
        return {
            "success": False,
            "error": exception.to_dict(),
            "recovery_action": f"fallback_{engine_name}",
            "should_retry": True,
            "max_retries": 2
        }
    
    def _handle_ai_model_exception(self, exception: AIModelException) -> Dict[str, Any]:
        """处理AI模型异常"""
        
        # 检查是否是速率限制错误
        if exception.error_code == ErrorCode.RATE_LIMIT_EXCEEDED:
            return {
                "success": False,
                "error": exception.to_dict(),
                "recovery_action": "wait_and_retry",
                "should_retry": True,
                "retry_delay": 60,
                "max_retries": 5
            }
        
        return {
            "success": False,
            "error": exception.to_dict(),
            "recovery_action": "switch_model",
            "should_retry": True,
            "max_retries": 3
        }
    
    def _handle_data_exception(self, exception: DataException) -> Dict[str, Any]:
        """处理数据异常"""
        return {
            "success": False,
            "error": exception.to_dict(),
            "recovery_action": "use_default_data",
            "should_retry": False
        }
    
    def _handle_unknown_exception(self, exception: Exception) -> Dict[str, Any]:
        """处理未知异常"""
        return {
            "success": False,
            "error": {
                "error_code": ErrorCode.UNKNOWN_ERROR.value,
                "level": ErrorLevel.ERROR.value,
                "message": str(exception),
                "timestamp": datetime.now().isoformat(),
                "traceback": traceback.format_exc()
            },
            "recovery_action": "log_and_continue",
            "should_retry": False
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计"""
        if not self.error_logs:
            return {"total_errors": 0}
        
        stats = {
            "total_errors": len(self.error_logs),
            "by_level": {},
            "by_error_code": {},
            "recent_errors": self.error_logs[-5:] if len(self.error_logs) > 5 else self.error_logs
        }
        
        for error in self.error_logs:
            level = error.get("level", "UNKNOWN")
            error_code = error.get("error_code", "UNKNOWN")
            
            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1
            stats["by_error_code"][error_code] = stats["by_error_code"].get(error_code, 0) + 1
        
        return stats
    
    def clear_error_logs(self):
        """清空错误日志"""
        self.error_logs.clear()

# 全局异常处理器
_exception_handler = ExceptionHandler()

def get_exception_handler() -> ExceptionHandler:
    """获取全局异常处理器"""
    return _exception_handler

def handle_exception(exception: Exception) -> Dict[str, Any]:
    """处理异常的便捷函数"""
    return _exception_handler.handle_exception(exception)

def register_exception_handler(exception_type: type, handler_func):
    """注册异常处理器的便捷函数"""
    _exception_handler.register_handler(exception_type, handler_func)

def register_recovery_strategy(error_code: ErrorCode, strategy_func):
    """注册恢复策略的便捷函数"""
    _exception_handler.register_recovery_strategy(error_code, strategy_func) 