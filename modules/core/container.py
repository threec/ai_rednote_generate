"""
依赖注入容器
管理组件和服务的依赖关系，实现松耦合架构

功能特点：
1. 自动依赖解析
2. 单例和多例模式
3. 循环依赖检测
4. 生命周期管理
5. 配置驱动的依赖注册
"""

from typing import Dict, Any, Type, Callable, Optional, List, Set
from abc import ABC, abstractmethod
from enum import Enum
import inspect
from functools import wraps

class ServiceLifetime(Enum):
    """服务生命周期"""
    SINGLETON = "singleton"  # 单例
    TRANSIENT = "transient"  # 瞬时
    SCOPED = "scoped"       # 作用域

class ServiceDescriptor:
    """服务描述符"""
    
    def __init__(self, 
                 service_type: Type,
                 implementation: Optional[Type] = None,
                 factory: Optional[Callable] = None,
                 instance: Optional[Any] = None,
                 lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
                 dependencies: Optional[List[str]] = None):
        self.service_type = service_type
        self.implementation = implementation or service_type
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime
        self.dependencies = dependencies or []
        self.created_instance = None

class DependencyContainer:
    """依赖注入容器"""
    
    def __init__(self):
        self.services: Dict[str, ServiceDescriptor] = {}
        self.scoped_instances: Dict[str, Any] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.creation_stack: List[str] = []
    
    def register_singleton(self, service_type: Type, 
                          implementation: Optional[Type] = None,
                          factory: Optional[Callable] = None,
                          instance: Optional[Any] = None,
                          dependencies: Optional[List[str]] = None) -> 'DependencyContainer':
        """注册单例服务"""
        return self._register_service(
            service_type, implementation, factory, instance,
            ServiceLifetime.SINGLETON, dependencies
        )
    
    def register_transient(self, service_type: Type,
                          implementation: Optional[Type] = None,
                          factory: Optional[Callable] = None,
                          dependencies: Optional[List[str]] = None) -> 'DependencyContainer':
        """注册瞬时服务"""
        return self._register_service(
            service_type, implementation, factory, None,
            ServiceLifetime.TRANSIENT, dependencies
        )
    
    def register_scoped(self, service_type: Type,
                       implementation: Optional[Type] = None,
                       factory: Optional[Callable] = None,
                       dependencies: Optional[List[str]] = None) -> 'DependencyContainer':
        """注册作用域服务"""
        return self._register_service(
            service_type, implementation, factory, None,
            ServiceLifetime.SCOPED, dependencies
        )
    
    def _register_service(self, service_type: Type,
                         implementation: Optional[Type],
                         factory: Optional[Callable],
                         instance: Optional[Any],
                         lifetime: ServiceLifetime,
                         dependencies: Optional[List[str]]) -> 'DependencyContainer':
        """注册服务"""
        service_name = self._get_service_name(service_type)
        
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            factory=factory,
            instance=instance,
            lifetime=lifetime,
            dependencies=dependencies or []
        )
        
        self.services[service_name] = descriptor
        
        # 更新依赖图
        self.dependency_graph[service_name] = set(dependencies or [])
        
        # 检查循环依赖
        self._check_circular_dependencies()
        
        return self
    
    def resolve(self, service_type: Type) -> Any:
        """解析服务"""
        service_name = self._get_service_name(service_type)
        return self._resolve_service(service_name)
    
    def _resolve_service(self, service_name: str) -> Any:
        """解析服务实现"""
        
        # 检查是否已在创建栈中（循环依赖检测）
        if service_name in self.creation_stack:
            raise RuntimeError(f"检测到循环依赖: {' -> '.join(self.creation_stack)} -> {service_name}")
        
        if service_name not in self.services:
            raise ValueError(f"服务未注册: {service_name}")
        
        descriptor = self.services[service_name]
        
        # 单例模式检查
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if descriptor.instance is not None:
                return descriptor.instance
            if descriptor.created_instance is not None:
                return descriptor.created_instance
        
        # 作用域模式检查
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if service_name in self.scoped_instances:
                return self.scoped_instances[service_name]
        
        # 创建实例
        self.creation_stack.append(service_name)
        try:
            instance = self._create_instance(descriptor)
            
            # 保存实例
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                descriptor.created_instance = instance
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                self.scoped_instances[service_name] = instance
            
            return instance
            
        finally:
            self.creation_stack.pop()
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """创建服务实例"""
        
        # 如果有预设实例
        if descriptor.instance is not None:
            return descriptor.instance
        
        # 如果有工厂方法
        if descriptor.factory is not None:
            dependencies = self._resolve_dependencies(descriptor.dependencies)
            return descriptor.factory(**dependencies)
        
        # 使用构造函数创建
        return self._create_from_constructor(descriptor)
    
    def _create_from_constructor(self, descriptor: ServiceDescriptor) -> Any:
        """从构造函数创建实例"""
        constructor = descriptor.implementation
        
        # 获取构造函数签名
        sig = inspect.signature(constructor.__init__)
        
        # 解析构造函数参数
        args = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # 尝试从依赖中解析
            if param_name in descriptor.dependencies:
                args[param_name] = self._resolve_service(param_name)
            elif param.annotation != inspect.Parameter.empty:
                # 尝试从类型注解解析
                try:
                    args[param_name] = self.resolve(param.annotation)
                except (ValueError, RuntimeError):
                    # 如果有默认值则使用默认值
                    if param.default != inspect.Parameter.empty:
                        args[param_name] = param.default
                    else:
                        raise ValueError(f"无法解析参数 {param_name} 的依赖")
        
        return constructor(**args)
    
    def _resolve_dependencies(self, dependencies: List[str]) -> Dict[str, Any]:
        """解析依赖列表"""
        resolved = {}
        for dep_name in dependencies:
            resolved[dep_name] = self._resolve_service(dep_name)
        return resolved
    
    def _get_service_name(self, service_type: Type) -> str:
        """获取服务名称"""
        if hasattr(service_type, '__name__'):
            return service_type.__name__
        return str(service_type)
    
    def _check_circular_dependencies(self):
        """检查循环依赖"""
        
        def dfs(node: str, visited: Set[str], path: Set[str]):
            if node in path:
                raise RuntimeError(f"检测到循环依赖: {node}")
            
            if node in visited:
                return
            
            visited.add(node)
            path.add(node)
            
            for dep in self.dependency_graph.get(node, []):
                dfs(dep, visited, path)
            
            path.remove(node)
        
        visited = set()
        for service_name in self.dependency_graph:
            if service_name not in visited:
                dfs(service_name, visited, set())
    
    def get_dependency_order(self) -> List[str]:
        """获取依赖顺序（拓扑排序）"""
        # 计算入度
        in_degree = {node: 0 for node in self.dependency_graph}
        for node in self.dependency_graph:
            for dep in self.dependency_graph[node]:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # 拓扑排序
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for dep in self.dependency_graph.get(node, []):
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)
        
        return result
    
    def clear_scoped(self):
        """清空作用域实例"""
        self.scoped_instances.clear()
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "total_services": len(self.services),
            "by_lifetime": {
                lifetime.value: sum(1 for desc in self.services.values() 
                                  if desc.lifetime == lifetime)
                for lifetime in ServiceLifetime
            },
            "dependency_graph": {
                name: list(deps) for name, deps in self.dependency_graph.items()
            },
            "services": {
                name: {
                    "type": desc.service_type.__name__,
                    "implementation": desc.implementation.__name__,
                    "lifetime": desc.lifetime.value,
                    "dependencies": desc.dependencies,
                    "has_instance": desc.created_instance is not None or desc.instance is not None
                }
                for name, desc in self.services.items()
            }
        }

    def cleanup(self):
        """清理容器"""
        for service_name, config in self.services.items():
            if config.get("cleanup_method"):
                instance = self.scoped_instances.get(service_name)
                if instance:
                    try:
                        cleanup_method = getattr(instance, config["cleanup_method"])
                        cleanup_method()
                    except Exception as e:
                        print(f"清理服务 {service_name} 失败: {e}")
        
        self.scoped_instances.clear()
        print("依赖注入容器已清理")
    
    def get_container_info(self) -> Dict[str, Any]:
        """获取容器信息"""
        return {
            "total_services": len(self.services),
            "active_instances": len(self.scoped_instances),
            "registered_services": list(self.services.keys()),
            "dependency_graph": self._get_dependency_graph(),
            "lifecycle_status": {
                service: "active" if service in self.scoped_instances else "registered"
                for service in self.services.keys()
            }
        }
    
    def _get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取依赖关系图"""
        graph = {}
        for service_name, config in self.services.items():
            dependencies = config.dependencies
            graph[service_name] = dependencies
        return graph

class EngineContainer(DependencyContainer):
    """引擎专用依赖容器"""
    
    def __init__(self):
        super().__init__()
        self._setup_default_services()
    
    def _setup_default_services(self):
        """设置默认服务"""
        # 注册配置服务
        from modules.core.config import get_config
        self.register_singleton(
            type(get_config()),
            factory=lambda: get_config()
        )
        
        # 注册日志服务
        from modules.utils import get_logger
        self.register_singleton(
            type(get_logger("engine")),
            factory=lambda: get_logger("engine")
        )
    
    def register_engine(self, engine_class: Type, dependencies: Optional[List[str]] = None):
        """注册引擎"""
        engine_name = engine_class.__name__.lower().replace("engine", "")
        
        # 自动检测依赖（基于构造函数参数）
        if dependencies is None:
            dependencies = self._auto_detect_dependencies(engine_class)
        
        return self.register_singleton(
            engine_class,
            dependencies=dependencies
        )
    
    def _auto_detect_dependencies(self, engine_class: Type) -> List[str]:
        """自动检测引擎依赖"""
        dependencies = []
        
        try:
            sig = inspect.signature(engine_class.__init__)
            for param_name, param in sig.parameters.items():
                if param_name in ['self', 'llm']:
                    continue
                
                # 如果参数类型是已注册的服务，则添加为依赖
                if param.annotation != inspect.Parameter.empty:
                    service_name = self._get_service_name(param.annotation)
                    if service_name in self.services:
                        dependencies.append(service_name)
        
        except Exception:
            pass  # 自动检测失败，返回空依赖列表
        
        return dependencies
    
    def create_workflow(self, workflow_class: Type):
        """创建工作流实例"""
        return self.resolve(workflow_class)

# 全局容器实例
_engine_container = None

def get_engine_container() -> EngineContainer:
    """获取全局引擎容器"""
    global _engine_container
    if _engine_container is None:
        _engine_container = EngineContainer()
    return _engine_container

def register_engine(engine_class: Type, dependencies: Optional[List[str]] = None):
    """注册引擎的便捷函数"""
    return get_engine_container().register_engine(engine_class, dependencies)

def resolve_engine(engine_class: Type):
    """解析引擎的便捷函数"""
    return get_engine_container().resolve(engine_class) 