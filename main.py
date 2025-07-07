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
import json

# 配置导入
from config import validate_config, OUTPUT_DIR, LOGS_DIR, CACHE_DIR, TEMPLATES_DIR

# 模块导入
from modules.strategy import run_strategy_and_planning
from modules.execution import execute_narrative_pipeline, initialize_execution_module
from modules.imaging import process_screenshot_config, check_imaging_capabilities, initialize_imaging_module
from modules.utils import get_logger, setup_logging
from modules.publisher import publish_content_sync

# ===================================
# 全局配置
# ===================================

logger = get_logger(__name__)

# ===================================
# 导入LangChain工作流（延迟导入避免依赖问题）
# ===================================

def get_langchain_workflow():
    """获取LangChain工作流实例（延迟导入）"""
    try:
        from modules.langchain_workflow import RedCubeWorkflow
        from modules.redcube_templates import redcube_templates
        return RedCubeWorkflow, redcube_templates
    except ImportError as e:
        logger.error(f"LangChain工作流模块导入失败: {e}")
        raise ImportError(f"请安装相关依赖: pip install langchain langchain-core langchain-google-genai langchain-community")

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
    output_dir: Optional[str] = None,
    auto_publish: bool = False
) -> Dict[str, Any]:
    """
    执行小红书内容自动化管线
    
    Args:
        topic (str): 内容主题
        force (bool): 是否强制重新生成，忽略缓存
        enable_imaging (bool): 是否启用成像功能
        output_dir (Optional[str]): 输出目录
        auto_publish (bool): 是否启用自动发布
        
    Returns:
        Dict[str, Any]: 执行结果
    """
    logger.info(f"程序启动参数: topic={topic}, force={force}, enable_imaging={enable_imaging}")
    
    # 生成时间戳用于会话标识
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 初始化结果对象
    final_result = {
        "status": "in_progress",
        "topic": topic,
        "timestamp": timestamp,
        "strategy_result": None,
        "execution_result": None,
        "imaging_result": None,
        "auto_publish": None,
        "session_directory": None,
        "output_directory": None,
        "total_images": 0
    }
    
    try:
        # 使用默认输出目录（如果未指定）
        if output_dir is None:
            output_dir = OUTPUT_DIR
        
        # 创建会话目录
        session_dir = os.path.join(output_dir, f"{topic}_{timestamp}")
        os.makedirs(session_dir, exist_ok=True)
        
        print(f"📂 会话目录: {session_dir}")
        
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
        # 阶段 4: 自动发布（可选）
        # ===================================
        if auto_publish:
            print("\n" + "=" * 80)
            print("🚀 阶段 4/4: 自动发布")  
            print("=" * 80)
            logger.info("开始执行自动发布阶段")
            
            try:
                # 读取生成的内容
                titles_file = os.path.join(output_dir, "xiaohongshu_titles.txt")
                content_file = os.path.join(output_dir, "xiaohongshu_content.txt")
                
                if not os.path.exists(titles_file) or not os.path.exists(content_file):
                    logger.error("缺少发布所需的文本文件")
                    print("❌ 缺少发布所需的文本文件")
                    raise Exception("缺少发布所需的文本文件")
                
                # 读取标题和内容
                with open(titles_file, 'r', encoding='utf-8') as f:
                    titles_content = f.read().strip()
                    # 提取第一个标题作为发布标题
                    first_title = titles_content.split('\n')[0].replace('1. ', '').strip()
                
                with open(content_file, 'r', encoding='utf-8') as f:
                    publish_content = f.read().strip()
                
                # 获取图片文件路径
                images_dir = os.path.join(output_dir, "images") if imaging_result else None
                image_paths = []
                
                if images_dir and os.path.exists(images_dir):
                    for file in os.listdir(images_dir):
                        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                            image_paths.append(os.path.join(images_dir, file))
                    image_paths.sort()  # 确保顺序一致
                
                if not image_paths:
                    logger.error("未找到可发布的图片文件")
                    print("❌ 未找到可发布的图片文件")
                    raise Exception("未找到可发布的图片文件")
                
                logger.info(f"准备发布: 标题='{first_title}', 内容长度={len(publish_content)}, 图片数量={len(image_paths)}")
                
                # 执行自动发布
                print(f"📝 发布标题: {first_title}")
                print(f"📄 内容长度: {len(publish_content)} 字符")
                print(f"📸 图片数量: {len(image_paths)} 张")
                print("🔄 开始自动发布...")
                
                publish_result = publish_content_sync(
                    image_paths=image_paths,
                    title=first_title,
                    content=publish_content,
                    headless=False  # 显示浏览器，便于用户监控
                )
                
                if publish_result["success"]:
                    print("✅ 完成 自动发布")
                    print("🎉 内容已成功发布到小红书！")
                    final_result["auto_publish"] = publish_result
                    
                    # 保存发布记录
                    publish_record = {
                        "timestamp": datetime.now().isoformat(),
                        "topic": topic,
                        "title": first_title,
                        "content_length": len(publish_content),
                        "image_count": len(image_paths),
                        "publish_result": publish_result
                    }
                    
                    publish_record_file = os.path.join(output_dir, "publish_record.json")
                    with open(publish_record_file, 'w', encoding='utf-8') as f:
                        json.dump(publish_record, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"发布记录已保存: {publish_record_file}")
                    
                else:
                    print("❌ 自动发布失败")
                    print(f"失败原因: {publish_result.get('message', '未知错误')}")
                    print("💡 建议: 检查网络连接和小红书登录状态")
                    
                    final_result["auto_publish"] = publish_result
                    logger.error(f"自动发布失败: {publish_result}")
                
            except ImportError as e:
                logger.error(f"自动发布模块导入失败: {e}")
                print("❌ 自动发布模块不可用")
                print("💡 请确保已安装 playwright: pip install playwright")
                final_result["auto_publish"] = {"success": False, "message": "模块导入失败"}
                
            except Exception as e:
                logger.error(f"自动发布过程中发生错误: {e}")
                print(f"❌ 自动发布失败: {str(e)}")
                final_result["auto_publish"] = {"success": False, "message": str(e)}
        
        # ===================================
        # 生成最终报告
        # ===================================
        print("\n" + "=" * 80)
        print("🎉 流水线执行完成")
        print("=" * 80)
        
        # 最终更新结果对象
        final_result.update({
            "status": "success",
            "strategy_result": strategy_result,
            "execution_result": execution_result,
            "imaging_result": imaging_result,
            "session_directory": session_dir,
            "output_directory": execution_result.get("output_directory"),
            "total_images": execution_result.get("total_images", 0)
        })
        
        # 显示最终信息
        print(f"📝 主题: {topic}")
        print(f"📁 输出目录: {execution_result.get('output_directory')}")
        print(f"🖼️ 生成内容图片: {execution_result.get('total_images', 0)}张")
        
        if imaging_result and imaging_result.get("status") == "success":
            summary = imaging_result.get("summary", {})
            if isinstance(summary, dict):
                print(f"📸 截图文件: {summary.get('successful_count', 0)}张")
            else:
                print(f"📸 截图文件: 已完成")
            print(f"📁 图片目录: {imaging_result.get('images_directory', '')}")
        
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

def run_langchain_workflow(
    topic: str,
    output_dir: Optional[str] = None,
    enable_imaging: bool = False
) -> Dict[str, Any]:
    """
    执行RedCube AI工作流
    
    Args:
        topic (str): 内容主题
        output_dir (Optional[str]): 输出目录
        enable_imaging (bool): 是否启用成像功能
        
    Returns:
        Dict[str, Any]: 执行结果
    """
    logger.info(f"启动RedCube AI工作流: topic={topic}, enable_imaging={enable_imaging}")
    
    # 生成时间戳用于会话标识
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 初始化结果对象
    result = {
        "status": "in_progress",
        "topic": topic,
        "timestamp": timestamp,
        "output_directory": None,
        "total_images": 0,
        "workflow_result": None
    }
    
    try:
        # 使用默认输出目录（如果未指定）
        if output_dir is None:
            output_dir = OUTPUT_DIR
        
        # 创建会话目录
        session_dir = os.path.join(output_dir, f"redcube_{topic}_{timestamp}")
        os.makedirs(session_dir, exist_ok=True)
        
        print(f"📂 RedCube会话目录: {session_dir}")
        
        # ===================================
        # RedCube AI 8引擎工作流
        # ===================================
        print("\n" + "=" * 80)
        print("🎯 RedCube AI 8引擎工作流启动")
        print("=" * 80)
        
        # 获取LangChain工作流模块（延迟导入）
        logger.info("正在导入RedCube AI工作流模块...")
        RedCubeWorkflow, redcube_templates = get_langchain_workflow()
        
        # 导入同步工作流函数
        from modules.langchain_workflow import run_redcube_workflow_sync
        logger.info("RedCube AI工作流模块导入成功")
        
        # 执行工作流
        logger.info(f"开始执行RedCube AI工作流，主题: {topic}")
        workflow_result = run_redcube_workflow_sync(topic, force_regenerate=False)
        logger.info("RedCube AI工作流执行成功")
        
        if not workflow_result:
            error_msg = "工作流返回空结果"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        print("✅ RedCube AI工作流执行完成")
        logger.info("RedCube AI工作流核心逻辑执行完成")
        
        # ===================================
        # 生成HTML页面
        # ===================================
        print("\n" + "=" * 80)
        print("🎨 生成专业级HTML页面")
        print("=" * 80)
        
        # 提取工作流结果
        workflow_data = workflow_result
        strategic_phase = workflow_data.get("strategic_phase", {})
        narrative_phase = workflow_data.get("narrative_phase", {})
        
        logger.info("开始提取工作流结果构建模板数据")
        
        # 安全提取数据的辅助函数
        def safe_get(data, keys, default=None):
            """安全地从嵌套字典中获取数据"""
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            return current if current is not None else default
        
        # 准备模板数据
        template_data = {
            "cover": {
                "title": safe_get(narrative_phase, ["narrative_prism", "hook", "title"], topic),
                "subtitle": safe_get(narrative_phase, ["narrative_prism", "hook", "subtitle"], "专业内容分享"),
                "tags": [safe_get(strategic_phase, ["strategy_compass", "content_strategy", "main_direction"], "实用分享")],
                "author": safe_get(strategic_phase, ["persona_core", "persona_profile", "name"], "专业分享者"),
                "icon": "🎯"
            },
            "content_pages": [],
            "comparison": None,
            "final": {
                "title": "总结与行动",
                "subtitle": "一起成长，共同进步",
                "key_points": safe_get(strategic_phase, ["insight_distiller", "big_idea", "core_insights"], ["要点1", "要点2", "要点3", "要点4"])[:4],
                "cta_text": "觉得有用请点赞收藏！",
                "cta_action": "评论区分享你的经验～",
                "author": safe_get(strategic_phase, ["persona_core", "persona_profile", "name"], "专业分享者"),
                "celebration_icon": "🎉"
            }
        }
        
        # 构建内容页面数据
        story_flow = safe_get(narrative_phase, ["narrative_prism", "story_flow"], [])
        if not story_flow:
            # 如果没有story_flow，创建基础内容页面
            content_insights = safe_get(strategic_phase, ["insight_distiller", "core_insights"], [])
            story_flow = [
                {
                    "title": f"核心要点 {i+1}",
                    "content": [insight] if isinstance(insight, str) else [str(insight)]
                } for i, insight in enumerate(content_insights[:4])
            ]
        
        for i, segment in enumerate(story_flow[:4]):  # 最多4个内容页
            content_list = segment.get("content", [])
            if isinstance(content_list, str):
                content_list = [content_list]
            elif not isinstance(content_list, list):
                content_list = [str(content_list)]
            
            page_data = {
                "title": segment.get("title", f"内容页 {i+1}"),
                "page_number": i + 2,  # 封面是1，从2开始
                "content_items": [
                    {
                        "icon": "✅",
                        "title": f"要点 {j+1}",
                        "description": str(point)
                    } for j, point in enumerate(content_list[:3])  # 每页最多3个要点
                ],
                "tip_text": f"重要提示：{segment.get('tip', '记住这些关键要点')}"
            }
            template_data["content_pages"].append(page_data)
        
        logger.info(f"模板数据构建完成，包含{len(template_data['content_pages'])}个内容页")
        
        # 生成HTML文件
        html_files = []
        
        # 1. 封面页
        cover_html = redcube_templates.generate_cover_page(template_data["cover"])
        cover_file = os.path.join(session_dir, "01_cover.html")
        with open(cover_file, 'w', encoding='utf-8') as f:
            f.write(cover_html)
        html_files.append(cover_file)
        print(f"✅ 封面页: {cover_file}")
        
        # 2. 内容页
        for i, page_data in enumerate(template_data["content_pages"]):
            content_html = redcube_templates.generate_content_page(page_data)
            content_file = os.path.join(session_dir, f"{i+2:02d}_content.html")
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(content_html)
            html_files.append(content_file)
            print(f"✅ 内容页 {i+1}: {content_file}")
        
        # 3. 结尾页
        final_html = redcube_templates.generate_final_page(template_data["final"])
        final_file = os.path.join(session_dir, f"{len(template_data['content_pages'])+2:02d}_final.html")
        with open(final_file, 'w', encoding='utf-8') as f:
            f.write(final_html)
        html_files.append(final_file)
        print(f"✅ 结尾页: {final_file}")
        
        # 保存工作流结果
        workflow_json_file = os.path.join(session_dir, "redcube_workflow_result.json")
        with open(workflow_json_file, 'w', encoding='utf-8') as f:
            json.dump(workflow_result, f, ensure_ascii=False, indent=2)
        print(f"✅ 工作流结果: {workflow_json_file}")
        
        # ===================================
        # 可选：生成图片
        # ===================================
        total_images = 0
        if enable_imaging:
            print("\n" + "=" * 80)
            print("📸 生成高保真图片")
            print("=" * 80)
            
            # 检查成像功能可用性
            capabilities = check_imaging_capabilities()
            available_methods = capabilities.get("available_method_names", [])
            
            if available_methods:
                print(f"🔧 检测到可用成像方案: {', '.join(available_methods)}")
                
                # 创建截图配置
                images_dir = os.path.join(session_dir, "images")
                os.makedirs(images_dir, exist_ok=True)
                
                screenshot_config = {
                    "config_version": "1.0",
                    "screenshot_method": available_methods[0],
                    "output_directory": images_dir,
                    "screenshot_files": []
                }
                
                for i, html_file in enumerate(html_files):
                    output_image = os.path.join(images_dir, f"page_{i+1:02d}.png")
                    screenshot_config["screenshot_files"].append({
                        "input_path": html_file,
                        "output_path": output_image,
                        "width": 448,
                        "height": 597
                    })
                
                # 保存截图配置
                screenshot_config_file = os.path.join(session_dir, "screenshot_config.json")
                with open(screenshot_config_file, 'w', encoding='utf-8') as f:
                    json.dump(screenshot_config, f, ensure_ascii=False, indent=2)
                
                # 执行截图
                try:
                    imaging_result = process_screenshot_config(screenshot_config_file)
                    
                    if imaging_result["status"] == "success":
                        summary = imaging_result.get("summary", {})
                        total_images = summary.get("successful_count", 0)
                        print(f"✅ 截图完成: {total_images}/{summary.get('total_files', 0)}")
                        print(f"📁 图片目录: {images_dir}")
                    else:
                        print(f"⚠️ 截图失败: {imaging_result.get('error', '未知错误')}")
                        
                except Exception as e:
                    print(f"⚠️ 截图过程中发生错误: {str(e)}")
            else:
                print("⚠️ 没有可用的成像方案")
                print("💡 提示: 安装 playwright 以启用高质量截图功能")
        
        # 更新结果
        result.update({
            "status": "success",
            "output_directory": session_dir,
            "total_images": total_images,
            "workflow_result": workflow_result,
            "html_files": html_files
        })
        
        return result
        
    except Exception as e:
        error_msg = f"RedCube AI工作流执行失败: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        result.update({
            "status": "error",
            "error": error_msg
        })
        return result

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
  python main.py --screenshot-only "output/宝宝第一次发烧怎么办_20250707_204312"

注意事项:
  - 首次运行建议先不启用成像功能，验证内容生成效果
  - 启用成像功能需要安装 playwright: pip install playwright 
  - --screenshot-only 可以对已生成的内容直接截图，无需重新生成
  - 生成的HTML文件可以手动截图或使用其他工具转换
        """
    )
    
    parser.add_argument(
        "-t", "--topic",
        type=str,
        required=False,
        help="内容主题（--screenshot-only模式下可选）"
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
        "--screenshot-only",
        type=str,
        help="只截图模式：指定现有输出目录路径，直接进行截图（不重新生成内容）"
    )
    
    parser.add_argument(
        "--auto-publish",
        action="store_true",
        help="启用自动发布功能，生成内容和图片后自动发布到小红书"
    )
    
    parser.add_argument(
        "--publish-only",
        type=str,
        help="只发布模式：指定现有输出目录路径，直接发布已生成的内容和图片"
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
    
    parser.add_argument(
        "--langchain-workflow",
        action="store_true",
        help="使用RedCube AI工作流系统（基于LangChain的8引擎架构）"
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 检查参数有效性
    if not args.screenshot_only and not args.publish_only and not args.topic:
        print("❌ 错误：必须提供 --topic 参数，或使用 --screenshot-only / --publish-only 模式")
        parser.print_help()
        sys.exit(1)
    
    # 如果使用LangChain工作流模式
    if args.langchain_workflow:
        print("🎯 RedCube AI工作流模式启动")
        print(f"📝 主题: {args.topic}")
        print(f"📁 输出目录: {args.output_dir or OUTPUT_DIR}")
        print(f"📸 启用成像: {'是' if args.enable_imaging else '否'}")
        print(f"🔊 详细日志: {'是' if args.verbose else '否'}")
        
        # 设置环境
        if not setup_environment():
            print("❌ 环境设置失败，程序退出")
            sys.exit(1)
        
        try:
            # 执行RedCube AI工作流
            result = run_langchain_workflow(
                topic=args.topic,
                output_dir=args.output_dir,
                enable_imaging=args.enable_imaging
            )
            
            # 根据结果设置退出码
            if result["status"] == "success":
                print("\n🎊 RedCube AI工作流成功完成！")
                print(f"📁 输出目录: {result['output_directory']}")
                if result['total_images'] > 0:
                    print(f"📸 生成图片: {result['total_images']} 张")
                print("🔥 专业级内容已准备就绪！")
                sys.exit(0)
            else:
                print(f"\n💥 RedCube AI工作流执行失败: {result.get('error', '未知错误')}")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\n🛑 用户中断RedCube AI工作流执行")
            logger.info("用户中断RedCube AI工作流执行")
            sys.exit(130)
        except Exception as e:
            print(f"\n💥 RedCube AI工作流执行过程中发生未捕获的错误: {str(e)}")
            logger.error(f"RedCube AI工作流未捕获的错误: {str(e)}")
            logger.error(traceback.format_exc())
            sys.exit(1)

    # 如果是只发布模式
    if args.publish_only:
        print("🚀 只发布模式启动")
        print(f"📁 目标目录: {args.publish_only}")
        
        # 设置环境
        if not setup_environment():
            print("❌ 环境设置失败，程序退出")
            sys.exit(1)
        
        # 检查目录和文件
        if not os.path.exists(args.publish_only):
            print(f"❌ 目标目录不存在: {args.publish_only}")
            sys.exit(1)
        
        titles_file = os.path.join(args.publish_only, "xiaohongshu_titles.txt")
        content_file = os.path.join(args.publish_only, "xiaohongshu_content.txt")
        images_dir = os.path.join(args.publish_only, "images")
        
        if not os.path.exists(titles_file) or not os.path.exists(content_file):
            print(f"❌ 缺少必要的文本文件")
            print(f"💡 请确保目录包含: xiaohongshu_titles.txt 和 xiaohongshu_content.txt")
            sys.exit(1)
        
        if not os.path.exists(images_dir):
            print(f"❌ 缺少图片目录: {images_dir}")
            sys.exit(1)
        
        # 获取图片文件
        image_paths = []
        for file in os.listdir(images_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_paths.append(os.path.join(images_dir, file))
        
        if not image_paths:
            print(f"❌ 图片目录中没有找到可用的图片文件")
            sys.exit(1)
        
        image_paths.sort()  # 确保顺序一致
        
        # 读取标题和内容
        try:
            with open(titles_file, 'r', encoding='utf-8') as f:
                titles_content = f.read().strip()
                first_title = titles_content.split('\n')[0].replace('1. ', '').strip()
            
            with open(content_file, 'r', encoding='utf-8') as f:
                publish_content = f.read().strip()
            
            print(f"📝 发布标题: {first_title}")
            print(f"📄 内容长度: {len(publish_content)} 字符")
            print(f"📸 图片数量: {len(image_paths)} 张")
            print("🔄 开始发布...")
            
            # 导入发布模块并执行发布
            try:
                from modules.publisher import publish_content_sync
                
                publish_result = publish_content_sync(
                    image_paths=image_paths,
                    title=first_title,
                    content=publish_content,
                    headless=False
                )
                
                if publish_result["success"]:
                    print("🎉 发布成功！")
                    
                    # 保存发布记录
                    publish_record = {
                        "timestamp": datetime.now().isoformat(),
                        "title": first_title,
                        "content_length": len(publish_content),
                        "image_count": len(image_paths),
                        "publish_result": publish_result
                    }
                    
                    publish_record_file = os.path.join(args.publish_only, "publish_record.json")
                    with open(publish_record_file, 'w', encoding='utf-8') as f:
                        json.dump(publish_record, f, ensure_ascii=False, indent=2)
                    
                    print(f"📋 发布记录已保存: {publish_record_file}")
                    sys.exit(0)
                else:
                    print("❌ 发布失败")
                    print(f"失败原因: {publish_result.get('message', '未知错误')}")
                    sys.exit(1)
                    
            except ImportError:
                print("❌ 自动发布模块不可用")
                print("💡 请确保已安装 playwright: pip install playwright")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ 读取文件或发布过程中发生错误: {str(e)}")
            sys.exit(1)

    # 如果是只截图模式
    if args.screenshot_only:
        print("📸 只截图模式启动")
        print(f"📁 目标目录: {args.screenshot_only}")
        
        # 设置环境
        if not setup_environment():
            print("❌ 环境设置失败，程序退出")
            sys.exit(1)
        
        # 查找screenshot_config.json文件
        screenshot_config_path = os.path.join(args.screenshot_only, "screenshot_config.json")
        
        if not os.path.exists(screenshot_config_path):
            print(f"❌ 找不到截图配置文件: {screenshot_config_path}")
            print("💡 请确保目录包含完整的生成内容")
            sys.exit(1)
        
        # 检查成像功能可用性
        capabilities = check_imaging_capabilities()
        available_methods = capabilities.get("available_method_names", [])
        
        if not available_methods:
            print("⚠️ 没有可用的成像方案")
            print("💡 提示: 安装 playwright 以启用高质量截图功能")
            sys.exit(1)
        
        print(f"🔧 检测到可用成像方案: {', '.join(available_methods)}")
        
        # 执行截图
        try:
            imaging_result = process_screenshot_config(screenshot_config_path)
            
            if imaging_result["status"] == "success":
                summary = imaging_result.get("summary", {})
                print("✅ 截图完成")
                print(f"📸 成功截图: {summary.get('successful_count', 0)}/{summary.get('total_files', 0)}")
                print(f"📁 图片目录: {imaging_result.get('images_directory', '')}")
                sys.exit(0)
            else:
                print("❌ 截图失败")
                print(f"错误: {imaging_result.get('error', '未知错误')}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ 截图过程中发生错误: {str(e)}")
            sys.exit(1)

    # 正常模式的显示信息
    print("🚀 小红书内容自动化管线启动")
    print(f"📝 主题: {args.topic}")
    print(f"📁 输出目录: {args.output_dir or OUTPUT_DIR}")
    print(f"🔄 强制重新生成: {'是' if args.force else '否'}")
    print(f"📸 启用成像: {'是' if args.enable_imaging else '否'}")
    print(f"🚀 启用自动发布: {'是' if args.auto_publish else '否'}")
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
            output_dir=args.output_dir,
            auto_publish=args.auto_publish
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
