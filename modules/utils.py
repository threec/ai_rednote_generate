"""
小红书内容自动化管线 - 通用工具模块
Xiaohongshu Content Automation Pipeline - Utility Module

这个模块提供了项目中所有其他模块需要的通用功能，包括：
- 目录管理和创建
- 统一的日志系统配置
- 文件操作（JSON读写）
- 错误处理和异常管理

所有功能都从config.py读取配置，确保整个项目的一致性。
"""

import os
import sys
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Any, Optional, Union

# ===================================
# 配置导入处理
# ===================================

# 为了确保在不同运行环境下都能正确导入config模块，我们需要处理路径
# 这里使用多种策略来保证导入的健壮性：

# 策略1: 尝试直接导入（适用于从项目根目录运行的情况）
try:
    from config import (
        CACHE_DIR, OUTPUT_DIR, LOGS_DIR, TEMPLATES_DIR,
        LOG_CONFIG, BASE_DIR
    )
except ImportError:
    # 策略2: 如果直接导入失败，尝试添加父目录到sys.path
    current_dir = Path(__file__).parent
    parent_dir = current_dir.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    try:
        from config import (
            CACHE_DIR, OUTPUT_DIR, LOGS_DIR, TEMPLATES_DIR,
            LOG_CONFIG, BASE_DIR
        )
    except ImportError as e:
        raise ImportError(f"无法导入config模块，请确保config.py文件存在于项目根目录: {e}")

# ===================================
# 1. 目录管理功能
# ===================================

def ensure_directories() -> bool:
    """
    确保项目所需的所有目录都存在
    
    检查并创建以下目录：
    - CACHE_DIR: 缓存目录
    - OUTPUT_DIR: 输出目录
    - LOGS_DIR: 日志目录
    - TEMPLATES_DIR: 模板目录
    
    Returns:
        bool: 如果所有目录都成功创建或已存在，返回True；否则返回False
    """
    directories = [
        ("缓存目录", CACHE_DIR),
        ("输出目录", OUTPUT_DIR),
        ("日志目录", LOGS_DIR),
        ("模板目录", TEMPLATES_DIR)
    ]
    
    success = True
    
    for dir_name, dir_path in directories:
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"✓ {dir_name} 已准备就绪: {dir_path}")
        except OSError as e:
            print(f"✗ 创建{dir_name}失败: {dir_path} - {e}")
            success = False
    
    return success

def check_directory_permissions() -> Dict[str, bool]:
    """
    检查关键目录的读写权限
    
    Returns:
        Dict[str, bool]: 各目录的权限状态
    """
    directories = {
        "cache": CACHE_DIR,
        "output": OUTPUT_DIR,
        "logs": LOGS_DIR,
        "templates": TEMPLATES_DIR
    }
    
    permissions = {}
    
    for name, path in directories.items():
        try:
            # 检查目录是否可读写
            test_file = os.path.join(path, ".test_write")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            permissions[name] = True
        except (OSError, IOError):
            permissions[name] = False
    
    return permissions

# ===================================
# 2. 日志系统配置
# ===================================

def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    设置项目的统一日志系统
    
    配置同时向控制台和轮换日志文件输出的日志处理器。
    日志配置从config.py的LOG_CONFIG字典中读取。
    
    Args:
        verbose (bool): 是否启用详细日志模式
                       True: 设置为DEBUG级别
                       False: 设置为INFO级别
    
    Returns:
        logging.Logger: 配置完成的根日志记录器
    """
    # 确保日志目录存在
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # 设置日志级别
    log_level = logging.DEBUG if verbose else getattr(logging, LOG_CONFIG["level"])
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有的处理器（避免重复配置）
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建日志格式器
    formatter = logging.Formatter(
        fmt=LOG_CONFIG["format"],
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 1. 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 2. 轮换文件处理器
    try:
        # 解析文件大小配置
        max_size = LOG_CONFIG["max_size"]
        if isinstance(max_size, str):
            if max_size.endswith("MB"):
                max_bytes = int(max_size[:-2]) * 1024 * 1024
            elif max_size.endswith("KB"):
                max_bytes = int(max_size[:-2]) * 1024
            else:
                max_bytes = int(max_size)
        else:
            max_bytes = max_size
        
        file_handler = RotatingFileHandler(
            filename=LOG_CONFIG["file"],
            maxBytes=max_bytes,
            backupCount=LOG_CONFIG["backup_count"],
            encoding=LOG_CONFIG.get("encoding", "utf-8")
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        print(f"✓ 日志系统已配置: {LOG_CONFIG['file']}")
        
    except Exception as e:
        print(f"✗ 配置文件日志处理器失败: {e}")
        # 即使文件处理器失败，控制台日志仍然可用
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    这是一个便捷函数，其他模块可以通过传入 __name__ 来获取
    专属的日志记录器，便于追踪日志来源。
    
    Args:
        name (str): 日志记录器的名称，通常使用模块的 __name__
    
    Returns:
        logging.Logger: 指定名称的日志记录器
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条信息日志")
    """
    return logging.getLogger(name)

# ===================================
# 3. 文件操作功能
# ===================================

def save_json(data: Union[Dict[str, Any], list], file_path: str) -> bool:
    """
    将数据保存为JSON文件
    
    以美化格式保存Python字典或列表为JSON文件，支持中文字符。
    
    Args:
        data (Union[Dict[str, Any], list]): 要保存的数据
        file_path (str): 保存文件的路径
    
    Returns:
        bool: 保存成功返回True，失败返回False
    
    Example:
        >>> data = {"name": "测试", "value": 123}
        >>> save_json(data, "test.json")
        True
    """
    try:
        # 确保目标目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(
                data,
                f,
                indent=4,           # 美化格式，使用4个空格缩进
                ensure_ascii=False, # 支持中文字符
                separators=(',', ': ')  # 清晰的分隔符
            )
        
        logger = get_logger(__name__)
        logger.info(f"JSON文件保存成功: {file_path}")
        return True
        
    except (OSError, IOError) as e:
        logger = get_logger(__name__)
        logger.error(f"保存JSON文件失败: {file_path} - {e}")
        return False
    except TypeError as e:
        logger = get_logger(__name__)
        logger.error(f"数据序列化失败: {file_path} - {e}")
        return False

def load_json(file_path: str) -> Optional[Union[Dict[str, Any], list]]:
    """
    从JSON文件加载数据
    
    加载JSON文件并返回Python对象，包含完整的错误处理。
    
    Args:
        file_path (str): JSON文件的路径
    
    Returns:
        Optional[Union[Dict[str, Any], list]]: 
            成功时返回加载的数据（字典或列表）
            失败时返回None
    
    Example:
        >>> data = load_json("test.json")
        >>> if data:
        ...     print(data["name"])
    """
    logger = get_logger(__name__)
    
    try:
        if not os.path.exists(file_path):
            logger.warning(f"JSON文件不存在: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"JSON文件加载成功: {file_path}")
        return data
        
    except FileNotFoundError:
        logger.error(f"JSON文件未找到: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON格式错误: {file_path} - {e}")
        return None
    except (OSError, IOError) as e:
        logger.error(f"读取JSON文件失败: {file_path} - {e}")
        return None

def backup_file(file_path: str, backup_suffix: str = ".backup") -> bool:
    """
    创建文件的备份副本
    
    Args:
        file_path (str): 要备份的文件路径
        backup_suffix (str): 备份文件的后缀，默认为".backup"
    
    Returns:
        bool: 备份成功返回True，失败返回False
    """
    if not os.path.exists(file_path):
        return False
    
    backup_path = file_path + backup_suffix
    
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        
        logger = get_logger(__name__)
        logger.info(f"文件备份成功: {file_path} -> {backup_path}")
        return True
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"文件备份失败: {file_path} - {e}")
        return False

# ===================================
# 4. 辅助工具函数
# ===================================

def get_file_size(file_path: str) -> Optional[int]:
    """
    获取文件大小（字节）
    
    Args:
        file_path (str): 文件路径
    
    Returns:
        Optional[int]: 文件大小（字节），文件不存在时返回None
    """
    try:
        return os.path.getsize(file_path)
    except OSError:
        return None

def format_file_size(size_bytes: int) -> str:
    """
    将字节数格式化为人类可读的文件大小
    
    Args:
        size_bytes (int): 文件大小（字节）
    
    Returns:
        str: 格式化后的文件大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def clean_filename(filename: str) -> str:
    """
    清理文件名，移除不安全的字符
    
    Args:
        filename (str): 原始文件名
    
    Returns:
        str: 清理后的安全文件名
    """
    import re
    
    # 移除或替换不安全的字符
    unsafe_chars = r'[<>:"/\\|?*]'
    filename = re.sub(unsafe_chars, '_', filename)
    
    # 移除多余的空格和点
    filename = filename.strip('. ')
    
    return filename

# ===================================
# 5. 系统信息和健康检查
# ===================================

def system_health_check() -> Dict[str, Any]:
    """
    执行系统健康检查
    
    Returns:
        Dict[str, Any]: 系统健康状况报告
    """
    logger = get_logger(__name__)
    
    health_report = {
        "timestamp": str(Path(__file__).stat().st_mtime),
        "directories": {},
        "permissions": {},
        "disk_space": {},
        "python_version": sys.version,
        "platform": sys.platform
    }
    
    # 检查目录存在性
    directories = {
        "cache": CACHE_DIR,
        "output": OUTPUT_DIR,
        "logs": LOGS_DIR,
        "templates": TEMPLATES_DIR
    }
    
    for name, path in directories.items():
        health_report["directories"][name] = {
            "exists": os.path.exists(path),
            "path": path,
            "is_writable": os.access(path, os.W_OK) if os.path.exists(path) else False
        }
    
    # 检查磁盘空间
    try:
        import shutil
        total, used, free = shutil.disk_usage(str(BASE_DIR))
        health_report["disk_space"] = {
            "total": format_file_size(total),
            "used": format_file_size(used),
            "free": format_file_size(free),
            "usage_percent": round((used / total) * 100, 2)
        }
    except Exception as e:
        logger.warning(f"无法获取磁盘空间信息: {e}")
        health_report["disk_space"] = {"error": str(e)}
    
    return health_report

# ===================================
# 模块初始化
# ===================================

def initialize_utils_module() -> bool:
    """
    初始化工具模块
    
    执行必要的初始化步骤，包括目录创建和权限检查。
    
    Returns:
        bool: 初始化成功返回True，失败返回False
    """
    print("正在初始化工具模块...")
    
    # 1. 确保目录存在
    if not ensure_directories():
        print("✗ 目录创建失败")
        return False
    
    # 2. 检查权限
    permissions = check_directory_permissions()
    failed_permissions = [name for name, status in permissions.items() if not status]
    
    if failed_permissions:
        print(f"✗ 以下目录权限不足: {', '.join(failed_permissions)}")
        return False
    
    print("✓ 工具模块初始化完成")
    return True

# 当模块被直接运行时，执行初始化和测试
if __name__ == "__main__":
    print("=== 工具模块测试 ===")
    
    # 初始化模块
    if initialize_utils_module():
        print("✓ 模块初始化成功")
    else:
        print("✗ 模块初始化失败")
        sys.exit(1)
    
    # 设置日志
    setup_logging(verbose=True)
    logger = get_logger(__name__)
    
    # 测试日志功能
    logger.info("这是一条测试日志信息")
    logger.warning("这是一条测试警告")
    
    # 测试文件操作
    test_data = {"test": "数据", "number": 42}
    test_file = os.path.join(CACHE_DIR, "test.json")
    
    if save_json(test_data, test_file):
        logger.info("JSON保存测试成功")
        
        loaded_data = load_json(test_file)
        if loaded_data == test_data:
            logger.info("JSON加载测试成功")
        else:
            logger.error("JSON加载测试失败")
    else:
        logger.error("JSON保存测试失败")
    
    # 系统健康检查
    health = system_health_check()
    logger.info(f"系统健康检查完成: {health}")
    
    print("=== 测试完成 ===")