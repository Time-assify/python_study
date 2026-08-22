"""Test engine module"""
import subprocess
import sys
import json
import time
import shutil
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from .models import TestResult, TestSuiteResult


class TestEngine:
    """Test engine using pytest"""
    
    def __init__(self, tests_dir: str = "tests", timeout: int = 60):
        self.tests_dir = Path(tests_dir)
        self.timeout = timeout
    
    def _check_json_report_plugin(self) -> bool:
        """Check if pytest-json-report is installed"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--co", "-q", "--json-report"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception):
            return False
    
    def run_submission(self, day: int, submission_path: str) -> TestSuiteResult:
        """Run user submission tests
        
        Args:
            day: Day number
            submission_path: Path to user's answer.py
            
        Returns:
            TestSuiteResult
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
        
        temp_dir = Path(tempfile.mkdtemp())
        report_file = None
        timed_out = False
        
        try:
            shutil.copy2(submission, temp_dir / "answer.py")
            shutil.copy2(test_file, temp_dir / test_file.name)
            
            report_file = temp_dir / "test_report.json"
            
            cmd = [
                sys.executable, "-m", "pytest",
                test_file.name,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={report_file}"
            ]
            
            env = os.environ.copy()
            env["PYTHONPATH"] = str(temp_dir)
            
            start_time = time.time()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=str(temp_dir),
                env=env
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                timed_out = True
                return TestSuiteResult(
                    total_tests=0, passed=0, failed=0, errors=1,
                    duration=self.timeout, test_results=[TestResult(
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
            duration = time.time() - start_time
            return TestSuiteResult(
                total_tests=0, passed=0, failed=0, errors=1,
                duration=duration, test_results=[TestResult(
                    test_name="exception", status="error", duration=duration,
                    message=str(e)
                )], score=0.0
            )
        finally:
            if report_file and report_file.exists():
                try:
                    report_file.unlink()
                except Exception:
                    pass
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
    
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
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return TestSuiteResult(
                    total_tests=0, passed=0, failed=0, errors=1,
                    duration=self.timeout, test_results=[TestResult(
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
            duration = time.time() - start_time
            return TestSuiteResult(
                total_tests=0, passed=0, failed=0, errors=1,
                duration=duration, test_results=[TestResult(
                    test_name="exception", status="error", duration=duration,
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
            
            score = self._calculate_score(passed, total)
            
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
        
        total = passed + failed + errors
        score = self._calculate_score(passed, total)
        
        return TestSuiteResult(
            total_tests=total, passed=passed, failed=failed,
            errors=errors, duration=duration,
            test_results=test_results, score=score
        )
    
    def _calculate_score(self, passed: int, total: int) -> float:
        """Calculate test score"""
        if total == 0:
            return 0.0
        return (passed / total) * 100
    
    def _create_empty_result(self, duration: float) -> TestSuiteResult:
        """Create empty result"""
        return TestSuiteResult(
            total_tests=0, passed=0, failed=0, errors=1,
            duration=duration, test_results=[], score=0.0
        )
