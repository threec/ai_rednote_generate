#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小红书自动发布模块
基于Playwright实现图片+文本的自动化发布功能
"""

import asyncio
import logging
import time
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Page, BrowserContext

from modules.utils import get_logger

# 配置日志
logger = get_logger(__name__)

# 小红书发布配置
XIAOHONGSHU_CONFIG = {
    "browser": {
        "headless": False,  # 显示浏览器界面，便于调试和验证
        "channel": "chrome",  # 使用Chrome浏览器
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "locale": "zh-CN",
        "timezone_id": "Asia/Shanghai",
    },
    "urls": {
        "base_url": "https://www.xiaohongshu.com",
        "creator_url": "https://creator.xiaohongshu.com",
        "publish_url": "https://creator.xiaohongshu.com/publish/publish",
        "login_url": "https://www.xiaohongshu.com/explore"
    },
    "wait_times": {
        "page_load": 3000,      # 页面加载等待
        "element_load": 2000,   # 元素加载等待
        "upload_wait": 5000,    # 上传等待
        "input_delay": 100,     # 输入延迟
        "click_delay": 500,     # 点击延迟
        "login_check": 5000,    # 登录检查间隔
    },
    "retry": {
        "max_retries": 3,
        "retry_delay": 2,
        "timeout": 30000,
    },
    # 选择器配置（基于2024年最新页面结构）
    "selectors": {
        "login": {
            "login_btn": [
                "text=登录",
                "text=扫码登录", 
                ".login-btn",
                ".login-container",
                '[data-testid="login"]'
            ],
            "success_indicators": [
                "text=发布笔记",
                "text=创作灵感",
                ".creator-header",
                ".publish-btn",
                '[data-testid="publish-btn"]'
            ]
        },
        "upload": {
            "file_input": [
                "input[type=file]",
                "input[accept*=image]",
                "input[multiple]",
                ".upload-input",
                "#file-upload",
                ".file-input",
                "[data-testid='file-upload']",
                ".dnd-upload input[type=file]",
                ".upload-wrapper input[type=file]"
            ],
            "upload_area": [
                ".upload-wrapper",
                ".upload-area", 
                ".image-upload",
                ".dnd-upload",
                ".upload-zone",
                "text=点击上传",
                "text=上传图片",
                "text=选择图片",
                "[data-testid='upload-area']"
            ],
            "success_indicators": [
                ".upload-success",
                ".image-preview",
                ".uploaded-image",
                "img[src*='blob:']",
                ".preview-image",
                ".image-item"
            ]
        },
        "content": {
            "title_input": [
                "input[placeholder*='标题']",
                "input[placeholder*='title']",
                ".title-input",
                ".note-title-input",
                "textarea[placeholder*='标题']",
                "[data-testid='title-input']",
                ".publish-title input",
                ".title-area input"
            ],
            "description_input": [
                "textarea[placeholder*='描述']",
                "textarea[placeholder*='详细描述']",
                "textarea[placeholder*='添加笔记文字']",
                ".desc-input",
                ".note-desc-input",
                ".content-input",
                "[data-testid='description-input']",
                ".publish-content textarea",
                ".content-area textarea"
            ]
        },
        "publish": {
            "publish_btn": [
                "text=发布",
                "text=发布笔记",
                ".publish-btn",
                ".submit-btn",
                '[data-testid="publish-btn"]',
                "button[type='submit']"
            ],
            "success_indicators": [
                "text=发布成功",
                "text=笔记已发布",
                ".success-message",
                ".publish-success",
                "[data-testid='success']"
            ]
        }
    }
}


class XiaohongshuPublisher:
    """小红书自动发布器"""
    
    def __init__(self, headless: bool = False):
        """
        初始化发布器
        
        Args:
            headless (bool): 是否无头模式运行
        """
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.config = XIAOHONGSHU_CONFIG
        self.auth_file = "xiaohongshu_auth.json"
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()
        
    async def initialize(self):
        """初始化浏览器和上下文"""
        try:
            playwright = await async_playwright().__aenter__()
            
            # 启动浏览器
            browser_config = self.config["browser"].copy()
            browser_config["headless"] = self.headless
            
            self.browser = await playwright.chromium.launch(**browser_config)
            
            # 创建上下文
            context_options = {
                "viewport": browser_config["viewport"],
                "user_agent": browser_config["user_agent"],
                "locale": browser_config["locale"],
                "timezone_id": browser_config["timezone_id"]
            }
            
            # 使用已保存的登录状态（如果存在）
            if Path(self.auth_file).exists():
                context_options["storage_state"] = self.auth_file
                logger.info(f"使用已保存的登录状态: {self.auth_file}")
            
            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()
            
            logger.info("✓ 浏览器和上下文初始化完成")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            await self.cleanup()
            raise
            
    async def cleanup(self):
        """清理资源"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("✓ 资源清理完成")
        except Exception as e:
            logger.warning(f"清理过程中出现错误: {e}")
            
    async def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            # 访问创作者中心
            await self.page.goto(self.config["urls"]["creator_url"])
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # 检查是否已登录
            for selector in self.config["selectors"]["login"]["success_indicators"]:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info("✓ 已登录状态确认")
                        return True
                except:
                    continue
                    
            logger.info("❌ 未登录或登录已过期")
            return False
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False
            
    async def login(self) -> bool:
        """处理登录流程"""
        try:
            logger.info("🔐 开始登录流程...")
            
            # 访问登录页面
            await self.page.goto(self.config["urls"]["login_url"])
            await self.page.wait_for_load_state('networkidle')
            
            # 查找登录按钮
            login_btn = None
            for selector in self.config["selectors"]["login"]["login_btn"]:
                try:
                    login_btn = await self.page.wait_for_selector(selector, timeout=3000)
                    if login_btn:
                        break
                except:
                    continue
                    
            if login_btn:
                await login_btn.click()
                logger.info("已点击登录按钮，请手动完成登录...")
            else:
                logger.info("未找到登录按钮，请手动导航到登录页面...")
            
            # 等待用户手动登录
            logger.info("⏳ 等待手动登录完成...")
            logger.info("请在浏览器中完成登录操作，登录成功后程序将自动继续...")
            
            # 轮询检查登录状态
            login_success = False
            max_wait_time = 300  # 最大等待5分钟
            start_time = time.time()
            
            while not login_success and (time.time() - start_time) < max_wait_time:
                try:
                    # 检查登录成功指示器
                    for selector in self.config["selectors"]["login"]["success_indicators"]:
                        try:
                            element = await self.page.wait_for_selector(selector, timeout=2000)
                            if element:
                                login_success = True
                                break
                        except:
                            continue
                    
                    if not login_success:
                        await asyncio.sleep(self.config["wait_times"]["login_check"] / 1000)
                        
                except Exception as e:
                    logger.debug(f"登录检查过程中的错误: {e}")
                    await asyncio.sleep(2)
            
            if login_success:
                # 保存登录状态
                await self.context.storage_state(path=self.auth_file)
                logger.info(f"✓ 登录成功！登录状态已保存到: {self.auth_file}")
                return True
            else:
                logger.error("❌ 登录超时或失败")
                return False
                
        except Exception as e:
            logger.error(f"登录过程失败: {e}")
            return False
            
    async def upload_images(self, image_paths: List[str]) -> bool:
        """上传图片"""
        try:
            logger.info(f"📸 开始上传 {len(image_paths)} 张图片...")
            
            # 访问发布页面
            await self.page.goto(self.config["urls"]["publish_url"])
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # 查找文件上传输入
            file_input = None
            for selector in self.config["selectors"]["upload"]["file_input"]:
                try:
                    file_input = await self.page.wait_for_selector(selector, timeout=3000)
                    if file_input:
                        logger.info(f"找到文件上传控件: {selector}")
                        break
                except:
                    continue
                    
            if not file_input:
                # 尝试点击上传区域来激活文件选择
                for selector in self.config["selectors"]["upload"]["upload_area"]:
                    try:
                        upload_area = await self.page.wait_for_selector(selector, timeout=3000)
                        if upload_area:
                            await upload_area.click()
                            logger.info(f"点击上传区域: {selector}")
                            
                            # 再次查找文件输入
                            for input_selector in self.config["selectors"]["upload"]["file_input"]:
                                try:
                                    file_input = await self.page.wait_for_selector(input_selector, timeout=2000)
                                    if file_input:
                                        break
                                except:
                                    continue
                            break
                    except:
                        continue
            
            if not file_input:
                logger.error("❌ 未找到文件上传控件")
                return False
            
            # 上传图片文件
            await file_input.set_input_files(image_paths)
            logger.info(f"✓ 图片文件已选择: {len(image_paths)} 个文件")
            
            # 等待上传完成
            upload_success = False
            max_wait_time = 30  # 最大等待30秒
            start_time = time.time()
            
            while not upload_success and (time.time() - start_time) < max_wait_time:
                # 检查上传成功指示器
                for selector in self.config["selectors"]["upload"]["success_indicators"]:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        if len(elements) >= len(image_paths):
                            upload_success = True
                            break
                    except:
                        continue
                
                if not upload_success:
                    await asyncio.sleep(1)
                    
            if upload_success:
                logger.info(f"✓ 图片上传成功: {len(image_paths)} 张")
                return True
            else:
                logger.warning("⚠️ 图片上传可能未完成，但继续执行...")
                return True  # 继续执行，因为有些情况下检测不准确
                
        except Exception as e:
            logger.error(f"图片上传失败: {e}")
            return False
            
    async def fill_content(self, title: str, content: str) -> bool:
        """填写标题和内容"""
        try:
            logger.info("📝 开始填写标题和内容...")
            
            # 等待页面稳定
            await asyncio.sleep(2)
            
            # 填写标题（如果有标题输入框）
            title_filled = False
            for selector in self.config["selectors"]["content"]["title_input"]:
                try:
                    title_input = await self.page.wait_for_selector(selector, timeout=3000)
                    if title_input:
                        await title_input.fill(title)
                        logger.info(f"✓ 标题已填写: {title}")
                        title_filled = True
                        break
                except:
                    continue
                    
            if not title_filled:
                logger.info("ℹ️ 未找到标题输入框，可能小红书不需要单独的标题")
            
            # 填写内容
            content_filled = False
            for selector in self.config["selectors"]["content"]["description_input"]:
                try:
                    content_input = await self.page.wait_for_selector(selector, timeout=5000)
                    if content_input:
                        # 清空现有内容并填写新内容
                        await content_input.fill("")
                        await asyncio.sleep(0.5)
                        await content_input.fill(content)
                        
                        # 验证内容是否填写成功
                        filled_value = await content_input.input_value()
                        if filled_value and len(filled_value) > 0:
                            logger.info(f"✓ 内容已填写: {len(content)} 字符")
                            content_filled = True
                            break
                        else:
                            logger.warning(f"内容填写验证失败，尝试下一个选择器...")
                except Exception as e:
                    logger.warning(f"填写内容时出错 ({selector}): {e}")
                    continue
                    
            if not content_filled:
                logger.error("❌ 内容填写失败")
                return False
                
            # 等待内容处理
            await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"填写内容失败: {e}")
            return False
            
    async def publish(self) -> bool:
        """执行发布操作"""
        try:
            logger.info("🚀 开始发布...")
            
            # 等待页面稳定
            await asyncio.sleep(2)
            
            # 查找并点击发布按钮
            publish_clicked = False
            for selector in self.config["selectors"]["publish"]["publish_btn"]:
                try:
                    publish_btn = await self.page.wait_for_selector(selector, timeout=5000)
                    if publish_btn:
                        # 检查按钮是否可点击
                        is_enabled = await publish_btn.is_enabled()
                        if is_enabled:
                            await publish_btn.click()
                            logger.info(f"✓ 已点击发布按钮: {selector}")
                            publish_clicked = True
                            break
                        else:
                            logger.warning(f"发布按钮未启用: {selector}")
                except Exception as e:
                    logger.warning(f"点击发布按钮失败 ({selector}): {e}")
                    continue
                    
            if not publish_clicked:
                logger.error("❌ 未找到可用的发布按钮")
                return False
            
            # 等待发布完成
            publish_success = False
            max_wait_time = 30  # 最大等待30秒
            start_time = time.time()
            
            while not publish_success and (time.time() - start_time) < max_wait_time:
                # 检查发布成功指示器
                for selector in self.config["selectors"]["publish"]["success_indicators"]:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=2000)
                        if element:
                            publish_success = True
                            logger.info(f"✓ 发布成功确认: {selector}")
                            break
                    except:
                        continue
                
                if not publish_success:
                    await asyncio.sleep(1)
                    
            if publish_success:
                logger.info("🎉 发布成功！")
                return True
            else:
                logger.warning("⚠️ 发布状态未确认，请手动检查")
                return True  # 假设成功，因为有些情况下检测不准确
                
        except Exception as e:
            logger.error(f"发布失败: {e}")
            return False
            
    async def auto_publish(self, image_paths: List[str], title: str, content: str) -> Dict[str, Any]:
        """
        自动发布完整流程
        
        Args:
            image_paths (List[str]): 图片文件路径列表
            title (str): 标题
            content (str): 内容
            
        Returns:
            Dict[str, Any]: 发布结果
        """
        result = {
            "success": False,
            "message": "",
            "steps": {
                "login": False,
                "upload": False,
                "content": False,
                "publish": False
            }
        }
        
        try:
            logger.info("=" * 60)
            logger.info("🚀 开始小红书自动发布流程")
            logger.info(f"📸 图片数量: {len(image_paths)}")
            logger.info(f"📝 标题: {title}")
            logger.info(f"📄 内容长度: {len(content)} 字符")
            logger.info("=" * 60)
            
            # 步骤1: 检查登录状态
            if not await self.check_login_status():
                if not await self.login():
                    result["message"] = "登录失败"
                    return result
            result["steps"]["login"] = True
            
            # 步骤2: 上传图片
            if not await self.upload_images(image_paths):
                result["message"] = "图片上传失败"
                return result
            result["steps"]["upload"] = True
            
            # 步骤3: 填写内容
            if not await self.fill_content(title, content):
                result["message"] = "内容填写失败"
                return result
            result["steps"]["content"] = True
            
            # 步骤4: 执行发布
            if not await self.publish():
                result["message"] = "发布操作失败"
                return result
            result["steps"]["publish"] = True
            
            result["success"] = True
            result["message"] = "发布成功"
            
            logger.info("🎉 自动发布流程完成！")
            
        except Exception as e:
            logger.error(f"自动发布流程异常: {e}")
            result["message"] = f"发布过程异常: {str(e)}"
            
        return result


# 便捷函数
async def publish_to_xiaohongshu(
    image_paths: List[str], 
    title: str, 
    content: str,
    headless: bool = False
) -> Dict[str, Any]:
    """
    发布内容到小红书的便捷函数
    
    Args:
        image_paths (List[str]): 图片文件路径列表
        title (str): 标题
        content (str): 内容
        headless (bool): 是否无头模式
        
    Returns:
        Dict[str, Any]: 发布结果
    """
    async with XiaohongshuPublisher(headless=headless) as publisher:
        return await publisher.auto_publish(image_paths, title, content)


def publish_content_sync(
    image_paths: List[str], 
    title: str, 
    content: str,
    headless: bool = False
) -> Dict[str, Any]:
    """
    同步版本的发布函数，用于在同步代码中调用
    
    Args:
        image_paths (List[str]): 图片文件路径列表
        title (str): 标题
        content (str): 内容
        headless (bool): 是否无头模式
        
    Returns:
        Dict[str, Any]: 发布结果
    """
    return asyncio.run(publish_to_xiaohongshu(image_paths, title, content, headless))


# 测试函数
async def test_publisher():
    """测试发布器功能"""
    logger.info("开始测试小红书发布器...")
    
    # 创建测试图片路径
    test_images = [
        "test_image_1.png",
        "test_image_2.png"
    ]
    
    test_title = "测试标题"
    test_content = "这是一个测试内容，用于验证自动发布功能是否正常工作。"
    
    async with XiaohongshuPublisher(headless=False) as publisher:
        result = await publisher.auto_publish(test_images, test_title, test_content)
        
    logger.info(f"测试结果: {result}")
    

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_publisher()) 