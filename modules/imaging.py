"""
小红书内容自动化管线 - 高保真成像模块
Xiaohongshu Content Automation Pipeline - High-Fidelity Imaging Module

这是流水线的最后一个环节，负责将HTML内容转化为高质量的图片。
使用Playwright浏览器自动化工具进行精确的页面截图。

主要功能：
1. HTML内容渲染：将HTML字符串保存为临时文件并在浏览器中加载
2. 自动化截图：使用Playwright控制浏览器进行精确截图
3. 批量处理：支持对多个页面元素进行批量截图
4. 高保真输出：生成高质量的PNG格式图片

安装要求：
使用本模块前，请确保已安装Playwright浏览器内核：
pip install playwright
playwright install chromium

或者安装所有浏览器：
playwright install
"""

import os
import tempfile
from typing import Dict, List, Any, Optional
from pathlib import Path
from playwright.sync_api import sync_playwright, Browser, Page, ElementHandle, Locator
import logging

# 导入项目配置和工具
# 截图配置 - 如果config.py中没有定义SCREENSHOT_CONFIG，使用默认配置
SCREENSHOT_CONFIG = {
    "width": 800,
    "height": 1200,
    "format": "png",
    "quality": 90,
    "full_page": False,
    "device_scale_factor": 2.0,
    "timeout": 30000  # 30秒超时
}

from .utils import get_logger

# ===================================
# 模块级别配置
# ===================================

logger = get_logger(__name__)

# 默认的页面CSS选择器
DEFAULT_PAGE_SELECTOR = ".page-to-screenshot"

# 支持的图片格式
SUPPORTED_FORMATS = ["png", "jpeg", "jpg"]

# ===================================
# 核心成像函数
# ===================================

def run_high_fidelity_imaging(
    html_content: str,
    output_dir: str,
    page_selector: str = DEFAULT_PAGE_SELECTOR,
    filename_prefix: str = "page"
) -> Dict[str, Any]:
    """
    执行高保真成像流程
    
    这是imaging模块的唯一入口函数，负责将HTML内容转化为高质量图片。
    
    流程步骤：
    1. 创建临时HTML文件
    2. 启动Playwright浏览器
    3. 设置视口和加载页面
    4. 定位截图元素
    5. 批量截图
    6. 清理临时文件
    
    Args:
        html_content (str): 要渲染的HTML内容
        output_dir (str): 截图保存的目录路径
        page_selector (str): 页面元素的CSS选择器，默认为".page-to-screenshot"
        filename_prefix (str): 生成图片的文件名前缀，默认为"page"
    
    Returns:
        Dict[str, Any]: 包含以下键的字典：
            - "success": bool, 是否成功
            - "image_paths": List[str], 生成的图片文件绝对路径列表
            - "total_images": int, 生成的图片总数
            - "error_message": str, 错误信息（如果有）
    
    Raises:
        Exception: 当截图过程中发生不可恢复的错误时
    """
    logger.info("开始高保真成像流程")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"页面选择器: {page_selector}")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化返回结果
    result = {
        "success": False,
        "image_paths": [],
        "total_images": 0,
        "error_message": ""
    }
    
    # 临时文件变量
    temp_html_file = None
    playwright = None
    browser = None
    
    try:
        # ===================================
        # 步骤1: 创建临时HTML文件
        # ===================================
        
        logger.info("创建临时HTML文件")
        temp_html_file = _create_temp_html_file(html_content, output_dir)
        logger.info(f"临时HTML文件已创建: {temp_html_file}")
        
        # ===================================
        # 步骤2: 启动Playwright浏览器
        # ===================================
        
        logger.info("启动Playwright浏览器")
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=True,  # 无头模式
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size={},{}'.format(
                    SCREENSHOT_CONFIG["width"],
                    SCREENSHOT_CONFIG["height"]
                )
            ]
        )
        
        # ===================================
        # 步骤3: 创建页面并设置视口
        # ===================================
        
        logger.info("创建浏览器页面")
        page = browser.new_page()
        
        # 设置视口大小
        page.set_viewport_size({
            "width": SCREENSHOT_CONFIG["width"],
            "height": SCREENSHOT_CONFIG["height"]
        })
        
        # 设置设备缩放因子（用于高DPI显示）
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        # ===================================
        # 步骤4: 加载HTML页面
        # ===================================
        
        logger.info("加载HTML页面")
        file_url = f"file://{temp_html_file.replace(os.sep, '/')}"
        logger.info(f"文件URL: {file_url}")
        
        page.goto(file_url, timeout=SCREENSHOT_CONFIG["timeout"])
        
        # 等待页面完全加载
        page.wait_for_load_state("networkidle")
        
        # ===================================
        # 步骤5: 定位截图元素
        # ===================================
        
        logger.info(f"查找截图元素: {page_selector}")
        elements = page.locator(page_selector).all()
        
        if not elements:
            logger.warning(f"未找到匹配的元素: {page_selector}")
            # 如果没有找到特定选择器，尝试截取整个页面
            logger.info("尝试截取整个页面")
            screenshot_path = _take_full_page_screenshot(page, output_dir, filename_prefix)
            if screenshot_path:
                result["image_paths"].append(screenshot_path)
                result["total_images"] = 1
        else:
            logger.info(f"找到 {len(elements)} 个截图元素")
            
            # ===================================
            # 步骤6: 批量截图
            # ===================================
            
            image_paths = _take_element_screenshots(
                elements, output_dir, filename_prefix
            )
            result["image_paths"].extend(image_paths)
            result["total_images"] = len(image_paths)
        
        # 标记成功
        result["success"] = True
        logger.info(f"成像流程完成，共生成 {result['total_images']} 张图片")
        
    except Exception as e:
        error_msg = f"高保真成像流程失败: {str(e)}"
        logger.error(error_msg)
        result["error_message"] = error_msg
        result["success"] = False
        
    finally:
        # ===================================
        # 步骤7: 清理资源
        # ===================================
        
        logger.info("清理资源")
        
        # 关闭浏览器
        if browser:
            try:
                browser.close()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")
        
        # 停止Playwright
        if playwright:
            try:
                playwright.stop()
                logger.info("Playwright已停止")
            except Exception as e:
                logger.warning(f"停止Playwright时出错: {e}")
        
        # 删除临时HTML文件
        if temp_html_file and os.path.exists(temp_html_file):
            try:
                os.remove(temp_html_file)
                logger.info("临时HTML文件已删除")
            except Exception as e:
                logger.warning(f"删除临时文件时出错: {e}")
    
    return result

# ===================================
# 辅助函数
# ===================================

def _create_temp_html_file(html_content: str, output_dir: str) -> str:
    """
    创建临时HTML文件
    
    Args:
        html_content (str): HTML内容
        output_dir (str): 输出目录
    
    Returns:
        str: 临时文件的绝对路径
    """
    temp_file_path = os.path.join(output_dir, "temp_render.html")
    
    try:
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 返回绝对路径
        return os.path.abspath(temp_file_path)
        
    except Exception as e:
        logger.error(f"创建临时HTML文件失败: {e}")
        raise

def _take_full_page_screenshot(
    page: Page,
    output_dir: str,
    filename_prefix: str
) -> Optional[str]:
    """
    截取整个页面的截图
    
    Args:
        page: Playwright页面对象
        output_dir: 输出目录
        filename_prefix: 文件名前缀
    
    Returns:
        Optional[str]: 截图文件的绝对路径，失败时返回None
    """
    try:
        output_path = os.path.join(output_dir, f"{filename_prefix}_full.png")
        
        page.screenshot(
            path=output_path,
            full_page=SCREENSHOT_CONFIG.get("full_page", True),
            quality=SCREENSHOT_CONFIG.get("quality", 90) if SCREENSHOT_CONFIG.get("format") == "jpeg" else None,
            type=SCREENSHOT_CONFIG.get("format", "png")
        )
        
        absolute_path = os.path.abspath(output_path)
        logger.info(f"整页截图已保存: {absolute_path}")
        return absolute_path
        
    except Exception as e:
        logger.error(f"整页截图失败: {e}")
        return None

def _take_element_screenshots(
    elements: List[Locator],
    output_dir: str,
    filename_prefix: str
) -> List[str]:
    """
    对多个元素进行批量截图
    
    Args:
        elements: 要截图的元素列表
        output_dir: 输出目录
        filename_prefix: 文件名前缀
    
    Returns:
        List[str]: 成功截图的文件绝对路径列表
    """
    image_paths = []
    
    for i, element in enumerate(elements, 1):
        try:
            # 生成文件名
            filename = f"{filename_prefix}_{i}.{SCREENSHOT_CONFIG.get('format', 'png')}"
            output_path = os.path.join(output_dir, filename)
            
            # 截图参数
            screenshot_options = {
                "path": output_path,
                "type": SCREENSHOT_CONFIG.get("format", "png")
            }
            
            # 如果是JPEG格式，添加质量参数
            if SCREENSHOT_CONFIG.get("format") in ["jpeg", "jpg"]:
                screenshot_options["quality"] = SCREENSHOT_CONFIG.get("quality", 90)
            
            # 执行截图
            element.screenshot(**screenshot_options)
            
            absolute_path = os.path.abspath(output_path)
            image_paths.append(absolute_path)
            logger.info(f"元素 {i} 截图已保存: {absolute_path}")
            
        except Exception as e:
            logger.error(f"元素 {i} 截图失败: {e}")
            continue
    
    return image_paths

def _optimize_html_for_screenshot(html_content: str) -> str:
    """
    优化HTML内容以适应截图
    
    为HTML添加一些CSS样式，确保截图效果最佳。
    
    Args:
        html_content (str): 原始HTML内容
    
    Returns:
        str: 优化后的HTML内容
    """
    # 添加基础CSS样式以优化截图效果
    optimization_css = """
    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background-color: #ffffff;
            color: #333333;
            line-height: 1.6;
        }
        
        .page-to-screenshot {
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            padding: 20px;
            max-width: 100%;
            box-sizing: border-box;
        }
        
        /* 确保图片和其他媒体元素不会溢出 */
        img, video, iframe {
            max-width: 100%;
            height: auto;
        }
        
        /* 字体渲染优化 */
        * {
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        /* 打印友好的样式 */
        @media screen {
            body {
                zoom: 1;
            }
        }
    </style>
    """
    
    # 如果HTML中没有包含<head>标签，添加基础结构
    if "<head>" not in html_content.lower():
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>小红书内容渲染</title>
            {optimization_css}
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
    else:
        # 如果已有head标签，在其中插入CSS
        html_content = html_content.replace("</head>", f"{optimization_css}</head>")
    
    return html_content

# ===================================
# 配置和验证函数
# ===================================

def validate_screenshot_config() -> bool:
    """
    验证截图配置的有效性
    
    Returns:
        bool: 配置是否有效
    """
    try:
        # 检查必要的配置项
        required_keys = ["width", "height", "format"]
        for key in required_keys:
            if key not in SCREENSHOT_CONFIG:
                logger.error(f"截图配置中缺少必要的键: {key}")
                return False
        
        # 检查宽度和高度
        if not isinstance(SCREENSHOT_CONFIG["width"], int) or SCREENSHOT_CONFIG["width"] <= 0:
            logger.error("截图宽度必须是正整数")
            return False
        
        if not isinstance(SCREENSHOT_CONFIG["height"], int) or SCREENSHOT_CONFIG["height"] <= 0:
            logger.error("截图高度必须是正整数")
            return False
        
        # 检查格式
        if SCREENSHOT_CONFIG["format"] not in SUPPORTED_FORMATS:
            logger.error(f"不支持的图片格式: {SCREENSHOT_CONFIG['format']}")
            return False
        
        logger.info("截图配置验证通过")
        return True
        
    except Exception as e:
        logger.error(f"验证截图配置时出错: {e}")
        return False

def get_screenshot_info() -> Dict[str, Any]:
    """
    获取当前截图配置信息
    
    Returns:
        Dict[str, Any]: 配置信息字典
    """
    return {
        "config": SCREENSHOT_CONFIG.copy(),
        "supported_formats": SUPPORTED_FORMATS,
        "default_selector": DEFAULT_PAGE_SELECTOR
    }

# ===================================
# 模块初始化
# ===================================

def initialize_imaging_module() -> bool:
    """
    初始化成像模块
    
    检查Playwright是否正确安装，验证配置等。
    
    Returns:
        bool: 初始化是否成功
    """
    logger.info("初始化成像模块")
    
    # 验证截图配置
    if not validate_screenshot_config():
        logger.error("截图配置验证失败")
        return False
    
    # 检查Playwright是否可用
    try:
        logger.info("检查Playwright可用性")
        playwright = sync_playwright().start()
        
        # 尝试启动浏览器
        browser = playwright.chromium.launch(headless=True)
        browser.close()
        playwright.stop()
        
        logger.info("Playwright检查通过")
        return True
        
    except Exception as e:
        logger.error(f"Playwright检查失败: {e}")
        logger.error("请确保已安装Playwright浏览器内核:")
        logger.error("pip install playwright")
        logger.error("playwright install chromium")
        return False

# ===================================
# 模块级别的自动初始化
# ===================================

if __name__ == "__main__":
    # 当直接运行此模块时，执行初始化检查
    if initialize_imaging_module():
        print("✓ 成像模块初始化成功")
    else:
        print("✗ 成像模块初始化失败")
