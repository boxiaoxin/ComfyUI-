#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI管理模块
"""

import os
import sys
import subprocess
import platform
import json
import requests
import time
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from comfyui_manager.utils.logger import Logger


class ComfyUIManager:
    """ComfyUI管理类"""
    
    def __init__(self):
        """初始化"""
        self.logger = Logger()
        self.system = platform.system()
        self.comfyui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ComfyUI")
        self.running_processes: Dict[int, subprocess.Popen] = {}
    
    def check_comfyui_installed(self) -> bool:
        """检查ComfyUI是否已安装"""
        return os.path.exists(self.comfyui_path) and os.path.exists(os.path.join(self.comfyui_path, "main.py"))
    
    def install_comfyui(self, git_repo: str = "https://github.com/comfyanonymous/ComfyUI.git") -> Dict[str, Any]:
        """安装ComfyUI"""
        try:
            self.logger.info(f"开始安装ComfyUI，仓库: {git_repo}")
            
            # 如果已存在，先删除
            if os.path.exists(self.comfyui_path):
                shutil.rmtree(self.comfyui_path)
            
            # 克隆仓库
            result = subprocess.run(["git", "clone", git_repo, self.comfyui_path], 
                                  capture_output=True, text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW if self.system == 'Windows' else 0)
            
            if result.returncode == 0:
                self.logger.info("ComfyUI克隆成功")
                return {"status": "success", "message": "ComfyUI安装成功"}
            else:
                self.logger.error(f"ComfyUI克隆失败: {result.stderr}")
                return {"status": "error", "message": f"克隆失败: {result.stderr}"}
        except Exception as e:
            self.logger.error(f"安装ComfyUI异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def update_comfyui(self) -> Dict[str, Any]:
        """更新ComfyUI"""
        try:
            if not self.check_comfyui_installed():
                return {"status": "error", "message": "ComfyUI未安装"}
            
            self.logger.info("开始更新ComfyUI")
            
            # 执行git pull
            result = subprocess.run(["git", "pull"], 
                                  cwd=self.comfyui_path, 
                                  capture_output=True, text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW if self.system == 'Windows' else 0)
            
            if result.returncode == 0:
                self.logger.info("ComfyUI更新成功")
                return {"status": "success", "message": "ComfyUI更新成功"}
            else:
                self.logger.error(f"ComfyUI更新失败: {result.stderr}")
                return {"status": "error", "message": f"更新失败: {result.stderr}"}
        except Exception as e:
            self.logger.error(f"更新ComfyUI异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def start_comfyui(self, env_name: Optional[str] = None, port: int = 8188, extra_args: Optional[List[str]] = None) -> Dict[str, Any]:
        """启动ComfyUI"""
        try:
            if not self.check_comfyui_installed():
                return {"status": "error", "message": "ComfyUI未安装"}
            
            # 确定Python可执行文件
            if env_name:
                env_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "venvs", env_name)
                if self.system == "Windows":
                    python_exe = os.path.join(env_dir, "Scripts", "python.exe")
                else:
                    python_exe = os.path.join(env_dir, "bin", "python")
                
                if not os.path.exists(python_exe):
                    return {"status": "error", "message": "虚拟环境不存在或Python可执行文件缺失"}
            else:
                python_exe = sys.executable
            
            self.logger.info(f"启动ComfyUI，端口: {port}")
            
            # 构建启动命令
            command = [python_exe, "main.py", "--port", str(port)]
            if extra_args:
                command.extend(extra_args)
            
            # 启动进程
            process = subprocess.Popen(command, 
                                     cwd=self.comfyui_path, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, 
                                     text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW if self.system == 'Windows' else 0)
            
            # 记录进程信息
            self.running_processes[port] = process
            
            # 等待启动完成
            time.sleep(2)
            
            # 检查进程是否仍在运行
            if process.poll() is None:
                self.logger.info(f"ComfyUI启动成功，端口: {port}")
                return {"status": "success", "message": f"ComfyUI启动成功，访问地址: http://localhost:{port}", "port": port}
            else:
                # 读取错误信息
                stderr = process.stderr.read()
                self.logger.error(f"ComfyUI启动失败: {stderr}")
                return {"status": "error", "message": f"启动失败: {stderr}"}
        except Exception as e:
            self.logger.error(f"启动ComfyUI异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def stop_comfyui(self, port: int = 8188) -> Dict[str, Any]:
        """停止ComfyUI"""
        try:
            if port in self.running_processes:
                process = self.running_processes[port]
                process.terminate()
                process.wait(timeout=5)
                del self.running_processes[port]
                self.logger.info(f"ComfyUI已停止，端口: {port}")
                return {"status": "success", "message": "ComfyUI已停止"}
            else:
                return {"status": "error", "message": "ComfyUI未运行"}
        except Exception as e:
            self.logger.error(f"停止ComfyUI异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def check_comfyui_status(self, port: int = 8188) -> Dict[str, Any]:
        """检查ComfyUI状态"""
        try:
            if port in self.running_processes:
                process = self.running_processes[port]
                if process.poll() is None:
                    return {"status": "running", "message": "ComfyUI正在运行"}
                else:
                    del self.running_processes[port]
                    return {"status": "stopped", "message": "ComfyUI已停止"}
            else:
                # 尝试通过HTTP检查
                try:
                    response = requests.get(f"http://localhost:{port}", timeout=2)
                    if response.status_code == 200:
                        return {"status": "running", "message": "ComfyUI正在运行"}
                except Exception as e:
                    self.logger.debug(f"HTTP检查失败: {str(e)}")
                return {"status": "stopped", "message": "ComfyUI未运行"}
        except Exception as e:
            self.logger.error(f"检查ComfyUI状态异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def get_comfyui_version(self) -> Dict[str, Any]:
        """获取ComfyUI版本"""
        try:
            if not self.check_comfyui_installed():
                return {"status": "error", "message": "ComfyUI未安装"}
            
            # 尝试通过git获取版本信息
            result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], 
                                  cwd=self.comfyui_path, 
                                  capture_output=True, text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW if self.system == 'Windows' else 0)
            
            if result.returncode == 0:
                commit_hash = result.stdout.strip()
                return {"status": "success", "version": commit_hash}
            else:
                return {"status": "error", "message": "无法获取版本信息"}
        except Exception as e:
            self.logger.error(f"获取ComfyUI版本异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def repair_comfyui(self) -> Dict[str, Any]:
        """智能修复ComfyUI"""
        try:
            if not self.check_comfyui_installed():
                return {"status": "error", "message": "ComfyUI未安装"}
            
            self.logger.info("开始修复ComfyUI")
            
            # 步骤1: 检查git状态
            result = subprocess.run(["git", "status"], 
                                  cwd=self.comfyui_path, 
                                  capture_output=True, text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW if self.system == 'Windows' else 0)
            
            # 步骤2: 尝试重置
            result = subprocess.run(["git", "reset", "--hard"], 
                                  cwd=self.comfyui_path, 
                                  capture_output=True, text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW if self.system == 'Windows' else 0)
            
            if result.returncode == 0:
                self.logger.info("ComfyUI修复成功")
                return {"status": "success", "message": "ComfyUI修复成功"}
            else:
                self.logger.error(f"ComfyUI修复失败: {result.stderr}")
                return {"status": "error", "message": f"修复失败: {result.stderr}"}
        except Exception as e:
            self.logger.error(f"修复ComfyUI异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def get_workflows_dir(self):
        """获取工作流目录，优先使用 user\default\workflows"""
        # 优先使用 user\default\workflows 目录
        workflows_dir = os.path.join(self.comfyui_path, "user", "default", "workflows")
        # 如果不存在，回退到根目录的 workflows
        if not os.path.exists(workflows_dir):
            workflows_dir = os.path.join(self.comfyui_path, "workflows")
        return workflows_dir
    
    def get_workflows(self) -> Dict[str, Any]:
        """获取工作流列表"""
        try:
            workflows_dir = self.get_workflows_dir()
            workflows: List[Dict[str, Any]] = []
            
            if os.path.exists(workflows_dir):
                for file in os.listdir(workflows_dir):
                    if file.endswith(".json"):
                        workflow_path = os.path.join(workflows_dir, file)
                        workflow_info = {
                            "name": os.path.splitext(file)[0],
                            "path": workflow_path,
                            "created_at": datetime.fromtimestamp(os.path.getctime(workflow_path)).strftime("%Y-%m-%d %H:%M:%S"),
                            "size": os.path.getsize(workflow_path)
                        }
                        workflows.append(workflow_info)
            
            return {"status": "success", "workflows": workflows}
        except Exception as e:
            self.logger.error(f"获取工作流列表异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def save_workflow(self, workflow_name: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """保存工作流"""
        try:
            workflows_dir = self.get_workflows_dir()
            if not os.path.exists(workflows_dir):
                os.makedirs(workflows_dir, exist_ok=True)
            
            workflow_path = os.path.join(workflows_dir, f"{workflow_name}.json")
            
            with open(workflow_path, "w", encoding="utf-8") as f:
                json.dump(workflow_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"工作流保存成功: {workflow_name}")
            return {"status": "success", "message": "工作流保存成功"}
        except Exception as e:
            self.logger.error(f"保存工作流异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
    
    def load_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """加载工作流"""
        try:
            workflows_dir = self.get_workflows_dir()
            workflow_path = os.path.join(workflows_dir, f"{workflow_name}.json")
            
            if not os.path.exists(workflow_path):
                return {"status": "error", "message": "工作流不存在"}
            
            with open(workflow_path, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)
            
            return {"status": "success", "workflow": workflow_data}
        except Exception as e:
            self.logger.error(f"加载工作流异常: {str(e)}")
            return {"status": "error", "message": f"异常: {str(e)}"}
