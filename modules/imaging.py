"""
小红书内容自动化管线 - 高保真成像模块
Xiaohongshu Content Automation Pipeline - High-Fidelity Imaging Module

这是流水线的最终阶段，负责将HTML代码转换为高质量的PNG图片。
实现"所见即所得"的完美转换，确保每张图片都符合小红书发布要求。

主要功能：
1. HTML到PNG的高保真转换
2. 多种技术方案支持（Playwright、html-to-image等）
3. 固定尺寸渲染（448x597px）
4. 批量处理多个HTML文件
5. 自动资源内联和样式优化
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import time
from datetime import datetime

# 导入工具和配置
from .utils import get_logger
from config import SCREENSHOT_CONFIG, XIAOHONGSHU_IMAGE_WIDTH, XIAOHONGSHU_IMAGE_HEIGHT

# ===================================
# 模块级配置
# ===================================

logger = get_logger(__name__)

# 成像技术方案配置
IMAGING_METHODS = {
    "playwright": {
        "name": "Playwright无头浏览器",
        "description": "终极方案，高保真截图",
        "priority": 1,
        "dependencies": ["playwright"]
    },
    "html_to_image": {
        "name": "html-to-image前端库",
        "description": "基础方案，前端实时截图",
        "priority": 2,
        "dependencies": ["requests"]
    },
    "fallback": {
        "name": "备用方案",
        "description": "生成提示图片",
        "priority": 3,
        "dependencies": []
    }
}

# ===================================
# 核心截图函数
# ===================================

async def capture_html_with_playwright(html_file: str, output_file: str, config: Dict[str, Any] = None) -> bool:
    """
    使用Playwright进行HTML截图
    
    Args:
        html_file (str): HTML文件路径
        output_file (str): 输出PNG文件路径
        config (Dict[str, Any]): 截图配置
        
    Returns:
        bool: 截图是否成功
    """
    try:
        # 动态导入Playwright
        from playwright.async_api import async_playwright
        
        # 使用传入的配置或默认配置
        screenshot_config = config or SCREENSHOT_CONFIG
        
        logger.info(f"开始使用Playwright截图: {html_file}")
        
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # 创建页面
            page = await browser.new_page(
                viewport={
                    'width': screenshot_config['width'],
                    'height': screenshot_config['height']
                },
                device_scale_factor=screenshot_config.get('device_scale_factor', 2)
            )
            
            # 加载HTML文件
            html_path = Path(html_file).as_uri()
            await page.goto(html_path, wait_until='networkidle')
            
            # 等待页面渲染完成
            await page.wait_for_timeout(1000)
            
            # 截图
            await page.screenshot(
                path=output_file,
                type=screenshot_config.get('format', 'png'),
                quality=screenshot_config.get('quality', 90),
                full_page=screenshot_config.get('full_page', False),
                clip=screenshot_config.get('clip')
            )
            
            await browser.close()
            
        logger.info(f"✓ Playwright截图成功: {output_file}")
        return True
        
    except ImportError:
        logger.warning("Playwright未安装，无法使用此方案")
        return False
    except Exception as e:
        logger.error(f"Playwright截图失败: {e}")
        return False

def capture_html_with_html2image(html_file: str, output_file: str, config: Dict[str, Any] = None) -> bool:
    """
    使用html2image进行HTML截图
    
    Args:
        html_file (str): HTML文件路径
        output_file (str): 输出PNG文件路径
        config (Dict[str, Any]): 截图配置
        
    Returns:
        bool: 截图是否成功
    """
    try:
        # 动态导入html2image
        from html2image import Html2Image
        
        # 使用传入的配置或默认配置
        screenshot_config = config or SCREENSHOT_CONFIG
        
        logger.info(f"开始使用html2image截图: {html_file}")
        
        # 初始化Html2Image
        hti = Html2Image(
            size=(screenshot_config['width'], screenshot_config['height']),
            output_path=os.path.dirname(output_file)
        )
        
        # 读取HTML内容
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 执行截图
        output_filename = os.path.basename(output_file)
        hti.screenshot(
            html_str=html_content,
            save_as=output_filename
        )
        
        logger.info(f"✓ html2image截图成功: {output_file}")
        return True
        
    except ImportError:
        logger.warning("html2image未安装，无法使用此方案")
        return False
    except Exception as e:
        logger.error(f"html2image截图失败: {e}")
        return False

def generate_fallback_image(html_file: str, output_file: str, config: Dict[str, Any] = None) -> bool:
    """
    生成备用提示图片
    
    Args:
        html_file (str): HTML文件路径
        output_file (str): 输出PNG文件路径
        config (Dict[str, Any]): 截图配置
        
    Returns:
        bool: 生成是否成功
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 使用传入的配置或默认配置
        screenshot_config = config or SCREENSHOT_CONFIG
        
        logger.info(f"生成备用提示图片: {output_file}")
        
        # 创建图片
        img = Image.new('RGB', 
                       (screenshot_config['width'], screenshot_config['height']), 
                       color='#f5f7fa')
        
        draw = ImageDraw.Draw(img)
        
        # 尝试使用系统字体
        try:
            font_title = ImageFont.truetype("arial.ttf", 24)
            font_content = ImageFont.truetype("arial.ttf", 14)
        except:
            font_title = ImageFont.load_default()
            font_content = ImageFont.load_default()
        
        # 绘制内容
        html_filename = os.path.basename(html_file)
        
        # 标题
        title = "小红书内容已生成"
        title_bbox = draw.textbbox((0, 0), title, font=font_title)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (screenshot_config['width'] - title_width) // 2
        draw.text((title_x, 100), title, fill='#333333', font=font_title)
        
        # 内容
        content_lines = [
            f"HTML文件：{html_filename}",
            f"图片尺寸：{screenshot_config['width']}x{screenshot_config['height']}",
            "请使用Playwright或其他工具进行截图",
            "以获得最佳视觉效果"
        ]
        
        y_offset = 200
        for line in content_lines:
            line_bbox = draw.textbbox((0, 0), line, font=font_content)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (screenshot_config['width'] - line_width) // 2
            draw.text((line_x, y_offset), line, fill='#666666', font=font_content)
            y_offset += 30
        
        # 保存图片
        img.save(output_file, 'PNG')
        
        logger.info(f"✓ 备用提示图片生成成功: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"备用图片生成失败: {e}")
        return False

# ===================================
# 高级成像函数
# ===================================

async def capture_single_html(html_file: str, output_file: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    对单个HTML文件进行截图，自动选择最佳方案
    
    Args:
        html_file (str): HTML文件路径
        output_file (str): 输出PNG文件路径
        config (Dict[str, Any]): 截图配置
        
    Returns:
        Dict[str, Any]: 截图结果
    """
    logger.info(f"开始单个HTML截图: {html_file}")
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 记录开始时间
    start_time = time.time()
    
    # 按优先级尝试不同的截图方案
    for method_name, method_info in sorted(IMAGING_METHODS.items(), key=lambda x: x[1]['priority']):
        logger.info(f"尝试使用 {method_info['name']} 进行截图")
        
        success = False
        
        if method_name == "playwright":
            success = await capture_html_with_playwright(html_file, output_file, config)
        elif method_name == "html_to_image":
            success = capture_html_with_html2image(html_file, output_file, config)
        elif method_name == "fallback":
            success = generate_fallback_image(html_file, output_file, config)
        
        if success:
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "status": "success",
                "method": method_name,
                "method_name": method_info['name'],
                "html_file": html_file,
                "output_file": output_file,
                "duration": duration,
                "file_size": os.path.getsize(output_file) if os.path.exists(output_file) else 0
            }
    
    # 如果所有方案都失败了
    end_time = time.time()
    duration = end_time - start_time
    
    return {
        "status": "error",
        "method": "none",
        "method_name": "所有方案失败",
        "html_file": html_file,
        "output_file": output_file,
        "duration": duration,
        "error": "所有截图方案都失败了"
    }

async def capture_multiple_html(html_files: List[str], output_dir: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    批量截图多个HTML文件
    
    Args:
        html_files (List[str]): HTML文件路径列表
        output_dir (str): 输出目录
        config (Dict[str, Any]): 截图配置
        
    Returns:
        Dict[str, Any]: 批量截图结果
    """
    logger.info(f"开始批量截图，共{len(html_files)}个文件")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 记录开始时间
    start_time = time.time()
    
    # 存储结果
    results = []
    successful_count = 0
    
    # 逐个处理HTML文件
    for i, html_file in enumerate(html_files, 1):
        logger.info(f"处理第{i}/{len(html_files)}个文件: {html_file}")
        
        # 生成输出文件名
        html_basename = os.path.basename(html_file)
        html_name = os.path.splitext(html_basename)[0]
        output_file = os.path.join(output_dir, f"{html_name}.png")
        
        # 执行截图
        result = await capture_single_html(html_file, output_file, config)
        results.append(result)
        
        if result["status"] == "success":
            successful_count += 1
            logger.info(f"✓ 截图成功: {output_file}")
        else:
            logger.warning(f"✗ 截图失败: {html_file}")
    
    # 计算总时间
    end_time = time.time()
    total_duration = end_time - start_time
    
    # 生成汇总报告
    summary = {
        "status": "completed",
        "total_files": len(html_files),
        "successful_count": successful_count,
        "failed_count": len(html_files) - successful_count,
        "success_rate": (successful_count / len(html_files)) * 100,
        "total_duration": total_duration,
        "average_duration": total_duration / len(html_files),
        "output_directory": output_dir,
        "results": results
    }
    
    logger.info(f"批量截图完成: {successful_count}/{len(html_files)} 成功")
    logger.info(f"总耗时: {total_duration:.2f}秒")
    
    return summary

# ===================================
# 主入口函数
# ===================================

def process_screenshot_config(config_file: str) -> Dict[str, Any]:
    """
    处理截图配置文件，执行批量截图
    
    Args:
        config_file (str): 截图配置文件路径
        
    Returns:
        Dict[str, Any]: 处理结果
    """
    logger.info(f"开始处理截图配置: {config_file}")
    
    try:
        # 加载配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 提取配置信息
        screenshot_config = config_data.get("config", SCREENSHOT_CONFIG)
        html_files = config_data.get("html_files", [])
        output_directory = config_data.get("output_directory", ".")
        image_names = config_data.get("image_names", [])
        
        # 验证HTML文件存在
        valid_html_files = []
        for html_file in html_files:
            if os.path.exists(html_file):
                valid_html_files.append(html_file)
            else:
                logger.warning(f"HTML文件不存在: {html_file}")
        
        if not valid_html_files:
            raise Exception("没有找到有效的HTML文件")
        
        # 创建images子目录
        images_dir = os.path.join(output_directory, "images")
        
        # 执行批量截图
        async def run_batch_capture():
            return await capture_multiple_html(valid_html_files, images_dir, screenshot_config)
        
        # 运行异步任务
        result = asyncio.run(run_batch_capture())
        
        # 保存结果报告
        report_path = os.path.join(output_directory, "screenshot_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"截图报告已保存: {report_path}")
        
        return {
            "status": "success",
            "config_file": config_file,
            "images_directory": images_dir,
            "report_path": report_path,
            "summary": result
        }
        
    except Exception as e:
        logger.error(f"处理截图配置失败: {e}")
        return {
            "status": "error",
            "config_file": config_file,
            "error": str(e)
        }

# ===================================
# 工具函数
# ===================================

def check_imaging_capabilities() -> Dict[str, Any]:
    """
    检查成像功能的可用性
    
    Returns:
        Dict[str, Any]: 可用性报告
    """
    logger.info("检查成像功能可用性")
    
    capabilities = {}
    
    # 检查Playwright
    try:
        import playwright
        capabilities["playwright"] = {
            "available": True,
            "version": playwright.__version__
        }
    except ImportError:
        capabilities["playwright"] = {
            "available": False,
            "reason": "未安装playwright"
        }
    
    # 检查html2image
    try:
        import html2image
        capabilities["html2image"] = {
            "available": True,
            "version": getattr(html2image, '__version__', 'unknown')
        }
    except ImportError:
        capabilities["html2image"] = {
            "available": False,
            "reason": "未安装html2image"
        }
    
    # 检查PIL
    try:
        import PIL
        capabilities["pillow"] = {
            "available": True,
            "version": PIL.__version__
        }
    except ImportError:
        capabilities["pillow"] = {
            "available": False,
            "reason": "未安装Pillow"
        }
    
    # 汇总
    available_methods = [name for name, info in capabilities.items() if info["available"]]
    
    summary = {
        "total_methods": len(capabilities),
        "available_methods": len(available_methods),
        "available_method_names": available_methods,
        "capabilities": capabilities,
        "recommended_method": "playwright" if "playwright" in available_methods else "fallback"
    }
    
    logger.info(f"可用成像方案: {available_methods}")
    
    return summary

# ===================================
# 模块初始化
# ===================================

def initialize_imaging_module() -> bool:
    """
    初始化成像模块
    
    Returns:
        bool: 初始化是否成功
    """
    logger.info("初始化成像模块")
    
    try:
        # 检查成像功能
        capabilities = check_imaging_capabilities()
        
        if capabilities["available_methods"] == 0:
            logger.warning("没有可用的成像方案，仅支持备用方案")
            return True
        
        logger.info("成像模块初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"成像模块初始化失败: {e}")
        return False

# ===================================
# 命令行支持
# ===================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
        result = process_screenshot_config(config_file)
        print(f"处理结果: {result}")
    else:
        # 检查功能
        capabilities = check_imaging_capabilities()
        print("成像功能检查:")
        print(json.dumps(capabilities, ensure_ascii=False, indent=2))
