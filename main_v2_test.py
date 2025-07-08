#!/usr/bin/env python3
"""
小红书内容自动化生成系统 V2.0 - 测试主程序
专注于测试新的V2.0架构和LangChain工作流

使用方法：
python main_v2_test.py "宝宝辅食添加的正确步骤"
"""

import argparse
import sys
import os
import asyncio
from pathlib import Path

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

def main():
    parser = argparse.ArgumentParser(description="RedCube AI V2.0 测试程序")
    parser.add_argument('topic', help='内容主题')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--config', type=str, help='配置文件路径')
    args = parser.parse_args()
    
    # 设置测试模式
    os.environ["REDCUBE_TEST_MODE"] = "true"
    
    print("🚀 RedCube AI V2.0 测试开始")
    print("=" * 50)
    
    try:
        # 1. 测试核心配置系统
        print("🔧 初始化核心组件...")
        from modules.core.config import initialize_config, get_config_value
        from modules.utils import get_logger
        
        config_file = args.config or "config.yaml"
        config = initialize_config(config_file)
        logger = get_logger("main_v2")
        
        print(f"✅ 配置系统初始化成功")
        print(f"📋 配置文件: {config_file}")
        
        # 2. 测试LangChain工作流
        print("\n🤖 启动V2.0 LangChain工作流...")
        
        try:
            from modules.langchain_workflow import RedCubeWorkflow
            
            # 创建工作流实例
            workflow = RedCubeWorkflow()
            
            print(f"✅ 工作流创建成功")
            print(f"🎯 主题: {args.topic}")
            
            # 执行工作流
            print("\n▶️ 执行8引擎工作流...")
            result = asyncio.run(workflow.execute_workflow(
                topic=args.topic,
                enable_git=False  # 测试模式下禁用Git
            ))
            
            if result.get("success"):
                print("\n🎉 工作流执行成功！")
                print(f"📊 结果概览:")
                
                # 显示各引擎结果
                for engine_name, engine_result in result.get("results", {}).items():
                    if engine_result and engine_result.get("content"):
                        content_length = len(str(engine_result["content"]))
                        print(f"  ✅ {engine_name}: {content_length}字符")
                    else:
                        print(f"  ❌ {engine_name}: 未完成")
                
                # 显示最终输出信息
                if "final_output" in result:
                    final_output = result["final_output"]
                    print(f"\n📝 最终输出:")
                    print(f"  - 输出目录: {final_output.get('output_dir', 'N/A')}")
                    print(f"  - 文件数量: {len(final_output.get('files', []))}")
                
            else:
                print(f"\n❌ 工作流执行失败: {result.get('error', '未知错误')}")
                return 1
                
        except ImportError as e:
            print(f"❌ LangChain工作流导入失败: {e}")
            print("💡 请确保已安装所需依赖")
            return 1
        except Exception as e:
            print(f"❌ 工作流执行异常: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
        
        print("\n✅ V2.0系统测试完成")
        return 0
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 