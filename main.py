#!/usr/bin/env python3
"""
小红书内容自动化管线 - 主程序
Xiaohongshu Content Automation Pipeline - Main Program

这是项目的统一入口，负责协调整个内容生产流水线。
从原始主题到最终的小红书多图内容，实现全自动化生产。

核心流程：
1. 战略规划 (Strategy) - 主题分析与策略制定
2. 叙事执行 (Execution) - 内容创作与HTML生成
3. 高保真成像 (Imaging) - HTML转图片（可选）

主要特性：
- 支持小红书多图内容生成
- 智能缓存机制
- 多种成像技术方案
- 完整的错误处理和日志记录
"""

import argparse
import sys
import os
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

# 配置导入
from config import validate_config, OUTPUT_DIR, LOGS_DIR, CACHE_DIR, TEMPLATES_DIR

# 模块导入
from modules.strategy import run_strategy_and_planning
from modules.execution import execute_narrative_pipeline, initialize_execution_module
from modules.imaging import process_screenshot_config, check_imaging_capabilities, initialize_imaging_module
from modules.utils import get_logger, setup_logging

# ===================================
# 全局配置
# ===================================

logger = get_logger(__name__)

# ===================================
# 核心函数
# ===================================

def setup_environment() -> bool:
    """
    设置运行环境，检查依赖和配置
    
    Returns:
        bool: 设置是否成功
    """
    try:
        # 设置日志系统
        log_file = setup_logging()
        if log_file:
            print(f"✓ 日志系统已配置: {log_file}")
        else:
            print("✓ 日志系统已配置")
        logger.info("日志系统初始化完成")
        
        # 验证配置
        config_valid = validate_config()
        if not config_valid:
            print("❌ 配置验证失败")
            return False
        
        # 检查并创建必要目录
        directories = {
            "缓存目录": CACHE_DIR,
            "输出目录": OUTPUT_DIR,
            "日志目录": LOGS_DIR,
            "模板目录": TEMPLATES_DIR
        }
        
        for name, path in directories.items():
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                    print(f"✓ {name} 已创建: {path}")
                except Exception as e:
                    print(f"❌ 创建{name}失败: {e}")
                    return False
            else:
                print(f"✓ {name} 已准备就绪: {path}")
        
        logger.info("目录结构检查完成")
        
        # 初始化模块
        if not initialize_execution_module():
            print("❌ 执行模块初始化失败")
            return False
        
        if not initialize_imaging_module():
            print("⚠️ 成像模块初始化警告（功能可能受限）")
            # 成像模块初始化失败不影响主流程
        
        return True
        
    except Exception as e:
        print(f"❌ 环境设置失败: {e}")
        return False

def run_xiaohongshu_pipeline(
    topic: str, 
    force: bool = False, 
    enable_imaging: bool = False,
    output_dir: str = None
) -> Dict[str, Any]:
    """
    运行小红书内容生产流水线
    
    Args:
        topic (str): 内容主题
        force (bool): 是否强制重新生成
        enable_imaging (bool): 是否启用成像功能
        output_dir (str): 输出目录
        
    Returns:
        Dict[str, Any]: 流水线执行结果
    """
    logger.info(f"程序启动参数: topic={topic}, force={force}, enable_imaging={enable_imaging}")
    
    # 使用默认输出目录（如果未指定）
    if output_dir is None:
        output_dir = OUTPUT_DIR
    
    # 创建会话目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(output_dir, f"{topic}_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)
    
    print(f"📂 会话目录: {session_dir}")
    
    try:
        # ===================================
        # 阶段 1: 战略规划
        # ===================================
        print("\n" + "=" * 80)
        print("🚀 阶段 1/3: 战略规划")
        print("=" * 80)
        
        logger.info("开始执行战略规划阶段")
        
        try:
            strategy_result = run_strategy_and_planning(topic)
            print("✅ 完成 战略规划")
        except Exception as e:
            print("❌ 失败 战略规划")
            print("-" * 80)
            logger.error(f"战略规划阶段失败: {str(e)}")
            raise Exception(f"战略规划阶段失败: {str(e)}")
        
        # ===================================
        # 阶段 2: 叙事执行
        # ===================================
        print("\n" + "=" * 80)
        print("🎬 阶段 2/3: 叙事执行")
        print("=" * 80)
        
        logger.info("开始执行叙事生成阶段")
        
        try:
            execution_result = execute_narrative_pipeline(
                blueprint=strategy_result,
                theme=topic,
                output_dir=output_dir
            )
            
            if execution_result["status"] == "success":
                print("✅ 完成 叙事执行")
                print(f"📁 输出目录: {execution_result['output_directory']}")
                print(f"🖼️ 生成图片数量: {execution_result['total_images']}")
            else:
                raise Exception(execution_result.get("error", "未知错误"))
                
        except Exception as e:
            print("❌ 失败 叙事执行")
            print("-" * 80)
            logger.error(f"叙事执行阶段失败: {str(e)}")
            raise Exception(f"叙事执行阶段失败: {str(e)}")
        
        # ===================================
        # 阶段 3: 高保真成像（可选）
        # ===================================
        imaging_result = None
        
        if enable_imaging:
            print("\n" + "=" * 80)
            print("📸 阶段 3/3: 高保真成像")
            print("=" * 80)
            
            logger.info("开始执行成像阶段")
            
            try:
                # 检查成像功能可用性
                capabilities = check_imaging_capabilities()
                available_methods = capabilities.get("available_method_names", [])
                
                if not available_methods:
                    print("⚠️ 跳过 高保真成像 - 没有可用的成像方案")
                    print("💡 提示: 安装 playwright 以启用高质量截图功能")
                    logger.warning("没有可用的成像方案，跳过成像阶段")
                else:
                    print(f"🔧 检测到可用成像方案: {', '.join(available_methods)}")
                    
                    # 查找截图配置文件
                    screenshot_config_path = execution_result.get("screenshot_config_path")
                    
                    if screenshot_config_path and os.path.exists(screenshot_config_path):
                        imaging_result = process_screenshot_config(screenshot_config_path)
                        
                        if imaging_result["status"] == "success":
                            summary = imaging_result.get("summary", {})
                            print("✅ 完成 高保真成像")
                            print(f"📸 成功截图: {summary.get('successful_count', 0)}/{summary.get('total_files', 0)}")
                            print(f"📁 图片目录: {imaging_result.get('images_directory', '')}")
                        else:
                            print("❌ 失败 高保真成像")
                            logger.error(f"成像阶段失败: {imaging_result.get('error', '未知错误')}")
                    else:
                        print("❌ 失败 高保真成像 - 找不到截图配置文件")
                        logger.error("找不到截图配置文件")
                
            except Exception as e:
                print("❌ 失败 高保真成像")
                print("-" * 80)
                logger.error(f"成像阶段失败: {str(e)}")
                # 成像阶段失败不影响整体流程
                imaging_result = {"status": "error", "error": str(e)}
        else:
            print("\n⏩ 跳过 高保真成像阶段")
            print("💡 使用 --enable-imaging 参数启用图片生成功能")
        
        # ===================================
        # 生成最终报告
        # ===================================
        print("\n" + "=" * 80)
        print("🎉 流水线执行完成")
        print("=" * 80)
        
        final_result = {
            "status": "success",
            "topic": topic,
            "timestamp": timestamp,
            "strategy_result": strategy_result,
            "execution_result": execution_result,
            "imaging_result": imaging_result,
            "session_directory": session_dir,
            "output_directory": execution_result.get("output_directory"),
            "total_images": execution_result.get("total_images", 0)
        }
        
        # 显示最终信息
        print(f"📝 主题: {topic}")
        print(f"📁 输出目录: {execution_result.get('output_directory')}")
        print(f"🖼️ 生成内容图片: {execution_result.get('total_images', 0)}张")
        
        if imaging_result and imaging_result.get("status") == "success":
            summary = imaging_result["summary"]
            print(f"📸 截图文件: {summary['successful_count']}张")
            print(f"📁 图片目录: {imaging_result['images_directory']}")
        
        print("\n📋 生成的文件:")
        output_dir_path = execution_result.get("output_directory")
        if output_dir_path and os.path.exists(output_dir_path):
            files = os.listdir(output_dir_path)
            for file in sorted(files):
                file_path = os.path.join(output_dir_path, file)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    if file_size > 1024:
                        size_str = f"{file_size/1024:.1f}KB"
                    else:
                        size_str = f"{file_size}B"
                    print(f"  - {file} ({size_str})")
        
        print("\n🎯 下一步操作:")
        print("  1. 查看生成的标题选项，选择最合适的")
        print("  2. 复制正文内容到小红书")
        print("  3. 如果已生成图片，直接上传使用")
        print("  4. 如果需要截图，使用生成的HTML文件")
        
        return final_result
        
    except Exception as e:
        logger.error(f"流水线执行过程中发生错误: {str(e)}")
        print(f"❌ 流水线执行失败: {str(e)}")
        
        # 显示详细错误信息
        print("\n📋 详细错误信息:")
        print(traceback.format_exc())
        
        return {
            "status": "error",
            "topic": topic,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def main():
    """
    主函数，处理命令行参数并执行流水线
    """
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(
        description="小红书内容自动化管线 - 从主题到多图内容的全自动生产",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py -t "宝宝第一次发烧怎么办"
  python main.py -t "如何培养孩子的阅读兴趣" --enable-imaging
  python main.py -t "新手爸爸必备技能" --force --enable-imaging

注意事项:
  - 首次运行建议先不启用成像功能，验证内容生成效果
  - 启用成像功能需要安装 playwright: pip install playwright 
  - 生成的HTML文件可以手动截图或使用其他工具转换
        """
    )
    
    parser.add_argument(
        "-t", "--topic",
        type=str,
        required=True,
        help="内容主题（必须）"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新生成所有内容，忽略缓存"
    )
    
    parser.add_argument(
        "--enable-imaging",
        action="store_true",
        help="启用高保真成像功能，将HTML转换为PNG图片"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="指定输出目录（可选，默认使用配置中的输出目录）"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细日志信息"
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 显示启动信息
    print("🚀 小红书内容自动化管线启动")
    print(f"📝 主题: {args.topic}")
    print(f"📁 输出目录: {args.output_dir or OUTPUT_DIR}")
    print(f"🔄 强制重新生成: {'是' if args.force else '否'}")
    print(f"📸 启用成像: {'是' if args.enable_imaging else '否'}")
    print(f"🔊 详细日志: {'是' if args.verbose else '否'}")
    
    # 设置环境
    if not setup_environment():
        print("❌ 环境设置失败，程序退出")
        sys.exit(1)
    
    try:
        # 执行流水线
        result = run_xiaohongshu_pipeline(
            topic=args.topic,
            force=args.force,
            enable_imaging=args.enable_imaging,
            output_dir=args.output_dir
        )
        
        # 根据结果设置退出码
        if result["status"] == "success":
            print("\n🎊 程序成功完成！")
            sys.exit(0)
        else:
            print(f"\n💥 程序执行失败: {result.get('error', '未知错误')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 用户中断程序执行")
        logger.info("用户中断程序执行")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 程序执行过程中发生未捕获的错误: {str(e)}")
        logger.error(f"未捕获的错误: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
