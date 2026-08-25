# -*- coding: utf-8 -*-
"""主窗口：侧边导航 + 页面栈。仅调用既有平台能力，不含业务逻辑。"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QMainWindow, QPushButton,
                               QStackedWidget, QVBoxLayout, QWidget)

from app.pages.dashboard import DashboardPage
from app.pages.progress_page import ProgressPage
from app.pages.submit_page import SubmitPage
from app.pages.task_page import TaskPage

PAGE_TITLES = ["首页", "今日学习", "提交代码", "学习记录"]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        from src.core.platform import TrainingPlatform  # 延迟导入：CLI核心不动
        self.platform = TrainingPlatform()

        self.setWindowTitle("Python Study — AI Engineer Training")
        self.resize(1024, 720)

        central = QWidget()
        layout = QHBoxLayout(central)

        # 侧边栏
        side = QVBoxLayout()
        brand = QLabel("Python Study")
        brand.setObjectName("Brand")
        side.addWidget(brand)

        self.nav = QListWidget()
        for t in PAGE_TITLES:
            QListWidgetItem(t, self.nav)
        self.nav.setFixedWidth(140)
        self.nav.currentRowChanged.connect(self._switch)
        side.addWidget(self.nav, 1)

        btn_day = QPushButton("设置今日 Day…")
        btn_day.clicked.connect(self._ask_day)
        side.addWidget(btn_day)
        layout.addLayout(side)

        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        layout.addWidget(line)

        # 页面栈
        self.stack = QStackedWidget()
        self.page_dashboard = DashboardPage(self.platform)
        self.page_task = TaskPage(self.platform)
        self.page_submit = SubmitPage(self.platform)
        self.page_progress = ProgressPage(self.platform)
        for w in (self.page_dashboard, self.page_task,
                  self.page_submit, self.page_progress):
            self.stack.addWidget(w)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        # 联动：任务页[开始学习] → 提交页并带入Day
        self.page_task.submit_requested.connect(self.goto_submit)
        self.nav.setCurrentRow(0)
        self.page_dashboard.refresh()

    # ---- 导航 ----
    def _switch(self, row: int):
        self.stack.setCurrentIndex(row)
        if row == 0:
            self.page_dashboard.refresh()
        elif row == 3:
            self.page_progress.refresh()

    def goto_task(self, day: int):
        self.page_task.set_day(day)
        self.nav.setCurrentRow(1)

    def goto_submit(self, day: int):
        self.page_submit.set_day(day)
        self.nav.setCurrentRow(2)

    def _ask_day(self):
        from PySide6.QtWidgets import QInputDialog
        day, ok = QInputDialog.getInt(
            self, "设置今日任务", "Day (1-40):",
            self.platform.current_day, 1, 40)
        if ok:
            self.platform.current_day = day
            self.page_dashboard.set_day(day)
            self.page_task.set_day(day)
            self.page_submit.set_day(day)
