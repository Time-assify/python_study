# Day 01 Tests: Python工程环境
#
# answer.py 必须实现（接口约定）:
# - create_project_structure(project_name) -> dict  包含 root/src/tests/configs/data/logs 键
# - create_config_file(config_path) -> bool         创建yaml配置文件
# - setup_logger(log_file, level=logging.INFO) -> logger  写入日志文件
import pytest
import os
import logging
import tempfile

try:
    import answer
except ModuleNotFoundError as e:
    if getattr(e, "name", "") == "answer":
        answer = None
    else:
        raise
except Exception:
    raise


def test_answer_module_imports():
    """answer exists -> import errors are FAIL; only skip when repo has no submission"""
    if answer is None:
        pytest.skip("no answer.py under review (TestEngine injects it during real grading)")


def _require(name):
    """获取answer中要求的函数；缺失时明确FAIL并提示"""
    if answer is None:
        pytest.skip("no answer.py under review")
    fn = getattr(answer, name, None)
    if fn is None:
        pytest.fail(f"必须实现 {name}()")
    return fn


@pytest.mark.skill("python.project_structure", "python.logging")
class TestProjectStructure:
    """测试项目结构创建"""

    def test_create_structure_returns_dict(self):
        """测试返回值是字典"""
        fn = _require("create_project_structure")
        with tempfile.TemporaryDirectory() as tmpdir:
            result = fn(os.path.join(tmpdir, "proj"))
            assert isinstance(result, dict)

    def test_create_structure_has_required_dirs(self):
        """测试包含必需的目录键"""
        fn = _require("create_project_structure")
        with tempfile.TemporaryDirectory() as tmpdir:
            result = fn(os.path.join(tmpdir, "proj"))
            for key in ["root", "src", "tests", "configs", "data", "logs"]:
                assert key in result, f"缺少目录: {key}"

    def test_create_structure_creates_directories(self):
        """边界条件: 测试实际创建了目录"""
        fn = _require("create_project_structure")
        with tempfile.TemporaryDirectory() as tmpdir:
            result = fn(os.path.join(tmpdir, "proj"))
            for dir_path in result.values():
                assert os.path.isdir(dir_path), f"目录不存在: {dir_path}"

    def test_create_structure_creates_init_file(self):
        """测试创建了__init__.py"""
        fn = _require("create_project_structure")
        with tempfile.TemporaryDirectory() as tmpdir:
            fn(os.path.join(tmpdir, "proj"))
            assert os.path.exists(os.path.join(tmpdir, "proj", "src", "__init__.py"))


@pytest.mark.skill("python.project_structure", "python.logging")
class TestConfigFile:
    """测试配置文件创建"""

    def test_create_config_returns_true(self):
        fn = _require("create_config_file")
        with tempfile.TemporaryDirectory() as tmpdir:
            assert fn(os.path.join(tmpdir, "config.yaml")) is True

    def test_create_config_creates_file_with_content(self):
        """边界条件: 文件存在且内容非空"""
        fn = _require("create_config_file")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            fn(path)
            assert os.path.exists(path)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            assert len(content) > 0
            assert "project" in content.lower() or "config" in content.lower()


@pytest.mark.skill("python.project_structure", "python.logging")
class TestLogger:
    """测试日志系统"""

    def test_setup_logger_creates_file(self):
        """错误处理: 日志文件被创建且可写入"""
        fn = _require("setup_logger")
        log_file = os.path.join(os.getcwd(), "test_temp_d01.log")
        lg = None
        try:
            lg = fn(log_file, level=logging.INFO)
            lg.info("测试日志消息")
            for h in lg.handlers:
                h.flush()
            assert os.path.exists(log_file), "日志文件未被创建"
            assert os.path.getsize(log_file) > 0, "日志文件为空"
        finally:
            if lg is not None:
                for h in lg.handlers[:]:
                    try:
                        h.close()
                    except Exception:
                        pass
                    lg.removeHandler(h)
            for h in logging.getLogger("ml_project").handlers[:]:
                try:
                    h.close()
                except Exception:
                    pass
                logging.getLogger("ml_project").removeHandler(h)
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except OSError:
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
