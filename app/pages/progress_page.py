# -*- coding: utf-8 -*-
"""学习记录页：替代 `python main.py progress`；含知识点掌握情况"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)


class ProgressPage(QWidget):
    def __init__(self, platform, parent=None):
        super().__init__(parent)
        self.platform = platform

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)

        title = QLabel("学习记录")
        title.setObjectName("H1")
        root.addWidget(title)

        stats_card = QFrame()
        stats_card.setFrameShape(QFrame.StyledPanel)
        stats_card.setObjectName("Card")
        g = QGridLayout(stats_card)
        g.setContentsMargins(16, 16, 16, 16)
        self.lbl_completed = QLabel("Completed Days: -")
        self.lbl_attempted = QLabel("Attempted Days: -")
        self.lbl_avg = QLabel("Average Score: -")
        self.lbl_subs = QLabel("Total Submissions: -")
        for i, w in enumerate((self.lbl_completed, self.lbl_attempted,
                               self.lbl_avg, self.lbl_subs)):
            g.addWidget(w, i // 2, i % 2)
        root.addWidget(stats_card)

        # 每日成绩
        lbl_days = QLabel("每日成绩")
        lbl_days.setObjectName("H2")
        root.addWidget(lbl_days)
        self.table_days = QTableWidget(0, 3)
        self.table_days.setHorizontalHeaderLabels(["Day", "Score", "Status"])
        self.table_days.horizontalHeader().setStretchLastSection(True)
        self.table_days.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table_days, 2)

        # 知识点掌握情况（缺口计数，越少越掌握）
        lbl_kp = QLabel("知识掌握情况（knowledge_points 缺口统计）")
        lbl_kp.setObjectName("H2")
        root.addWidget(lbl_kp)
        self.table_gaps = QTableWidget(0, 3)
        self.table_gaps.setHorizontalHeaderLabels(
            ["Knowledge Point", "Skill", "累计失败次数"])
        self.table_gaps.horizontalHeader().setStretchLastSection(True)
        self.table_gaps.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table_gaps, 2)

        self.refresh()

    def refresh(self):
        stats = self.platform.get_statistics() or {}
        self.lbl_completed.setText(
            f"Completed Days: {stats.get('completed_days', 0)}/40")
        self.lbl_attempted.setText(
            f"Attempted Days: {stats.get('attempted_days', 0)}/40")
        self.lbl_avg.setText(f"Average Score: {stats.get('average_score', 0):.1f}")
        self.lbl_subs.setText(
            f"Total Submissions: {stats.get('total_submissions', 0)}")

        rows = self.platform.get_all_progress() or []
        self.table_days.setRowCount(len(rows))
        for i, p in enumerate(rows):
            status = "PASS" if p.score >= 60 else "FAIL"
            for col, val in enumerate((str(p.day), f"{p.score:.1f}", status)):
                item = QTableWidgetItem(val)
                if col == 2:
                    fg = Qt.darkGreen if status == "PASS" else Qt.darkRed
                    item.setForeground(fg)
                self.table_days.setItem(i, col, item)

        try:
            gaps = self.platform.database.get_knowledge_gap_records(limit=20) or []
        except Exception:
            gaps = []
        self.table_gaps.setRowCount(len(gaps))
        for i, g in enumerate(gaps):
            kp = g.get("knowledge_point") or {}
            for col, val in enumerate((
                    kp.get("name", ""), g.get("skill", ""),
                    str(g.get("count", 0)))):
                self.table_gaps.setItem(i, col, QTableWidgetItem(val))
