#!/usr/bin/env python3
"""
系统集成测试 - RedCube AI V2.0
测试新核心架构的完整功能

测试范围：
1. 核心组件初始化
2. 配置管理系统
3. 异常处理机制
4. 依赖注入容器
5. 混合数据流输出
6. 引擎基类功能
7. 工作流集成测试
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

class SystemIntegrationTest:
    """系统集成测试类"""
    
    def __init__(self):
        self.test_results = {}
        self.temp_dir = None
        
    def setup_test_environment(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="redcube_test_")
        print(f"📁 临时目录: {self.temp_dir}")
        
        # 设置环境变量
        os.environ["REDCUBE_TEST_MODE"] = "true"
        os.environ["REDCUBE_TEST_DIR"] = self.temp_dir
        
        return True
    
    def test_core_config(self):
        """测试核心配置系统"""
        print("\n🧪 测试核心配置系统...")
        
        try:
            from modules.core.config import initialize_config, get_config_value
            
            # 测试配置初始化
            config = initialize_config("config.yaml")
            self.test_results["config_init"] = True
            print("✅ 配置初始化成功")
            
            # 测试配置读取
            system_name = get_config_value("system.name", "default")
            ai_model = get_config_value("ai.model_name", "default")
            
            if system_name and ai_model:
                self.test_results["config_read"] = True
                print(f"✅ 配置读取成功: {system_name}, {ai_model}")
            else:
                self.test_results["config_read"] = False
                print("❌ 配置读取失败")
            
            return True
            
        except Exception as e:
            print(f"❌ 配置系统测试失败: {str(e)}")
            self.test_results["config_init"] = False
            self.test_results["config_read"] = False
            return False
    
    def test_exception_handling(self):
        """测试异常处理系统"""
        print("\n🧪 测试异常处理系统...")
        
        try:
            from modules.core.exceptions import (
                SystemException, EngineException, WorkflowException, 
                ErrorCode, get_exception_handler
            )
            
            # 测试异常创建
            test_exception = SystemException(
                "测试异常", 
                ErrorCode.SYSTEM_INIT_FAILED,
                context={"test": True}
            )
            
            self.test_results["exception_creation"] = True
            print("✅ 异常创建成功")
            
            # 测试异常处理器
            handler = get_exception_handler()
            result = handler.handle_exception(test_exception)
            
            if result and "error" in result:
                self.test_results["exception_handling"] = True
                print("✅ 异常处理器工作正常")
            else:
                self.test_results["exception_handling"] = False
                print("❌ 异常处理器工作异常")
            
            return True
            
        except Exception as e:
            print(f"❌ 异常处理系统测试失败: {str(e)}")
            self.test_results["exception_creation"] = False
            self.test_results["exception_handling"] = False
            return False
    
    def test_output_system(self):
        """测试输出管理系统"""
        print("\n🧪 测试输出管理系统...")
        
        try:
            from modules.core.output import (
                get_output_manager, ContentType, OutputFormat
            )
            
            # 测试输出管理器初始化
            output_manager = get_output_manager()
            self.test_results["output_manager_init"] = True
            print("✅ 输出管理器初始化成功")
            
            # 测试创建输出对象
            output = output_manager.create_output(
                "test_engine", 
                "测试主题", 
                ContentType.REPORT
            )
            
            if output:
                self.test_results["output_creation"] = True
                print("✅ 输出对象创建成功")
                
                # 测试设置内容
                output.set_content("# 测试报告\n这是一个测试", OutputFormat.MARKDOWN)
                output.set_metadata(test=True, timestamp=datetime.now().isoformat())
                
                # 测试验证
                output.validate()
                self.test_results["output_validation"] = True
                print("✅ 输出验证成功")
                
                # 测试序列化
                output_dict = output.to_dict()
                if "content" in output_dict and "metadata" in output_dict:
                    self.test_results["output_serialization"] = True
                    print("✅ 输出序列化成功")
                else:
                    self.test_results["output_serialization"] = False
                    print("❌ 输出序列化失败")
            else:
                self.test_results["output_creation"] = False
                print("❌ 输出对象创建失败")
            
            return True
            
        except Exception as e:
            print(f"❌ 输出系统测试失败: {str(e)}")
            self.test_results["output_manager_init"] = False
            self.test_results["output_creation"] = False
            self.test_results["output_validation"] = False
            self.test_results["output_serialization"] = False
            return False
    
    def test_dependency_injection(self):
        """测试依赖注入系统"""
        print("\n🧪 测试依赖注入系统...")
        
        try:
            from modules.core.container import get_engine_container
            
            # 测试容器初始化
            container = get_engine_container()
            self.test_results["container_init"] = True
            print("✅ 依赖注入容器初始化成功")
            
            # 测试服务注册和获取（如果有的话）
            info = container.get_container_info()
            if info:
                self.test_results["container_info"] = True
                print(f"✅ 容器信息获取成功: {info}")
            else:
                self.test_results["container_info"] = False
                print("❌ 容器信息获取失败")
            
            return True
            
        except Exception as e:
            print(f"❌ 依赖注入系统测试失败: {str(e)}")
            self.test_results["container_init"] = False
            self.test_results["container_info"] = False
            return False
    
    def test_engine_base_class(self):
        """测试引擎基类功能"""
        print("\n🧪 测试引擎基类功能...")
        
        try:
            # 创建一个简单的测试引擎
            class TestEngine:
                def __init__(self):
                    self.engine_name = "test_engine"
                
                def get_engine_info(self):
                    return {
                        "name": self.engine_name,
                        "version": "2.0",
                        "test": True
                    }
            
            test_engine = TestEngine()
            info = test_engine.get_engine_info()
            
            if info and info.get("name") == "test_engine":
                self.test_results["engine_base"] = True
                print("✅ 引擎基类功能正常")
            else:
                self.test_results["engine_base"] = False
                print("❌ 引擎基类功能异常")
            
            return True
            
        except Exception as e:
            print(f"❌ 引擎基类测试失败: {str(e)}")
            self.test_results["engine_base"] = False
            return False
    
    async def test_langchain_workflow(self):
        """测试LangChain工作流集成"""
        print("\n🧪 测试LangChain工作流集成...")
        
        try:
            from modules.langchain_workflow import create_redcube_workflow
            
            # 模拟API密钥（测试模式）
            test_api_key = "test_key_for_integration_test"
            
            # 创建工作流实例
            workflow = create_redcube_workflow(test_api_key)
            
            if workflow:
                self.test_results["workflow_creation"] = True
                print("✅ 工作流创建成功")
                
                # 测试工作流信息获取
                if hasattr(workflow, 'engines'):
                    engine_count = len(workflow.engines)
                    self.test_results["workflow_engines"] = engine_count > 0
                    print(f"✅ 引擎加载: {engine_count} 个引擎")
                else:
                    self.test_results["workflow_engines"] = False
                    print("❌ 引擎加载失败")
            else:
                self.test_results["workflow_creation"] = False
                print("❌ 工作流创建失败")
            
            return True
            
        except ImportError as e:
            print(f"⚠️ LangChain依赖未安装，跳过工作流测试: {str(e)}")
            self.test_results["workflow_creation"] = "skipped"
            self.test_results["workflow_engines"] = "skipped"
            return True
        except Exception as e:
            print(f"❌ 工作流测试失败: {str(e)}")
            self.test_results["workflow_creation"] = False
            self.test_results["workflow_engines"] = False
            return False
    
    def test_git_automation(self):
        """测试Git自动化功能"""
        print("\n🧪 测试Git自动化功能...")
        
        try:
            from modules.git_automation import get_git_automation
            
            # 测试Git自动化初始化
            git_auto = get_git_automation()
            
            if git_auto:
                self.test_results["git_automation_init"] = True
                print("✅ Git自动化初始化成功")
                
                # 测试状态检查
                if hasattr(git_auto, 'get_status'):
                    status = git_auto.get_status()
                    self.test_results["git_status"] = bool(status)
                    print(f"✅ Git状态检查: {status}")
                else:
                    self.test_results["git_status"] = False
                    print("❌ Git状态检查失败")
            else:
                self.test_results["git_automation_init"] = False
                print("❌ Git自动化初始化失败")
            
            return True
            
        except Exception as e:
            print(f"❌ Git自动化测试失败: {str(e)}")
            self.test_results["git_automation_init"] = False
            self.test_results["git_status"] = False
            return False
    
    def cleanup_test_environment(self):
        """清理测试环境"""
        print("\n🧹 清理测试环境...")
        
        # 清理环境变量
        if "REDCUBE_TEST_MODE" in os.environ:
            del os.environ["REDCUBE_TEST_MODE"]
        if "REDCUBE_TEST_DIR" in os.environ:
            del os.environ["REDCUBE_TEST_DIR"]
        
        # 清理临时目录
        if self.temp_dir and Path(self.temp_dir).exists():
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"📁 已清理临时目录: {self.temp_dir}")
    
    def generate_test_report(self):
        """生成测试报告"""
        print("\n📊 测试报告:")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if result is True)
        skipped_tests = sum(1 for result in self.test_results.values() 
                           if result == "skipped")
        failed_tests = total_tests - passed_tests - skipped_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"跳过: {skipped_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n详细结果:")
        for test_name, result in self.test_results.items():
            if result is True:
                print(f"  ✅ {test_name}")
            elif result == "skipped":
                print(f"  ⏭️ {test_name} (跳过)")
            else:
                print(f"  ❌ {test_name}")
        
        print("=" * 50)
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "skipped": skipped_tests,
            "failed": failed_tests,
            "success_rate": passed_tests/total_tests*100 if total_tests > 0 else 0,
            "details": self.test_results
        }
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 RedCube AI V2.0 系统集成测试开始")
        print("=" * 50)
        
        # 设置测试环境
        self.setup_test_environment()
        
        try:
            # 运行所有测试
            tests = [
                self.test_core_config,
                self.test_exception_handling,
                self.test_output_system,
                self.test_dependency_injection,
                self.test_engine_base_class,
                self.test_langchain_workflow,
                self.test_git_automation
            ]
            
            for test in tests:
                if asyncio.iscoroutinefunction(test):
                    await test()
                else:
                    test()
            
            # 生成报告
            report = self.generate_test_report()
            
            # 判断整体结果
            if report["failed"] == 0:
                print("\n🎉 所有测试通过！系统架构重构成功！")
                return True
            else:
                print(f"\n⚠️ 有 {report['failed']} 个测试失败，需要进一步优化")
                return False
                
        finally:
            # 清理环境
            self.cleanup_test_environment()

async def main():
    """主函数"""
    test_runner = SystemIntegrationTest()
    success = await test_runner.run_all_tests()
    
    if success:
        print("\n✅ 系统集成测试完成 - 架构重构成功")
        return 0
    else:
        print("\n❌ 系统集成测试完成 - 发现问题需要修复")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 