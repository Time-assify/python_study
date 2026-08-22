"""测试引擎模块"""
import subprocess
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    status: str  # passed, failed, error
    duration: float
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TestSuiteResult:
    """测试套件结果"""
    total_tests: int
    passed: int
    failed: int
    errors: int
    duration: float
    test_results: List[TestResult]
    score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "duration": self.duration,
            "score": self.score,
            "test_results": [t.to_dict() for t in self.test_results]
        }


class TestEngine:
    """测试引擎
    
    使用pytest执行测试，收集结果并评分。
    """
    
    def __init__(self, tests_dir: str = "tests", timeout: int = 60):
        """初始化测试引擎
        
        Args:
            tests_dir: 测试文件目录
            timeout: 测试超时时间（秒）
        """
        self.tests_dir = Path(tests_dir)
        self.timeout = timeout
    
    def run_tests(self, test_file: str = None, verbose: bool = True) -> TestSuiteResult:
        """运行测试
        
        Args:
            test_file: 指定测试文件，None则运行所有测试
            verbose: 是否显示详细输出
            
        Returns:
            TestSuiteResult对象
        """
        # 构建pytest命令
        cmd = [sys.executable, "-m", "pytest"]
        
        if test_file:
            cmd.append(test_file)
        else:
            cmd.append(str(self.tests_dir))
        
        if verbose:
            cmd.append("-v")
        
        # 添加JSON报告输出
        report_file = self.tests_dir / "test_report.json"
        cmd.extend(["--tb=short", f"--json-report={report_file}"])
        
        start_time = time.time()
        
        try:
            # 执行pytest
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return TestSuiteResult(
                    total_tests=0,
                    passed=0,
                    failed=0,
                    errors=1,
                    duration=self.timeout,
                    test_results=[TestResult(
                        test_name="timeout",
                        status="error",
                        duration=self.timeout,
                        message="测试执行超时"
                    )],
                    score=0.0
                )
            
            duration = time.time() - start_time
            
            # 尝试读取JSON报告
            if report_file.exists():
                return self._parse_json_report(report_file, duration)
            
            # 如果没有JSON报告，解析stdout
            return self._parse_stdout(stdout, stderr, duration, return_code)
            
        except Exception as e:
            duration = time.time() - start_time
            return TestSuiteResult(
                total_tests=0,
                passed=0,
                failed=0,
                errors=1,
                duration=duration,
                test_results=[TestResult(
                    test_name="exception",
                    status="error",
                    duration=duration,
                    message=str(e)
                )],
                score=0.0
            )
    
    def run_specific_test(self, test_file: str, test_name: str) -> TestSuiteResult:
        """运行特定测试
        
        Args:
            test_file: 测试文件路径
            test_name: 测试函数名
            
        Returns:
            TestSuiteResult对象
        """
        cmd = [sys.executable, "-m", "pytest", f"{test_file}::{test_name}", "-v"]
        
        start_time = time.time()
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            duration = time.time() - start_time
            
            return self._parse_stdout(stdout, stderr, duration, process.returncode)
            
        except Exception as e:
            duration = time.time() - start_time
            return TestSuiteResult(
                total_tests=1,
                passed=0,
                failed=0,
                errors=1,
                duration=duration,
                test_results=[TestResult(
                    test_name=test_name,
                    status="error",
                    duration=duration,
                    message=str(e)
                )],
                score=0.0
            )
    
    def _parse_json_report(self, report_file: Path, duration: float) -> TestSuiteResult:
        """解析JSON报告"""
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            test_results = []
            for test in report.get("tests", []):
                test_results.append(TestResult(
                    test_name=test.get("nodeid", "unknown"),
                    status=test.get("outcome", "unknown"),
                    duration=test.get("duration", 0),
                    message=test.get("call", {}).get("longrepr", "")
                ))
            
            summary = report.get("summary", {})
            total = summary.get("total", 0)
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            errors = summary.get("error", 0)
            
            # 计算分数
            score = self._calculate_score(passed, failed, errors, total)
            
            return TestSuiteResult(
                total_tests=total,
                passed=passed,
                failed=failed,
                errors=errors,
                duration=duration,
                test_results=test_results,
                score=score
            )
            
        except Exception as e:
            print(f"解析JSON报告失败: {e}")
            return self._create_empty_result(duration)
    
    def _parse_stdout(self, stdout: str, stderr: str, duration: float, return_code: int) -> TestSuiteResult:
        """解析标准输出"""
        test_results = []
        passed = 0
        failed = 0
        errors = 0
        
        # 简单解析pytest输出
        lines = stdout.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("PASSED"):
                passed += 1
                test_results.append(TestResult(
                    test_name=line,
                    status="passed",
                    duration=0
                ))
            elif line.startswith("FAILED"):
                failed += 1
                test_results.append(TestResult(
                    test_name=line,
                    status="failed",
                    duration=0,
                    message=line
                ))
            elif line.startswith("ERROR"):
                errors += 1
                test_results.append(TestResult(
                    test_name=line,
                    status="error",
                    duration=0,
                    message=line
                ))
        
        total = passed + failed + errors
        score = self._calculate_score(passed, failed, errors, total)
        
        return TestSuiteResult(
            total_tests=total,
            passed=passed,
            failed=failed,
            errors=errors,
            duration=duration,
            test_results=test_results,
            score=score
        )
    
    def _calculate_score(self, passed: int, failed: int, errors: int, total: int) -> float:
        """计算测试分数
        
        评分规则：
        - 功能测试：50%
        - 通过率：50%
        """
        if total == 0:
            return 0.0
        
        # 通过率分数（50%）
        pass_rate = passed / total
        pass_score = pass_rate * 50
        
        # 功能完整性分数（50%）
        # 每个测试代表一个功能点
        functionality_score = (passed / max(total, 1)) * 50
        
        total_score = pass_score + functionality_score
        return min(100.0, total_score)
    
    def _create_empty_result(self, duration: float) -> TestSuiteResult:
        """创建空结果"""
        return TestSuiteResult(
            total_tests=0,
            passed=0,
            failed=0,
            errors=1,
            duration=duration,
            test_results=[],
            score=0.0
        )
    
    def get_test_files(self) -> List[str]:
        """获取所有测试文件"""
        test_files = []
        if self.tests_dir.exists():
            for file in self.tests_dir.glob("*.py"):
                if file.name.startswith("test_"):
                    test_files.append(str(file))
        return test_files
    
    def validate_test_file(self, test_file: str) -> Dict[str, Any]:
        """验证测试文件格式"""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否包含测试函数
            if "def test_" not in content:
                return {
                    "valid": False,
                    "message": "测试文件中没有找到测试函数（以test_开头）"
                }
            
            # 检查是否导入pytest
            if "import pytest" not in content and "from pytest" not in content:
                return {
                    "valid": False,
                    "message": "测试文件中没有导入pytest"
                }
            
            return {
                "valid": True,
                "message": "测试文件格式正确"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"验证测试文件失败: {str(e)}"
            }
    
    def generate_test_template(self, function_name: str, function_code: str = "") -> str:
        """生成测试模板
        
        Args:
            function_name: 要测试的函数名
            function_code: 函数代码（可选）
            
        Returns:
            测试代码模板
        """
        template = f'''"""测试{function_name}函数"""
import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_{function_name}_basic():
    """测试{function_name}基本功能"""
    # TODO: 实现基本功能测试
    pass


def test_{function_name}_edge_cases():
    """测试{function_name}边界情况"""
    # TODO: 实现边界情况测试
    pass


def test_{function_name}_error_handling():
    """测试{function_name}错误处理"""
    # TODO: 实现错误处理测试
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
        return template