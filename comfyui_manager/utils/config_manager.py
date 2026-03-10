#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import os
import json
from typing import Any, Dict, List, Optional, Union
from comfyui_manager.utils.logger import Logger


class ConfigManager:
    """配置管理类"""
    
    def __init__(self):
        """初始化"""
        self.logger = Logger()
        self.config_file = self._get_config_file_path()
        self.config = self._load_config()
    
    def _get_config_file_path(self) -> str:
        """获取配置文件路径"""
        # 配置文件路径：项目根目录下的config.json
        config_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(config_dir, "config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            self.logger.info(f"尝试加载配置文件: {self.config_file}")
            if os.path.exists(self.config_file):
                self.logger.info(f"配置文件存在: {self.config_file}")
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"成功加载配置文件: {self.config_file}")
                # 只记录配置的键，不记录值，避免敏感信息泄露
                self.logger.info(f"配置键: {list(config.keys())}")
                return config
            else:
                # 配置文件不存在，返回默认配置
                self.logger.info(f"配置文件不存在，使用默认配置: {self.config_file}")
                return self._get_default_config()
        except Exception as e:
            self.logger.error(f"加载配置失败: {str(e)}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "services_running": False,
            "last_tab": "system",
            "window_position": [100, 100],
            "window_size": [960, 640],
            "venv_path": None,
            "use_embedded_python": True,
            "use_embedded_git": True
        }
    
    def save_config(self) -> None:
        """保存配置"""
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"成功保存配置文件: {self.config_file}")
        except Exception as e:
            self.logger.error(f"保存配置失败: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.config[key] = value
        self.save_config()
    
    def get_services_running(self) -> bool:
        """获取服务运行状态"""
        return self.get("services_running", False)
    
    def set_services_running(self, running: bool) -> None:
        """设置服务运行状态"""
        self.set("services_running", running)
    
    def get_last_tab(self) -> str:
        """获取最后选中的标签页"""
        return self.get("last_tab", "system")
    
    def set_last_tab(self, tab: str) -> None:
        """设置最后选中的标签页"""
        self.set("last_tab", tab)
    
    def get_window_position(self) -> List[int]:
        """获取窗口位置"""
        return self.get("window_position", [100, 100])
    
    def set_window_position(self, position: List[int]) -> None:
        """设置窗口位置"""
        self.set("window_position", position)
    
    def get_window_size(self) -> List[int]:
        """获取窗口大小"""
        return self.get("window_size", [960, 640])
    
    def set_window_size(self, size: List[int]) -> None:
        """设置窗口大小"""
        self.set("window_size", size)
    
    def reload_config(self) -> None:
        """重新加载配置文件"""
        self.config = self._load_config()
    
    def get_venv_path(self) -> Optional[str]:
        """获取虚拟环境路径"""
        # 每次获取虚拟环境路径时都重新加载配置，确保获取最新的路径
        self.reload_config()
        return self.get("venv_path", None)
    
    def set_venv_path(self, venv_path: Optional[str]) -> None:
        """设置虚拟环境路径"""
        self.set("venv_path", venv_path)
    
    def get_use_embedded_python(self) -> bool:
        """获取是否使用嵌入的 Python"""
        return self.get("use_embedded_python", True)
    
    def set_use_embedded_python(self, use: bool) -> None:
        """设置是否使用嵌入的 Python"""
        self.set("use_embedded_python", use)
    
    def get_use_embedded_git(self) -> bool:
        """获取是否使用嵌入的 Git"""
        return self.get("use_embedded_git", True)
    
    def set_use_embedded_git(self, use: bool) -> None:
        """设置是否使用嵌入的 Git"""
        self.set("use_embedded_git", use)


# 创建全局配置管理器实例
config_manager = ConfigManager()
