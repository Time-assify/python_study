"""Test engine module

TestEngine只负责：运行pytest、解析结果。
环境准备/清理由TestLoader负责（P1-2）。
数据模型统一使用 .models 中的 TestResult / TestSuiteResult（P0-2）。
"""
import importlib.util
import subprocess
import sys
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from .models import TestResult, TestSuiteResult
from .test_loader import TestLoader


class TestEngine:
    """Test engine using pytest"""
    
    def __init__(self, tests_dir: str = "tests", timeout: int = 60):
        self.tests_dir = Path(tests_dir)
        self.timeout = timeout
        self.test_loader = TestLoader(tests_dir=tests_dir)
    
    @staticmethod
    def _check_json_report_plugin() -> bool:
        """Check if pytest-json-report is installed
        
        P0-6: 使用importlib检测插件，不运行pytest collection。
        插件检查不能依赖项目测试是否成功collect。
        """
        try:
            return importlib.util.find_spec("pytest_jsonreport") is not None
        except (ImportError, ValueError):
            return False
    
    def run_submission(self, day: int, submission_path: str) -> TestSuiteResult:
        """Run user submission tests
        
        Args:
            day: Day number
            submission_path: Path to user's answer.py
            
        Returns:
            TestSuiteResult (timeout字段明确传播)
        """
        test_file = self.tests_dir / f"day{day:02d}_test.py"
        if not test_file.exists():
            return TestSuiteResult(
                total_tests=0, passed=0, failed=0, errors=1,
                duration=0, test_results=[TestResult(
                    test_name="file_check", status="error", duration=0,
                    message=f"Test file not found: {test_file}"
                )], score=0.0
            )
        
        submission = Path(submission_path)
        if not submission.exists():
            return TestSuiteResult(
                total_tests=0, passed=0, failed=0, errors=1,
                duration=0, test_results=[TestResult(
                    test_name="file_check", status="error", duration=0,
                    message=f"Submission file not found: {submission_path}"
                )], score=0.0
            )
        
        if not self._check_json_report_plugin():
            return TestSuiteResult(
                total_tests=0, passed=0, failed=0, errors=1,
                duration=0, test_results=[TestResult(
                    test_name="plugin_check", status="error", duration=0,
                    message="pytest-json-report not installed. Run: pip install pytest-json-report"
                )], score=0.0
            )
        
        report_file = None
        
        # P1-2: TestLoader负责准备/清理环境
        try:
            env_dir = self.test_loader.load_test_environment(day, submission_path)
        except FileNotFoundError as e:
            return TestSuiteResult(
                total_tests=0, passed=0, failed=0, errors=1,
                duration=0, test_results=[TestResult(
                    test_name="env_setup", status="error", duration=0,
                    message=str(e)
                )], score=0.0
            )
        
        timed_out = False
        
        try:
            report_file = env_dir / "test_report.json"
            
            cmd = [
                sys.executable, "-m", "pytest",
                test_file.name,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={report_file}",
                # 隔离子进程tmp目录，避免依赖系统temproot
                "--basetemp", str(env_dir / "_bt"),
            ]
            
            env = os.environ.copy()
            env["PYTHONPATH"] = str(env_dir)
            env["PYTEST_DEBUG_TEMPROOT"] = str(env_dir)
            
            start_time = time.time()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=str(env_dir),
                env=env
            )
            
            stdout = stderr = ""
            return_code = -1
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                timed_out = True
                # P0-2: 超时必须显式设置 timeout=True
                return TestSuiteResult(
                    total_tests=0, passed=0, failed=0, errors=1,
                    duration=self.timeout,
                    timeout=True,
                    test_results=[TestResult(
                        test_name="timeout", status="error", duration=self.timeout,
                        message="Test execution timed out"
                    )], score=0.0
                )
            
            duration = time.time() - start_time
            
            if report_file.exists():
                result = self._parse_json_report(report_file, duration)
                result.timeout = timed_out
                return result
            
            return self._parse_stdout(stdout, stderr, duration, return_code)
            
        except Exception as e:
            return TestSuiteResult(
                total_tests=0, passed=0, failed=0, errors=1,
                duration=0, test_results=[TestResult(
                    test_name="exception", status="error", duration=0,
                    message=str(e)
                )], score=0.0
            )
        finally:
            self.test_loader.cleanup(env_dir)
    
    def run_tests(self, test_file: str, verbose: bool = True) -> TestSuiteResult:
        """Run tests - requires test_file parameter
        
        Args:
            test_file: Test file path (required)
            verbose: Show detailed output
            
        Returns:
            TestSuiteResult
        """
        if not test_file:
            return TestSuiteResult(
                total_tests=0, passed=0, failed=0, errors=1,
                duration=0, test_results=[TestResult(
                    test_name="param_check", status="error", duration=0,
                    message="test_file is required"
                )], score=0.0
            )
        
        if not self._check_json_report_plugin():
            return TestSuiteResult(
                total_tests=0, passed=0, failed=0, errors=1,
                duration=0, test_results=[TestResult(
                    test_name="plugin_check", status="error", duration=0,
                    message="pytest-json-report not installed. Run: pip install pytest-json-report"
                )], score=0.0
            )
        
        cmd = [sys.executable, "-m", "pytest", test_file]
        
        if verbose:
            cmd.append("-v")
        
        report_file = self.tests_dir / "test_report.json"
        cmd.extend(["--tb=short", "--json-report", f"--json-report-file={report_file}"])
        
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
            
            stdout = stderr = ""
            return_code = -1
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return TestSuiteResult(
                    total_tests=0, passed=0, failed=0, errors=1,
                    duration=self.timeout,
                    timeout=True,
                    test_results=[TestResult(
                        test_name="timeout", status="error", duration=self.timeout,
                        message="Test execution timed out"
                    )], score=0.0
                )
            
            duration = time.time() - start_time
            
            if report_file.exists():
                result = self._parse_json_report(report_file, duration)
                try:
                    report_file.unlink()
                except Exception:
                    pass
                return result
            
            return self._parse_stdout(stdout, stderr, duration, return_code)
            
        except Exception as e:
            return TestSuiteResult(
                total_tests=0, passed=0, failed=0, errors=1,
                duration=0, test_results=[TestResult(
                    test_name="exception", status="error", duration=0,
                    message=str(e)
                )], score=0.0
            )
    
    def _parse_json_report(self, report_file: Path, duration: float) -> TestSuiteResult:
        """Parse JSON report"""
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
            
            score = self._calculate_score(passed, failed, errors)
            
            return TestSuiteResult(
                total_tests=total, passed=passed, failed=failed,
                errors=errors, duration=duration,
                test_results=test_results, score=score
            )
            
        except Exception as e:
            return self._create_empty_result(duration)
    
    def _parse_stdout(self, stdout: str, stderr: str, duration: float, return_code: int) -> TestSuiteResult:
        """Parse standard output"""
        test_results = []
        passed = 0
        failed = 0
        errors = 0
        
        lines = stdout.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("PASSED"):
                passed += 1
                test_results.append(TestResult(test_name=line, status="passed", duration=0))
            elif line.startswith("FAILED"):
                failed += 1
                test_results.append(TestResult(test_name=line, status="failed", duration=0, message=line))
            elif line.startswith("ERROR"):
                errors += 1
                test_results.append(TestResult(test_name=line, status="error", duration=0, message=line))
        
        score = self._calculate_score(passed, failed, errors)
        
        return TestSuiteResult(
            total_tests=passed + failed + errors, passed=passed, failed=failed,
            errors=errors, duration=duration,
            test_results=test_results, score=score
        )
    
    def _calculate_score(self, passed: int, failed: int = 0, errors: int = 0) -> float:
        """Calculate test score
        
        skipped测试不计入分母，避免环境缺库导致的不公平扣分。
        """
        graded_total = passed + failed + errors
        if graded_total == 0:
            return 0.0
        return (passed / graded_total) * 100
    
    def _create_empty_result(self, duration: float) -> TestSuiteResult:
        """Create empty result"""
        return TestSuiteResult(
            total_tests=0, passed=0, failed=0, errors=1,
            duration=duration, test_results=[], score=0.0
        )
