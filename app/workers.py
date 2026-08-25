# -*- coding: utf-8 -*-
"""后台线程：把耗时的评估流水线移出UI线程（不改动平台核心逻辑）"""
from pathlib import Path

from PySide6.QtCore import QThread, Signal


class EvaluationWorker(QThread):
    """调用现有 evaluate_submission 流水线；结果通过信号回传UI线程"""

    finished_ok = Signal(object)   # EvaluationResult
    failed = Signal(str)

    def __init__(self, platform, day: int, answer_path: str, parent=None):
        super().__init__(parent)
        self._platform = platform
        self._day = day
        self._path = answer_path

    def run(self):
        try:
            result = self._platform.evaluate_submission(self._day, Path(self._path))
            self.finished_ok.emit(result)
        except Exception as e:  # 任何异常都不允许击穿UI
            self.failed.emit(str(e))
