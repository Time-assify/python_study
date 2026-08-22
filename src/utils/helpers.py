"""工具函数模块"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class Helpers:
    """工具函数集合"""
    
    @staticmethod
    def load_json(file_path: str) -> Optional[Dict[str, Any]]:
        """加载JSON文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的字典，失败返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载JSON文件失败: {e}")
            return None
    
    @staticmethod
    def save_json(data: Dict[str, Any], file_path: str, indent: int = 2) -> bool:
        """保存JSON文件
        
        Args:
            data: 要保存的数据
            file_path: 文件路径
            indent: 缩进空格数
            
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            return True
        except Exception as e:
            print(f"保存JSON文件失败: {e}")
            return False
    
    @staticmethod
    def load_yaml(file_path: str) -> Optional[Dict[str, Any]]:
        """加载YAML文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的字典，失败返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"加载YAML文件失败: {e}")
            return None
    
    @staticmethod
    def save_yaml(data: Dict[str, Any], file_path: str) -> bool:
        """保存YAML文件
        
        Args:
            data: 要保存的数据
            file_path: 文件路径
            
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            print(f"保存YAML文件失败: {e}")
            return False
    
    @staticmethod
    def ensure_dir(dir_path: str) -> bool:
        """确保目录存在
        
        Args:
            dir_path: 目录路径
            
        Returns:
            是否成功
        """
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"创建目录失败: {e}")
            return False
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """获取文件扩展名
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件扩展名（不含点号）
        """
        return Path(file_path).suffix.lstrip('.')
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """格式化时间
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时间字符串
        """
        if seconds < 60:
            return f"{seconds:.2f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.2f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.2f}小时"
    
    @staticmethod
    def format_score(score: float) -> str:
        """格式化分数
        
        Args:
            score: 分数
            
        Returns:
            格式化的分数字符串
        """
        if score >= 90:
            return f"{score:.1f} (优秀)"
        elif score >= 80:
            return f"{score:.1f} (良好)"
        elif score >= 70:
            return f"{score:.1f} (中等)"
        elif score >= 60:
            return f"{score:.1f} (及格)"
        else:
            return f"{score:.1f} (不及格)"
    
    @staticmethod
    def get_timestamp() -> str:
        """获取当前时间戳"""
        return datetime.now().isoformat()
    
    @staticmethod
    def validate_day(day: int) -> bool:
        """验证天数
        
        Args:
            day: 天数
            
        Returns:
            是否有效
        """
        return 1 <= day <= 40
    
    @staticmethod
    def get_phase_info(day: int) -> Dict[str, Any]:
        """获取阶段信息
        
        Args:
            day: 天数
            
        Returns:
            阶段信息字典
        """
        phases = {
            1: {
                "name": "Python工程",
                "range": (1, 7),
                "description": "Python基础和工程化"
            },
            2: {
                "name": "PyTorch",
                "range": (8, 18),
                "description": "PyTorch深度学习框架"
            },
            3: {
                "name": "深度学习",
                "range": (19, 30),
                "description": "深度学习应用"
            },
            4: {
                "name": "AI Agent",
                "range": (31, 40),
                "description": "AI智能体开发"
            }
        }
        
        for phase_num, phase_info in phases.items():
            start, end = phase_info["range"]
            if start <= day <= end:
                return {
                    "phase": phase_num,
                    "name": phase_info["name"],
                    "description": phase_info["description"],
                    "day_in_phase": day - start + 1,
                    "total_days_in_phase": end - start + 1
                }
        
        return {"phase": 0, "name": "未知", "description": "未知阶段"}
    
    @staticmethod
    def print_separator(char: str = "=", length: int = 50) -> None:
        """打印分隔线"""
        print(char * length)
    
    @staticmethod
    def print_header(text: str) -> None:
        """打印标题"""
        Helpers.print_separator()
        print(text.center(50))
        Helpers.print_separator()
    
    @staticmethod
    def print_success(message: str) -> None:
        """打印成功消息"""
        print(f"✓ {message}")
    
    @staticmethod
    def print_error(message: str) -> None:
        """打印错误消息"""
        print(f"✗ {message}")
    
    @staticmethod
    def print_warning(message: str) -> None:
        """打印警告消息"""
        print(f"⚠ {message}")
    
    @staticmethod
    def print_info(message: str) -> None:
        """打印信息消息"""
        print(f"ℹ {message}")