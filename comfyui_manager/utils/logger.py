#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


class Logger:
    """日志管理类"""
    
    def __init__(self):
        """初始化日志系统"""
        # 创建日志目录
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 日志文件名（固定文件名，不按日期存储）
        self.log_file = os.path.join(self.log_dir, "comfyui_manager.log")
        
        # 配置根日志
        self.logger = logging.getLogger("ComfyUI_Manager")
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 文件处理器
            file_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'  # 使用UTF-8编码
            )
            file_handler.setLevel(logging.DEBUG)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            # 设置控制台处理器的编码为UTF-8
            console_handler.encoding = 'utf-8'
            
            # 格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # 添加处理器
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        
        # 日志写入计数器，用于控制清理频率
        self.log_count = 0
        # 清理阈值，每写入100条日志检查一次
        self.cleanup_threshold = 100
    
    def debug(self, message: str, extra=None) -> None:
        """调试日志"""
        self.logger.debug(message, extra=extra)
        self._check_cleanup()
    
    def info(self, message: str, extra=None) -> None:
        """信息日志"""
        self.logger.info(message, extra=extra)
        self._check_cleanup()
    
    def warning(self, message: str, extra=None) -> None:
        """警告日志"""
        self.logger.warning(message, extra=extra)
        self._check_cleanup()
    
    def error(self, message: str, extra=None) -> None:
        """错误日志"""
        self.logger.error(message, extra=extra)
        self._check_cleanup()
    
    def critical(self, message: str, extra=None) -> None:
        """严重错误日志"""
        self.logger.critical(message, extra=extra)
        self._check_cleanup()
    
    def _check_cleanup(self) -> None:
        """检查是否需要清理日志"""
        self.log_count += 1
        if self.log_count >= self.cleanup_threshold:
            self.log_count = 0
            self.cleanup_logs()
    
    def cleanup_logs(self) -> None:
        """自动清理日志文件，保持文件大小在合理范围内"""
        try:
            if not os.path.exists(self.log_file):
                return
            
            # 检查文件大小（1024KB = 1MB）
            file_size = os.path.getsize(self.log_file) / 1024  # 转换为KB
            
            if file_size >= 1024:  # 达到1024KB时清理
                # 目标大小：128KB
                target_size = 128 * 1024  # 转换为字节
                
                try:
                    # 以二进制模式打开文件，避免编码问题
                    with open(self.log_file, 'rb') as f:
                        # 定位到文件末尾
                        f.seek(0, os.SEEK_END)
                        file_length = f.tell()
                        
                        # 从文件末尾向前读取，直到达到目标大小
                        current_position = file_length
                        bytes_read = 0
                        
                        # 向前读取，寻找换行符，确保完整行
                        while current_position > 0 and bytes_read < target_size:
                            current_position -= 1
                            f.seek(current_position)
                            byte = f.read(1)
                            if byte == b'\n':
                                # 找到换行符，从这里开始保留
                                current_position += 1
                                break
                            bytes_read += 1
                        
                        # 读取要保留的内容
                        f.seek(current_position)
                        content_to_keep = f.read()
                    
                    # 确保保留的内容大小小于目标大小
                    if len(content_to_keep) > target_size:
                        # 如果仍然超过目标大小，再次调整
                        content_lines = content_to_keep.decode('utf-8', errors='ignore').split('\n')
                        while len('\n'.join(content_lines).encode('utf-8')) > target_size and content_lines:
                            content_lines.pop(0)  # 移除最早的日志行
                        content_to_keep = '\n'.join(content_lines).encode('utf-8')
                    
                    # 写回保留的内容
                    with open(self.log_file, 'wb') as f:
                        f.write(content_to_keep)
                    
                    # 记录清理操作 - 直接打印，避免再次触发清理
                    print(f"日志文件已清理，大小从 {file_size:.2f}KB 减少到 {len(content_to_keep)/1024:.2f}KB")
                except Exception as e:
                    # 如果清理失败，尝试更简单的方法：直接清空文件
                    print(f"日志清理失败，尝试清空文件: {str(e)}")
                    with open(self.log_file, 'wb') as f:
                        f.write(b'')
                    print("日志文件已清空")
        except Exception as e:
            # 避免清理过程影响正常日志功能
            print(f"日志清理失败: {str(e)}")
