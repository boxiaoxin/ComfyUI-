#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理模块
用于管理应用程序的缓存数据，包括虚拟环境路径等
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from comfyui_manager.utils.logger import Logger


class CacheManager:
    """缓存管理类"""
    
    def __init__(self):
        """初始化"""
        self.logger = Logger()
        # 获取缓存目录
        self.cache_dir = self.get_cache_dir()
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        # 缓存文件路径
        self.cache_file = os.path.join(self.cache_dir, "app_cache.json")
        # 加载缓存
        self.cache = self.load_cache()
    
    def get_cache_dir(self) -> str:
        """获取缓存目录"""
        if os.name == "nt":  # Windows
            app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
            return os.path.join(app_data, "ComfyUI-Manager", "cache")
        else:  # Linux/macOS
            return os.path.join(os.path.expanduser("~"), ".comfyui-manager", "cache")
    
    def load_cache(self) -> Dict[str, Any]:
        """加载缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    # 确保 venv_paths 字段存在
                    if "venv_paths" not in cache:
                        cache["venv_paths"] = []
                    # 如果有 venv_path 但没有在 venv_paths 中，添加进去
                    if "venv_path" in cache and cache["venv_path"]:
                        if cache["venv_path"] not in cache["venv_paths"]:
                            cache["venv_paths"].append(cache["venv_path"])
                            # 保存更新后的缓存
                            with open(self.cache_file, 'w', encoding='utf-8') as f:
                                json.dump(cache, f, ensure_ascii=False, indent=2)
                    return cache
            except Exception as e:
                self.logger.error(f"加载缓存失败: {e}")
        return {"venv_paths": []}
    
    def save_cache(self) -> bool:
        """保存缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"保存缓存失败: {e}")
            return False
    
    def get_venv_path(self) -> Optional[str]:
        """获取保存的虚拟环境路径"""
        return self.cache.get("venv_path", None)
    
    def set_venv_path(self, venv_path: str) -> bool:
        """保存虚拟环境路径"""
        self.cache["venv_path"] = venv_path
        # 同时添加到虚拟环境列表
        self.add_venv_path(venv_path)
        self.cache["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.save_cache()
    
    def clear_venv_path(self) -> bool:
        """清除虚拟环境路径"""
        if "venv_path" in self.cache:
            del self.cache["venv_path"]
            return self.save_cache()
        return True
    
    def get_venv_paths(self) -> List[str]:
        """获取所有保存的虚拟环境路径"""
        return self.cache.get("venv_paths", [])
    
    def add_venv_path(self, venv_path: str) -> bool:
        """添加虚拟环境路径"""
        if "venv_paths" not in self.cache:
            self.cache["venv_paths"] = []
        # 避免重复添加
        if venv_path not in self.cache["venv_paths"]:
            self.cache["venv_paths"].append(venv_path)
            self.cache["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self.save_cache()
        return True
    
    def remove_venv_path(self, venv_path: str) -> bool:
        """移除虚拟环境路径"""
        if "venv_paths" in self.cache and venv_path in self.cache["venv_paths"]:
            self.cache["venv_paths"].remove(venv_path)
            self.cache["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self.save_cache()
        return True
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        info = {
            "cache_file": self.cache_file,
            "last_updated": self.cache.get("last_updated", "从未更新"),
            "venv_path": self.cache.get("venv_path", "未设置"),
            "venv_paths": self.cache.get("venv_paths", [])
        }
        return info


# 单例模式
cache_manager = CacheManager()

