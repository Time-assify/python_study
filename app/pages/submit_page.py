# -*- coding: utf-8 -*-
"""提交代码页：替代 `python main.py submit N`；后台线程跑评估流水线"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFileDialog, QFrame, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QSpinBox, QTextBrowser,
                               QVBoxLayout, QWidget)

from app.workers import EvaluationWorker


class SubmitPage(QWidget):
    def __init__(self, platform, parent=None):
        super().__init__(parent)
        self.platform = platform
        self.day = platform.current_day
        self._worker = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)

        title = QLabel("提交代码")
        title.setObjectName("H1")
        root.addWidget(title)

        # 打包(exe)环境下诚实提示：完整评测链路建议源码方式运行
        if getattr(sys, "frozen", False):
            tip = QLabel("⚠ 打包运行提示：exe内评测子进程受限于冻结环境，"
                         "如遇评分异常请用源码方式运行（pip install -r "
                         "requirements*.txt 后 python run_app.py）。详见 build_app.md")
            tip.setWordWrap(True)
            tip.setStyleSheet("color: #b45309;")
            root.addWidget(tip)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Day:"))
        self.spin_day = QSpinBox()
        self.spin_day.setRange(1, 40)
        self.spin_day.setValue(self.day)
        bar.addWidget(self.spin_day)
        self.edit_path = QLineEdit()
        self.edit_path.setPlaceholderText("选择你的 answer.py …")
        bar.addWidget(self.edit_path, 1)
        btn_browse = QPushButton("浏览…")
        btn_browse.clicked.connect(self._browse)
        bar.addWidget(btn_browse)
        self.btn_submit = QPushButton("提交")
        self.btn_submit.clicked.connect(self._submit)
        bar.addWidget(self.btn_submit)
        root.addLayout(bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        root.addWidget(self.lbl_status)

        # 分数卡片
        score_card = QFrame()
        score_card.setFrameShape(QFrame.StyledPanel)
        score_card.setObjectName("Card")
        s = QHBoxLayout(score_card)
        s.setContentsMargins(16, 12, 16, 12)
        self.lbl_test = QLabel("Test Score: -")
        self.lbl_ai = QLabel("AI Score: -")
        self.lbl_final = QLabel("Final Score: -")
        for w in (self.lbl_test, self.lbl_ai, self.lbl_final):
            s.addWidget(w)
        root.addWidget(score_card)

        self.feedback = QTextBrowser(self)
        self.feedback.setPlaceholderText(
            "提交后这里显示 AI Feedback:\nStrengths / Issues / Knowledge Gaps / Next Learning")
        root.addWidget(self.feedback, 1)

    def set_day(self, day: int):
        self.day = day
        self.spin_day.setValue(day)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 answer.py", "",
                                              "Python Files (*.py)")
        if path:
            self.edit_path.setText(path)

    def _submit(self):
        if self._worker is not None and self._worker.isRunning():
            return
        path = self.edit_path.text().strip()
        if not path:
            self.lbl_status.setText("请先选择 answer.py 文件")
            return
        self.day = int(self.spin_day.value())
        self.btn_submit.setEnabled(False)
        self.lbl_status.setText(f"评测中… Day {self.day}（pytest运行约需数秒，请稍候）")
        self._worker = EvaluationWorker(self.platform, self.day, path)
        self._worker.finished_ok.connect(self._on_result)
        self._worker.failed.connect(self._on_error)
        self._worker.start()

    def _on_result(self, result):
        self.btn_submit.setEnabled(True)
        self.lbl_status.setText("评测完成 ✓")
        self.lbl_test.setText(f"Test Score: {result.test_score:.1f}")
        ai = "N/A" if result.ai_score is None else f"{result.ai_score:.1f}"
        self.lbl_ai.setText(f"AI Score: {ai}")
        self.lbl_final.setText(f"Final Score: {result.final_score:.1f}")

        review = result.ai_review or {}
        sections = [
            ("Strengths", review.get("strengths")),
            ("Issues", review.get("issues")),
            ("Knowledge Gaps", review.get("knowledge_gaps")),
            ("Improvement", review.get("improvement")),
            ("Next Learning", review.get("next_learning")),
        ]
        html = "<h2>AI Feedback</h2>"
        any_section = False
        for name, items in sections:
            html += f"<h3>{name}</h3>"
            if items:
                any_section = True
                html += "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
            else:
                html += "<p><em>-</em></p>"
        if not any_section:
            html += "<p><em>本次无AI反馈（AI不可用时仅按pytest评分）</em></p>"
        self.feedback.setHtml(html)
        self._worker = None

    def _on_error(self, message: str):
        self.btn_submit.setEnabled(True)
        self.lbl_status.setText(f"评测失败: {message}")
        self._worker = None
