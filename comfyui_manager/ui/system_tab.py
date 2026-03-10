#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统信息标签页
"""

import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from comfyui_manager.modules.system_detector import SystemDetector
from comfyui_manager.utils.logger import Logger
from comfyui_manager.utils.language_manager import lang_manager


class DetectionThread(QThread):
    """检测线程"""
    update_progress = pyqtSignal(int, str)
    detection_finished = pyqtSignal(dict)
    
    def run(self):
        """运行检测"""
        try:
            detector = SystemDetector()
            
            # 定义进度回调函数
            def progress_callback(progress, message):
                self.update_progress.emit(progress, message)
            
            # 运行完整检测（会自动保存到缓存）
            results = detector.run_complete_detection(progress_callback=progress_callback)
            
            self.detection_finished.emit(results)
        except Exception as e:
            # 发送错误信息
            self.detection_finished.emit({"errors": [{"模块": "检测线程", "错误": str(e), "严重程度": "错误"}]})


class SystemTab(QWidget):
    """系统信息标签页"""
    
    def __init__(self, parent=None):
        """初始化"""
        super().__init__(parent)
        self.logger = Logger()
        self.detection_thread = None
        # 点击时间记录，用于防重复点击
        self.last_click_time = {}
        self.click_cooldown = 2  # 点击冷却时间（秒）
        # 获取当前主题
        import json
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        self.theme = 1  # 默认深色主题
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.theme = config.get("theme", 1)
            except Exception as e:
                self.logger.error(f"读取主题设置失败: {e}")

        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 初始化样式
        self._init_styles()
        
        # 设置样式
        self.setStyleSheet(self.widget_style)
        
        # 二级菜单按钮容器
        menu_container = QWidget()
        menu_layout = QHBoxLayout(menu_container)
        
        # 存储当前高亮的按钮
        self.current_highlighted_button = None
        
        # 系统检测按钮
        self.system_detect_button = QPushButton(lang_manager.get("system_detect"))
        self.system_detect_button.clicked.connect(lambda: self._handle_button_click(self.system_detect_button, self.start_detection))
        menu_layout.addWidget(self.system_detect_button)
        
        # 硬件信息按钮
        self.hardware_info_button = QPushButton(lang_manager.get("hardware_info"))
        self.hardware_info_button.clicked.connect(lambda: self._handle_button_click(self.hardware_info_button, self.show_hardware_info))
        menu_layout.addWidget(self.hardware_info_button)
        
        # 存储状态按钮
        self.storage_status_button = QPushButton(lang_manager.get("storage_status"))
        self.storage_status_button.clicked.connect(lambda: self._handle_button_click(self.storage_status_button, self.show_storage_status))
        menu_layout.addWidget(self.storage_status_button)
        
        # 功能软件按钮
        self.software_button = QPushButton(lang_manager.get("software_info"))
        self.software_button.clicked.connect(lambda: self._handle_button_click(self.software_button, self.show_software_info))
        menu_layout.addWidget(self.software_button)
        
        layout.addWidget(menu_container)
        
        # 添加占位符，使信息窗口向下移动，与一级菜单的下边框水平
        layout.addStretch()
        
        # 系统信息容器（包含系统信息和进度条）
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(12, 12, 12, 12)
        
        # 系统信息
        self.system_info = QTextEdit()
        self.system_info.setReadOnly(True)
        self.system_info.setMinimumHeight(400)
        self.system_info.setStyleSheet(self.text_edit_style)
        info_layout.addWidget(self.system_info, 1)
        
        # 自动加载缓存数据
        self._load_cache_data()
        
        # 进度条（添加到系统信息条框内部）
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)  # 隐藏文字，避免显示不全
        self.progress_bar.setMaximumHeight(16)  # 增加高度一倍
        self.progress_bar.setStyleSheet(self.progress_bar_style)
        info_layout.addWidget(self.progress_bar)
        
        # 设置容器样式，使其与系统信息条框一致
        info_container.setStyleSheet(self.container_style)
        
        # 将容器添加到主布局
        layout.addWidget(info_container, 1)
    
    def _init_styles(self):
        """初始化样式"""
        # 根据主题设置样式
        if self.theme == 0:  # 浅色主题
            # 组件样式 - 与一级菜单颜色一致
            self.widget_style = """
                QWidget {
                    background: transparent;
                    color: #333333;
                }
                QPushButton {
                    background: rgba(0, 0, 0, 0.05);
                    color: #333333;
                    border: 1px solid rgba(0, 0, 0, 0.2);
                    padding: 12px 15px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.1);
                    border-color: rgba(0, 0, 0, 0.3);
                    color: #333333;
                }
                QPushButton:disabled {
                    background: rgba(0, 0, 0, 0.05);
                    color: rgba(0, 0, 0, 0.4);
                    border-color: rgba(0, 0, 0, 0.1);
                }
            """
            # 高亮按钮样式
            self.highlighted_button_style = """
                QPushButton {
                    background: rgba(25, 118, 210, 0.1);
                    border-color: rgba(25, 118, 210, 0.3);
                    color: #333333;
                    padding: 12px 15px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                    box-shadow: 0 2px 12px rgba(25, 118, 210, 0.2);
                }
            """
            
            # 文本编辑框样式
            self.text_edit_style = """
                QTextEdit {
                    background: transparent;
                    color: #041a47;
                    border: none;
                    border-radius: 0;
                    padding: 0;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 13px;
                    margin: 0;
                }
                QScrollBar:vertical {
                    background: rgba(0, 0, 0, 0.05);
                    width: 10px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical {
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 5px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background: rgba(0, 0, 0, 0.5);
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    background: transparent;
                    height: 0;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: transparent;
                }
                QScrollBar:horizontal {
                    background: rgba(0, 0, 0, 0.05);
                    height: 10px;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal {
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 5px;
                    min-width: 20px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: rgba(0, 0, 0, 0.5);
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    background: transparent;
                    width: 0;
                }
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                    background: transparent;
                }
            """
            
            # 进度条样式
            self.progress_bar_style = """
                QProgressBar {
                    background: rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(0, 0, 0, 0.2);
                    border-radius: 4px;
                    padding: 1px;
                    margin-top: 8px;
                }
                QProgressBar::chunk {
                    background: #0077be;
                    border-radius: 3px;
                }
            """
        else:  # 深色主题
            # 组件样式
            self.widget_style = """
                QWidget {
                    background: transparent;
                    color: #ffffff;
                }
                QPushButton {
                    background: rgba(255, 255, 255, 0.2);
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 0.4);
                    padding: 12px 15px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.3);
                    border-color: rgba(255, 255, 255, 0.6);
                }
                QPushButton:disabled {
                    background: rgba(255, 255, 255, 0.1);
                    color: rgba(255, 255, 255, 0.6);
                    border-color: rgba(255, 255, 255, 0.2);
                }
            """
            # 高亮按钮样式
            self.highlighted_button_style = """
                QPushButton {
                    background: rgba(255, 255, 255, 0.4);
                    border-color: rgba(255, 255, 255, 0.5);
                    color: #ffffff;
                    padding: 12px 15px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                    box-shadow: 0 2px 12px rgba(255, 255, 255, 0.25);
                }
            """
            
            # 文本编辑框样式
            self.text_edit_style = """
                QTextEdit {
                    background: transparent;
                    color: #041a47;
                    border: none;
                    border-radius: 0;
                    padding: 0;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 13px;
                    margin: 0;
                }
                QScrollBar:vertical {
                    background: rgba(0, 0, 0, 0.1);
                    width: 10px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical {
                    background: rgba(255, 255, 255, 0.6);
                    border-radius: 5px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background: rgba(255, 255, 255, 0.8);
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    background: transparent;
                    height: 0;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: transparent;
                }
                QScrollBar:horizontal {
                    background: rgba(0, 0, 0, 0.1);
                    height: 10px;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal {
                    background: rgba(255, 255, 255, 0.6);
                    border-radius: 5px;
                    min-width: 20px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: rgba(255, 255, 255, 0.8);
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    background: transparent;
                    width: 0;
                }
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                    background: transparent;
                }
            """
            
            # 进度条样式
            self.progress_bar_style = """
                QProgressBar {
                    background: rgba(0, 0, 0, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                    padding: 1px;
                    margin-top: 8px;
                }
                QProgressBar::chunk {
                    background: #0077be;
                    border-radius: 3px;
                }
            """
        
        # 容器样式（通用）
        self.container_style = """
            QWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(25, 118, 210, 0.4);
                border-radius: 8px;
            }
        """
    
    def _disable_buttons(self):
        """禁用所有按钮"""
        self.system_detect_button.setEnabled(False)
        self.hardware_info_button.setEnabled(False)
        self.storage_status_button.setEnabled(False)
        self.software_button.setEnabled(False)
    
    def _enable_buttons(self):
        """启用所有按钮"""
        self.system_detect_button.setEnabled(True)
        self.hardware_info_button.setEnabled(True)
        self.storage_status_button.setEnabled(True)
        self.software_button.setEnabled(True)
    
    def _reset_progress(self):
        """重置进度条"""
        self.progress_bar.setValue(0)
    
    def is_click_valid(self, button_id):
        """检查点击是否有效（防重复点击）
        
        Args:
            button_id: 按钮唯一标识
            
        Returns:
            bool: True表示点击有效，False表示点击无效
        """
        current_time = time.time()
        last_time = self.last_click_time.get(button_id, 0)
        
        if current_time - last_time < self.click_cooldown:
            # 点击过于频繁，无效
            self.logger.info(f"点击过于频繁，{button_id} 按钮在 {self.click_cooldown} 秒内不可重复点击")
            return False
        
        # 更新点击时间
        self.last_click_time[button_id] = current_time
        self.logger.info(f"点击有效，更新 {button_id} 按钮的点击时间为 {current_time}")
        return True
    
    def _handle_button_click(self, button, callback):
        """处理按钮点击事件，实现高亮功能
        
        Args:
            button: 被点击的按钮
            callback: 原始的点击处理函数
        """
        # 重置当前高亮按钮的样式
        if self.current_highlighted_button:
            self.current_highlighted_button.setStyleSheet("")
        
        # 为当前点击的按钮设置高亮样式
        button.setStyleSheet(self.highlighted_button_style)
        
        # 更新当前高亮按钮
        self.current_highlighted_button = button
        
        # 调用原始的点击处理函数
        callback()
    
    def _load_cache_data(self):
        """加载缓存数据"""
        try:
            from comfyui_manager.modules.system_detector import SystemDetector
            
            # 尝试加载缓存
            detector = SystemDetector()
            cached_results = detector.load_cache()
            
            if cached_results:
                # 缓存存在，直接使用缓存数据
                self.logger.info("自动加载缓存的检测结果")
                self.system_info.setPlainText(lang_manager.get("loading_cache"))
                
                # 显示缓存结果
                info_text = self.format_detection_results(cached_results)
                self.system_info.setPlainText(info_text)
                # 记录格式化后的结果的前100个字符，以便调试
                self.logger.info(f"格式化后的检测结果: {info_text[:100]}...")
            else:
                # 没有缓存，显示默认提示
                self.system_info.setPlainText(lang_manager.get("click_to_detect"))
        except Exception as e:
            self.logger.error(f"加载缓存数据失败: {e}")
            self.system_info.setPlainText(lang_manager.get("click_to_detect"))
    
    def start_detection(self):
        """开始检测"""
        # 检查点击是否有效
        if not self.is_click_valid("system_detect"):
            return
            
        try:
            self.logger.info("开始系统检测")
            # 禁用所有按钮
            self._disable_buttons()
            
            # 清除旧缓存，进行新的检测
            self.logger.info("清除旧缓存，进行新的系统检测")
            detector = SystemDetector()
            detector.clear_cache()
            
            # 开始新的检测
            self.system_info.setPlainText(lang_manager.get("detecting_system"))
            
            # 停止之前的线程（如果存在）
            if self.detection_thread and self.detection_thread.isRunning():
                self.detection_thread.terminate()
                self.detection_thread.wait()
            
            # 创建并启动检测线程
            self.detection_thread = DetectionThread()
            self.detection_thread.update_progress.connect(self.update_progress)
            self.detection_thread.detection_finished.connect(self.detection_finished)
            self.detection_thread.start()
        except Exception as e:
            self.logger.error(f"启动检测失败: {e}")
            self.system_info.setPlainText(lang_manager.get("start_detection_failed").format(error=str(e)))
            self._enable_buttons()
            self._reset_progress()
    
    def show_hardware_info(self):
        """显示硬件信息"""
        # 检查点击是否有效
        if not self.is_click_valid("hardware_info"):
            return
            
        try:
            self.logger.info("显示硬件信息")
            # 禁用所有按钮
            self._disable_buttons()
            
            # 尝试加载缓存
            detector = SystemDetector()
            cached_results = detector.load_cache()
            
            if cached_results:
                # 缓存存在，直接使用缓存数据
                self.logger.info("使用缓存的检测结果")
                self.system_info.setPlainText(lang_manager.get("loading_cache"))
                self.progress_bar.setValue(100)
                
                # 显示缓存结果
                info_text = self.format_hardware_info_results(cached_results)
                self.system_info.setPlainText(info_text)
                
                # 启用所有按钮
                self._enable_buttons()
                self._reset_progress()
                return
            else:
                # 没有缓存，提示用户先运行系统检测
                self.logger.info("没有检测缓存数据")
                self.system_info.setPlainText(lang_manager.get("no_cache_data"))
                
                # 启用所有按钮
                self._enable_buttons()
                self._reset_progress()
                return
        except Exception as e:
            self.logger.error(f"显示硬件信息失败: {e}")
            self.system_info.setPlainText(lang_manager.get("show_hardware_failed").format(error=str(e)))
            self._enable_buttons()
            self._reset_progress()
    
    def show_storage_status(self):
        """显示存储状态"""
        # 检查点击是否有效
        if not self.is_click_valid("storage_status"):
            return
            
        try:
            self.logger.info("显示存储状态")
            # 禁用所有按钮
            self._disable_buttons()
            
            # 尝试加载缓存
            detector = SystemDetector()
            cached_results = detector.load_cache()
            
            if cached_results:
                # 缓存存在，直接使用缓存数据
                self.logger.info("使用缓存的检测结果")
                self.system_info.setPlainText(lang_manager.get("loading_cache"))
                self.progress_bar.setValue(100)
                
                # 显示缓存结果
                info_text = self.format_storage_status_results(cached_results)
                self.system_info.setPlainText(info_text)
                
                # 启用所有按钮
                self._enable_buttons()
                self._reset_progress()
                return
            else:
                # 没有缓存，提示用户先运行系统检测
                self.logger.info("没有检测缓存数据")
                self.system_info.setPlainText(lang_manager.get("no_cache_data"))
                
                # 启用所有按钮
                self._enable_buttons()
                self._reset_progress()
                return
        except Exception as e:
            self.logger.error(f"显示存储状态失败: {e}")
            self.system_info.setPlainText(lang_manager.get("show_storage_failed").format(error=str(e)))
            self._enable_buttons()
            self._reset_progress()
    
    def show_software_info(self):
        """显示功能软件信息"""
        # 检查点击是否有效
        if not self.is_click_valid("software_info"):
            return
            
        try:
            self.logger.info("显示功能软件信息")
            # 禁用所有按钮
            self._disable_buttons()
            
            # 尝试加载缓存
            detector = SystemDetector()
            cached_results = detector.load_cache()
            
            if cached_results:
                # 缓存存在，直接使用缓存数据
                self.logger.info("使用缓存的检测结果")
                self.system_info.setPlainText(lang_manager.get("loading_cache"))
                self.progress_bar.setValue(100)
                
                # 显示缓存结果
                info_text = self.format_software_info_results(cached_results)
                self.system_info.setPlainText(info_text)
                
                # 启用所有按钮
                self._enable_buttons()
                self._reset_progress()
                return
            else:
                # 没有缓存，提示用户先运行系统检测
                self.logger.info("没有检测缓存数据")
                self.system_info.setPlainText(lang_manager.get("no_cache_data"))
                
                # 启用所有按钮
                self._enable_buttons()
                self._reset_progress()
                return
        except Exception as e:
            self.logger.error(f"显示功能软件信息失败: {e}")
            self.system_info.setPlainText(lang_manager.get("show_software_failed").format(error=str(e)))
            self._enable_buttons()
            self._reset_progress()
    
    def update_progress(self, value, message):
        """更新进度"""
        try:
            # 更新进度条
            self.progress_bar.setValue(value)
            # 记录日志
            self.logger.info(f"检测进度: {value}% - {message}")
        except Exception as e:
            self.logger.error(f"更新进度失败: {e}")
    
    def detection_finished(self, results):
        """检测完成"""
        try:
            self.logger.info("系统检测完成")
            # 启用所有按钮
            self._enable_buttons()
            
            # 重置进度条
            self._reset_progress()
            
            # 格式化检测结果
            info_text = self.format_detection_results(results)
            self.system_info.setPlainText(info_text)
            
            # 记录到日志
            self.logger.info("系统检测完成，详细信息已显示")
            # 只记录关键信息，避免日志过大
            self.logger.info(f"检测结果概览: 系统信息={len(results.get('system', {}))}项, CPU信息={len(results.get('cpu', {}))}项, GPU数量={len(results.get('gpu', []))}")
        except Exception as e:
            self.logger.error(f"处理检测结果失败: {e}")
            self.system_info.setPlainText(lang_manager.get("processing_results_failed").format(error=str(e)))
    
    def hardware_info_finished(self, results):
        """硬件信息检测完成"""
        try:
            self.logger.info("硬件信息检测完成")
            # 启用所有按钮
            self._enable_buttons()
            
            # 重置进度条
            self._reset_progress()
            
            # 格式化硬件检测结果
            info_text = self.format_hardware_info_results(results)
            self.system_info.setPlainText(info_text)
            
            # 记录到日志
            self.logger.info("硬件信息检测完成，详细信息已显示")
        except Exception as e:
            self.logger.error(f"处理硬件检测结果失败: {e}")
            self.system_info.setPlainText(lang_manager.get("processing_hardware_failed").format(error=str(e)))
    
    def storage_status_finished(self, results):
        """存储状态检测完成"""
        try:
            self.logger.info("存储状态检测完成")
            # 启用所有按钮
            self._enable_buttons()
            
            # 重置进度条
            self._reset_progress()
            
            # 格式化存储状态检测结果
            info_text = self.format_storage_status_results(results)
            self.system_info.setPlainText(info_text)
            
            # 记录到日志
            self.logger.info("存储状态检测完成，详细信息已显示")
        except Exception as e:
            self.logger.error(f"处理存储状态检测结果失败: {e}")
            self.system_info.setPlainText(lang_manager.get("processing_storage_failed").format(error=str(e)))
    
    def software_info_finished(self, results):
        """功能软件信息检测完成"""
        try:
            self.logger.info("功能软件信息检测完成")
            # 启用所有按钮
            self._enable_buttons()
            
            # 重置进度条
            self._reset_progress()
            
            # 格式化功能软件信息检测结果
            info_text = self.format_software_info_results(results)
            self.system_info.setPlainText(info_text)
            
            # 记录到日志
            self.logger.info("功能软件信息检测完成，详细信息已显示")
        except Exception as e:
            self.logger.error(f"处理功能软件信息检测结果失败: {e}")
            self.system_info.setPlainText(lang_manager.get("processing_software_failed").format(error=str(e)))
    
    def _get_translated_key(self, key):
        """根据当前语言获取翻译后的键名"""
        # 中文到英文的键名映射
        key_mapping = {
            # 元数据
            "检测时间": "Detection Time",
            "操作系统": "Operating System",
            "Python版本": "Python Version",
            "检测工具版本": "Detection Tool Version",
            "管理员权限": "Admin Rights",
            "缓存时间": "Cache Time",
            
            # 系统信息
            "系统类型": "System Type",
            "系统版本": "System Version",
            "系统架构": "System Architecture",
            "主机名": "Hostname",
            "Windows版本": "Windows Version",
            
            # CPU信息
            "品牌型号": "Brand Model",
            "架构": "Architecture",
            "逻辑核心数": "Logical Cores",
            "物理核心数": "Physical Cores",
            "CPU使用率(%)": "CPU Usage(%)",
            
            # GPU信息
            "型号": "Model",
            "厂商": "Vendor",
            "类型": "Type",
            "检测方法": "Detection Method",
            "专用显存(GB)": "Dedicated VRAM(GB)",
            "驱动版本": "Driver Version",
            "Intel Arc系列": "Intel Arc Series",
            "官方显存规格": "Official VRAM Spec",
            "显存类型": "VRAM Type",
            "显存说明": "VRAM Description",
            "状态": "Status",
            "建议": "Suggestion",
            
            # 内存信息
            "总物理内存(GB)": "Total Physical Memory(GB)",
            "可用物理内存(GB)": "Available Physical Memory(GB)",
            "已用物理内存(GB)": "Used Physical Memory(GB)",
            "物理内存使用率(%)": "Physical Memory Usage(%)",
            "内存模块": "Memory Modules",
            "容量(GB)": "Capacity(GB)",
            "速度(MHz)": "Speed(MHz)",
            "制造商": "Manufacturer",
            "型号": "Model",
            
            # 存储信息
            "设备": "Device",
            "挂载点": "Mount Point",
            "文件系统": "File System",
            "总容量(GB)": "Total Capacity(GB)",
            "可用容量(GB)": "Available Capacity(GB)",
            "已用容量(GB)": "Used Capacity(GB)",
            "使用率(%)": "Usage(%)",
            
            # 网络信息
            "类型": "Type",
            "接口名": "Interface Name",
            "状态": "Status",
            "IPv4地址": "IPv4 Address",
            "子网掩码": "Subnet Mask",
            "IPv6地址": "IPv6 Address",
            "检测时间": "Detection Time",
            
            # Python信息
            "命令": "Command",
            "版本": "Version",
            "路径": "Path",
            "Pip可用": "Pip Available",
            "检测方法": "Detection Method",
            
            # Git信息
            "版本": "Version",
            "状态": "Status",
            "路径": "Path",
            "类型": "Type",
            "建议": "Suggestion",
            
            # 错误信息
            "模块": "Module",
            "错误": "Error",
            "时间": "Time",
            "严重程度": "Severity"
        }
        
        # 英文到中文的键名映射（反向映射）
        reverse_key_mapping = {v: k for k, v in key_mapping.items()}
        
        # 根据当前语言返回相应的键名
        current_language = lang_manager.get_language()
        if current_language == "English":
            if key in key_mapping:
                return key_mapping[key]
        else:  # 中文
            if key in reverse_key_mapping:
                return reverse_key_mapping[key]
        return key
    
    def _translate_value(self, key, value):
        """根据键名和当前语言翻译值"""
        # 中文到英文的值映射
        value_mapping = {
            # 检测方法
            "当前Python": "Current Python",
            "Windows WMI": "Windows WMI",
            "Linux lspci": "Linux lspci",
            "macOS system_profiler": "macOS system_profiler",
            "系统命令": "System Command",
            
            # 状态
            "已安装": "Installed",
            "未安装": "Not Installed",
            "未知": "Unknown",
            "未检测到显卡": "No GPU detected",
            "未检测到存储设备": "No storage devices detected",
            "未检测到Python": "No Python detected",
            
            # 类型
            "独立显卡": "Dedicated GPU",
            "集成显卡": "Integrated GPU",
            "内嵌Git": "Embedded Git",
            "系统Git": "System Git",
            "网络接口": "Network Interface",
            "蓝牙网络连接": "Bluetooth Network Connection",
            
            # 建议
            "请检查驱动和权限": "Please check drivers and permissions",
            "请检查权限": "Please check permissions",
            "请安装Python 3.9或更高版本": "Please install Python 3.9 or higher",
            "请检查Git安装": "Please check Git installation",
            "请安装Git": "Please install Git",
            
            # 其他
            "是": "Yes",
            "否": "No",
            "True": "True",
            "False": "False"
        }
        
        # 英文到中文的值映射（反向映射）
        reverse_value_mapping = {v: k for k, v in value_mapping.items()}
        
        # 根据当前语言返回相应的值
        current_language = lang_manager.get_language()
        if current_language == "English":
            if value in value_mapping:
                return value_mapping[value]
            # 处理包含中文的网络接口名称
            if isinstance(value, str) and "本地连接" in value:
                return value.replace("本地连接", "Local Connection")
        else:  # 中文
            if value in reverse_value_mapping:
                return reverse_value_mapping[value]
            # 处理包含英文的网络接口名称
            if isinstance(value, str) and "Local Connection" in value:
                return value.replace("Local Connection", "本地连接")
        return value
    
    def format_detection_results(self, results):
        """格式化检测结果"""
        try:
            info_text = ""
            
            # 元数据
            info_text += f"=== {lang_manager.get('detection_overview')} ===\n"
            for key, value in results.get("metadata", {}).items():
                translated_key = self._get_translated_key(key)
                translated_value = self._translate_value(key, value)
                info_text += f"{translated_key}: {translated_value}\n"
            info_text += "\n"
            
            # 系统信息
            info_text += f"=== {lang_manager.get('system_overview')} ===\n"
            for key, value in results.get("system", {}).items():
                translated_key = self._get_translated_key(key)
                translated_value = self._translate_value(key, value)
                info_text += f"{translated_key}: {translated_value}\n"
            info_text += "\n"
            
            # CPU信息
            info_text += f"=== {lang_manager.get('cpu_info')} ===\n"
            for key, value in results.get("cpu", {}).items():
                translated_key = self._get_translated_key(key)
                translated_value = self._translate_value(key, value)
                info_text += f"{translated_key}: {translated_value}\n"
            info_text += "\n"
            
            # GPU信息
            info_text += f"=== {lang_manager.get('gpu_info')} ===\n"
            for i, gpu in enumerate(results.get("gpu", [])):
                info_text += f"GPU {i+1}:\n"
                for key, value in gpu.items():
                    translated_key = self._get_translated_key(key)
                    translated_value = self._translate_value(key, value)
                    info_text += f"  {translated_key}: {translated_value}\n"
            info_text += "\n"
            
            # 内存信息
            info_text += f"=== {lang_manager.get('memory_info')} ===\n"
            for key, value in results.get("memory", {}).items():
                translated_key = self._get_translated_key(key)
                if key == "内存模块" and isinstance(value, list):
                    info_text += f"{translated_key}:\n"
                    for module in value:
                        for module_key, module_value in module.items():
                            translated_module_key = self._get_translated_key(module_key)
                            translated_module_value = self._translate_value(module_key, module_value)
                            info_text += f"  {translated_module_key}: {translated_module_value}\n"
                else:
                    translated_value = self._translate_value(key, value)
                    info_text += f"{translated_key}: {translated_value}\n"
            info_text += "\n"
            
            # 存储信息
            info_text += f"=== {lang_manager.get('storage_info')} ===\n"
            for i, storage in enumerate(results.get("storage", [])):
                info_text += f"{lang_manager.get('storage_info')} {i+1}:\n"
                for key, value in storage.items():
                    translated_key = self._get_translated_key(key)
                    translated_value = self._translate_value(key, value)
                    info_text += f"  {translated_key}: {translated_value}\n"
            info_text += "\n"
            
            # 网络信息
            info_text += f"=== {lang_manager.get('network_info')} ===\n"
            for i, network in enumerate(results.get("network", [])):
                info_text += f"{lang_manager.get('network_info')} {i+1}:\n"
                for key, value in network.items():
                    translated_key = self._get_translated_key(key)
                    if key == "IPv6地址" and isinstance(value, list):
                        info_text += f"  {translated_key}:\n"
                        for addr in value:
                            info_text += f"    - {addr}\n"
                    else:
                        translated_value = self._translate_value(key, value)
                        info_text += f"  {translated_key}: {translated_value}\n"
            info_text += "\n"
            
            # Python信息
            info_text += f"=== {lang_manager.get('python_info')} ===\n"
            for i, python in enumerate(results.get("python", [])):
                info_text += f"Python {i+1}:\n"
                for key, value in python.items():
                    translated_key = self._get_translated_key(key)
                    translated_value = self._translate_value(key, value)
                    info_text += f"  {translated_key}: {translated_value}\n"
            info_text += "\n"
            
            # Git信息
            info_text += f"=== {lang_manager.get('git_info')} ===\n"
            git_info = results.get("git", {})
            if git_info:
                for key, value in git_info.items():
                    translated_key = self._get_translated_key(key)
                    translated_value = self._translate_value(key, value)
                    info_text += f"{translated_key}: {translated_value}\n"
            else:
                info_text += f"{lang_manager.get('no_git_info')}\n"
            info_text += "\n"
            
            # 错误信息
            error_list = [error for error in results.get("errors", []) if error.get('严重程度') == "error"]
            if error_list:
                info_text += f"=== {lang_manager.get('error_info')} ===\n"
                for error in error_list:
                    translated_module = self._get_translated_key("模块")
                    translated_error = self._get_translated_key("错误")
                    translated_module_value = self._translate_value("模块", error.get('模块'))
                    translated_error_value = self._translate_value("错误", error.get('错误'))
                    info_text += f"{translated_module}: {translated_module_value}, {translated_error}: {translated_error_value}\n"
            
            return info_text
        except Exception as e:
            return lang_manager.get("format_error").format(error=str(e))
    
    def format_hardware_info_results(self, results):
        """格式化硬件检测结果"""
        try:
            info_text = ""
            
            # 检测概览
            info_text += f"=== {lang_manager.get('hardware_detection_overview')} ===\n"
            detection_time_key = self._get_translated_key("检测时间")
            detection_time_value = results.get('metadata', {}).get('检测时间', '未知')
            translated_detection_time_value = self._translate_value("检测时间", detection_time_value)
            info_text += f"{lang_manager.get('detection_time')}: {translated_detection_time_value}\n"
            info_text += "\n"
            
            # CPU信息
            info_text += f"=== {lang_manager.get('cpu_info')} ===\n"
            for key, value in results.get("cpu", {}).items():
                translated_key = self._get_translated_key(key)
                translated_value = self._translate_value(key, value)
                info_text += f"{translated_key}: {translated_value}\n"
            info_text += "\n"
            
            # GPU信息
            info_text += f"=== {lang_manager.get('gpu_info')} ===\n"
            for i, gpu in enumerate(results.get("gpu", [])):
                info_text += f"GPU {i+1}:\n"
                for key, value in gpu.items():
                    translated_key = self._get_translated_key(key)
                    translated_value = self._translate_value(key, value)
                    info_text += f"  {translated_key}: {translated_value}\n"
            info_text += "\n"
            
            # 内存信息
            info_text += f"=== {lang_manager.get('memory_info')} ===\n"
            for key, value in results.get("memory", {}).items():
                translated_key = self._get_translated_key(key)
                if key == "内存模块" and isinstance(value, list):
                    info_text += f"{translated_key}:\n"
                    for module in value:
                        for module_key, module_value in module.items():
                            translated_module_key = self._get_translated_key(module_key)
                            translated_module_value = self._translate_value(module_key, module_value)
                            info_text += f"  {translated_module_key}: {translated_module_value}\n"
                else:
                    translated_value = self._translate_value(key, value)
                    info_text += f"{translated_key}: {translated_value}\n"
            info_text += "\n"
            
            # 存储信息
            info_text += f"=== {lang_manager.get('storage_info')} ===\n"
            for i, storage in enumerate(results.get("storage", [])):
                info_text += f"{lang_manager.get('storage_info')} {i+1}:\n"
                for key, value in storage.items():
                    translated_key = self._get_translated_key(key)
                    translated_value = self._translate_value(key, value)
                    info_text += f"  {translated_key}: {translated_value}\n"
            
            return info_text
        except Exception as e:
            return lang_manager.get("format_hardware_error").format(error=str(e))
    
    def format_storage_status_results(self, results):
        """格式化存储状态检测结果"""
        try:
            info_text = ""
            
            # 检测概览
            info_text += f"=== {lang_manager.get('storage_detection_overview')} ===\n"
            detection_time_value = results.get('metadata', {}).get('检测时间', '未知')
            translated_detection_time_value = self._translate_value("检测时间", detection_time_value)
            info_text += f"{lang_manager.get('detection_time')}: {translated_detection_time_value}\n"
            info_text += "\n"
            
            # 存储信息
            info_text += f"=== {lang_manager.get('storage_info')} ===\n"
            for i, storage in enumerate(results.get("storage", [])):
                info_text += f"{lang_manager.get('storage_info')} {i+1}:\n"
                for key, value in storage.items():
                    translated_key = self._get_translated_key(key)
                    translated_value = self._translate_value(key, value)
                    info_text += f"  {translated_key}: {translated_value}\n"
            
            return info_text
        except Exception as e:
            return lang_manager.get("format_storage_error").format(error=str(e))
    
    def format_software_info_results(self, results):
        """格式化功能软件信息检测结果"""
        try:
            info_text = ""
            
            # 检测概览
            info_text += f"=== {lang_manager.get('software_detection_overview')} ===\n"
            detection_time_value = results.get('metadata', {}).get('检测时间', '未知')
            translated_detection_time_value = self._translate_value("检测时间", detection_time_value)
            info_text += f"{lang_manager.get('detection_time')}: {translated_detection_time_value}\n"
            info_text += "\n"
            
            # Python信息
            info_text += f"=== {lang_manager.get('python_info')} ===\n"
            for i, python in enumerate(results.get("python", [])):
                info_text += f"Python {i+1}:\n"
                for key, value in python.items():
                    translated_key = self._get_translated_key(key)
                    translated_value = self._translate_value(key, value)
                    info_text += f"  {translated_key}: {translated_value}\n"
            info_text += "\n"

            
            # Git信息
            info_text += f"=== {lang_manager.get('git_info')} ===\n"
            git_info = results.get("git", {})
            if git_info:
                for key, value in git_info.items():
                    translated_key = self._get_translated_key(key)
                    translated_value = self._translate_value(key, value)
                    info_text += f"{translated_key}: {translated_value}\n"
            else:
                info_text += f"{lang_manager.get('no_git_info')}\n"
            info_text += "\n"
            
            return info_text
        except Exception as e:
            return lang_manager.get("format_software_error").format(error=str(e))
    
    def refresh_ui(self):
        """刷新UI，根据当前语言设置更新界面文本"""
        # 刷新语言设置
        lang_manager.refresh_language()
        
        # 更新按钮文本
        self.system_detect_button.setText(lang_manager.get("system_detect"))
        self.hardware_info_button.setText(lang_manager.get("hardware_info"))
        self.storage_status_button.setText(lang_manager.get("storage_status"))
        self.software_button.setText(lang_manager.get("software_info"))
        
        # 重新加载缓存数据以更新显示文本
        self._load_cache_data()
    

