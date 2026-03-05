#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虚拟环境管理模块
"""

import os
import sys
import subprocess
import platform
import shutil
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

from comfyui_manager.utils.logger import Logger


class EnvironmentManager:
    """虚拟环境管理类"""
    
    def __init__(self):
        """初始化"""
        self.logger = Logger()
        self.system = platform.system()
        self.python_versions: List[str] = []
        self.virtual_envs: List[Dict[str, Any]] = []
    
    def get_virtual_envs(self) -> List[Dict[str, Any]]:
        """获取所有虚拟环境"""
        envs: List[Dict[str, Any]] = []
        env_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "venvs")
        
        if os.path.exists(env_dir):
            for env_name in os.listdir(env_dir):
                env_path = os.path.join(env_dir, env_name)
                if os.path.isdir(env_path):
                    env_info = {
                        "name": env_name,
                        "path": env_path,
                        "created_at": datetime.fromtimestamp(os.path.getctime(env_path)).strftime("%Y-%m-%d %H:%M:%S"),
                        "status": self.check_env_status(env_path)
                    }
                    envs.append(env_info)
        
        self.virtual_envs = envs
        return envs
    
    def check_env_status(self, env_path: str) -> str:
        """检查虚拟环境状态"""
        # 检查Python可执行文件是否存在
        if self.system == "Windows":
            python_exe = os.path.join(env_path, "Scripts", "python.exe")
        else:
            python_exe = os.path.join(env_path, "bin", "python")
        
        if os.path.exists(python_exe):
            try:
                result = subprocess.run([python_exe, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return "正常"
            except Exception as e:
                self.logger.warning(f"检查虚拟环境状态异常: {str(e)}")
        
        return "异常"
    
    def create_virtual_env(self, env_name: str, python_version: Optional[str] = None) -> Dict[str, Any]:
        """创建虚拟环境"""
        try:
            env_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "venvs")
            if not os.path.exists(env_dir):
                os.makedirs(env_dir)
            
            env_path = os.path.join(env_dir, env_name)
            if os.path.exists(env_path):
                return {"status": "error", "message": "虚拟环境已存在"}
            
            # 创建虚拟环境
            self.logger.info(f"创建虚拟环境: {env_name}")
            
            # 使用venv模块创建虚拟环境
            result = subprocess.run([sys.executable, "-m", "venv", env_path], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"虚拟环境创建成功: {env_name}")
                return {"status": "success", "message": "虚拟环境创建成功", "path": env_path}
            else:
                self.logger.error(f"虚拟环境创建失败: {result.stderr}")
                return {"status": "error", "message": f"创建失败: {result.stderr}"}
        except Exception as e:
            self.logger.error(f"创建虚拟环境异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def install_pytorch(self, env_name: str, cuda_version: Optional[str] = None) -> Dict[str, Any]:
        """安装PyTorch"""
        try:
            env_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "venvs")
            env_path = os.path.join(env_dir, env_name)
            
            if not os.path.exists(env_path):
                return {"status": "error", "message": "虚拟环境不存在"}
            
            # 确定pip路径
            if self.system == "Windows":
                pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
            else:
                pip_exe = os.path.join(env_path, "bin", "pip")
            
            if not os.path.exists(pip_exe):
                return {"status": "error", "message": "pip不存在"}
            
            self.logger.info(f"安装PyTorch到虚拟环境: {env_name}")
            
            # 构建PyTorch安装命令
            if cuda_version:
                # 安装带CUDA的PyTorch
                torch_packages = ["torch", "torchvision", "torchaudio"]
                if cuda_version == "11.8":
                    index_url = "https://download.pytorch.org/whl/cu118"
                elif cuda_version == "12.1":
                    index_url = "https://download.pytorch.org/whl/cu121"
                else:
                    index_url = "https://download.pytorch.org/whl/cu118"
                
                command = [pip_exe, "install", "--index-url", index_url] + torch_packages
            else:
                # 安装CPU版本的PyTorch
                command = [pip_exe, "install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"]
            
            # 执行安装
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"PyTorch安装成功: {env_name}")
                return {"status": "success", "message": "PyTorch安装成功"}
            else:
                self.logger.error(f"PyTorch安装失败: {result.stderr}")
                return {"status": "error", "message": f"安装失败: {result.stderr}"}
        except Exception as e:
            self.logger.error(f"安装PyTorch异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def install_dependencies(self, env_name: str, dependencies: List[str]) -> Dict[str, Any]:
        """安装依赖包"""
        try:
            env_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "venvs")
            env_path = os.path.join(env_dir, env_name)
            
            if not os.path.exists(env_path):
                return {"status": "error", "message": "虚拟环境不存在"}
            
            # 确定pip路径
            if self.system == "Windows":
                pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
            else:
                pip_exe = os.path.join(env_path, "bin", "pip")
            
            if not os.path.exists(pip_exe):
                return {"status": "error", "message": "pip不存在"}
            
            self.logger.info(f"安装依赖到虚拟环境: {env_name}")
            
            # 执行安装
            command = [pip_exe, "install"] + dependencies
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"依赖安装成功: {env_name}")
                return {"status": "success", "message": "依赖安装成功"}
            else:
                self.logger.error(f"依赖安装失败: {result.stderr}")
                return {"status": "error", "message": f"安装失败: {result.stderr}"}
        except Exception as e:
            self.logger.error(f"安装依赖异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def delete_virtual_env(self, env_name: str) -> Dict[str, Any]:
        """删除虚拟环境"""
        try:
            env_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "venvs")
            env_path = os.path.join(env_dir, env_name)
            
            if not os.path.exists(env_path):
                return {"status": "error", "message": "虚拟环境不存在"}
            
            self.logger.info(f"删除虚拟环境: {env_name}")
            
            # 删除虚拟环境目录
            shutil.rmtree(env_path)
            
            self.logger.info(f"虚拟环境删除成功: {env_name}")
            return {"status": "success", "message": "虚拟环境删除成功"}
        except Exception as e:
            self.logger.error(f"删除虚拟环境异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def get_env_packages(self, env_name: str) -> Dict[str, Any]:
        """获取虚拟环境中的包"""
        try:
            env_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "venvs")
            env_path = os.path.join(env_dir, env_name)
            
            if not os.path.exists(env_path):
                return {"status": "error", "message": "虚拟环境不存在"}
            
            # 确定pip路径
            if self.system == "Windows":
                pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
            else:
                pip_exe = os.path.join(env_path, "bin", "pip")
            
            if not os.path.exists(pip_exe):
                return {"status": "error", "message": "pip不存在"}
            
            # 执行pip list
            result = subprocess.run([pip_exe, "list", "--format=json"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                return {"status": "success", "packages": packages}
            else:
                return {"status": "error", "message": f"获取失败: {result.stderr}"}
        except Exception as e:
            self.logger.error(f"获取包列表异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def upgrade_pip(self, env_name: str) -> Dict[str, Any]:
        """升级pip"""
        try:
            env_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "venvs")
            env_path = os.path.join(env_dir, env_name)
            
            if not os.path.exists(env_path):
                return {"status": "error", "message": "虚拟环境不存在"}
            
            # 确定pip路径
            if self.system == "Windows":
                python_exe = os.path.join(env_path, "Scripts", "python.exe")
            else:
                python_exe = os.path.join(env_path, "bin", "python")
            
            if not os.path.exists(python_exe):
                return {"status": "error", "message": "Python不存在"}
            
            self.logger.info(f"升级pip: {env_name}")
            
            # 执行pip升级
            result = subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"pip升级成功: {env_name}")
                return {"status": "success", "message": "pip升级成功"}
            else:
                self.logger.error(f"pip升级失败: {result.stderr}")
                return {"status": "error", "message": f"升级失败: {result.stderr}"}
        except Exception as e:
            self.logger.error(f"升级pip异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
