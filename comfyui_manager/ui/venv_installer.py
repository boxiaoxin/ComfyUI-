#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虚拟环境安装模块
负责PyTorch和其他依赖的安装
"""

from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import sys
import os


class PyTorchInstallThread(QThread):
    """PyTorch安装线程"""
    # 定义信号
    update_output = pyqtSignal(str)
    update_progress = pyqtSignal(int)
    installation_finished = pyqtSignal(bool, str, str)
    
    def __init__(self, pip_path, install_command, gpu_type, venv_path):
        super().__init__()
        self.pip_path = pip_path
        self.install_command = install_command
        self.gpu_type = gpu_type
        self.venv_path = venv_path
    
    def run(self):
        """线程运行方法"""
        installed = False
        error_message = ""
        torch_version_info = ""
        
        # 添加网络加速参数
        def add_network_acceleration(cmd):
            """添加网络加速参数"""
            # 添加超时设置
            cmd.extend(["--timeout", "120"])
            # 添加重试机制
            cmd.extend(["--retries", "5"])
            # 添加代理设置（如果环境变量中有代理）
            if os.environ.get("HTTP_PROXY"):
                cmd.extend(["--proxy", os.environ.get("HTTP_PROXY")])
            elif os.environ.get("http_proxy"):
                cmd.extend(["--proxy", os.environ.get("http_proxy")])
            # 添加缓存设置
            cmd.extend(["--no-cache-dir"])
            return cmd
        
        try:
            # 构建命令
            if isinstance(self.pip_path, list):
                cmd = self.pip_path + self.install_command
            else:
                cmd = [self.pip_path] + self.install_command
            
            # 添加网络加速参数
            cmd = add_network_acceleration(cmd)
            
            # 立即发送初始输出，让用户知道安装开始
            try:
                initial_text = f"正在安装显卡PyTorch...\n虚拟环境: {self.venv_path}\n显卡类型: {self.gpu_type}\n安装命令: {' '.join(cmd)}\n\n正在启动安装进程...\n"
                self.update_output.emit(initial_text)
            except Exception as emit_error:
                pass
            
            # 逐步更新进度，让用户看到安装过程
            try:
                self.update_progress.emit(60)
            except:
                pass
            
            # 执行命令并捕获输出
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            
            output_lines = []
            progress = 60  # 初始进度
            
            try:
                # 使用更可靠的方式读取输出
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    output_lines.append(line)
                    # 限制显示的行数
                    if len(output_lines) > 50:
                        output_lines = output_lines[-50:]
                    # 发送输出更新信号
                    try:
                        display_text = f"正在安装显卡PyTorch...\n虚拟环境: {self.venv_path}\n显卡类型: {self.gpu_type}\n安装命令: {' '.join(cmd)}\n\n正在下载和安装...\n" + ''.join(output_lines)
                        self.update_output.emit(display_text)
                    except Exception as emit_error:
                        # 忽略信号发送错误，继续执行
                        pass
                    
                    # 根据输出内容更新进度
                    line_lower = line.lower()
                    if "downloading" in line_lower:
                        progress = 70
                        try:
                            self.update_progress.emit(progress)
                        except:
                            pass
                    elif "installing" in line_lower or "building wheel" in line_lower:
                        progress = 80
                        try:
                            self.update_progress.emit(progress)
                        except:
                            pass
                    elif "successfully installed" in line_lower:
                        progress = 90
                        try:
                            self.update_progress.emit(progress)
                        except:
                            pass
                    elif "requirement already satisfied" in line_lower:
                        # 已经安装的情况，也更新进度
                        progress = 85
                        try:
                            self.update_progress.emit(progress)
                        except:
                            pass
            except Exception as read_error:
                # 忽略读取输出错误，继续执行
                error_message = f"读取输出时出错: {str(read_error)}"
                # 发送错误信息
                try:
                    error_text = f"正在安装显卡PyTorch...\n虚拟环境: {self.venv_path}\n显卡类型: {self.gpu_type}\n安装命令: {' '.join(cmd)}\n\n读取输出时出错: {str(read_error)}\n"
                    self.update_output.emit(error_text)
                except:
                    pass
            
            try:
                process.wait(timeout=300)  # 设置5分钟超时
                # 安装完成
                progress = 100
                try:
                    self.update_progress.emit(progress)
                except:
                    pass
            except subprocess.TimeoutExpired:
                # 超时错误
                error_message = "安装超时，可能是网络问题或包过大"
                process.terminate()
                try:
                    timeout_text = f"正在安装显卡PyTorch...\n虚拟环境: {self.venv_path}\n显卡类型: {self.gpu_type}\n安装命令: {' '.join(cmd)}\n\n安装超时，可能是网络问题或包过大\n"
                    self.update_output.emit(timeout_text)
                    # 超时也设置进度为100
                    self.update_progress.emit(100)
                except:
                    pass
            except Exception as wait_error:
                # 忽略等待进程错误，继续执行
                error_message = f"等待进程时出错: {str(wait_error)}"
                try:
                    wait_error_text = f"正在安装显卡PyTorch...\n虚拟环境: {self.venv_path}\n显卡类型: {self.gpu_type}\n安装命令: {' '.join(cmd)}\n\n等待进程时出错: {str(wait_error)}\n"
                    self.update_output.emit(wait_error_text)
                    # 错误也设置进度为100
                    self.update_progress.emit(100)
                except:
                    pass
            
            if process.returncode == 0:
                installed = True
                # 根据命令确定安装的版本信息
                if "cu" in ' '.join(self.install_command):
                    torch_version_info = "CUDA版本的PyTorch"
                elif "rocm" in ' '.join(self.install_command):
                    torch_version_info = "ROCm版本的PyTorch"
                elif "xpu" in ' '.join(self.install_command):
                    torch_version_info = "Intel XPU版本的PyTorch"
                else:
                    torch_version_info = "CPU版本的PyTorch"
            else:
                error_message = ''.join(output_lines)
        except Exception as e:
            error_message = f"安装过程出错: {str(e)}"
            # 出错时也将进度设置为100，确保进度条完成
            try:
                self.update_progress.emit(100)
            except:
                pass
            # 发送错误信息
            try:
                error_text = f"正在安装显卡PyTorch...\n虚拟环境: {self.venv_path}\n显卡类型: {self.gpu_type}\n安装命令: {' '.join(cmd)}\n\n安装过程出错: {str(e)}\n"
                self.update_output.emit(error_text)
            except:
                pass
        
        try:
            # 发送完成信号
            self.installation_finished.emit(installed, error_message, torch_version_info)
        except Exception as emit_error:
            # 忽略信号发送错误
            pass
