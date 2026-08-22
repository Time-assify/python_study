"""任务管理器模块"""
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Task:
    """任务数据类"""
    day: int
    title: str
    goal: str
    task: str
    description: str
    tests: List[str]
    resources: List[str] = None
    hints: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "day": self.day,
            "title": self.title,
            "goal": self.goal,
            "task": self.task,
            "description": self.description,
            "tests": self.tests,
            "resources": self.resources or [],
            "hints": self.hints or []
        }


class TaskManager:
    """任务管理器
    
    管理40天学习任务，提供任务查询、加载等功能。
    """
    
    def __init__(self, tasks_dir: str = "tasks", config_path: str = "configs/config.yaml"):
        """初始化任务管理器
        
        Args:
            tasks_dir: 任务文件目录
            config_path: 配置文件路径
        """
        self.tasks_dir = Path(tasks_dir)
        self.config = self._load_config(config_path)
        self.tasks_cache: Dict[int, Task] = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def get_task(self, day: int) -> Optional[Task]:
        """获取指定天的任务
        
        Args:
            day: 天数（1-40）
            
        Returns:
            Task对象，如果不存在则返回None
        """
        if day < 1 or day > 40:
            raise ValueError("天数必须在1-40之间")
            
        # 检查缓存
        if day in self.tasks_cache:
            return self.tasks_cache[day]
            
        # 加载任务文件
        task_file = self.tasks_dir / f"day{day:02d}.json"
        if not task_file.exists():
            return None
            
        with open(task_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        task = Task(
            day=data["day"],
            title=data["title"],
            goal=data["goal"],
            task=data["task"],
            description=data.get("description", ""),
            tests=data["tests"],
            resources=data.get("resources", []),
            hints=data.get("hints", [])
        )
        
        # 缓存任务
        self.tasks_cache[day] = task
        return task
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务
        
        Returns:
            任务列表
        """
        tasks = []
        for day in range(1, 41):
            task = self.get_task(day)
            if task:
                tasks.append(task)
        return tasks
    
    def get_task_by_title(self, title: str) -> Optional[Task]:
        """根据标题查找任务
        
        Args:
            title: 任务标题
            
        Returns:
            Task对象
        """
        for day in range(1, 41):
            task = self.get_task(day)
            if task and task.title == title:
                return task
        return None
    
    def get_phase_tasks(self, phase: int) -> List[Task]:
        """获取指定阶段的任务
        
        Args:
            phase: 阶段编号（1-4）
            
        Returns:
            该阶段的任务列表
        """
        phase_ranges = {
            1: range(1, 8),    # Day01-Day07: Python工程
            2: range(8, 19),   # Day08-Day18: PyTorch
            3: range(19, 31),  # Day19-Day30: 深度学习
            4: range(31, 41)   # Day31-Day40: AI Agent
        }
        
        if phase not in phase_ranges:
            raise ValueError("阶段编号必须在1-4之间")
            
        tasks = []
        for day in phase_ranges[phase]:
            task = self.get_task(day)
            if task:
                tasks.append(task)
        return tasks
    
    def create_task(self, task_data: Dict[str, Any]) -> Task:
        """创建新任务
        
        Args:
            task_data: 任务数据字典
            
        Returns:
            创建的Task对象
        """
        task = Task(
            day=task_data["day"],
            title=task_data["title"],
            goal=task_data["goal"],
            task=task_data["task"],
            description=task_data.get("description", ""),
            tests=task_data["tests"],
            resources=task_data.get("resources", []),
            hints=task_data.get("hints", [])
        )
        
        # 保存到文件
        task_file = self.tasks_dir / f"day{task.day:02d}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task.to_dict(), f, ensure_ascii=False, indent=2)
            
        # 更新缓存
        self.tasks_cache[task.day] = task
        return task
    
    def update_task(self, day: int, updates: Dict[str, Any]) -> Optional[Task]:
        """更新任务
        
        Args:
            day: 天数
            updates: 更新的字段
            
        Returns:
            更新后的Task对象
        """
        task = self.get_task(day)
        if not task:
            return None
            
        # 更新字段
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        # 保存到文件
        task_file = self.tasks_dir / f"day{day:02d}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task.to_dict(), f, ensure_ascii=False, indent=2)
            
        # 更新缓存
        self.tasks_cache[day] = task
        return task
    
    def delete_task(self, day: int) -> bool:
        """删除任务
        
        Args:
            day: 天数
            
        Returns:
            是否删除成功
        """
        task_file = self.tasks_dir / f"day{day:02d}.json"
        if task_file.exists():
            task_file.unlink()
            if day in self.tasks_cache:
                del self.tasks_cache[day]
            return True
        return False
    
    def get_task_count(self) -> int:
        """获取任务总数"""
        count = 0
        for day in range(1, 41):
            if self.get_task(day):
                count += 1
        return count
    
    def get_next_task(self, current_day: int) -> Optional[Task]:
        """获取下一个任务
        
        Args:
            current_day: 当前天数
            
        Returns:
            下一个Task对象
        """
        for day in range(current_day + 1, 41):
            task = self.get_task(day)
            if task:
                return task
        return None
    
    def get_previous_task(self, current_day: int) -> Optional[Task]:
        """获取上一个任务
        
        Args:
            current_day: 当前天数
            
        Returns:
            上一个Task对象
        """
        for day in range(current_day - 1, 0, -1):
            task = self.get_task(day)
            if task:
                return task
        return None