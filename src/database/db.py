"""数据库模块"""
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class ProgressRecord:
    """学习进度记录"""
    id: Optional[int] = None
    day: int = 0
    score: float = 0.0
    test_result: Dict[str, Any] = None
    ai_review: Dict[str, Any] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if self.test_result is None:
            self.test_result = {}
        if self.ai_review is None:
            self.ai_review = {}
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class SubmissionRecord:
    """提交记录"""
    id: Optional[int] = None
    day: int = 0
    file_path: str = ""
    commit_time: str = ""
    score: float = 0.0
    
    def __post_init__(self):
        if not self.commit_time:
            self.commit_time = datetime.now().isoformat()


class Database:
    """SQLite数据库管理类
    
    管理学习进度和提交记录。
    """
    
    def __init__(self, db_path: str = "data/progress.db"):
        """初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        # 创建progress表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day INTEGER NOT NULL,
                score REAL DEFAULT 0.0,
                test_result TEXT DEFAULT '{}',
                ai_review TEXT DEFAULT '{}',
                timestamp TEXT NOT NULL,
                UNIQUE(day)
            )
        """)
        
        # 创建submissions表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                commit_time TEXT NOT NULL,
                score REAL DEFAULT 0.0,
                FOREIGN KEY (day) REFERENCES progress(day)
            )
        """)
        
        # 创建review_history表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS review_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day INTEGER NOT NULL,
                code_snippet TEXT DEFAULT '',
                review_result TEXT DEFAULT '{}',
                timestamp TEXT NOT NULL
            )
        """)
        
        # 创建submission_history表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS submission_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day INTEGER NOT NULL,
                task_id TEXT DEFAULT '',
                code_path TEXT NOT NULL,
                test_score REAL DEFAULT 0.0,
                ai_score REAL DEFAULT 0.0,
                final_score REAL DEFAULT 0.0,
                created_time TEXT NOT NULL
            )
        """)
        
        self.conn.commit()
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # Progress表操作
    
    def save_progress(self, progress: ProgressRecord) -> int:
        """保存学习进度
        
        Args:
            progress: ProgressRecord对象
            
        Returns:
            记录ID
        """
        try:
            cursor = self.conn.execute("""
                INSERT OR REPLACE INTO progress (day, score, test_result, ai_review, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                progress.day,
                progress.score,
                json.dumps(progress.test_result),
                json.dumps(progress.ai_review),
                progress.timestamp
            ))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"保存进度失败: {e}")
            return -1
    
    def get_progress(self, day: int) -> Optional[ProgressRecord]:
        """获取指定天的学习进度
        
        Args:
            day: 天数
            
        Returns:
            ProgressRecord对象
        """
        try:
            cursor = self.conn.execute(
                "SELECT * FROM progress WHERE day = ?", (day,)
            )
            row = cursor.fetchone()
            
            if row:
                return ProgressRecord(
                    id=row["id"],
                    day=row["day"],
                    score=row["score"],
                    test_result=json.loads(row["test_result"]),
                    ai_review=json.loads(row["ai_review"]),
                    timestamp=row["timestamp"]
                )
            return None
        except sqlite3.Error as e:
            print(f"获取进度失败: {e}")
            return None
    
    def get_all_progress(self) -> List[ProgressRecord]:
        """获取所有学习进度
        
        Returns:
            ProgressRecord列表
        """
        try:
            cursor = self.conn.execute("SELECT * FROM progress ORDER BY day")
            rows = cursor.fetchall()
            
            progress_list = []
            for row in rows:
                progress_list.append(ProgressRecord(
                    id=row["id"],
                    day=row["day"],
                    score=row["score"],
                    test_result=json.loads(row["test_result"]),
                    ai_review=json.loads(row["ai_review"]),
                    timestamp=row["timestamp"]
                ))
            return progress_list
        except sqlite3.Error as e:
            print(f"获取所有进度失败: {e}")
            return []
    
    def update_progress_score(self, day: int, score: float) -> bool:
        """更新指定天的分数
        
        Args:
            day: 天数
            score: 新分数
            
        Returns:
            是否更新成功
        """
        try:
            self.conn.execute(
                "UPDATE progress SET score = ? WHERE day = ?",
                (score, day)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"更新分数失败: {e}")
            return False
    
    def delete_progress(self, day: int) -> bool:
        """删除指定天的进度
        
        Args:
            day: 天数
            
        Returns:
            是否删除成功
        """
        try:
            self.conn.execute("DELETE FROM progress WHERE day = ?", (day,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"删除进度失败: {e}")
            return False
    
    # Submissions表操作
    
    def save_submission(self, submission: SubmissionRecord) -> int:
        """保存提交记录
        
        Args:
            submission: SubmissionRecord对象
            
        Returns:
            记录ID
        """
        try:
            cursor = self.conn.execute("""
                INSERT INTO submissions (day, file_path, commit_time, score)
                VALUES (?, ?, ?, ?)
            """, (
                submission.day,
                submission.file_path,
                submission.commit_time,
                submission.score
            ))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"保存提交记录失败: {e}")
            return -1
    
    def get_submissions_by_day(self, day: int) -> List[SubmissionRecord]:
        """获取指定天的所有提交记录
        
        Args:
            day: 天数
            
        Returns:
            SubmissionRecord列表
        """
        try:
            cursor = self.conn.execute(
                "SELECT * FROM submissions WHERE day = ? ORDER BY commit_time DESC",
                (day,)
            )
            rows = cursor.fetchall()
            
            submissions = []
            for row in rows:
                submissions.append(SubmissionRecord(
                    id=row["id"],
                    day=row["day"],
                    file_path=row["file_path"],
                    commit_time=row["commit_time"],
                    score=row["score"]
                ))
            return submissions
        except sqlite3.Error as e:
            print(f"获取提交记录失败: {e}")
            return []
    
    def get_latest_submission(self, day: int) -> Optional[SubmissionRecord]:
        """获取指定天的最新提交记录
        
        Args:
            day: 天数
            
        Returns:
            SubmissionRecord对象
        """
        try:
            cursor = self.conn.execute(
                "SELECT * FROM submissions WHERE day = ? ORDER BY commit_time DESC LIMIT 1",
                (day,)
            )
            row = cursor.fetchone()
            
            if row:
                return SubmissionRecord(
                    id=row["id"],
                    day=row["day"],
                    file_path=row["file_path"],
                    commit_time=row["commit_time"],
                    score=row["score"]
                )
            return None
        except sqlite3.Error as e:
            print(f"获取最新提交记录失败: {e}")
            return None
    
    def get_total_submissions(self) -> int:
        """获取总提交次数"""
        try:
            cursor = self.conn.execute("SELECT COUNT(*) as count FROM submissions")
            row = cursor.fetchone()
            return row["count"] if row else 0
        except sqlite3.Error as e:
            print(f"获取总提交次数失败: {e}")
            return 0
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 总完成天数
            cursor = self.conn.execute("SELECT COUNT(DISTINCT day) as completed_days FROM progress")
            completed_days = cursor.fetchone()["completed_days"]
            
            # 平均分
            cursor = self.conn.execute("SELECT AVG(score) as avg_score FROM progress")
            avg_score = cursor.fetchone()["avg_score"] or 0.0
            
            # 最高分
            cursor = self.conn.execute("SELECT MAX(score) as max_score FROM progress")
            max_score = cursor.fetchone()["max_score"] or 0.0
            
            # 总提交次数
            total_submissions = self.get_total_submissions()
            
            return {
                "completed_days": completed_days,
                "total_days": 40,
                "completion_rate": completed_days / 40 * 100,
                "average_score": round(avg_score, 2),
                "max_score": round(max_score, 2),
                "total_submissions": total_submissions
            }
        except sqlite3.Error as e:
            print(f"获取统计信息失败: {e}")
            return {}
    
    # Review History表操作
    
    def save_review_history(self, day: int, code_snippet: str, review_result: Dict[str, Any]) -> int:
        """保存AI审查历史
        
        Args:
            day: 天数
            code_snippet: 代码片段（前500字符）
            review_result: 审查结果JSON
            
        Returns:
            记录ID
        """
        try:
            cursor = self.conn.execute("""
                INSERT INTO review_history (day, code_snippet, review_result, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                day,
                code_snippet,
                json.dumps(review_result),
                datetime.now().isoformat()
            ))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"保存审查历史失败: {e}")
            return -1
    
    def get_review_history(self, day: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """获取AI审查历史
        
        Args:
            day: 指定天数（None则获取所有）
            limit: 返回数量限制
            
        Returns:
            审查历史列表
        """
        try:
            if day is not None:
                cursor = self.conn.execute(
                    "SELECT * FROM review_history WHERE day = ? ORDER BY timestamp DESC LIMIT ?",
                    (day, limit)
                )
            else:
                cursor = self.conn.execute(
                    "SELECT * FROM review_history ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
            
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "day": row["day"],
                    "code_snippet": row["code_snippet"],
                    "review_result": json.loads(row["review_result"]),
                    "timestamp": row["timestamp"]
                }
                for row in rows
            ]
        except sqlite3.Error as e:
            print(f"获取审查历史失败: {e}")
            return []
    
    # Submission History表操作
    
    def save_submission_history(self, record: 'LearningRecord') -> int:
        """保存提交历史记录
        
        Args:
            record: LearningRecord对象
            
        Returns:
            记录ID
        """
        try:
            cursor = self.conn.execute("""
                INSERT INTO submission_history 
                (day, task_id, code_path, test_score, ai_score, final_score, created_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record.day,
                record.task_id,
                record.submission_path,
                record.test_score,
                record.ai_score,
                record.final_score,
                record.timestamp
            ))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"保存提交历史失败: {e}")
            return -1
    
    def get_submission_history(self, day: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取提交历史
        
        Args:
            day: 指定天数（None则获取所有）
            limit: 返回数量限制
            
        Returns:
            提交历史列表
        """
        try:
            if day is not None:
                cursor = self.conn.execute(
                    "SELECT * FROM submission_history WHERE day = ? ORDER BY created_time DESC LIMIT ?",
                    (day, limit)
                )
            else:
                cursor = self.conn.execute(
                    "SELECT * FROM submission_history ORDER BY created_time DESC LIMIT ?",
                    (limit,)
                )
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "day": row["day"],
                    "task_id": row["task_id"],
                    "code_path": row["code_path"],
                    "test_score": row["test_score"],
                    "ai_score": row["ai_score"],
                    "final_score": row["final_score"],
                    "created_time": row["created_time"]
                }
                for row in rows
            ]
        except sqlite3.Error as e:
            print(f"获取提交历史失败: {e}")
            return []
    
    def get_submission_count(self, day: Optional[int] = None) -> int:
        """获取提交次数"""
        try:
            if day is not None:
                cursor = self.conn.execute(
                    "SELECT COUNT(*) as count FROM submission_history WHERE day = ?",
                    (day,)
                )
            else:
                cursor = self.conn.execute("SELECT COUNT(*) as count FROM submission_history")
            row = cursor.fetchone()
            return row["count"] if row else 0
        except sqlite3.Error as e:
            print(f"获取提交次数失败: {e}")
            return 0
    
    def get_average_score(self) -> float:
        """获取平均分"""
        try:
            cursor = self.conn.execute("SELECT AVG(final_score) as avg_score FROM submission_history")
            row = cursor.fetchone()
            return round(row["avg_score"] or 0.0, 2)
        except sqlite3.Error as e:
            print(f"获取平均分失败: {e}")
            return 0.0
    
    def get_error_statistics(self) -> Dict[str, int]:
        """获取错误统计（从review_history中提取knowledge_gaps）"""
        try:
            cursor = self.conn.execute(
                "SELECT review_result FROM review_history ORDER BY timestamp DESC LIMIT 100"
            )
            rows = cursor.fetchall()
            error_stats = {}
            for row in rows:
                try:
                    review = json.loads(row["review_result"])
                    for gap in review.get("knowledge_gaps", []):
                        error_stats[gap] = error_stats.get(gap, 0) + 1
                except (json.JSONDecodeError, AttributeError):
                    continue
            return error_stats
        except sqlite3.Error as e:
            print(f"获取错误统计失败: {e}")
            return {}