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
    """SQLite数据库管理类"""
    
    def __init__(self, db_path: str = "data/progress.db"):
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
                review_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            )
        """)
        
        # 创建submission_history表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS submission_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day INTEGER NOT NULL,
                task_id TEXT DEFAULT '',
                submission_path TEXT NOT NULL,
                test_score REAL DEFAULT 0.0,
                ai_score REAL,
                final_score REAL DEFAULT 0.0,
                errors_json TEXT DEFAULT '[]',
                knowledge_gaps_json TEXT DEFAULT '[]',
                suggestions_json TEXT DEFAULT '[]',
                timestamp TEXT NOT NULL
            )
        """)
        
        self.conn.commit()
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ========== Progress表操作 ==========
    
    def save_progress(self, progress: ProgressRecord) -> int:
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
        try:
            cursor = self.conn.execute("SELECT * FROM progress WHERE day = ?", (day,))
            row = cursor.fetchone()
            if row:
                return ProgressRecord(
                    id=row["id"], day=row["day"], score=row["score"],
                    test_result=json.loads(row["test_result"]),
                    ai_review=json.loads(row["ai_review"]),
                    timestamp=row["timestamp"]
                )
            return None
        except sqlite3.Error as e:
            print(f"获取进度失败: {e}")
            return None
    
    def get_all_progress(self) -> List[ProgressRecord]:
        try:
            cursor = self.conn.execute("SELECT * FROM progress ORDER BY day")
            rows = cursor.fetchall()
            return [
                ProgressRecord(
                    id=row["id"], day=row["day"], score=row["score"],
                    test_result=json.loads(row["test_result"]),
                    ai_review=json.loads(row["ai_review"]),
                    timestamp=row["timestamp"]
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            print(f"获取所有进度失败: {e}")
            return []
    
    def update_progress_score(self, day: int, score: float) -> bool:
        try:
            self.conn.execute("UPDATE progress SET score = ? WHERE day = ?", (score, day))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"更新分数失败: {e}")
            return False
    
    def delete_progress(self, day: int) -> bool:
        try:
            self.conn.execute("DELETE FROM progress WHERE day = ?", (day,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"删除进度失败: {e}")
            return False
    
    # ========== Submissions表操作 ==========
    
    def save_submission(self, submission: SubmissionRecord) -> int:
        try:
            cursor = self.conn.execute("""
                INSERT INTO submissions (day, file_path, commit_time, score)
                VALUES (?, ?, ?, ?)
            """, (submission.day, submission.file_path, submission.commit_time, submission.score))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"保存提交记录失败: {e}")
            return -1
    
    def get_submissions_by_day(self, day: int) -> List[SubmissionRecord]:
        try:
            cursor = self.conn.execute(
                "SELECT * FROM submissions WHERE day = ? ORDER BY commit_time DESC", (day,)
            )
            return [
                SubmissionRecord(
                    id=row["id"], day=row["day"], file_path=row["file_path"],
                    commit_time=row["commit_time"], score=row["score"]
                )
                for row in cursor.fetchall()
            ]
        except sqlite3.Error as e:
            print(f"获取提交记录失败: {e}")
            return []
    
    def get_latest_submission(self, day: int) -> Optional[SubmissionRecord]:
        try:
            cursor = self.conn.execute(
                "SELECT * FROM submissions WHERE day = ? ORDER BY commit_time DESC LIMIT 1", (day,)
            )
            row = cursor.fetchone()
            if row:
                return SubmissionRecord(
                    id=row["id"], day=row["day"], file_path=row["file_path"],
                    commit_time=row["commit_time"], score=row["score"]
                )
            return None
        except sqlite3.Error as e:
            print(f"获取最新提交记录失败: {e}")
            return None
    
    def get_total_submissions(self) -> int:
        try:
            cursor = self.conn.execute("SELECT COUNT(*) as count FROM submissions")
            row = cursor.fetchone()
            return row["count"] if row else 0
        except sqlite3.Error as e:
            print(f"获取总提交次数失败: {e}")
            return 0
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计信息
        
        P0-2语义修正:
        - attempted_days: progress中出现过的day数量（含0分提交）
        - completed_days: score >= 60 的day数量
        - total_submissions: 以submission_history为唯一事实来源
        """
        try:
            cursor = self.conn.execute(
                "SELECT COUNT(DISTINCT day) as attempted FROM progress"
            )
            attempted_days = cursor.fetchone()["attempted"]
            
            cursor = self.conn.execute(
                "SELECT COUNT(DISTINCT day) as completed FROM progress "
                "WHERE score >= 60"
            )
            completed_days = cursor.fetchone()["completed"]
            
            cursor = self.conn.execute("SELECT AVG(score) as avg_score FROM progress")
            avg_score = cursor.fetchone()["avg_score"] or 0.0
            
            cursor = self.conn.execute("SELECT MAX(score) as max_score FROM progress")
            max_score = cursor.fetchone()["max_score"] or 0.0
            
            # 真实attempt history唯一事实来源：submission_history
            total_submissions = self.get_submission_count()
            
            return {
                "attempted_days": attempted_days,
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
    
    # ========== Review History表操作 ==========
    
    def save_review_history(self, day: int, code_snippet: str, review_result: Dict[str, Any]) -> int:
        try:
            cursor = self.conn.execute("""
                INSERT INTO review_history (day, code_snippet, review_json, created_at)
                VALUES (?, ?, ?, ?)
            """, (day, code_snippet, json.dumps(review_result, ensure_ascii=False), datetime.now().isoformat()))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"保存审查历史失败: {e}")
            return -1
    
    def get_review_history(self, day: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            if day is not None:
                cursor = self.conn.execute(
                    "SELECT * FROM review_history WHERE day = ? ORDER BY created_at DESC LIMIT ?",
                    (day, limit)
                )
            else:
                cursor = self.conn.execute(
                    "SELECT * FROM review_history ORDER BY created_at DESC LIMIT ?", (limit,)
                )
            return [
                {
                    "id": row["id"],
                    "day": row["day"],
                    "code_snippet": row["code_snippet"],
                    "review_result": json.loads(row["review_json"]),
                    "timestamp": row["created_at"]
                }
                for row in cursor.fetchall()
            ]
        except sqlite3.Error as e:
            print(f"获取审查历史失败: {e}")
            return []
    
    # ========== Submission History表操作 ==========
    
    def save_submission_history(self, record) -> int:
        """保存LearningRecord到submission_history"""
        try:
            cursor = self.conn.execute("""
                INSERT INTO submission_history 
                (day, task_id, submission_path, test_score, ai_score, final_score,
                 errors_json, knowledge_gaps_json, suggestions_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.day,
                record.task_id,
                record.submission_path,
                record.test_score,
                record.ai_score,
                record.final_score,
                json.dumps(record.errors, ensure_ascii=False),
                json.dumps(record.knowledge_gaps, ensure_ascii=False),
                json.dumps(record.suggestions, ensure_ascii=False),
                record.timestamp
            ))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"保存提交历史失败: {e}")
            return -1
    
    def get_submission_history(self, day: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            if day is not None:
                cursor = self.conn.execute(
                    "SELECT * FROM submission_history WHERE day = ? ORDER BY timestamp DESC LIMIT ?",
                    (day, limit)
                )
            else:
                cursor = self.conn.execute(
                    "SELECT * FROM submission_history ORDER BY timestamp DESC LIMIT ?", (limit,)
                )
            return [
                {
                    "id": row["id"],
                    "day": row["day"],
                    "task_id": row["task_id"],
                    "submission_path": row["submission_path"],
                    "test_score": row["test_score"],
                    "ai_score": row["ai_score"],
                    "final_score": row["final_score"],
                    "errors": json.loads(row["errors_json"]),
                    "knowledge_gaps": json.loads(row["knowledge_gaps_json"]),
                    "suggestions": json.loads(row["suggestions_json"]),
                    "timestamp": row["timestamp"]
                }
                for row in cursor.fetchall()
            ]
        except sqlite3.Error as e:
            print(f"获取提交历史失败: {e}")
            return []
    
    def get_submission_count(self, day: Optional[int] = None) -> int:
        """获取提交次数 - 兼容旧调用"""
        try:
            if day is not None:
                cursor = self.conn.execute(
                    "SELECT COUNT(*) as count FROM submission_history WHERE day = ?", (day,)
                )
            else:
                cursor = self.conn.execute("SELECT COUNT(*) as count FROM submission_history")
            row = cursor.fetchone()
            return row["count"] if row else 0
        except sqlite3.Error as e:
            print(f"获取提交次数失败: {e}")
            return 0
    
    def get_average_score(self) -> float:
        try:
            cursor = self.conn.execute("SELECT AVG(final_score) as avg_score FROM submission_history")
            row = cursor.fetchone()
            return round(row["avg_score"] or 0.0, 2)
        except sqlite3.Error as e:
            print(f"获取平均分失败: {e}")
            return 0.0
    
    def get_score_history(self, limit: int = 10) -> List[float]:
        try:
            cursor = self.conn.execute(
                "SELECT final_score FROM submission_history ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
            return [row["final_score"] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"获取分数历史失败: {e}")
            return []
    
    def get_error_statistics(self) -> Dict[str, int]:
        """从submission_history的errors_json中统计客观错误类型"""
        try:
            cursor = self.conn.execute(
                "SELECT errors_json FROM submission_history ORDER BY timestamp DESC LIMIT 100"
            )
            stats = {}
            for row in cursor.fetchall():
                try:
                    errors = json.loads(row["errors_json"])
                    for err in errors:
                        err_type = err.get("error_type", "Unknown")
                        stats[err_type] = stats.get(err_type, 0) + 1
                except (json.JSONDecodeError, AttributeError):
                    continue
            return stats
        except sqlite3.Error as e:
            print(f"获取错误统计失败: {e}")
            return {}
    
    def get_knowledge_gap_statistics(self) -> Dict[str, int]:
        """从review_history的review_json中统计AI判断的知识漏洞"""
        try:
            cursor = self.conn.execute(
                "SELECT review_json FROM review_history ORDER BY created_at DESC LIMIT 100"
            )
            stats = {}
            for row in cursor.fetchall():
                try:
                    review = json.loads(row["review_json"])
                    for gap in review.get("knowledge_gaps", []):
                        stats[gap] = stats.get(gap, 0) + 1
                except (json.JSONDecodeError, AttributeError):
                    continue
            return stats
        except sqlite3.Error as e:
            print(f"获取知识漏洞统计失败: {e}")
            return {}
    
    def get_recent_strengths(self, limit: int = 5) -> List[str]:
        try:
            cursor = self.conn.execute(
                "SELECT review_json FROM review_history ORDER BY created_at DESC LIMIT ?", (limit,)
            )
            strengths = []
            for row in cursor.fetchall():
                try:
                    review = json.loads(row["review_json"])
                    strengths.extend(review.get("strengths", []))
                except (json.JSONDecodeError, AttributeError):
                    continue
            seen = set()
            unique = []
            for s in strengths:
                if s not in seen:
                    seen.add(s)
                    unique.append(s)
            return unique[:10]
        except sqlite3.Error as e:
            print(f"获取strengths失败: {e}")
            return []
    
    def update_profile(self) -> Dict[str, Any]:
        """根据历史记录更新学生画像"""
        total = self.get_submission_count()
        avg_score = self.get_average_score()
        error_stats = self.get_error_statistics()
        knowledge_gap_stats = self.get_knowledge_gap_statistics()
        score_history = self.get_score_history(limit=10)
        recent_strengths = self.get_recent_strengths()
        
        # 计算趋势
        trend = "stable"
        if len(score_history) >= 3:
            recent = score_history[:3]
            older = score_history[3:6] if len(score_history) >= 6 else score_history[3:]
            if older:
                recent_avg = sum(recent) / len(recent)
                older_avg = sum(older) / len(older)
                if recent_avg > older_avg + 5:
                    trend = "improving"
                elif recent_avg < older_avg - 5:
                    trend = "declining"
        
        # 综合薄弱点（结合error_statistics和knowledge_gap_statistics）
        weaknesses = []
        for error_type, count in sorted(error_stats.items(), key=lambda x: -x[1]):
            if count >= 2:
                weaknesses.append(f"{error_type} ({count}次)")
        for gap, count in sorted(knowledge_gap_stats.items(), key=lambda x: -x[1]):
            if count >= 2:
                weaknesses.append(f"{gap} ({count}次)")
        
        return {
            "total_submissions": total,
            "average_score": avg_score,
            "error_statistics": error_stats,
            "knowledge_gap_statistics": knowledge_gap_stats,
            "weaknesses": weaknesses,
            "strengths": recent_strengths,
            "trend": trend
        }
