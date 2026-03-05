#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内嵌工具管理模块
用于管理内嵌的Python和Git软件
"""

import os
import sys
import subprocess
import shutil

from comfyui_manager.utils.config_manager import config_manager


class EmbeddedTools:
    """内嵌工具管理类"""
    
    def __init__(self):
        """初始化"""
        # 获取内嵌工具目录
        self.embedded_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "embedded"
        )
        
        # Python相关路径
        self.python_dir = os.path.join(self.embedded_dir, "python")
        self.python_exe = os.path.join(self.python_dir, "python.exe")
        
        # Git相关路径
        self.git_dir = os.path.join(self.embedded_dir, "Git")
        self.git_exe = os.path.join(self.git_dir, "bin", "git.exe")
        
        # 缓存工具路径
        self._cached_python_path = None
        self._cached_git_path = None
    
    def get_python_path(self):
        """获取Python可执行文件路径"""
        # 使用缓存
        if self._cached_python_path:
            # 验证缓存路径是否仍然有效
            if os.path.exists(self._cached_python_path):
                return self._cached_python_path
            else:
                # 缓存路径无效，清除缓存
                self._cached_python_path = None
        
        # 检查是否使用内嵌Python
        use_embedded = config_manager.get_use_embedded_python()
        
        # 优先使用内嵌Python（如果设置为使用）
        if use_embedded and os.path.exists(self.python_exe):
            # 验证Python可执行文件
            if self._verify_executable(self.python_exe, ["--version"]):
                self._cached_python_path = self.python_exe
                return self._cached_python_path
        
        # 否则使用系统Python
        if self._verify_executable(sys.executable, ["--version"]):
            self._cached_python_path = sys.executable
            return self._cached_python_path
        
        # 尝试其他Python路径
        python_candidates = [
            "python",
            "python3",
            os.path.join(os.environ.get("ProgramFiles", "C:\Program Files"), "Python312", "python.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\Program Files (x86)"), "Python312", "python.exe")
        ]
        
        for candidate in python_candidates:
            try:
                if shutil.which(candidate):
                    candidate_path = shutil.which(candidate)
                    if self._verify_executable(candidate_path, ["--version"]):
                        self._cached_python_path = candidate_path
                        return self._cached_python_path
            except Exception:
                pass
        
        return None
    
    def get_git_path(self):
        """获取Git可执行文件路径"""
        # 使用缓存
        if self._cached_git_path:
            # 验证缓存路径是否仍然有效
            if os.path.exists(self._cached_git_path):
                return self._cached_git_path
            else:
                # 缓存路径无效，清除缓存
                self._cached_git_path = None
        
        # 检查是否使用内嵌Git
        use_embedded = config_manager.get_use_embedded_git()
        
        # 优先使用内嵌Git（如果设置为使用）
        if use_embedded and os.path.exists(self.git_exe):
            # 验证Git可执行文件
            if self._verify_executable(self.git_exe, ["--version"]):
                self._cached_git_path = self.git_exe
                return self._cached_git_path
        
        # 否则尝试系统Git
        try:
            git_path = shutil.which("git")
            if git_path and self._verify_executable(git_path, ["--version"]):
                self._cached_git_path = git_path
                return self._cached_git_path
        except Exception as e:
            print(f"尝试获取系统Git失败: {e}")
        
        # 最后尝试常见路径
        common_git_paths = [
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\bin\git.exe",
            os.path.join(os.environ.get("USERPROFILE", ""), r"AppData\Local\Programs\Git\bin\git.exe")
        ]
        for path in common_git_paths:
            if os.path.exists(path) and self._verify_executable(path, ["--version"]):
                self._cached_git_path = path
                return self._cached_git_path
        
        return None
    
    def _verify_executable(self, path, args):
        """验证可执行文件是否有效"""
        try:
            result = subprocess.run([path] + args, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_python_version(self):
        """获取Python版本"""
        python_path = self.get_python_path()
        if python_path:
            try:
                result = subprocess.run([python_path, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return result.stdout.strip().split()[1]
            except Exception:
                pass
        return "未知"
    
    def get_git_version(self):
        """获取Git版本"""
        git_path = self.get_git_path()
        if git_path:
            try:
                result = subprocess.run([git_path, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return result.stdout.strip().split()[2]
            except Exception:
                pass
        return "未知"
    
    def run_python(self, args, **kwargs):
        """运行Python命令"""
        python_path = self.get_python_path()
        try:
            return subprocess.run([python_path] + args, **kwargs)
        except Exception as e:
            raise Exception(f"运行Python命令失败: {e}")
    
    def run_git(self, args, **kwargs):
        """运行Git命令"""
        git_path = self.get_git_path()
        if not git_path:
            raise Exception("Git未找到")
        try:
            return subprocess.run([git_path] + args, **kwargs)
        except Exception as e:
            raise Exception(f"运行Git命令失败: {e}")
    
    def is_python_embedded(self):
        """检查是否使用内嵌Python"""
        return os.path.exists(self.python_exe)
    
    def is_git_embedded(self):
        """检查是否使用内嵌Git"""
        return os.path.exists(self.git_exe)
    
    def clear_cache(self):
        """清除缓存"""
        self._cached_python_path = None
        self._cached_git_path = None


# 单例模式
embedded_tools = EmbeddedTools()
