# -*- coding: utf-8 -*-
"""首页 Dashboard：今日任务 + 总体进度 + 薄弱知识点"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QSizePolicy, QVBoxLayout, QWidget)


class DashboardPage(QWidget):
    def __init__(self, platform, parent=None):
        super().__init__(parent)
        self.platform = platform
        self.day = platform.current_day

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("Python Study — 学习首页")
        title.setObjectName("H1")
        root.addWidget(title)

        # 今日任务卡片
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setObjectName("Card")
        form = QGridLayout(card)
        form.setContentsMargins(16, 16, 16, 16)

        cap = QLabel("今日任务")
        cap.setObjectName("H2")
        form.addWidget(cap, 0, 0, 1, 2)

        self.lbl_day = QLabel("Day --")
        self.lbl_day.setObjectName("H1")
        form.addWidget(self.lbl_day, 1, 0)

        self.lbl_topic = QLabel("-")
        self.lbl_topic.setWordWrap(True)
        form.addWidget(self.lbl_topic, 1, 1)

        self.lbl_time = QLabel("预计时间: - min")
        form.addWidget(self.lbl_time, 2, 0)
        self.lbl_phase = QLabel("")
        form.addWidget(self.lbl_phase, 2, 1)

        self.btn_go_task = QPushButton("查看今日详情 →")
        self.btn_go_task.clicked.connect(self._go_task)
        form.addWidget(self.btn_go_task, 3, 0, 1, 2, Qt.AlignLeft)
        root.addWidget(card)

        # 进度统计卡片
        stats_card = QFrame()
        stats_card.setFrameShape(QFrame.StyledPanel)
        stats_card.setObjectName("Card")
        sform = QGridLayout(stats_card)
        sform.setContentsMargins(16, 16, 16, 16)
        cap2 = QLabel("学习进度")
        cap2.setObjectName("H2")
        sform.addWidget(cap2, 0, 0, 1, 2)

        self.lbl_completed = QLabel("Completed: -/40")
        self.lbl_attempted = QLabel("Attempted: -/40")
        self.lbl_avg = QLabel("平均分: -")
        for i, w in enumerate((self.lbl_completed, self.lbl_attempted, self.lbl_avg)):
            sform.addWidget(w, 1 + i // 2, i % 2)
        root.addWidget(stats_card)

        # 知识薄弱点
        weak_card = QFrame()
        weak_card.setFrameShape(QFrame.StyledPanel)
        weak_card.setObjectName("Card")
        wv = QVBoxLayout(weak_card)
        wv.setContentsMargins(16, 16, 16, 16)
        cap3 = QLabel("知识薄弱点 Top 5")
        cap3.setObjectName("H2")
        wv.addWidget(cap3)
        self.lbl_weak = QLabel("暂无数据——先完成几次提交吧")
        self.lbl_weak.setWordWrap(True)
        self.lbl_weak.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.lbl_weak.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        wv.addWidget(self.lbl_weak)
        root.addWidget(weak_card)

        root.addStretch(1)
        self.refresh()

    def _go_task(self):
        win = self.window()
        if hasattr(win, "goto_task"):
            win.goto_task(self.day)

    def set_day(self, day: int):
        self.day = day
        self.refresh()

    def refresh(self):
        task = self.platform.get_task(self.day)
        if task:
            phase = self.platform.helpers.get_phase_info(self.day)
            self.lbl_day.setText(f"Day {self.day}")
            self.lbl_topic.setText(f"{task.title}\n{task.goal}")
            self.lbl_time.setText(f"预计时间: ~{task.estimated_minutes} min "
                                  f"(难度 {task.difficulty}/5)")
            self.lbl_phase.setText(f"Phase: {phase['name']}")

        stats = self.platform.get_statistics() or {}
        self.lbl_completed.setText(
            f"Completed: {stats.get('completed_days', 0)}/40")
        self.lbl_attempted.setText(
            f"Attempted: {stats.get('attempted_days', 0)}/40")
        self.lbl_avg.setText(f"平均分: {stats.get('average_score', 0):.1f}")

        gaps = []
        try:
            gaps = self.platform.database.get_knowledge_gap_records(limit=5) or []
        except Exception:
            gaps = []
        if gaps:
            lines = [f"• {g['knowledge_point'].get('name', g['skill'])}"
                     f"（{g['skill']}，累计失败 {g['count']} 次）" for g in gaps]
            self.lbl_weak.setText("\n".join(lines))
        else:
            self.lbl_weak.setText("暂无数据——先完成几次提交吧")
