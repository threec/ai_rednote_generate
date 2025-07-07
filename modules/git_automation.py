"""
Git自动化提交系统
智能管理代码变更的保存和提交

功能特点：
1. 关键节点自动提交
2. 智能提交信息生成
3. 变更检测和分析
4. 支持手动触发
5. 提交历史管理
"""

import os
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import difflib
import re

from .utils import get_logger

class GitAutomation:
    """Git自动化管理器"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.logger = get_logger("git_automation")
        self.commit_config = {
            "auto_commit": True,
            "commit_on_engine_complete": True,
            "commit_on_major_changes": True,
            "commit_on_bug_fixes": True,
            "max_files_per_commit": 20,
            "exclude_patterns": [
                "*.pyc", "__pycache__", ".pytest_cache", 
                "*.log", "logs/*", "cache/*", "output/*"
            ]
        }
        self.last_commit_hash = self._get_last_commit_hash()
        
    def _get_last_commit_hash(self) -> str:
        """获取最后一次提交的hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',  # 明确指定UTF-8编码
                errors='ignore'    # 忽略编码错误
            )
            return result.stdout.strip() if result.stdout else ""
        except subprocess.CalledProcessError:
            return ""
        except UnicodeDecodeError:
            return ""
        except Exception:
            return ""
    
    def _run_git_command(self, command: List[str]) -> Tuple[bool, str]:
        """执行git命令"""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',  # 明确指定UTF-8编码
                errors='ignore'    # 忽略编码错误
            )
            return True, result.stdout.strip() if result.stdout else ""
        except subprocess.CalledProcessError as e:
            error_msg = f"Git命令失败: {' '.join(command)}\n错误: {e.stderr if e.stderr else 'Unknown error'}"
            self.logger.error(error_msg)
            return False, error_msg
        except UnicodeDecodeError as e:
            error_msg = f"Git命令编码错误: {' '.join(command)}\n错误: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Git命令异常: {' '.join(command)}\n错误: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def check_git_status(self) -> Dict[str, Any]:
        """检查git状态"""
        success, output = self._run_git_command(["git", "status", "--porcelain"])
        if not success:
            return {"has_changes": False, "error": output}
        
        changes = []
        for line in output.split('\n'):
            if line.strip():
                status = line[:2]
                file_path = line[3:].strip()
                changes.append({
                    "status": status,
                    "file": file_path,
                    "type": self._get_change_type(status)
                })
        
        return {
            "has_changes": len(changes) > 0,
            "changes": changes,
            "total_files": len(changes)
        }
    
    def _get_change_type(self, status: str) -> str:
        """获取变更类型"""
        if status.startswith('A'):
            return "新增"
        elif status.startswith('M'):
            return "修改"
        elif status.startswith('D'):
            return "删除"
        elif status.startswith('R'):
            return "重命名"
        elif status.startswith('?'):
            return "未跟踪"
        else:
            return "其他"
    
    def generate_commit_message(self, changes: List[Dict[str, Any]], 
                              context: str = "", 
                              commit_type: str = "feat") -> str:
        """生成智能提交信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 分析变更类型
        file_types = {}
        change_types = {}
        
        for change in changes:
            file_path = change["file"]
            change_type = change["type"]
            
            # 统计文件类型
            if file_path.endswith('.py'):
                file_types['Python'] = file_types.get('Python', 0) + 1
            elif file_path.endswith('.md'):
                file_types['文档'] = file_types.get('文档', 0) + 1
            elif file_path.endswith('.json'):
                file_types['配置'] = file_types.get('配置', 0) + 1
            else:
                file_types['其他'] = file_types.get('其他', 0) + 1
            
            # 统计变更类型
            change_types[change_type] = change_types.get(change_type, 0) + 1
        
        # 生成主标题
        if context:
            title = f"{commit_type}: {context}"
        else:
            main_change = max(change_types.items(), key=lambda x: x[1])[0]
            main_file_type = max(file_types.items(), key=lambda x: x[1])[0]
            title = f"{commit_type}: {main_change}{main_file_type}文件"
        
        # 生成详细信息
        details = []
        details.append(f"📊 变更统计: {len(changes)}个文件")
        
        if change_types:
            type_summary = ", ".join([f"{k}({v})" for k, v in change_types.items()])
            details.append(f"📝 变更类型: {type_summary}")
        
        if file_types:
            file_summary = ", ".join([f"{k}({v})" for k, v in file_types.items()])
            details.append(f"📁 文件类型: {file_summary}")
        
        # 重要文件特别标注
        important_files = []
        for change in changes:
            file_path = change["file"]
            if any(keyword in file_path.lower() for keyword in 
                   ['main.py', 'config.py', 'workflow', 'engine']):
                important_files.append(f"  - {change['type']}: {file_path}")
        
        if important_files:
            details.append("🔥 重要文件:")
            details.extend(important_files)
        
        details.append(f"⏰ 提交时间: {timestamp}")
        
        return f"{title}\n\n" + "\n".join(details)
    
    def auto_commit(self, context: str = "", 
                   commit_type: str = "feat",
                   force: bool = False) -> Dict[str, Any]:
        """自动提交变更"""
        if not self.commit_config["auto_commit"] and not force:
            return {"success": False, "message": "自动提交已禁用"}
        
        # 检查状态
        status = self.check_git_status()
        if not status["has_changes"]:
            return {"success": False, "message": "没有需要提交的变更"}
        
        changes = status["changes"]
        
        # 检查文件数量限制
        if len(changes) > self.commit_config["max_files_per_commit"]:
            self.logger.warning(f"变更文件过多({len(changes)}个)，建议分批提交")
        
        try:
            # 添加文件到暂存区
            self.logger.info("添加文件到暂存区...")
            success, output = self._run_git_command(["git", "add", "."])
            if not success:
                return {"success": False, "message": f"添加文件失败: {output}"}
            
            # 生成提交信息
            commit_message = self.generate_commit_message(changes, context, commit_type)
            
            # 执行提交
            self.logger.info("执行git提交...")
            success, output = self._run_git_command(["git", "commit", "-m", commit_message])
            if not success:
                return {"success": False, "message": f"提交失败: {output}"}
            
            # 更新最后提交hash
            self.last_commit_hash = self._get_last_commit_hash()
            
            self.logger.info(f"✅ Git提交成功: {len(changes)}个文件")
            
            return {
                "success": True,
                "message": "提交成功",
                "commit_hash": self.last_commit_hash,
                "files_count": len(changes),
                "commit_message": commit_message
            }
            
        except Exception as e:
            error_msg = f"自动提交失败: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    def commit_on_engine_complete(self, engine_name: str, topic: str) -> Dict[str, Any]:
        """引擎完成时自动提交"""
        if not self.commit_config["commit_on_engine_complete"]:
            return {"success": False, "message": "引擎完成提交已禁用"}
        
        context = f"完成{engine_name}引擎处理 - {topic}"
        return self.auto_commit(context, "feat")
    
    def commit_on_bug_fix(self, bug_description: str) -> Dict[str, Any]:
        """Bug修复时自动提交"""
        if not self.commit_config["commit_on_bug_fixes"]:
            return {"success": False, "message": "Bug修复提交已禁用"}
        
        context = f"修复Bug - {bug_description}"
        return self.auto_commit(context, "fix")
    
    def commit_on_major_change(self, change_description: str) -> Dict[str, Any]:
        """重大变更时自动提交"""
        if not self.commit_config["commit_on_major_changes"]:
            return {"success": False, "message": "重大变更提交已禁用"}
        
        context = f"重大变更 - {change_description}"
        return self.auto_commit(context, "feat")
    
    def commit_architecture_update(self, update_description: str) -> Dict[str, Any]:
        """架构更新时自动提交"""
        context = f"架构更新 - {update_description}"
        return self.auto_commit(context, "refactor")
    
    def create_commit_checkpoint(self, checkpoint_name: str) -> Dict[str, Any]:
        """创建提交检查点"""
        context = f"检查点 - {checkpoint_name}"
        return self.auto_commit(context, "checkpoint")
    
    def get_commit_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取提交历史"""
        success, output = self._run_git_command([
            "git", "log", f"--max-count={limit}", 
            "--pretty=format:%H|%an|%ad|%s", "--date=iso"
        ])
        
        if not success:
            return []
        
        commits = []
        for line in output.split('\n'):
            if line.strip():
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })
        
        return commits
    
    def get_changes_since_last_commit(self) -> List[str]:
        """获取自上次提交以来的变更"""
        success, output = self._run_git_command([
            "git", "diff", "--name-only", "HEAD"
        ])
        
        if not success:
            return []
        
        return [line.strip() for line in output.split('\n') if line.strip()]
    
    def configure_auto_commit(self, **kwargs):
        """配置自动提交设置"""
        self.commit_config.update(kwargs)
        self.logger.info(f"Git自动提交配置已更新: {kwargs}")
    
    def manual_commit(self, message: str) -> Dict[str, Any]:
        """手动提交"""
        status = self.check_git_status()
        if not status["has_changes"]:
            return {"success": False, "message": "没有需要提交的变更"}
        
        try:
            # 添加所有文件
            success, output = self._run_git_command(["git", "add", "."])
            if not success:
                return {"success": False, "message": f"添加文件失败: {output}"}
            
            # 提交
            success, output = self._run_git_command(["git", "commit", "-m", message])
            if not success:
                return {"success": False, "message": f"提交失败: {output}"}
            
            self.last_commit_hash = self._get_last_commit_hash()
            
            return {
                "success": True,
                "message": "手动提交成功",
                "commit_hash": self.last_commit_hash
            }
            
        except Exception as e:
            return {"success": False, "message": f"手动提交失败: {str(e)}"}


# 全局git自动化实例
_git_automation = None

def get_git_automation() -> GitAutomation:
    """获取全局Git自动化实例"""
    global _git_automation
    if _git_automation is None:
        _git_automation = GitAutomation()
    return _git_automation

def auto_commit_if_needed(context: str = "", commit_type: str = "feat") -> bool:
    """如果需要的话自动提交"""
    git_auto = get_git_automation()
    result = git_auto.auto_commit(context, commit_type)
    return result["success"]

def commit_checkpoint(checkpoint_name: str) -> bool:
    """创建提交检查点"""
    git_auto = get_git_automation()
    result = git_auto.create_commit_checkpoint(checkpoint_name)
    return result["success"] 