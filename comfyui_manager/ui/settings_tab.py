#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置标签页
"""

import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QProgressBar,
    QLabel, QLineEdit, QFileDialog, QComboBox, QGroupBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt

from comfyui_manager.utils.logger import Logger
from comfyui_manager.utils.language_manager import lang_manager


class SettingsTab(QWidget):
    """设置标签页"""
    
    def __init__(self, parent=None):
        """初始化"""
        super().__init__(parent)
        self.logger = Logger()
        self.current_theme = 1  # 默认深色主题
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 读取当前主题设置
        import json
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        config = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        self.current_theme = config.get("theme", 1)  # 默认深色主题
        
        # 初始化样式
        self._init_styles()
        
        # 设置样式
        self.setStyleSheet(self.widget_style)
        
        # 二级菜单按钮容器
        menu_container = QWidget()
        menu_layout = QHBoxLayout(menu_container)
        
        # 刷新语言设置
        lang_manager.refresh_language()
        
        # 存储当前高亮的按钮
        self.current_highlighted_button = None
        
        # 主题设置按钮
        self.theme_button = QPushButton(lang_manager.get("theme"))
        self.theme_button.clicked.connect(lambda: self._handle_button_click(self.theme_button, self.show_theme_settings))
        menu_layout.addWidget(self.theme_button)
        
        # 语言设置按钮
        self.language_button = QPushButton(lang_manager.get("language"))
        self.language_button.clicked.connect(lambda: self._handle_button_click(self.language_button, self.show_language_settings))
        menu_layout.addWidget(self.language_button)
        
        # 日志设置按钮
        self.log_button = QPushButton(lang_manager.get("logs"))
        self.log_button.clicked.connect(lambda: self._handle_button_click(self.log_button, self.show_log_settings))
        menu_layout.addWidget(self.log_button)
        
        # 版本信息按钮
        self.version_button = QPushButton(lang_manager.get("version"))
        self.version_button.clicked.connect(lambda: self._handle_button_click(self.version_button, self.show_version_settings))
        menu_layout.addWidget(self.version_button)
        
        layout.addWidget(menu_container)
        
        # 添加占位符，使信息窗口向下移动，与一级菜单的下边框水平
        layout.addStretch()
        
        # 设置信息容器
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(12, 12, 12, 12)
        
        # 设置信息
        self.settings_info = QTextEdit()
        self.settings_info.setReadOnly(True)
        self.settings_info.setMinimumHeight(400)
        self.settings_info.setStyleSheet(self.text_edit_style)
        info_layout.addWidget(self.settings_info, 1)
        

        
        # 设置容器样式
        info_container.setStyleSheet(self.container_style)
        
        # 将容器添加到主布局
        layout.addWidget(info_container, 1)
        
        # 显示默认设置
        self.show_theme_settings()
    
    def refresh_ui(self):
        """刷新UI，根据当前语言设置和主题更新界面"""
        # 刷新语言设置
        lang_manager.refresh_language()
        
        # 重新读取当前主题设置
        import json
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        config = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        self.current_theme = config.get("theme", 1)  # 默认深色主题
        
        # 重新初始化样式
        self._init_styles()
        
        # 更新样式
        self.setStyleSheet(self.widget_style)
        
        # 更新二级菜单按钮文本
        self.theme_button.setText(lang_manager.get("theme"))
        self.language_button.setText(lang_manager.get("language"))
        self.log_button.setText(lang_manager.get("logs"))
        self.version_button.setText(lang_manager.get("version"))
        
        # 重新显示当前设置
        if hasattr(self, 'current_settings') and self.current_settings == 'theme':
            self.show_theme_settings()
        elif hasattr(self, 'current_settings') and self.current_settings == 'language':
            self.show_language_settings()
        elif hasattr(self, 'current_settings') and self.current_settings == 'logs':
            self.show_log_settings()
        elif hasattr(self, 'current_settings') and self.current_settings == 'version':
            self.show_version_settings()
        else:
            self.show_theme_settings()
    
    def _init_styles(self):
        """初始化样式"""
        # 根据主题生成样式
        if self.current_theme == 0:  # 浅色主题
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
        else:  # 深色主题
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
        
        # 容器样式
        self.container_style = """
            QWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(25, 118, 210, 0.4);
                border-radius: 8px;
            }
        """
    
    def show_theme_settings(self):
        """显示主题设置"""
        try:
            self.current_settings = 'theme'
            self.logger.info("显示主题设置")
            
            # 读取当前设置
            import json
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            
            # 获取当前主题设置
            current_theme = config.get("theme", 1)  # 默认深色主题
            
            # 生成主题设置文本
            settings_text = f"=== {lang_manager.get('theme_settings')} ===\n"
            settings_text += f"{lang_manager.get('current_theme')}: "
            if current_theme == 0:
                settings_text += f"{lang_manager.get('light_theme')}\n"
            else:
                settings_text += f"{lang_manager.get('dark_theme')}\n"
            settings_text += "\n"
            settings_text += f"{lang_manager.get('theme_options')}:\n"
            settings_text += f"0. {lang_manager.get('light_theme')}\n"
            settings_text += f"1. {lang_manager.get('dark_theme')}\n"
            settings_text += "\n"
            settings_text += lang_manager.get('theme_note')
            
            # 打印生成的文本
            print(f"生成的主题设置文本: {settings_text}")
            
            # 更新设置信息
            self.settings_info.setPlainText(settings_text)
            
            # 移除之前可能存在的所有按钮
            from PyQt5.QtWidgets import QPushButton
            for widget in self.settings_info.parentWidget().children():
                if isinstance(widget, QPushButton):
                    widget.deleteLater()
            
            # 确保主题值只在0和1之间
            if current_theme not in [0, 1]:
                current_theme = 1  # 默认为深色主题
            
            # 创建主题切换按钮
            if current_theme == 0:
                button_text = "切换到深色主题"
            else:
                button_text = "切换到浅色主题"
            theme_button = QPushButton(button_text)
            theme_button.clicked.connect(self.switch_theme)
            theme_button.setStyleSheet("""
                QPushButton {
                    background: rgba(25, 118, 210, 0.8);
                    color: #ffffff;
                    border: 1px solid rgba(25, 118, 210, 1);
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(25, 118, 210, 1);
                }
            """)
            
            # 将按钮添加到信息容器
            info_container = self.settings_info.parentWidget()
            info_layout = info_container.layout()
            info_layout.addWidget(theme_button)
        except Exception as e:
            self.logger.error(f"显示主题设置失败: {e}")
            self.settings_info.setPlainText(f"{lang_manager.get('theme_settings')} failed: {str(e)}")
    
    def show_language_settings(self):
        """显示语言设置"""
        try:
            self.current_settings = 'language'
            self.logger.info("显示语言设置")
            
            # 读取当前设置
            import json
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            
            # 获取当前语言设置
            current_language = config.get("language", "简体中文")
            
            # 生成语言设置文本
            settings_text = f"=== {lang_manager.get('language_settings')} ===\n"
            settings_text += f"{lang_manager.get('current_language')}: {current_language}\n"
            settings_text += "\n"
            settings_text += f"{lang_manager.get('language_options')}:\n"
            settings_text += f"1. {lang_manager.get('chinese')}\n"
            settings_text += f"2. {lang_manager.get('english')}\n"
            settings_text += "\n"
            settings_text += lang_manager.get('language_note')
            
            # 更新设置信息
            self.settings_info.setPlainText(settings_text)
            
            # 移除之前可能存在的所有按钮
            from PyQt5.QtWidgets import QPushButton
            for widget in self.settings_info.parentWidget().children():
                if isinstance(widget, QPushButton):
                    widget.deleteLater()
            
            # 创建语言选择按钮
            if current_language == "简体中文":
                lang_button = QPushButton(lang_manager.get('switch_to_english'))
                lang_button.clicked.connect(lambda: self.change_language("English"))
            else:
                lang_button = QPushButton(lang_manager.get('switch_to_chinese'))
                lang_button.clicked.connect(lambda: self.change_language("简体中文"))
            
            lang_button.setStyleSheet("""
                QPushButton {
                    background: rgba(25, 118, 210, 0.8);
                    color: #ffffff;
                    border: 1px solid rgba(25, 118, 210, 1);
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(25, 118, 210, 1);
                }
            """)
            
            # 将按钮添加到信息容器
            info_container = self.settings_info.parentWidget()
            info_layout = info_container.layout()
            info_layout.addWidget(lang_button)
        except Exception as e:
            self.logger.error(f"显示语言设置失败: {e}")
            self.settings_info.setPlainText(f"{lang_manager.get('language_settings')} failed: {str(e)}")
    
    def change_language(self, language):
        """更改语言设置"""
        try:
            import json
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
            
            # 读取现有配置
            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            
            # 更新语言设置
            config["language"] = language
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 刷新语言管理器
            lang_manager.refresh_language()
            
            # 通知主窗口更新所有标签页的UI
            from PyQt5.QtWidgets import QApplication
            main_window = QApplication.instance().activeWindow()
            if main_window and hasattr(main_window, 'tab_config'):
                # 更新所有标签页的UI
                for tab_name, tab in main_window.tab_config.items():
                    if hasattr(tab, 'refresh_ui'):
                        tab.refresh_ui()
                # 更新主窗口的侧边栏菜单项文本
                if hasattr(main_window, 'menu_buttons') and hasattr(main_window, 'menu_config'):
                    for key, button in main_window.menu_buttons.items():
                        if key in main_window.menu_config:
                            button.setText(lang_manager.get(main_window.menu_config[key].get("name_key", key)))
                # 更新主窗口的状态栏消息
                if hasattr(main_window, 'current_tab'):
                    if main_window.current_tab == "system":
                        main_window.status_bar.showMessage(lang_manager.get("status_tab_system"))
                    elif main_window.current_tab == "one_click_install":
                        main_window.status_bar.showMessage(lang_manager.get("status_tab_install"))
                    elif main_window.current_tab == "smart_fix":
                        main_window.status_bar.showMessage(lang_manager.get("status_tab_fix"))
                    elif main_window.current_tab == "file_management":
                        main_window.status_bar.showMessage(lang_manager.get("status_tab_file"))
                    elif main_window.current_tab == "one_click_start":
                        main_window.status_bar.showMessage(lang_manager.get("status_tab_start"))
                    elif main_window.current_tab == "settings":
                        main_window.status_bar.showMessage(lang_manager.get("status_tab_settings"))
            
            # 显示成功消息
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, lang_manager.get('language_changed'), lang_manager.get('language_changed_message'))
        except Exception as e:
            self.logger.error(f"更改语言设置失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Failed to change language: {str(e)}")
    
    def show_log_settings(self):
        """显示日志设置"""
        try:
            self.current_settings = 'logs'
            self.logger.info("显示日志设置")
            
            # 读取当前设置
            import json
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            
            # 获取当前日志级别设置
            current_log_level = config.get("log_level", "INFO")
            
            # 生成日志设置文本
            settings_text = f"=== {lang_manager.get('log_settings')} ===\n"
            settings_text += f"{lang_manager.get('current_log_level')}: {current_log_level}\n"
            settings_text += "\n"
            settings_text += f"{lang_manager.get('log_level_options')}:\n"
            settings_text += f"1. DEBUG - {lang_manager.get('debug_info')}\n"
            settings_text += f"2. INFO - {lang_manager.get('info_info')}\n"
            settings_text += f"3. WARNING - {lang_manager.get('warning_info')}\n"
            settings_text += f"4. ERROR - {lang_manager.get('error_info')}\n"
            settings_text += "\n"
            settings_text += f"{lang_manager.get('log_note')}\n"
            settings_text += "\n"
            settings_text += f"{lang_manager.get('log_operation')}\n"
            settings_text += f"{lang_manager.get('view_log')} →\n"
            
            # 更新设置信息
            self.settings_info.setPlainText(settings_text)
            
            # 添加查看日志按钮
            from PyQt5.QtWidgets import QPushButton
            
            # 移除之前可能存在的所有按钮
            from PyQt5.QtWidgets import QPushButton
            for widget in self.settings_info.parentWidget().children():
                if isinstance(widget, QPushButton):
                    widget.deleteLater()
            
            # 创建新的查看日志按钮
            view_log_button = QPushButton(lang_manager.get('view_log'))
            view_log_button.clicked.connect(self.view_log)
            view_log_button.setStyleSheet("""
                QPushButton {
                    background: rgba(25, 118, 210, 0.8);
                    color: #ffffff;
                    border: 1px solid rgba(25, 118, 210, 1);
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(25, 118, 210, 1);
                }
            """)
            
            # 将按钮添加到信息容器
            info_container = self.settings_info.parentWidget()
            info_layout = info_container.layout()
            info_layout.addWidget(view_log_button)
        except Exception as e:
            self.logger.error(f"显示日志设置失败: {e}")
            self.settings_info.setPlainText(f"{lang_manager.get('log_settings')} failed: {str(e)}")
    
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
    
    def show_version_settings(self):
        """显示版本设置"""
        try:
            self.current_settings = 'version'
            self.logger.info("显示版本设置")
            
            # 生成版本信息文本
            settings_text = f"=== {lang_manager.get('version_settings')} ===\n"
            settings_text += f"{lang_manager.get('current_version')}: 1.0.0\n"
            settings_text += "\n"
            settings_text += f"{lang_manager.get('check_update_note')}\n"
            settings_text += "\n"
            settings_text += f"{lang_manager.get('about')}: {lang_manager.get('about_text')}"
            
            # 更新设置信息
            self.settings_info.setPlainText(settings_text)
            
            # 移除之前可能存在的所有按钮
            from PyQt5.QtWidgets import QPushButton
            for widget in self.settings_info.parentWidget().children():
                if isinstance(widget, QPushButton):
                    widget.deleteLater()
            
            # 创建检查更新按钮
            check_update_button = QPushButton(lang_manager.get('check_update'))
            check_update_button.clicked.connect(self.check_update)
            check_update_button.setStyleSheet("""
                QPushButton {
                    background: rgba(25, 118, 210, 0.8);
                    color: #ffffff;
                    border: 1px solid rgba(25, 118, 210, 1);
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(25, 118, 210, 1);
                }
            """)
            
            # 将按钮添加到信息容器
            info_container = self.settings_info.parentWidget()
            info_layout = info_container.layout()
            info_layout.addWidget(check_update_button)
        except Exception as e:
            self.logger.error(f"显示版本设置失败: {e}")
            self.settings_info.setPlainText(f"{lang_manager.get('version_settings')} failed: {str(e)}")
    
    def view_log(self):
        """查看日志"""
        try:
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
            if os.path.exists(log_path):
                # 查找最新的日志文件
                log_files = [f for f in os.listdir(log_path) if f.endswith('.log')]
                if log_files:
                    # 按修改时间排序，获取最新的日志文件
                    log_files.sort(key=lambda x: os.path.getmtime(os.path.join(log_path, x)), reverse=True)
                    latest_log = os.path.join(log_path, log_files[0])
                    
                    # 创建日志查看器窗口
                    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
                    from PyQt5.QtCore import Qt
                    
                    log_window = QDialog(self)
                    log_window.setWindowTitle(f"{lang_manager.get('log_viewer')} - {log_files[0]}")
                    log_window.setMinimumSize(800, 600)
                    
                    layout = QVBoxLayout(log_window)
                    
                    # 日志内容显示
                    log_text = QTextEdit()
                    log_text.setReadOnly(True)
                    log_text.setStyleSheet("""
                        QTextEdit {
                            background: #041a47;
                            color: #ffffff;
                            font-family: 'Consolas', 'Monaco', monospace;
                            font-size: 12px;
                        }
                    """)
                    
                    # 读取日志文件内容（只读取最后1000行，提高速度）
                    def tail(filepath, lines=1000):
                        """读取文件的最后N行"""
                        import os
                        with open(filepath, 'rb') as f:
                            f.seek(0, os.SEEK_END)
                            size = f.tell()
                            block = 1024
                            data = b''
                            lines_found = 0
                            
                            while size > 0 and lines_found < lines:
                                # 每次读取一个块
                                step = min(block, size)
                                size -= step
                                f.seek(size)
                                data = f.read(step) + data
                                lines_found = data.count(b'\n')
                            
                            # 解码并返回最后N行
                            try:
                                content = data.decode('utf-8', errors='ignore')
                                lines_list = content.split('\n')
                                return '\n'.join(lines_list[-lines:])
                            except:
                                return ''
                    
                    log_content = tail(latest_log, 1000)
                    log_text.setPlainText(log_content)
                    
                    # 自动滚动到末尾
                    log_text.moveCursor(log_text.textCursor().End)
                    
                    # 按钮布局
                    button_layout = QHBoxLayout()
                    button_layout.addStretch()
                    
                    # 关闭按钮
                    close_button = QPushButton(lang_manager.get('close'))
                    close_button.clicked.connect(log_window.close)
                    close_button.setStyleSheet("""
                        QPushButton {
                            background: rgba(25, 118, 210, 0.8);
                            color: #ffffff;
                            border: 1px solid rgba(25, 118, 210, 1);
                            padding: 8px 16px;
                            border-radius: 4px;
                            font-size: 14px;
                            font-weight: 500;
                        }
                        QPushButton:hover {
                            background: rgba(25, 118, 210, 1);
                        }
                    """)
                    button_layout.addWidget(close_button)
                    
                    layout.addWidget(log_text)
                    layout.addLayout(button_layout)
                    
                    # 显示窗口
                    log_window.exec_()
                else:
                    # 没有日志文件，打开日志目录
                    import subprocess
                    subprocess.run(["explorer", log_path], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            else:
                self.logger.error(lang_manager.get('log_dir_not_exists'))
        except Exception as e:
            self.logger.error(f"查看日志失败: {e}")
    
    def check_update(self):
        """检查更新"""
        try:
            self.logger.info("检查更新")
            
            # 模拟检查更新的过程
            import time
            from PyQt5.QtWidgets import QMessageBox, QProgressDialog
            
            # 显示进度对话框
            progress = QProgressDialog(lang_manager.get('checking_update'), lang_manager.get('cancel'), 0, 100, self)
            progress.setWindowTitle(lang_manager.get('check_update'))
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            
            # 模拟检查过程
            for i in range(101):
                time.sleep(0.01)  # 模拟网络请求延迟
                progress.setValue(i)
                if progress.wasCanceled():
                    break
            
            # 模拟检查结果
            # 这里可以替换为实际的版本检查逻辑，例如从服务器获取最新版本
            try:
                # 模拟网络请求失败的情况（20%概率）
                import random
                if random.random() < 0.2:
                    raise Exception("网络连接失败，无法检查更新")
                
                current_version = "1.0.0"
                # 模拟有新版本或无新版本的情况（50%概率）
                if random.random() < 0.5:
                    latest_version = "1.1.0"  # 模拟有新版本
                else:
                    latest_version = "1.0.0"  # 模拟无新版本
                
                if latest_version > current_version:
                    # 有更新
                    reply = QMessageBox.question(
                        self, 
                        lang_manager.get('update_available'), 
                        lang_manager.get('update_message').format(current=current_version, latest=latest_version),
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.Yes:
                        # 这里可以添加更新逻辑
                        QMessageBox.information(self, lang_manager.get('updating'), lang_manager.get('updating_message'))
                        # 模拟更新过程
                        progress = QProgressDialog(lang_manager.get('updating_progress'), lang_manager.get('cancel'), 0, 100, self)
                        progress.setWindowTitle(lang_manager.get('updating'))
                        progress.setMinimumDuration(0)
                        progress.setValue(0)
                        progress.show()
                        
                        for i in range(101):
                            time.sleep(0.02)  # 模拟下载和安装过程
                            progress.setValue(i)
                            if progress.wasCanceled():
                                break
                        
                        QMessageBox.information(self, lang_manager.get('update_complete'), lang_manager.get('update_complete_message'))
                else:
                    # 无更新
                    QMessageBox.information(self, lang_manager.get('check_update'), lang_manager.get('no_update_message'))
            except Exception as e:
                # 检测失败
                self.logger.error(f"检查更新失败: {e}")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, lang_manager.get('update_failed'), lang_manager.get('update_failed_message').format(error=str(e)))
        except Exception as e:
            self.logger.error(f"检查更新失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, lang_manager.get('update_failed'), lang_manager.get('update_failed_message').format(error=str(e)))
    
    def switch_theme(self):
        """切换主题"""
        try:
            import json
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
            
            # 读取现有配置
            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            
            # 切换主题
            current_theme = config.get("theme", 1)
            new_theme = (current_theme + 1) % 2  # 0: 浅色, 1: 深色
            config["theme"] = new_theme
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 显示成功消息
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "主题已更改", "主题已更改，请重启应用程序以应用更改。")
            
            # 重新显示主题设置
            self.show_theme_settings()
        except Exception as e:
            self.logger.error(f"切换主题失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", f"切换主题失败: {str(e)}")
    
    def save_settings(self):
        """保存设置"""
        try:
            self.logger.info("保存设置")
            
            # 保存设置到配置文件
            import json
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
            
            # 读取现有配置
            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.logger.info("设置保存成功")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, lang_manager.get('save_success'), lang_manager.get('save_success_message'))
        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, lang_manager.get('save_failed'), lang_manager.get('save_failed_message').format(error=str(e)))
