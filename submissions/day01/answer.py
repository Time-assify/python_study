"""Day 01: Python工程环境 - 创建ML项目模板"""
import os
import logging
from pathlib import Path
from typing import Dict


def create_project_structure(project_name: str) -> Dict[str, str]:
    """创建项目目录结构
    
    Args:
        project_name: 项目名称
        
    Returns:
        目录结构字典
    """
    structure = {
        "root": project_name,
        "src": os.path.join(project_name, "src"),
        "tests": os.path.join(project_name, "tests"),
        "configs": os.path.join(project_name, "configs"),
        "data": os.path.join(project_name, "data"),
        "logs": os.path.join(project_name, "logs"),
        "docs": os.path.join(project_name, "docs"),
    }
    
    for dir_path in structure.values():
        os.makedirs(dir_path, exist_ok=True)
    
    # 创建__init__.py
    init_file = os.path.join(structure["src"], "__init__.py")
    with open(init_file, "w") as f:
        f.write("")
    
    return structure


def create_config_file(config_path: str) -> bool:
    """创建配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        是否创建成功
    """
    config_content = """# ML Project Configuration
project:
  name: my_ml_project
  version: 1.0.0

paths:
  data: data/
  models: models/
  logs: logs/

training:
  batch_size: 32
  learning_rate: 0.001
  epochs: 100
"""
    
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)
        return True
    except Exception:
        return False


def setup_logger(log_file: str, level: int = logging.INFO) -> None:
    """设置日志系统
    
    Args:
        log_file: 日志文件路径
        level: 日志级别
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logger = logging.getLogger("ml_project")
    logger.setLevel(level)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


if __name__ == "__main__":
    structure = create_project_structure("test_project")
    print("项目结构:", structure)