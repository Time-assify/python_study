# -*- coding: utf-8 -*-
"""桌面应用冒烟测试：无头(offscreen)构建MainWindow + CLI回归 + 入口自检"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6", reason="PySide6未安装(pip install -r requirements-app.txt)")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def window(qapp):
    from app.main_window import MainWindow
    w = MainWindow()
    yield w
    w.close()


def test_window_builds_with_four_pages(window):
    assert window.stack.count() == 4
    titles = [window.nav.item(i).text() for i in range(4)]
    assert titles == ["首页", "今日学习", "提交代码", "学习记录"]


def test_dashboard_populates(window):
    page = window.page_dashboard
    page.refresh()
    assert "Day" in page.lbl_day.text()
    assert "Completed" in page.lbl_completed.text()


def test_task_page_sections_and_no_test_leak(window):
    page = window.page_task
    page.set_day(1)
    text = page.view.toPlainText()
    for section in ("Goal:", "Prerequisites", "Required API",
                    "Core Task", "Mastery"):
        assert section in text, f"缺少区块: {section}"
    assert "test_" not in text, "GUI不得泄露测试函数名"
    assert "create_project_structure" in text


def test_hint_progressive_unlock(window):
    """默认隐藏高级hint：看过L1才解锁L2，看过L2才解锁L3"""
    page = window.page_task
    page.set_day(2)
    assert not page.btn_l2.isEnabled() and not page.btn_l3.isEnabled()
    page.show_level(1)
    assert page.btn_l2.isEnabled() and not page.btn_l3.isEnabled()
    page.show_level(2)
    assert page.btn_l3.isEnabled()
    assert "[Level 2]" in page.hint_view.toPlainText()


def test_progress_page_stats_tables(window):
    page = window.page_progress
    page.refresh()
    assert "Completed Days" in page.lbl_completed.text()
    assert page.table_gaps.columnCount() == 3
    assert page.table_days.columnCount() == 3


def test_submit_page_rejects_empty_path(window):
    page = window.page_submit
    page.edit_path.clear()
    page._submit()
    assert "请先选择" in page.lbl_status.text()


# ------------------------------------------------------------------
# 入口与CLI回归（子进程级验收）
# ------------------------------------------------------------------

def test_run_app_check_mode():
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    r = subprocess.run([sys.executable, str(ROOT / "run_app.py"), "--check"],
                       capture_output=True, env=env, cwd=str(ROOT), timeout=120)
    assert r.returncode == 0, r.stderr.decode(errors="ignore")
    assert b"OK" in r.stdout


def test_cli_still_works():
    """重要限制验收: GUI新增后原CLI不受影响"""
    r = subprocess.run([sys.executable, "-X", "utf8", "main.py", "task", "1"],
                       capture_output=True, cwd=str(ROOT), timeout=120)
    assert r.returncode == 0, r.stderr.decode(errors="ignore")
    assert "Day 1".encode("utf-8") in r.stdout or b"Day 1" in r.stdout
