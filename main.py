#!/usr/bin/env python3
"""
小红书内容自动化管线 - 主程序
Xiaohongshu Content Automation Pipeline - Main Program

这是整个内容生产流水线的总指挥程序，负责协调所有模块的执行。

使用方法：
    python main.py -t "如何培养孩子的阅读兴趣"
    python main.py -t "育儿话题" --force --verbose
    python main.py -t "教育方法" --skip-imaging --output-dir ./custom_output

主要功能：
1. 命令行接口 - 用户友好的参数配置
2. 流水线协调 - 串联三个核心阶段
3. 会话管理 - 独立的时间戳输出目录
4. 错误处理 - 完善的异常处理和日志记录
5. 进度显示 - 清晰的阶段状态展示
"""

import os
import sys
import argparse
import traceback
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# 导入项目模块
try:
    from config import OUTPUT_DIR, BASE_DIR
    from modules.utils import setup_logging, ensure_directories, save_json
    from modules.strategy import run_strategy_and_planning
    from modules.execution import run_narrative_and_visual
    from modules.imaging import run_high_fidelity_imaging
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保所有模块文件都在正确的位置")
    sys.exit(1)

# ===================================
# 全局变量
# ===================================

logger = None  # 将在main函数中初始化

# ===================================
# 命令行参数解析
# ===================================

def create_argument_parser() -> argparse.ArgumentParser:
    """
    创建命令行参数解析器
    
    Returns:
        argparse.ArgumentParser: 配置好的参数解析器
    """
    parser = argparse.ArgumentParser(
        description="小红书内容自动化管线 - 从主题到图片的完整内容生产流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  %(prog)s -t "如何培养孩子的阅读兴趣"
  %(prog)s -t "育儿话题" --force --verbose
  %(prog)s -t "教育方法" --skip-imaging --output-dir ./custom_output
  %(prog)s -t "亲子关系" --force --verbose --output-dir ./results

阶段说明：
  1. 战略规划 - 分析主题，生成内容策略蓝图
  2. 叙事执行 - 根据策略生成文案和HTML
  3. 高保真成像 - 将HTML转化为高质量图片

更多信息请查看项目文档。
        """
    )
    
    # 必需参数
    parser.add_argument(
        "-t", "--topic",
        type=str,
        required=True,
        help="内容主题（必需）。例如：'如何培养孩子的阅读兴趣'"
    )
    
    # 可选参数
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新执行所有阶段，忽略所有缓存"
    )
    
    parser.add_argument(
        "--skip-imaging",
        action="store_true",
        help="跳过最后的成像阶段，只生成文案和HTML"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=OUTPUT_DIR,
        help=f"指定输出目录（默认：{OUTPUT_DIR}）"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出（DEBUG级别）"
    )
    
    return parser

# ===================================
# 会话管理
# ===================================

def create_session_directory(topic: str, base_output_dir: str) -> str:
    """
    创建带时间戳的会话目录
    
    Args:
        topic (str): 内容主题
        base_output_dir (str): 基础输出目录
    
    Returns:
        str: 会话目录的绝对路径
    """
    # 清理主题名称，去除非法字符
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_topic = safe_topic.replace(' ', '_')
    
    # 限制主题名长度
    if len(safe_topic) > 50:
        safe_topic = safe_topic[:50]
    
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 创建会话目录名
    session_dir_name = f"{safe_topic}_{timestamp}"
    session_dir_path = os.path.join(base_output_dir, session_dir_name)
    
    # 创建目录
    os.makedirs(session_dir_path, exist_ok=True)
    
    return os.path.abspath(session_dir_path)

# ===================================
# 结果保存函数
# ===================================

def save_session_results(
    session_dir: str,
    topic: str,
    strategy_result: Dict[str, Any],
    execution_result: Tuple[Dict[str, Any], str],
    imaging_result: Optional[Dict[str, Any]] = None
) -> bool:
    """
    保存会话结果到会话目录
    
    Args:
        session_dir (str): 会话目录路径
        topic (str): 主题
        strategy_result (Dict[str, Any]): 策略规划结果
        execution_result (Tuple[Dict[str, Any], str]): 执行结果(设计规范, HTML内容)
        imaging_result (Optional[Dict[str, Any]]): 成像结果
    
    Returns:
        bool: 保存是否成功
    """
    try:
        # 解包执行结果
        design_spec, html_content = execution_result
        
        # 保存策略蓝图
        strategy_path = os.path.join(session_dir, "creative_blueprint.json")
        save_json(strategy_result, strategy_path)
        if logger:
            logger.info(f"✓ 策略蓝图已保存: {strategy_path}")
        
        # 保存设计规范
        design_path = os.path.join(session_dir, "design_spec.json")
        save_json(design_spec, design_path)
        if logger:
            logger.info(f"✓ 设计规范已保存: {design_path}")
        
        # 保存HTML内容
        html_path = os.path.join(session_dir, "final_content.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        if logger:
            logger.info(f"✓ HTML内容已保存: {html_path}")
        
        # 保存成像结果（如果有）
        if imaging_result:
            imaging_path = os.path.join(session_dir, "imaging_result.json")
            save_json(imaging_result, imaging_path)
            if logger:
                logger.info(f"✓ 成像结果已保存: {imaging_path}")
        
        # 创建会话摘要
        summary = {
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "session_dir": session_dir,
            "files_generated": {
                "strategy_blueprint": "creative_blueprint.json",
                "design_spec": "design_spec.json",
                "html_content": "final_content.html"
            },
            "statistics": {
                "total_phases": 3 if imaging_result else 2,
                "images_generated": imaging_result.get("total_images", 0) if imaging_result else 0,
                "success": True
            }
        }
        
        if imaging_result:
            summary["files_generated"]["imaging_result"] = "imaging_result.json"
            summary["files_generated"]["images"] = [
                os.path.basename(path) for path in imaging_result.get("image_paths", [])
            ]
        
        summary_path = os.path.join(session_dir, "session_summary.json")
        save_json(summary, summary_path)
        if logger:
            logger.info(f"✓ 会话摘要已保存: {summary_path}")
        
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"保存会话结果时发生错误: {e}")
        return False

# ===================================
# 进度显示函数
# ===================================

def print_phase_header(phase_name: str, phase_number: int, total_phases: int):
    """打印阶段开始标题"""
    print("\n" + "=" * 80)
    print(f"🚀 阶段 {phase_number}/{total_phases}: {phase_name}")
    print("=" * 80)

def print_phase_footer(phase_name: str, success: bool = True):
    """打印阶段结束标题"""
    status = "✅ 完成" if success else "❌ 失败"
    print(f"\n{status} {phase_name}")
    print("-" * 80)

def print_final_summary(
    topic: str,
    session_dir: str,
    total_phases: int,
    imaging_result: Optional[Dict[str, Any]] = None
):
    """打印最终摘要"""
    print("\n" + "🎉" * 20)
    print("🎯 内容生产流水线执行完成!")
    print("🎉" * 20)
    print(f"\n📝 主题: {topic}")
    print(f"📁 输出目录: {session_dir}")
    print(f"⚙️ 执行阶段: {total_phases}/3")
    
    if imaging_result:
        print(f"🖼️ 生成图片: {imaging_result.get('total_images', 0)} 张")
        if imaging_result.get('image_paths'):
            print("📸 图片文件:")
            for path in imaging_result['image_paths']:
                print(f"   - {os.path.basename(path)}")
    
    print(f"\n📂 查看完整结果: {session_dir}")
    print("=" * 80)

# ===================================
# 主程序逻辑
# ===================================

def main():
    """
    主程序入口函数
    
    协调整个内容生产流水线的执行：
    1. 解析命令行参数
    2. 初始化系统
    3. 创建会话目录
    4. 串联执行三个阶段
    5. 保存结果和生成摘要
    """
    global logger
    
    # ===================================
    # 1. 解析命令行参数
    # ===================================
    
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # ===================================
    # 2. 初始化系统
    # ===================================
    
    try:
        # 初始化日志系统
        logger = setup_logging(verbose=args.verbose)
        logger.info("日志系统初始化完成")
        
        # 确保目录存在
        if not ensure_directories():
            print("❌ 目录初始化失败")
            sys.exit(1)
        logger.info("目录结构检查完成")
        
        # 显示启动信息
        print("🚀 小红书内容自动化管线启动")
        print(f"📝 主题: {args.topic}")
        print(f"📁 输出目录: {args.output_dir}")
        print(f"🔄 强制重新生成: {'是' if args.force else '否'}")
        print(f"⏩ 跳过成像: {'是' if args.skip_imaging else '否'}")
        print(f"🔊 详细日志: {'是' if args.verbose else '否'}")
        
        logger.info(f"程序启动参数: topic={args.topic}, force={args.force}, skip_imaging={args.skip_imaging}")
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    # ===================================
    # 3. 创建会话目录
    # ===================================
    
    try:
        session_dir = create_session_directory(args.topic, args.output_dir)
        logger.info(f"会话目录已创建: {session_dir}")
        print(f"📂 会话目录: {session_dir}")
        
    except Exception as e:
        logger.error(f"创建会话目录失败: {e}")
        print(f"❌ 创建会话目录失败: {e}")
        sys.exit(1)
    
    # ===================================
    # 4. 执行内容生产流水线
    # ===================================
    
    total_phases = 2 if args.skip_imaging else 3
    strategy_result = None
    execution_result = None
    imaging_result = None
    
    try:
        # ===================================
        # 阶段1: 战略规划
        # ===================================
        
        print_phase_header("战略规划", 1, total_phases)
        logger.info("开始执行战略规划阶段")
        
        try:
            strategy_result = run_strategy_and_planning(args.topic)
            logger.info("战略规划阶段完成")
            print_phase_footer("战略规划", True)
            
        except Exception as e:
            logger.error(f"战略规划阶段失败: {e}")
            print_phase_footer("战略规划", False)
            raise
        
        # ===================================
        # 阶段2: 叙事与视觉执行
        # ===================================
        
        print_phase_header("叙事与视觉执行", 2, total_phases)
        logger.info("开始执行叙事与视觉生成阶段")
        
        try:
            execution_result = run_narrative_and_visual(
                blueprint=strategy_result,
                force_regenerate=args.force,
                force_html_only=False
            )
            logger.info("叙事与视觉执行阶段完成")
            print_phase_footer("叙事与视觉执行", True)
            
        except Exception as e:
            logger.error(f"叙事与视觉执行阶段失败: {e}")
            print_phase_footer("叙事与视觉执行", False)
            raise
        
        # ===================================
        # 阶段3: 高保真成像（可选）
        # ===================================
        
        if not args.skip_imaging:
            print_phase_header("高保真成像", 3, total_phases)
            logger.info("开始执行高保真成像阶段")
            
            try:
                # 提取HTML内容
                design_spec, html_content = execution_result
                
                # 执行成像
                imaging_result = run_high_fidelity_imaging(
                    html_content=html_content,
                    output_dir=session_dir,
                    page_selector=".page-to-screenshot",
                    filename_prefix="xiaohongshu_page"
                )
                
                if imaging_result["success"]:
                    logger.info(f"高保真成像阶段完成，生成 {imaging_result['total_images']} 张图片")
                    print_phase_footer("高保真成像", True)
                else:
                    logger.error(f"高保真成像阶段失败: {imaging_result.get('error_message', '未知错误')}")
                    print_phase_footer("高保真成像", False)
                    # 成像失败不中断流程，但记录错误
                    
            except Exception as e:
                logger.error(f"高保真成像阶段失败: {e}")
                print_phase_footer("高保真成像", False)
                # 成像失败不中断流程，但记录错误
                imaging_result = {
                    "success": False,
                    "error_message": str(e),
                    "total_images": 0,
                    "image_paths": []
                }
        
        # ===================================
        # 5. 保存结果和生成摘要
        # ===================================
        
        logger.info("开始保存会话结果")
        save_success = save_session_results(
            session_dir=session_dir,
            topic=args.topic,
            strategy_result=strategy_result,
            execution_result=execution_result,
            imaging_result=imaging_result
        )
        
        if save_success:
            logger.info("会话结果保存完成")
        else:
            logger.warning("会话结果保存部分失败")
        
        # 打印最终摘要
        print_final_summary(
            topic=args.topic,
            session_dir=session_dir,
            total_phases=total_phases,
            imaging_result=imaging_result
        )
        
        logger.info("内容生产流水线执行完成")
        
    except KeyboardInterrupt:
        logger.info("用户中断程序执行")
        print("\n\n⚠️ 用户中断程序执行")
        sys.exit(130)  # 标准的键盘中断退出码
        
    except Exception as e:
        logger.error(f"流水线执行过程中发生错误: {e}")
        print(f"\n❌ 流水线执行失败: {e}")
        print("\n📋 详细错误信息:")
        traceback.print_exc()
        
        # 尝试保存部分结果
        if strategy_result and execution_result:
            logger.info("尝试保存部分结果")
            try:
                save_session_results(
                    session_dir=session_dir,
                    topic=args.topic,
                    strategy_result=strategy_result,
                    execution_result=execution_result,
                    imaging_result=imaging_result
                )
                print(f"📂 部分结果已保存到: {session_dir}")
            except Exception as save_error:
                logger.error(f"保存部分结果时也发生错误: {save_error}")
        
        sys.exit(1)

# ===================================
# 程序入口
# ===================================

if __name__ == "__main__":
    main()
