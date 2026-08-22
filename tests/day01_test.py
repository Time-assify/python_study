# Day 01 Tests: Python工程环境
import pytest
import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path

# 添加submissions目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "submissions" / "day01"))

from answer import create_project_structure, create_config_file, setup_logger


class TestProjectStructure:
    """测试项目结构创建"""
    
    def test_create_structure_returns_dict(self):
        """测试返回值是字典"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_name = os.path.join(tmpdir, "test_project")
            result = create_project_structure(project_name)
            assert isinstance(result, dict)
    
    def test_create_structure_has_required_dirs(self):
        """测试包含必需的目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_name = os.path.join(tmpdir, "test_project")
            result = create_project_structure(project_name)
            
            required_keys = ["root", "src", "tests", "configs", "data", "logs"]
            for key in required_keys:
                assert key in result, f"缺少目录: {key}"
    
    def test_create_structure_creates_directories(self):
        """测试实际创建了目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_name = os.path.join(tmpdir, "test_project")
            result = create_project_structure(project_name)
            
            for dir_path in result.values():
                assert os.path.isdir(dir_path), f"目录不存在: {dir_path}"
    
    def test_create_structure_creates_init_file(self):
        """测试创建了__init__.py"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_name = os.path.join(tmpdir, "test_project")
            create_project_structure(project_name)
            
            init_file = os.path.join(project_name, "src", "__init__.py")
            assert os.path.exists(init_file), "__init__.py不存在"


class TestConfigFile:
    """测试配置文件创建"""
    
    def test_create_config_returns_true(self):
        """测试返回True"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            result = create_config_file(config_path)
            assert result is True
    
    def test_create_config_creates_file(self):
        """测试创建了文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            create_config_file(config_path)
            assert os.path.exists(config_path)
    
    def test_create_config_has_content(self):
        """测试文件有内容"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            create_config_file(config_path)
            
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert len(content) > 0
                assert "project" in content.lower() or "config" in content.lower()


class TestLogger:
    """测试日志系统"""
    
    def test_setup_logger_creates_file(self):
        """测试创建日志文件"""
        log_file = os.path.join(os.getcwd(), "test_temp.log")
        try:
            # 清除之前的处理器
            logger = logging.getLogger("ml_project")
            logger.handlers.clear()
            
            setup_logger(log_file)
            logger.info("测试日志消息")
            
            # 刷新处理器
            for handler in logger.handlers:
                handler.flush()
            
            assert os.path.exists(log_file)
        finally:
            # 清理
            for handler in logging.getLogger("ml_project").handlers[:]:
                handler.close()
                logging.getLogger("ml_project").removeHandler(handler)
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except:
                    pass
    
    def test_setup_logger_writes_content(self):
        """测试日志文件有内容"""
        log_file = os.path.join(os.getcwd(), "test_temp2.log")
        try:
            # 清除之前的处理器
            logger = logging.getLogger("ml_project")
            logger.handlers.clear()
            
            setup_logger(log_file, level=logging.INFO)
            logger.info("测试日志消息")
            
            # 刷新处理器
            for handler in logger.handlers:
                handler.flush()
            
            assert os.path.getsize(log_file) > 0
        finally:
            # 清理
            for handler in logging.getLogger("ml_project").handlers[:]:
                handler.close()
                logging.getLogger("ml_project").removeHandler(handler)
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except:
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])