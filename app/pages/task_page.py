# -*- coding: utf-8 -*-
"""今日学习页：替代 `python main.py task N`；内嵌分级Hint（默认隐藏高级提示）"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton,
                               QTextBrowser, QVBoxLayout, QWidget)


class TaskPage(QWidget):
    submit_requested = Signal(int)   # [开始学习] → 跳转提交页

    def __init__(self, platform, parent=None):
        super().__init__(parent)
        self.platform = platform
        self.day = platform.current_day
        self._task = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)

        top = QHBoxLayout()
        self.lbl_title = QLabel("今日学习")
        self.lbl_title.setObjectName("H1")
        top.addWidget(self.lbl_title)
        top.addStretch(1)

        self.btn_study = QPushButton("[开始学习] → 提交代码")
        self.btn_study.clicked.connect(self._on_study)
        top.addWidget(self.btn_study)
        root.addLayout(top)

        self.view = QTextBrowser(self)
        self.view.setOpenExternalLinks(True)
        root.addWidget(self.view, 3)

        # Hint 区：默认只开放 Level 1，逐级解锁
        hint_bar = QHBoxLayout()
        self.btn_l1 = QPushButton("Level 1 方向提示")
        self.btn_l2 = QPushButton("Level 2 实现思路")
        self.btn_l3 = QPushButton("Level 3 伪代码")
        for i, b in enumerate((self.btn_l1, self.btn_l2, self.btn_l3), start=1):
            b.clicked.connect(lambda _=False, lv=i: self.show_level(lv))
            hint_bar.addWidget(b)
        # 高级hint默认禁用（隐藏内容）
        self.btn_l2.setEnabled(False)
        self.btn_l3.setEnabled(False)
        hint_bar.addStretch(1)
        root.addLayout(hint_bar)

        self.hint_view = QTextBrowser(self)
        self.hint_view.setMaximumHeight(140)
        self.hint_view.setPlaceholderText("卡住了再点上方按钮按级查看提示；先自己想！")
        root.addWidget(self.hint_view, 1)

        self.set_day(self.day)

    def _on_study(self):
        self.submit_requested.emit(self.day)

    def set_day(self, day: int):
        self.day = day
        task = self.platform.get_task(day)
        self._task = task
        if not task:
            self.view.setPlainText(f"Day {day} 任务不存在")
            return

        prereq = "\n".join(f"  <li>{p}</li>" for p in (task.prerequisites or [])) \
            or "  <li>无——可直接开始</li>"
        api_html = ""
        for a in (task.required_api or []):
            api_html += (f"<p><code>{a.get('signature', '')}</code><br>"
                         f"<small>{a.get('description', '')}</small></p>")
        api_html = api_html or "<p><em>本日无独立接口契约</em></p>"
        mastery = "\n".join(f"  <li>{m}</li>" for m in (task.mastery or []))
        challenge = task.optional_challenge or "无"

        html = f"""
        <h1>Day {day}: {task.title}</h1>
        <p><b>Goal:</b> {task.goal} &nbsp;|&nbsp;
           <b>Estimated:</b> ~{task.estimated_minutes} min &nbsp;|&nbsp;
           <b>Difficulty:</b> {task.difficulty}/5</p>
        <h2>Prerequisites</h2>
        <ul>{prereq}</ul>
        <h2>Required API</h2>
        {api_html}
        <h2>Core Task</h2>
        <p>{task.core_task or task.task}</p>
        <h2>Mastery（掌握标准）</h2>
        <ul>{mastery}</ul>
        <h2>Optional Challenge（不影响当天通过）</h2>
        <p>{challenge}</p>
        """
        self.view.setHtml(html)

        # 重置提示解锁状态
        self.hint_view.clear()
        self.btn_l1.setEnabled(True)
        self.btn_l2.setEnabled(False)
        self.btn_l3.setEnabled(False)

    def show_level(self, level: int):
        """显示对应级别hint并解锁下一级（默认隐藏高级提示）"""
        if not self._task:
            return
        items = [h["content"] for h in (self._task.hint_levels or [])
                 if h.get("level") == level]
        if not items:
            self.hint_view.setPlainText(f"Day {self.day} 暂无 Level {level} 提示")
        else:
            body = "<br>".join(f"• {c}" for c in items)
            self.hint_view.setHtml(f"<b>[Level {level}]</b><br>{body}")
        # 解锁链: 看过L1才开L2, 看过L2才开L3
        if level == 1:
            self.btn_l2.setEnabled(True)
        elif level == 2:
            self.btn_l3.setEnabled(True)
