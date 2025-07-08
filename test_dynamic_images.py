#!/usr/bin/env python3
"""
测试动态图片数量功能
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

async def test_dynamic_image_count():
    """测试动态图片数量功能"""
    
    print("🚀 开始测试动态图片数量功能...")
    
    # 测试主题 - 选择中等复杂度的主题
    topic = "宝宝辅食过敏怎么预防和处理"
    print(f"📋 测试主题: {topic}")
    
    try:
        # 导入模块
        from modules.langchain_workflow import create_redcube_workflow
        
        print("✅ 模块导入成功")
        
        # 创建工作流
        workflow = create_redcube_workflow()
        print("✅ 工作流创建成功")
        
        # 执行工作流
        print("⚡ 开始执行工作流...")
        result = await workflow.execute_workflow(topic, verbose=True)
        
        # 分析结果
        if result.get("success", False):
            print("✅ 工作流执行成功！")
            
            # 检查策略结果中的图片数量
            if "strategy_result" in result:
                strategy = result["strategy_result"]
                creative_blueprint = strategy.get("creative_blueprint", {})
                visual_plan = creative_blueprint.get("visual_plan", {})
                image_count = visual_plan.get("image_count")
                
                print(f"📊 AI智能决定的图片数量: {image_count}")
                
                # 显示图片规划详情
                images = visual_plan.get("images", [])
                if images:
                    print(f"📸 图片规划详情 (共{len(images)}张):")
                    for i, img in enumerate(images[:5], 1):  # 只显示前5张
                        purpose = img.get("purpose", "未指定功能")
                        print(f"   {i}. {purpose}")
                    if len(images) > 5:
                        print(f"   ... 还有{len(images)-5}张图片")
                
                # 检查复杂度评估
                content_strategy = creative_blueprint.get("content_strategy", {})
                complexity = content_strategy.get("complexity_assessment", "未评估")
                print(f"🧠 主题复杂度评估: {complexity}")
            
            # 检查输出目录
            if "output_directory" in result:
                output_dir = result["output_directory"]
                print(f"📁 输出目录: {output_dir}")
                
                # 检查生成的文件
                if os.path.exists(output_dir):
                    files = os.listdir(output_dir)
                    html_files = [f for f in files if f.endswith('.html')]
                    print(f"📄 生成的HTML文件数量: {len(html_files)}")
                    
                    # 读取设计规范文件检查图片数量
                    design_spec_file = os.path.join(output_dir, "design_spec.json")
                    if os.path.exists(design_spec_file):
                        with open(design_spec_file, 'r', encoding='utf-8') as f:
                            design_spec = json.load(f)
                            total_images = design_spec.get("content_overview", {}).get("total_images", 0)
                            print(f"📋 设计规范中的图片数量: {total_images}")
                    
                    print("🎉 动态图片数量功能测试成功！")
                else:
                    print("⚠️ 输出目录不存在")
        else:
            print("❌ 工作流执行失败")
            if "error" in result:
                print(f"错误信息: {result['error']}")
    
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        print("请检查模块路径和依赖项")
    except Exception as e:
        print(f"❌ 执行过程出错: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    try:
        asyncio.run(test_dynamic_image_count())
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    main() 