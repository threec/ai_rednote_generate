#!/usr/bin/env python3
"""
小红书内容自动化生成系统 - 主程序
集成RedCube AI工作流和Git自动化系统

功能特点:
1. 完整的内容生成流程
2. 多种工作流选择
3. 自动化Git提交
4. 详细的日志记录
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

from modules.utils import get_logger
from modules.strategy import generate_content_strategy
from modules.execution import execute_content_creation
from modules.publisher import publish_content
from modules.git_automation import get_git_automation, commit_checkpoint

def main():
    parser = argparse.ArgumentParser(
        description="小红书内容自动化生成系统 V2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py -t "新手妈妈如何给宝宝添加辅食" --langchain-workflow --git-auto
  python main.py -t "如何培养孩子的阅读兴趣" --strategy-only --verbose
  python main.py -t "宝宝夜哭不止怎么办" --publish --git-auto
  python main.py -t "测试主题" --config custom_config.yaml --verbose
        """
    )
    
    # 必需参数
    parser.add_argument('-t', '--topic', required=True, 
                       help='内容主题')
    
    # 工作流选择
    workflow_group = parser.add_mutually_exclusive_group()
    workflow_group.add_argument('--langchain-workflow', action='store_true',
                               help='使用LangChain工作流 (RedCube AI V2.0)')
    workflow_group.add_argument('--traditional-workflow', action='store_true',
                               help='使用传统工作流')
    workflow_group.add_argument('--strategy-only', action='store_true',
                               help='仅生成策略')
    
    # Git自动化选项
    parser.add_argument('--git-auto', action='store_true',
                       help='启用Git自动化提交')
    parser.add_argument('--git-checkpoint', type=str,
                       help='创建Git检查点')
    parser.add_argument('--git-message', type=str,
                       help='手动Git提交消息')
    
    # 其他选项
    parser.add_argument('--publish', action='store_true',
                       help='发布内容到小红书')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    parser.add_argument('--force-regenerate', action='store_true',
                       help='强制重新生成')
    parser.add_argument('--config', type=str,
                       help='配置文件路径')
    parser.add_argument('--validate-config', action='store_true',
                       help='验证配置文件并退出')
    
    args = parser.parse_args()
    
    try:
        # 初始化核心组件
        try:
            from modules.core.config import initialize_config, get_config, get_config_value
            from modules.core.exceptions import get_exception_handler
            
            # 初始化配置系统
            config_file = args.config or "config.yaml"
            config = initialize_config(config_file)
            exception_handler = get_exception_handler()
            
            # 配置验证模式
            if args.validate_config:
                print("✅ 配置文件验证成功")
                print(f"📊 配置统计:")
                print(f"  - 配置项总数: {len(config.get_all_config())}")
                print(f"  - 引擎启用数: {sum(1 for k, v in config.get_all_config().items() if k.startswith('engines.') and k.endswith('.enabled') and v)}")
                print(f"  - Git自动化: {'启用' if get_config_value('git.auto_commit', True) else '禁用'}")
                return
            
            # 设置日志级别
            logger = get_logger()
            if args.verbose:
                logger.info("🚀 小红书内容自动化生成系统 V2.0 启动...")
                logger.info(f"📋 使用配置文件: {config_file}")
                logger.info(f"🔧 核心组件已初始化")
                
        except ImportError as e:
            # 回退到传统模式
            logger = get_logger()
            logger.warning(f"⚠️ 核心组件导入失败，回退到传统模式: {str(e)}")
            config = None
            exception_handler = None
    
    # 初始化Git自动化
    git_auto = None
    if args.git_auto:
        git_auto = get_git_automation()
        logger.info("📝 Git自动化已启用")
    
    # 手动Git操作
    if args.git_checkpoint:
        if not git_auto:
            git_auto = get_git_automation()
        result = git_auto.create_commit_checkpoint(args.git_checkpoint)
        if result["success"]:
            logger.info(f"✅ 检查点创建成功: {args.git_checkpoint}")
        else:
            logger.error(f"❌ 检查点创建失败: {result['message']}")
        return
    
    if args.git_message:
        if not git_auto:
            git_auto = get_git_automation()
        result = git_auto.manual_commit(args.git_message)
        if result["success"]:
            logger.info(f"✅ 手动提交成功: {args.git_message}")
        else:
            logger.error(f"❌ 手动提交失败: {result['message']}")
        return
    
        # 开始工作流
        if args.git_auto:
            commit_checkpoint(f"开始内容生成 - {args.topic}")
        
        # 选择工作流
        if args.langchain_workflow:
            result = run_langchain_workflow(args, logger, git_auto)
        elif args.traditional_workflow:
            result = run_traditional_workflow(args, logger, git_auto)
        elif args.strategy_only:
            result = run_strategy_only(args, logger, git_auto)
        else:
            # 默认使用LangChain工作流
            logger.info("未指定工作流，使用默认的LangChain工作流")
            result = run_langchain_workflow(args, logger, git_auto)
        
        # 发布内容
        if args.publish and result.get("success"):
            logger.info("📤 准备发布内容...")
            if args.git_auto:
                commit_checkpoint(f"准备发布 - {args.topic}")
            
            try:
                from modules.publisher import publish_content
                publish_result = publish_content(result)
                if publish_result.get("success"):
                    logger.info("✅ 内容发布成功")
                    if args.git_auto and git_auto:
                        git_auto.auto_commit(f"完成内容发布 - {args.topic}", "feat")
                else:
                    logger.error("❌ 内容发布失败")
            except ImportError:
                logger.warning("⚠️ 发布模块未找到，跳过发布步骤")
        
        # 最终提交
        if args.git_auto and git_auto and result.get("success"):
            final_commit = git_auto.auto_commit(
                f"完成内容生成项目 - {args.topic}", "feat"
            )
            if final_commit["success"]:
                logger.info("🎉 项目完成，所有变更已提交Git")
        
        logger.info("✅ 程序执行完成")
        
    except Exception as e:
        logger.error(f"❌ 程序执行失败: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def run_langchain_workflow(args, logger, git_auto):
    """运行LangChain工作流"""
    logger.info("🔄 启动LangChain工作流 (RedCube AI)")
    
    try:
        # 延迟导入LangChain依赖
        from modules.langchain_workflow import create_redcube_workflow
        from modules.models import get_api_key
        
        # 获取API密钥
        api_key = get_api_key()
        if not api_key:
            logger.error("❌ 未找到API密钥，请配置GOOGLE_API_KEY环境变量")
            return {"success": False, "error": "API密钥未配置"}
        
        # 创建工作流
        workflow = create_redcube_workflow(api_key)
        
        # 配置Git自动化
        if git_auto:
            workflow.configure_git_automation(
                auto_commit=True,
                commit_on_engine_complete=True,
                commit_on_major_changes=True
            )
        
        # 执行工作流
        import asyncio
        result = asyncio.run(workflow.execute_workflow(
            topic=args.topic,
            enable_git=bool(git_auto)
        ))
        
        logger.info("🎯 LangChain工作流执行完成")
        return {"success": True, "result": result}
        
    except ImportError as e:
        logger.error(f"❌ LangChain模块导入失败: {str(e)}")
        logger.info("💡 请确保已安装LangChain依赖: pip install -r requirements.txt")
        return {"success": False, "error": "LangChain依赖未安装"}
    except Exception as e:
        logger.error(f"❌ LangChain工作流执行失败: {str(e)}")
        return {"success": False, "error": str(e)}

def run_traditional_workflow(args, logger, git_auto):
    """运行传统工作流"""
    logger.info("🔄 启动传统工作流")
    
    try:
        # 1. 策略生成
        logger.info("📊 生成内容策略...")
        strategy_result = generate_content_strategy(args.topic)
        
        if git_auto:
            git_auto.auto_commit(f"生成内容策略 - {args.topic}", "feat")
        
        # 2. 内容创作
        logger.info("🎨 执行内容创作...")
        creation_result = execute_content_creation(
            topic=args.topic,
            strategy=strategy_result,
            force_regenerate=args.force_regenerate
        )
        
        if git_auto:
            git_auto.auto_commit(f"完成内容创作 - {args.topic}", "feat")
        
        logger.info("🎯 传统工作流执行完成")
        return {
            "success": True,
            "strategy": strategy_result,
            "creation": creation_result
        }
        
    except Exception as e:
        logger.error(f"❌ 传统工作流执行失败: {str(e)}")
        return {"success": False, "error": str(e)}

def run_strategy_only(args, logger, git_auto):
    """仅运行策略生成"""
    logger.info("🔄 仅生成内容策略")
    
    try:
        strategy_result = generate_content_strategy(args.topic)
        
        if git_auto:
            git_auto.auto_commit(f"生成内容策略 - {args.topic}", "feat")
        
        logger.info("🎯 策略生成完成")
        return {"success": True, "strategy": strategy_result}
        
    except Exception as e:
        logger.error(f"❌ 策略生成失败: {str(e)}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    main()
