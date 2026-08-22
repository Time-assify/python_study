"""提交管理器模块"""
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class Submission:
    """提交记录数据类"""
    id: Optional[int] = None
    day: int = 0
    file_path: str = ""
    commit_time: str = ""
    version: int = 1
    score: float = 0.0
    comments: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SubmissionManager:
    """提交管理器
    
    负责接收用户代码、保存历史版本、管理提交记录。
    """
    
    def __init__(self, submissions_dir: str = "submissions"):
        """初始化提交管理器
        
        Args:
            submissions_dir: 提交文件存储目录
        """
        self.submissions_dir = Path(submissions_dir)
        self.submissions_dir.mkdir(parents=True, exist_ok=True)
    
    def submit_code(self, 
                   day: int, 
                   code: str, 
                   filename: str = "answer.py",
                   score: float = 0.0,
                   comments: str = "") -> Submission:
        """提交代码
        
        Args:
            day: 天数
            code: 代码内容
            filename: 文件名
            score: 分数
            comments: 评论
            
        Returns:
            Submission对象
        """
        # 创建day目录
        day_dir = self.submissions_dir / f"day{day:02d}"
        day_dir.mkdir(exist_ok=True)
        
        # 获取版本号
        version = self._get_next_version(day_dir, filename)
        
        # 生成文件名（包含版本号）
        if version > 1:
            name, ext = Path(filename).stem, Path(filename).suffix
            versioned_filename = f"{name}_v{version}{ext}"
        else:
            versioned_filename = filename
        
        # 保存代码文件
        file_path = day_dir / versioned_filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # 更新当前版本文件（无版本号）
        current_file = day_dir / filename
        with open(current_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # 创建提交记录
        submission = Submission(
            day=day,
            file_path=str(file_path),
            commit_time=datetime.now().isoformat(),
            version=version,
            score=score,
            comments=comments
        )
        
        # 保存提交记录到JSON文件
        self._save_submission_record(submission)
        
        return submission
    
    def get_submissions(self, day: int) -> List[Submission]:
        """获取指定天的所有提交记录
        
        Args:
            day: 天数
            
        Returns:
            提交记录列表
        """
        records_file = self.submissions_dir / f"day{day:02d}" / "records.json"
        
        if not records_file.exists():
            return []
        
        try:
            with open(records_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            return [Submission(**record) for record in records]
        except Exception as e:
            print(f"读取提交记录失败: {e}")
            return []
    
    def get_latest_submission(self, day: int) -> Optional[Submission]:
        """获取指定天的最新提交
        
        Args:
            day: 天数
            
        Returns:
            最新的Submission对象
        """
        submissions = self.get_submissions(day)
        if not submissions:
            return None
        
        # 按版本号排序，返回最新的
        submissions.sort(key=lambda x: x.version, reverse=True)
        return submissions[0]
    
    def get_submission_count(self, day: int) -> int:
        """获取指定天的提交次数
        
        Args:
            day: 天数
            
        Returns:
            提交次数
        """
        submissions = self.get_submissions(day)
        return len(submissions)
    
    def get_code(self, day: int, version: int = None) -> Optional[str]:
        """获取代码内容
        
        Args:
            day: 天数
            version: 版本号，None则获取最新版本
            
        Returns:
            代码内容
        """
        day_dir = self.submissions_dir / f"day{day:02d}"
        
        if not day_dir.exists():
            return None
        
        if version is None:
            # 获取最新版本
            submission = self.get_latest_submission(day)
            if submission:
                file_path = Path(submission.file_path)
            else:
                file_path = day_dir / "answer.py"
        else:
            # 获取指定版本
            file_path = day_dir / f"answer_v{version}.py"
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        return None
    
    def delete_submission(self, day: int, version: int = None) -> bool:
        """删除提交
        
        Args:
            day: 天数
            version: 版本号，None则删除所有版本
            
        Returns:
            是否删除成功
        """
        day_dir = self.submissions_dir / f"day{day:02d}"
        
        if not day_dir.exists():
            return False
        
        try:
            if version is None:
                # 删除整个目录
                shutil.rmtree(day_dir)
            else:
                # 删除特定版本
                file_path = day_dir / f"answer_v{version}.py"
                if file_path.exists():
                    file_path.unlink()
            
            return True
        except Exception as e:
            print(f"删除提交失败: {e}")
            return False
    
    def get_all_days_with_submissions(self) -> List[int]:
        """获取所有有提交的天数
        
        Returns:
            天数列表
        """
        days = []
        for item in self.submissions_dir.iterdir():
            if item.is_dir() and item.name.startswith("day"):
                try:
                    day_num = int(item.name[3:])
                    days.append(day_num)
                except ValueError:
                    continue
        
        return sorted(days)
    
    def get_submission_statistics(self) -> Dict[str, Any]:
        """获取提交统计信息
        
        Returns:
            统计信息字典
        """
        all_days = self.get_all_days_with_submissions()
        
        total_submissions = 0
        for day in all_days:
            total_submissions += self.get_submission_count(day)
        
        return {
            "total_days": len(all_days),
            "total_submissions": total_submissions,
            "average_submissions_per_day": round(total_submissions / max(len(all_days), 1), 1)
        }
    
    def _get_next_version(self, day_dir: Path, filename: str) -> int:
        """获取下一个版本号"""
        submissions = []
        
        for file in day_dir.glob(f"{Path(filename).stem}_v*.py"):
            try:
                # 提取版本号
                parts = file.stem.split('_v')
                if len(parts) > 1:
                    version = int(parts[-1])
                    submissions.append(version)
            except ValueError:
                continue
        
        if not submissions:
            return 1
        
        return max(submissions) + 1
    
    def _save_submission_record(self, submission: Submission):
        """保存提交记录"""
        day_dir = self.submissions_dir / f"day{submission.day:02d}"
        day_dir.mkdir(exist_ok=True)
        
        records_file = day_dir / "records.json"
        
        # 读取现有记录
        records = []
        if records_file.exists():
            try:
                with open(records_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            except:
                records = []
        
        # 添加新记录
        records.append(submission.to_dict())
        
        # 保存记录
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    
    def backup_submissions(self, backup_dir: str) -> bool:
        """备份所有提交
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            是否备份成功
        """
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            shutil.copytree(
                self.submissions_dir,
                backup_path / "submissions",
                dirs_exist_ok=True
            )
            
            return True
        except Exception as e:
            print(f"备份失败: {e}")
            return False
    
    def restore_submissions(self, backup_dir: str) -> bool:
        """恢复提交
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            是否恢复成功
        """
        try:
            backup_path = Path(backup_dir) / "submissions"
            
            if not backup_path.exists():
                print("备份目录不存在")
                return False
            
            # 清空当前目录
            shutil.rmtree(self.submissions_dir)
            
            # 恢复备份
            shutil.copytree(backup_path, self.submissions_dir)
            
            return True
        except Exception as e:
            print(f"恢复失败: {e}")
            return False