#!/usr/bin/env python3
"""
Git提交工具 - 便捷的Git自动化管理

用法:
    python git_commit_tool.py --auto                    # 自动提交
    python git_commit_tool.py --message "修复bug"       # 手动提交
    python git_commit_tool.py --checkpoint "测试完成"   # 创建检查点
    python git_commit_tool.py --status                  # 查看状态
    python git_commit_tool.py --history                 # 查看历史
    python git_commit_tool.py --config                  # 配置设置
"""

import argparse
import sys
import json
from pathlib import Path

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

from modules.git_automation import get_git_automation
from modules.utils import get_logger

def main():
    parser = argparse.ArgumentParser(
        description="Git自动化提交工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python git_commit_tool.py --auto                    # 自动提交所有变更
  python git_commit_tool.py --message "修复引擎Bug"    # 手动提交并指定消息
  python git_commit_tool.py --checkpoint "架构升级"    # 创建检查点
  python git_commit_tool.py --status                  # 查看Git状态
  python git_commit_tool.py --history                 # 查看提交历史
  python git_commit_tool.py --config --auto-commit=false  # 禁用自动提交
        """
    )
    
    # 主要操作选项
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--auto', action='store_true', 
                      help='自动分析并提交变更')
    group.add_argument('--message', '-m', type=str, 
                      help='手动提交并指定提交消息')
    group.add_argument('--checkpoint', '-c', type=str, 
                      help='创建检查点提交')
    group.add_argument('--status', '-s', action='store_true',
                      help='查看Git状态')
    group.add_argument('--history', action='store_true',
                      help='查看提交历史')
    group.add_argument('--config', action='store_true',
                      help='配置Git自动化设置')
    
    # 附加选项
    parser.add_argument('--type', '-t', type=str, default='feat',
                       choices=['feat', 'fix', 'refactor', 'docs', 'style', 'test', 'chore'],
                       help='提交类型 (默认: feat)')
    parser.add_argument('--force', '-f', action='store_true',
                       help='强制执行操作')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    
    # 配置选项
    parser.add_argument('--auto-commit', type=str, choices=['true', 'false'],
                       help='启用/禁用自动提交')
    parser.add_argument('--engine-commit', type=str, choices=['true', 'false'],
                       help='启用/禁用引擎完成提交')
    parser.add_argument('--max-files', type=int,
                       help='单次提交最大文件数')
    
    args = parser.parse_args()
    
    # 获取Git自动化实例
    git_auto = get_git_automation()
    logger = get_logger("git_commit_tool")
    
    if args.verbose:
        logger.info("Git提交工具启动...")
    
    try:
        if args.auto:
            # 自动提交
            result = git_auto.auto_commit(
                context="手动触发自动提交",
                commit_type=args.type,
                force=args.force
            )
            print_result(result, "自动提交")
            
        elif args.message:
            # 手动提交
            result = git_auto.manual_commit(args.message)
            print_result(result, "手动提交")
            
        elif args.checkpoint:
            # 检查点提交
            result = git_auto.create_commit_checkpoint(args.checkpoint)
            print_result(result, "检查点提交")
            
        elif args.status:
            # 查看状态
            status = git_auto.check_git_status()
            print_status(status)
            
        elif args.history:
            # 查看历史
            history = git_auto.get_commit_history(10)
            print_history(history)
            
        elif args.config:
            # 配置设置
            config_updates = {}
            if args.auto_commit:
                config_updates['auto_commit'] = args.auto_commit == 'true'
            if args.engine_commit:
                config_updates['commit_on_engine_complete'] = args.engine_commit == 'true'
            if args.max_files:
                config_updates['max_files_per_commit'] = args.max_files
            
            if config_updates:
                git_auto.configure_auto_commit(**config_updates)
                print(f"✅ 配置已更新: {config_updates}")
            else:
                print_config(git_auto.commit_config)
                
    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")
        sys.exit(1)

def print_result(result: dict, operation: str):
    """打印操作结果"""
    if result["success"]:
        print(f"✅ {operation}成功")
        if "commit_hash" in result:
            print(f"📝 提交Hash: {result['commit_hash'][:8]}...")
        if "files_count" in result:
            print(f"📊 文件数量: {result['files_count']}")
        if "commit_message" in result:
            print(f"💬 提交信息: {result['commit_message'].split()[0]}")
    else:
        print(f"❌ {operation}失败: {result['message']}")

def print_status(status: dict):
    """打印Git状态"""
    print("📋 Git状态:")
    print(f"  有变更: {'是' if status['has_changes'] else '否'}")
    
    if status['has_changes']:
        print(f"  变更文件: {status['total_files']}个")
        print("\n📁 变更列表:")
        
        for change in status['changes']:
            icon = {
                "新增": "🆕",
                "修改": "📝", 
                "删除": "🗑️",
                "重命名": "📄",
                "未跟踪": "❓"
            }.get(change['type'], "📄")
            
            print(f"  {icon} {change['type']}: {change['file']}")

def print_history(history: list):
    """打印提交历史"""
    print("📚 提交历史:")
    
    for i, commit in enumerate(history, 1):
        print(f"\n{i}. {commit['hash'][:8]}... ({commit['date'][:10]})")
        print(f"   👤 {commit['author']}")
        print(f"   💬 {commit['message']}")

def print_config(config: dict):
    """打印配置信息"""
    print("⚙️ 当前配置:")
    
    config_descriptions = {
        "auto_commit": "自动提交",
        "commit_on_engine_complete": "引擎完成提交",
        "commit_on_major_changes": "重大变更提交",
        "commit_on_bug_fixes": "Bug修复提交",
        "max_files_per_commit": "单次提交最大文件数"
    }
    
    for key, value in config.items():
        description = config_descriptions.get(key, key)
        status = "✅" if value else "❌" if isinstance(value, bool) else "📝"
        print(f"  {status} {description}: {value}")

if __name__ == "__main__":
    main() 