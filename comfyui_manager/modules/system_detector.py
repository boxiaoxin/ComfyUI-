#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统信息检测模块
支持：Windows, Linux, macOS
重点解决：Intel Arc显卡识别、显存准确检测
"""

import os
import sys
import platform
import subprocess
import psutil
import cpuinfo
import socket
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

# 将项目根目录添加到Python模块搜索路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from comfyui_manager.utils.embedded_tools import embedded_tools


class SystemDetector:
    """系统检测类"""
    
    def __init__(self):
        """初始化"""
        self.system = platform.system()
        self.is_admin = False  # 初始化为False，稍后在方法中更新
        self.detection_time = datetime.now()
        
        # 检测结果存储
        self.results: Dict[str, Any] = {
            "metadata": {
                "检测时间": self.detection_time.strftime("%Y-%m-%d %H:%M:%S"),
                "操作系统": self.get_os_name(),
                "Python版本": platform.python_version(),
                "检测工具版本": "1.0",
                "管理员权限": self.is_admin
            },
            "system": {},
            "cpu": {},
            "gpu": [],
            "memory": {},
            "storage": [],
            "network": [],
            "python": [],
            "git": {},
            "errors": []
        }
    
    def get_os_name(self) -> str:
        """获取操作系统名称"""
        return platform.system()
    
    def log_error(self, module: str, error: str, severity: str = "warning") -> None:
        """记录错误信息"""
        error_entry = {
            "模块": module,
            "错误": error,
            "时间": datetime.now().strftime("%H:%M:%S"),
            "严重程度": severity
        }
        self.results["errors"].append(error_entry)
    
    def detect_system_info(self) -> None:
        """检测系统信息"""
        try:
            info: Dict[str, Any] = {}
            
            # 基本系统信息
            info["系统类型"] = self.get_os_name()
            info["系统版本"] = platform.version()
            info["系统架构"] = platform.architecture()[0]
            info["主机名"] = socket.gethostname()
            info["Python版本"] = platform.python_version()
            
            # Windows特定信息
            if self.system == "Windows":
                try:
                    import pythoncom
                    import wmi
                    
                    # 初始化COM
                    pythoncom.CoInitialize()
                    
                    w = wmi.WMI()
                    for os_info in w.Win32_OperatingSystem():
                        info["Windows版本"] = os_info.Caption
                        info["系统架构"] = os_info.OSArchitecture
                        break
                    
                    # 释放COM
                    pythoncom.CoUninitialize()
                except Exception as e:
                    self.log_error("Windows版本检测", str(e))
            
            self.results["system"] = info
        except Exception as e:
            self.log_error("系统信息检测", str(e))
            self.results["system"] = {"错误": str(e)}
    
    def detect_cpu_info(self) -> None:
        """检测CPU信息"""
        try:
            info: Dict[str, Any] = {}
            
            # 获取CPU信息
            cpu_info = cpuinfo.get_cpu_info()
            info["品牌型号"] = cpu_info.get("brand_raw", "未知")
            info["架构"] = platform.architecture()[0]
            info["逻辑核心数"] = os.cpu_count()
            
            # 获取物理核心数
            info["物理核心数"] = self.get_physical_cores()
            
            # 计算CPU使用率
            info["CPU使用率(%)"] = f"{psutil.cpu_percent(interval=1):.1f}"
            
            self.results["cpu"] = info
        except Exception as e:
            self.log_error("CPU信息检测", str(e))
            self.results["cpu"] = {"错误": str(e)}
    
    def get_physical_cores(self) -> int:
        """获取物理核心数"""
        try:
            if self.system == "Windows":
                import wmi
                w = wmi.WMI()
                for cpu in w.Win32_Processor():
                    return cpu.NumberOfCores
            elif self.system == "Linux":
                with open("/proc/cpuinfo", "r") as f:
                    cores = 0
                    for line in f:
                        if line.strip().startswith("cpu cores"):
                            cores = int(line.split(":")[1].strip())
                            break
                    return cores
            elif self.system == "Darwin":
                result = subprocess.run(["sysctl", "-n", "hw.physicalcpu"], 
                                      capture_output=True, text=True)
                return int(result.stdout.strip())
        except Exception as e:
            self.log_error("物理核心数检测", str(e))
        
        # 如果无法获取物理核心数，返回逻辑核心数的一半作为估算
        return max(1, os.cpu_count() // 2)
    
    def detect_gpu_info(self) -> None:
        """检测GPU信息"""
        try:
            gpus: List[Dict[str, Any]] = []
            
            if self.system == "Windows":
                # Windows GPU检测
                try:
                    import pythoncom
                    import wmi
                    
                    # 初始化COM
                    pythoncom.CoInitialize()
                    
                    w = wmi.WMI()
                    for gpu in w.Win32_VideoController():
                        try:
                            gpu_info = {
                                "型号": getattr(gpu, "Name", "未知"),
                                "厂商": self.infer_gpu_vendor(getattr(gpu, "Name", "")),
                                "类型": self.determine_gpu_type(getattr(gpu, "Name", "")),
                                "检测方法": "Windows WMI"
                            }
                            if hasattr(gpu, "AdapterRAM") and gpu.AdapterRAM:
                                gpu_info["专用显存(GB)"] = f"{(gpu.AdapterRAM / (1024**3)):.2f}"
                            if hasattr(gpu, "DriverVersion") and gpu.DriverVersion:
                                gpu_info["驱动版本"] = gpu.DriverVersion
                            
                            # 特别处理Intel Arc显卡
                            gpu_name = getattr(gpu, "Name", "").lower()
                            if gpu_info["厂商"] == "Intel" and "arc" in gpu_name:
                                gpu_info["类型"] = "独立显卡"
                                gpu_info["Intel Arc系列"] = True
                                
                                # Arc A770显存修正
                                if "a770" in gpu_name:
                                    gpu_info["官方显存规格"] = "16 GB"
                                    gpu_info["显存类型"] = "GDDR6"
                                    gpu_info["显存说明"] = "Intel Arc A770 16GB专用显存"
                            
                            gpus.append(gpu_info)
                        except Exception as e:
                            self.log_error("Windows GPU检测 - 单个GPU", str(e))
                    
                    # 释放COM
                    pythoncom.CoUninitialize()
                except Exception as e:
                    self.log_error("Windows GPU检测", str(e))
            
            elif self.system == "Linux":
                # Linux GPU检测
                try:
                    result = subprocess.run(["lspci", "-nn"], 
                                          capture_output=True, text=True)
                    for line in result.stdout.split("\n"):
                        if "VGA" in line or "3D" in line or "Display" in line:
                            gpu_info = {
                                "型号": line.split(":")[2].strip() if len(line.split(":")) > 2 else "未知",
                                "厂商": self.infer_gpu_vendor(line),
                                "类型": self.determine_gpu_type(line),
                                "检测方法": "Linux lspci",
                                "PCI信息": line.strip()
                            }
                            gpus.append(gpu_info)
                except Exception as e:
                    self.log_error("Linux GPU检测", str(e))
            
            elif self.system == "Darwin":
                # macOS GPU检测
                try:
                    result = subprocess.run(["system_profiler", "SPDisplaysDataType"], 
                                          capture_output=True, text=True)
                    current_gpu: Dict[str, Any] = {}
                    for line in result.stdout.split("\n"):
                        if line.strip().startswith("Chipset Model:"):
                            current_gpu["型号"] = line.split(":")[1].strip()
                        elif line.strip().startswith("Vendor:"):
                            current_gpu["厂商"] = line.split(":")[1].strip()
                        elif line.strip().startswith("VRAM (Total):"):
                            current_gpu["专用显存"] = line.split(":")[1].strip()
                        elif line.strip() == "" and current_gpu:
                            current_gpu["类型"] = "独立显卡"
                            current_gpu["检测方法"] = "macOS system_profiler"
                            gpus.append(current_gpu)
                            current_gpu = {}
                except Exception as e:
                    self.log_error("macOS GPU检测", str(e))
            
            # 如果没有检测到GPU，添加默认信息
            if not gpus:
                gpus.append({"状态": "未检测到显卡", "建议": "请检查驱动和权限"})
            
            self.results["gpu"] = gpus
        except Exception as e:
            self.log_error("GPU信息检测", str(e))
            self.results["gpu"] = [{"错误": str(e)}]
    
    def infer_gpu_vendor(self, name: str) -> str:
        """推断GPU厂商"""
        name_lower = str(name).lower()
        
        if any(keyword in name_lower for keyword in ["nvidia", "geforce", "quadro"]):
            return "NVIDIA"
        elif any(keyword in name_lower for keyword in ["amd", "radeon", "rx"]):
            return "AMD"
        elif any(keyword in name_lower for keyword in ["intel", "arc"]):
            return "Intel"
        elif "apple" in name_lower:
            return "Apple"
        return "未知"
    
    def determine_gpu_type(self, name: str) -> str:
        """判断GPU类型"""
        name_lower = str(name).lower()
        
        # Intel Arc明确为独立显卡
        if "arc" in name_lower:
            return "独立显卡"
        
        # 集成显卡关键字
        integrated_keywords = [
            "intel", "hd graphics", "uhd graphics", "iris xe", 
            "xe graphics", "radeon graphics", "vega graphics"
        ]
        
        if any(keyword in name_lower for keyword in integrated_keywords) and "arc" not in name_lower:
            return "集成显卡"
        
        # 默认独立显卡
        return "独立显卡"
    
    def detect_memory_info(self) -> None:
        """检测内存信息"""
        try:
            info: Dict[str, Any] = {}
            
            # 物理内存
            total_mem = psutil.virtual_memory().total
            available_mem = psutil.virtual_memory().available
            used_mem = total_mem - available_mem
            
            info["总物理内存(GB)"] = f"{(total_mem / (1024**3)):.2f}"
            info["可用物理内存(GB)"] = f"{(available_mem / (1024**3)):.2f}"
            info["已用物理内存(GB)"] = f"{(used_mem / (1024**3)):.2f}"
            info["物理内存使用率(%)"] = f"{psutil.virtual_memory().percent:.1f}"
            
            # Windows内存模块信息
            if self.system == "Windows":
                try:
                    import pythoncom
                    import wmi
                    
                    # 初始化COM
                    pythoncom.CoInitialize()
                    
                    w = wmi.WMI()
                    modules: List[Dict[str, Any]] = []
                    for memory in w.Win32_PhysicalMemory():
                        module_info = {
                            "容量(GB)": f"{(int(memory.Capacity) / (1024**3)):.1f}",
                            "速度(MHz)": memory.Speed,
                            "制造商": memory.Manufacturer,
                            "型号": memory.PartNumber
                        }
                        modules.append(module_info)
                    if modules:
                        info["内存模块"] = modules
                    
                    # 释放COM
                    pythoncom.CoUninitialize()
                except Exception as e:
                    self.log_error("内存模块检测", str(e))
            
            self.results["memory"] = info
        except Exception as e:
            self.log_error("内存信息检测", str(e))
            self.results["memory"] = {"错误": str(e)}
    
    def detect_storage_info(self) -> None:
        """检测存储信息"""
        try:
            disks: List[Dict[str, Any]] = []
            
            # 使用psutil检测磁盘信息
            for partition in psutil.disk_partitions():
                if partition.fstype:
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_info = {
                            "设备": partition.device,
                            "挂载点": partition.mountpoint,
                            "文件系统": partition.fstype,
                            "总容量(GB)": f"{(usage.total / (1024**3)):.2f}",
                            "可用容量(GB)": f"{(usage.free / (1024**3)):.2f}",
                            "已用容量(GB)": f"{(usage.used / (1024**3)):.2f}",
                            "使用率(%)": f"{usage.percent:.1f}"
                        }
                        disks.append(disk_info)
                    except Exception as e:
                        self.log_error(f"存储检测 - {partition.device}", str(e))
            
            # 如果没有检测到存储设备，添加默认信息
            if not disks:
                disks.append({"状态": "未检测到存储设备", "建议": "请检查权限"})
            
            self.results["storage"] = disks
        except Exception as e:
            self.log_error("存储信息检测", str(e))
            self.results["storage"] = [{"错误": str(e)}]
    
    def detect_network_info(self) -> None:
        """检测网络信息"""
        try:
            interfaces: List[Dict[str, Any]] = []
            
            # 主机信息
            interfaces.append({
                "类型": "主机信息",
                "主机名": socket.gethostname(),
                "IPv4地址": self.get_ipv4_address(),
                "检测时间": datetime.now().strftime("%H:%M:%S")
            })
            
            # 详细网络接口信息
            for interface, addrs in psutil.net_if_addrs().items():
                iface_info: Dict[str, Any] = {
                    "类型": "网络接口",
                    "接口名": interface,
                    "状态": "未知"
                }
                
                # 地址信息
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        iface_info["IPv4地址"] = addr.address
                        iface_info["子网掩码"] = addr.netmask
                    elif addr.family == socket.AF_INET6:
                        if "IPv6地址" not in iface_info:
                            iface_info["IPv6地址"] = []
                        iface_info["IPv6地址"].append(addr.address)
                
                # 排除回环接口
                if interface not in ["lo", "Loopback Pseudo-Interface 1"]:
                    interfaces.append(iface_info)
            
            self.results["network"] = interfaces
        except Exception as e:
            self.log_error("网络信息检测", str(e))
            self.results["network"] = [{"错误": str(e)}]
    
    def get_ipv4_address(self) -> str:
        """获取IPv4地址"""
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                if interface not in ["lo", "Loopback Pseudo-Interface 1"]:
                    for addr in addrs:
                        if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                            return addr.address
            return "127.0.0.1"
        except Exception:
            return "127.0.0.1"
    
    def detect_python_info(self) -> None:
        """检测Python信息"""
        try:
            python_versions: List[Dict[str, Any]] = []
            
            # 当前Python版本
            current_python = {
                "命令": "python",
                "版本": platform.python_version(),
                "路径": sys.executable,
                "Pip可用": self.check_pip_available(),
                "检测方法": "当前Python"
            }
            python_versions.append(current_python)
            
            # 尝试检测其他Python版本
            if self.system == "Windows":
                python_commands = ["python3", "python3.9", "python3.10", "python3.11", "python3.12"]
            else:
                python_commands = ["python3", "python3.9", "python3.10", "python3.11", "python3.12"]
            
            for cmd in python_commands:
                try:
                    result = subprocess.run([cmd, "--version"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        version_match = result.stdout.strip().split()[1]
                        
                        # 尝试获取Python路径
                        if self.system == "Windows":
                            path_result = subprocess.run(["where", cmd], 
                                                        capture_output=True, text=True, timeout=5)
                        else:
                            path_result = subprocess.run(["which", cmd], 
                                                        capture_output=True, text=True, timeout=5)
                        python_path = path_result.stdout.strip() if path_result.returncode == 0 else "未知"
                        
                        # 检查pip是否可用
                        pip_available = False
                        try:
                            subprocess.run([cmd, "-m", "pip", "--version"], 
                                         capture_output=True, text=True, timeout=5)
                            pip_available = True
                        except Exception:
                            pip_available = False
                        
                        python_versions.append({
                            "命令": cmd,
                            "版本": version_match,
                            "路径": python_path,
                            "Pip可用": pip_available,
                            "检测方法": f"{self.system}命令"
                        })
                except Exception:
                    pass
            
            # 如果没有检测到Python，添加默认信息
            if not python_versions:
                python_versions.append({"状态": "未检测到Python", "建议": "请安装Python 3.9或更高版本"})
            
            self.results["python"] = python_versions
        except Exception as e:
            self.log_error("Python信息检测", str(e))
            self.results["python"] = [{"错误": str(e)}]
    
    def detect_git_info(self) -> None:
        """检测Git信息"""
        try:
            git_info: Dict[str, Any] = {}
            
            # 使用embedded_tools获取Git路径
            git_path = embedded_tools.get_git_path()
            
            if git_path:
                # 尝试运行git --version
                try:
                    result = subprocess.run([git_path, "--version"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        # 提取版本信息
                        version_line = result.stdout.strip()
                        if version_line.startswith("git version"):
                            version = version_line.split()[2]
                            git_info["版本"] = version
                            git_info["状态"] = "已安装"
                            git_info["路径"] = git_path
                            # 检查是否为内嵌Git
                            if embedded_tools.is_git_embedded():
                                git_info["类型"] = "内嵌Git"
                            else:
                                git_info["类型"] = "系统Git"
                except Exception as e:
                    self.log_error("Git检测 - 运行git", str(e))
                    git_info["状态"] = "未安装"
                    git_info["建议"] = "请检查Git安装"
            else:
                git_info["状态"] = "未安装"
                git_info["建议"] = "请安装Git"
                self.log_error("Git检测", "未找到Git可执行文件")
            
            self.results["git"] = git_info
        except Exception as e:
            self.log_error("Git信息检测", str(e))
            self.results["git"] = {"错误": str(e)}
    
    def check_pip_available(self) -> bool:
        """检查pip是否可用"""
        try:
            import pip
            return True
        except ImportError:
            return False
    
    def get_cache_path(self) -> str:
        """获取缓存文件路径"""
        # 获取应用程序数据目录
        if self.system == "Windows":
            app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
            cache_dir = os.path.join(app_data, "ComfyUI-Manager", "cache")
        else:
            cache_dir = os.path.join(os.path.expanduser("~"), ".comfyui-manager", "cache")
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        # 缓存文件路径
        return os.path.join(cache_dir, "system_detection_cache.json")
    
    def save_cache(self, results: Dict[str, Any]) -> bool:
        """保存检测结果到缓存"""
        try:
            cache_path = self.get_cache_path()
            
            # 检查缓存文件大小
            if os.path.exists(cache_path):
                file_size = os.path.getsize(cache_path)
                # 如果缓存文件超过10MB，清理旧缓存
                if file_size > 10 * 1024 * 1024:
                    os.remove(cache_path)
                    self.log_error("缓存保存", "缓存文件过大，已清理")
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                # 添加缓存时间戳
                results["metadata"]["缓存时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                json.dump(results, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.log_error("缓存保存", str(e))
            return False
    
    def load_cache(self, max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
        """从缓存加载检测结果
        
        Args:
            max_age_hours: 缓存最大有效期（小时）
        """
        try:
            cache_path = self.get_cache_path()
            if os.path.exists(cache_path):
                # 检查缓存文件大小
                file_size = os.path.getsize(cache_path)
                if file_size > 10 * 1024 * 1024:
                    self.log_error("缓存加载", "缓存文件过大，已清理")
                    os.remove(cache_path)
                    return None
                
                # 检查缓存过期时间
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 检查缓存时间
                    cache_time_str = data.get("metadata", {}).get("缓存时间")
                    if cache_time_str:
                        try:
                            cache_time = datetime.strptime(cache_time_str, "%Y-%m-%d %H:%M:%S")
                            current_time = datetime.now()
                            age_hours = (current_time - cache_time).total_seconds() / 3600
                            
                            if age_hours > max_age_hours:
                                self.log_error("缓存加载", f"缓存已过期（{age_hours:.1f}小时）")
                                return None
                        except Exception as e:
                            self.log_error("缓存时间解析", str(e))
                    
                    return data
            return None
        except Exception as e:
            self.log_error("缓存加载", str(e))
            return None
    
    def clear_cache(self) -> bool:
        """清理缓存"""
        try:
            cache_path = self.get_cache_path()
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return True
        except Exception as e:
            self.log_error("缓存清理", str(e))
            return False
    
    def run_complete_detection(self, progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """运行完整检测
        
        Args:
            progress_callback: 进度更新回调函数，接收两个参数：进度值(0-100)和消息
        """
        import concurrent.futures
        
        # 清除旧的缓存
        self.clear_cache()
        self.log_error("缓存清理", "检测前已清理旧缓存")
        
        # 检测任务列表
        tasks = [
            ('system', self.detect_system_info, '检测系统信息...'),
            ('cpu', self.detect_cpu_info, '检测CPU信息...'),
            ('gpu', self.detect_gpu_info, '检测GPU信息...'),
            ('memory', self.detect_memory_info, '检测内存信息...'),
            ('storage', self.detect_storage_info, '检测存储信息...'),
            ('network', self.detect_network_info, '检测网络信息...'),
            ('python', self.detect_python_info, '检测Python信息...'),
            ('git', self.detect_git_info, '检测Git信息...')
        ]
        
        total_tasks = len(tasks)
        completed_tasks = 0
        
        # 发送初始进度
        if progress_callback:
            progress_callback(10, '开始系统检测...')
        
        # 使用线程池并行执行检测任务，提高检测速度
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # 提交检测任务
            futures = {}
            for task_name, task_func, task_msg in tasks:
                futures[task_name] = executor.submit(task_func)
            
            # 等待任务完成并更新进度
            for name, future in futures.items():
                try:
                    future.result()
                    completed_tasks += 1
                    # 计算进度
                    progress = 10 + int((completed_tasks / total_tasks) * 80)
                    # 发送进度更新
                    if progress_callback:
                        task_msg = next((msg for tname, tfunc, msg in tasks if tname == name), '完成任务')
                        progress_callback(progress, task_msg)
                except Exception as e:
                    self.log_error(f"并行检测-{name}", str(e))
        
        # 发送完成进度
        if progress_callback:
            progress_callback(100, '检测完成')
        
        # 保存检测结果到缓存
        self.save_cache(self.results)
        self.log_error("缓存保存", "检测结果已保存到新缓存")
        
        return self.results


# 测试代码
if __name__ == "__main__":
    import json
    detector = SystemDetector()
    results = detector.run_complete_detection()
    print(json.dumps(results, ensure_ascii=False, indent=2))