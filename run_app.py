# -*- coding: utf-8 -*-
"""Python Study 桌面应用入口

用法:
    python run_app.py            # 启动GUI
    python run_app.py --check    # 无头自检(构建主窗口后立即退出, 用于CI/排障)
"""
import os
import sys

ROOT = str(__file__).rsplit(os.sep, 1)[0]
if ROOT and ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main(argv=None) -> int:
    argv = list(sys.argv if argv is None else argv)
    check_mode = "--check" in argv
    argv = [a for a in argv if a != "--check"]
    if check_mode:
        # offscreen必须在QApplication构造前设置
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("未检测到 PySide6。请先执行:")
        print("    pip install -r requirements-app.txt")
        return 1

    from app.main_window import MainWindow

    app = QApplication(argv)
    app.setApplicationName("PythonStudy")
    window = MainWindow()
    window.resize(1024, 720)

    if check_mode:
        # 构建成功即认为启动路径健康
        pages = window.stack.count()
        window.close()
        print(f"OK: MainWindow built with {pages} pages")
        return 0

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
