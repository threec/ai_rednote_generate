"""
统一配置管理系统
整合所有分散的配置项，提供统一的配置接口

功能特点：
1. 统一的配置加载和管理
2. 环境变量支持
3. 配置验证和类型检查
4. 热更新支持
5. 配置继承和覆盖
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

class ConfigSource(Enum):
    """配置来源"""
    DEFAULT = "default"
    FILE = "file"
    ENV = "environment"
    OVERRIDE = "override"

@dataclass
class ConfigItem:
    """配置项"""
    key: str
    value: Any
    source: ConfigSource
    required: bool = False
    description: str = ""
    type_hint: type = str

class SystemConfig:
    """系统配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config.yaml"
        self.config_data = {}
        self.config_sources = {}
        self.validators = {}
        
        # 初始化默认配置
        self._init_default_config()
        
        # 加载配置
        self.load_config()
        
        # 验证配置
        self.validate_config()
    
    def _init_default_config(self):
        """初始化默认配置"""
        
        # 系统基础配置
        self.set_default("system.name", "ai_rednote_generate")
        self.set_default("system.version", "2.0.0")
        self.set_default("system.debug", False)
        self.set_default("system.log_level", "INFO")
        
        # 目录配置
        self.set_default("paths.cache_dir", "cache")
        self.set_default("paths.output_dir", "output")
        self.set_default("paths.logs_dir", "logs")
        self.set_default("paths.templates_dir", "templates")
        
        # AI模型配置
        self.set_default("ai.model_name", "gemini-pro")
        self.set_default("ai.temperature", 0.7)
        self.set_default("ai.max_tokens", 2048)
        self.set_default("ai.retry_attempts", 3)
        self.set_default("ai.timeout", 30)
        
        # 工作流配置
        self.set_default("workflow.enable_cache", True)
        self.set_default("workflow.cache_ttl", 3600)
        self.set_default("workflow.parallel_engines", False)
        self.set_default("workflow.max_concurrent", 4)
        
        # 引擎配置
        self.set_default("engines.persona_core.enabled", True)
        self.set_default("engines.strategy_compass.enabled", True)
        self.set_default("engines.truth_detector.enabled", True)
        self.set_default("engines.insight_distiller.enabled", True)
        self.set_default("engines.narrative_prism.enabled", True)
        self.set_default("engines.atomic_designer.enabled", True)
        self.set_default("engines.visual_encoder.enabled", True)
        self.set_default("engines.hifi_imager.enabled", True)
        
        # Git自动化配置
        self.set_default("git.auto_commit", True)
        self.set_default("git.commit_on_engine_complete", True)
        self.set_default("git.commit_on_major_changes", True)
        self.set_default("git.commit_on_bug_fixes", True)
        self.set_default("git.max_files_per_commit", 20)
        
        # 输出配置
        self.set_default("output.format", "auto")  # auto, json, text, hybrid
        self.set_default("output.quality", "high")
        self.set_default("output.compression", False)
        
        # 错误处理配置
        self.set_default("error_handling.max_retries", 3)
        self.set_default("error_handling.retry_delay", 1.0)
        self.set_default("error_handling.fail_fast", False)
        self.set_default("error_handling.save_error_logs", True)
        
        # 性能配置
        self.set_default("performance.enable_profiling", False)
        self.set_default("performance.memory_limit", "2GB")
        self.set_default("performance.execution_timeout", 300)
        
        # 安全配置
        self.set_default("security.api_key_encryption", False)
        self.set_default("security.output_sanitization", True)
        self.set_default("security.rate_limiting", True)
    
    def set_default(self, key: str, value: Any, description: str = ""):
        """设置默认配置项"""
        self.config_data[key] = ConfigItem(
            key=key,
            value=value,
            source=ConfigSource.DEFAULT,
            description=description
        )
    
    def load_config(self):
        """加载配置文件"""
        
        # 1. 从文件加载
        self._load_from_file()
        
        # 2. 从环境变量加载
        self._load_from_env()
        
        # 3. 从命令行参数加载（如果需要）
        # self._load_from_args()
    
    def _load_from_file(self):
        """从配置文件加载"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            # 创建默认配置文件
            self._create_default_config_file()
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.yaml':
                    file_config = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    file_config = json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
            
            # 扁平化配置并更新
            flat_config = self._flatten_dict(file_config)
            for key, value in flat_config.items():
                if key in self.config_data:
                    self.config_data[key].value = value
                    self.config_data[key].source = ConfigSource.FILE
                else:
                    self.config_data[key] = ConfigItem(
                        key=key,
                        value=value,
                        source=ConfigSource.FILE
                    )
                    
        except Exception as e:
            print(f"警告: 配置文件加载失败: {e}")
    
    def _load_from_env(self):
        """从环境变量加载"""
        env_prefix = "REDCUBE_"
        
        for key, config_item in self.config_data.items():
            env_key = f"{env_prefix}{key.upper().replace('.', '_')}"
            env_value = os.environ.get(env_key)
            
            if env_value is not None:
                # 类型转换
                try:
                    if isinstance(config_item.value, bool):
                        env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif isinstance(config_item.value, int):
                        env_value = int(env_value)
                    elif isinstance(config_item.value, float):
                        env_value = float(env_value)
                    elif isinstance(config_item.value, list):
                        env_value = env_value.split(',')
                    
                    config_item.value = env_value
                    config_item.source = ConfigSource.ENV
                    
                except ValueError as e:
                    print(f"警告: 环境变量 {env_key} 类型转换失败: {e}")
    
    def _create_default_config_file(self):
        """创建默认配置文件"""
        config_dict = {}
        
        for key, config_item in self.config_data.items():
            self._set_nested_dict(config_dict, key, config_item.value)
        
        config_path = Path(self.config_file)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
        
        print(f"创建默认配置文件: {config_path}")
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """扁平化嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _set_nested_dict(self, d: Dict[str, Any], key: str, value: Any):
        """设置嵌套字典的值"""
        keys = key.split('.')
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        config_item = self.config_data.get(key)
        if config_item:
            return config_item.value
        return default
    
    def set(self, key: str, value: Any, source: ConfigSource = ConfigSource.OVERRIDE):
        """设置配置值"""
        if key in self.config_data:
            self.config_data[key].value = value
            self.config_data[key].source = source
        else:
            self.config_data[key] = ConfigItem(
                key=key,
                value=value,
                source=source
            )
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置段"""
        result = {}
        prefix = f"{section}."
        
        for key, config_item in self.config_data.items():
            if key.startswith(prefix):
                sub_key = key[len(prefix):]
                result[sub_key] = config_item.value
        
        return result
    
    def validate_config(self):
        """验证配置"""
        errors = []
        
        # 检查必需的配置项
        required_keys = [
            "system.name",
            "ai.model_name",
            "paths.cache_dir",
            "paths.output_dir"
        ]
        
        for key in required_keys:
            if key not in self.config_data or self.config_data[key].value is None:
                errors.append(f"必需的配置项缺失: {key}")
        
        # 检查API密钥（测试模式下跳过）
        if not os.environ.get("REDCUBE_TEST_MODE"):
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                errors.append("缺少 GOOGLE_API_KEY 环境变量")
        
        # 检查目录是否存在
        paths_to_check = ["paths.cache_dir", "paths.output_dir", "paths.logs_dir"]
        for path_key in paths_to_check:
            if path_key in self.config_data:
                path_value = self.config_data[path_key].value
                path_obj = Path(path_value)
                if not path_obj.exists():
                    path_obj.mkdir(parents=True, exist_ok=True)
        
        if errors:
            raise ValueError("配置验证失败:\n" + "\n".join(errors))
    
    def reload_config(self):
        """重新加载配置"""
        self.load_config()
        self.validate_config()
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            "total_configs": len(self.config_data),
            "sources": {
                source.value: sum(1 for item in self.config_data.values() 
                                 if item.source == source)
                for source in ConfigSource
            },
            "config_file": self.config_file,
            "file_exists": Path(self.config_file).exists()
        }
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置项"""
        return {key: item.value for key, item in self.config_data.items()}
    
    def export_config(self, output_file: str):
        """导出配置到文件"""
        config_dict = {}
        
        for key, config_item in self.config_data.items():
            self._set_nested_dict(config_dict, key, config_item.value)
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            if output_path.suffix.lower() == '.yaml':
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            elif output_path.suffix.lower() == '.json':
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"不支持的输出格式: {output_path.suffix}")

# 全局配置实例
_system_config = None

def get_config() -> SystemConfig:
    """获取全局配置实例"""
    global _system_config
    if _system_config is None:
        _system_config = SystemConfig()
    return _system_config

def reload_config():
    """重新加载全局配置"""
    global _system_config
    if _system_config:
        _system_config.reload_config()

# 便捷函数
def get_config_value(key: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    return get_config().get(key, default)

def set_config_value(key: str, value: Any):
    """设置配置值的便捷函数"""
    get_config().set(key, value)

def initialize_config(config_file: Optional[str] = None) -> SystemConfig:
    """初始化配置系统的便捷函数"""
    global _system_config
    _system_config = SystemConfig(config_file)
    return _system_config

def get_all_config() -> Dict[str, Any]:
    """获取所有配置项的便捷函数"""
    config = get_config()
    return {key: item.value for key, item in config.config_data.items()}

# SystemConfig类的get_all_config方法通过实例方法提供 