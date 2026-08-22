"""代码执行器模块"""
import subprocess
import sys
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExecutionResult:
    """执行结果数据类"""
    status: str  # success, error, timeout
    time: float  # 执行时间（秒）
    stdout: str
    stderr: str
    return_code: int
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status,
            "time": self.time,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_code": self.return_code,
            "timestamp": self.timestamp
        }


class CodeExecutor:
    """代码执行器
    
    使用subprocess安全执行Python代码。
    支持超时限制、错误捕获、输出记录。
    """
    
    def __init__(self, timeout: int = 30, max_output_size: int = 10000):
        """初始化代码执行器
        
        Args:
            timeout: 超时时间（秒）
            max_output_size: 最大输出大小（字符数）
        """
        self.timeout = timeout
        self.max_output_size = max_output_size
    
    def execute_code(self, code: str, working_dir: str = None) -> ExecutionResult:
        """执行Python代码
        
        Args:
            code: Python代码字符串
            working_dir: 工作目录
            
        Returns:
            ExecutionResult对象
        """
        # 创建临时文件存储代码
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            return self._execute_file(temp_file, working_dir)
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def execute_file(self, file_path: str, working_dir: str = None) -> ExecutionResult:
        """执行Python文件
        
        Args:
            file_path: Python文件路径
            working_dir: 工作目录
            
        Returns:
            ExecutionResult对象
        """
        if not os.path.exists(file_path):
            return ExecutionResult(
                status="error",
                time=0.0,
                stdout="",
                stderr=f"文件不存在: {file_path}",
                return_code=-1,
                timestamp=datetime.now().isoformat()
            )
        
        return self._execute_file(file_path, working_dir)
    
    def _execute_file(self, file_path: str, working_dir: str = None) -> ExecutionResult:
        """执行Python文件（内部方法）"""
        start_time = datetime.now()
        
        try:
            # 构建执行命令
            cmd = [sys.executable, file_path]
            
            # 设置工作目录
            if working_dir is None:
                working_dir = os.path.dirname(file_path) or "."
            
            # 执行代码
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                # 超时处理
                process.kill()
                stdout, stderr = process.communicate()
                return ExecutionResult(
                    status="timeout",
                    time=self.timeout,
                    stdout=self._truncate_output(stdout),
                    stderr="执行超时",
                    return_code=-1,
                    timestamp=datetime.now().isoformat()
                )
            
            # 计算执行时间
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 判断执行状态
            status = "success" if return_code == 0 else "error"
            
            return ExecutionResult(
                status=status,
                time=execution_time,
                stdout=self._truncate_output(stdout),
                stderr=self._truncate_output(stderr),
                return_code=return_code,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return ExecutionResult(
                status="error",
                time=execution_time,
                stdout="",
                stderr=f"执行异常: {str(e)}",
                return_code=-1,
                timestamp=datetime.now().isoformat()
            )
    
    def execute_with_input(self, code: str, input_data: str, working_dir: str = None) -> ExecutionResult:
        """执行带输入的Python代码
        
        Args:
            code: Python代码字符串
            input_data: 输入数据
            working_dir: 工作目录
            
        Returns:
            ExecutionResult对象
        """
        # 创建临时文件存储代码
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            start_time = datetime.now()
            
            # 构建执行命令
            cmd = [sys.executable, temp_file]
            
            # 设置工作目录
            if working_dir is None:
                working_dir = os.path.dirname(temp_file) or "."
            
            # 执行代码
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            try:
                stdout, stderr = process.communicate(
                    input=input_data, 
                    timeout=self.timeout
                )
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return ExecutionResult(
                    status="timeout",
                    time=self.timeout,
                    stdout=self._truncate_output(stdout),
                    stderr="执行超时",
                    return_code=-1,
                    timestamp=datetime.now().isoformat()
                )
            
            # 计算执行时间
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 判断执行状态
            status = "success" if return_code == 0 else "error"
            
            return ExecutionResult(
                status=status,
                time=execution_time,
                stdout=self._truncate_output(stdout),
                stderr=self._truncate_output(stderr),
                return_code=return_code,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return ExecutionResult(
                status="error",
                time=execution_time,
                stdout="",
                stderr=f"执行异常: {str(e)}",
                return_code=-1,
                timestamp=datetime.now().isoformat()
            )
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def _truncate_output(self, output: str) -> str:
        """截断过长的输出"""
        if len(output) > self.max_output_size:
            return output[:self.max_output_size] + "\n... (输出被截断)"
        return output
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """验证代码语法
        
        Args:
            code: Python代码字符串
            
        Returns:
            验证结果字典
        """
        try:
            compile(code, '<string>', 'exec')
            return {
                "valid": True,
                "message": "语法正确"
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "message": f"语法错误: {e.msg}",
                "line": e.lineno,
                "offset": e.offset
            }
    
    def get_python_info(self) -> Dict[str, str]:
        """获取Python环境信息"""
        return {
            "python_version": sys.version,
            "python_path": sys.executable,
            "platform": sys.platform
        }