# -*- coding: utf-8 -*-
"""讲义生成入口

用法:
    python tools/textbook/generate.py           # 默认生成Part1预览
    python tools/textbook/generate.py --all     # 全部四部分(后续轮次逐步补齐)
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.textbook.build_docx import build_document  # noqa: E402
from tools.textbook.content_part1 import PART1  # noqa: E402

PARTS_READY = {"1": PART1}

OUT = ROOT / "docs" / "Python_Study_40_Days_Course_Textbook.docx"


def main():
    parser = argparse.ArgumentParser(description="生成课程讲义docx")
    parser.add_argument("--all", action="store_true", help="生成全部已完成的部分")
    args = parser.parse_args()

    if args.all:
        parts = [PARTS_READY[k] for k in sorted(PARTS_READY)]
    else:
        parts = [PART1]

    out = build_document(OUT, parts)
    print(f"generated: {out} ({out.stat().st_size / 1024:.0f} KB, "
          f"{sum(len(p['days']) for p in parts)} days)")
    if len(PARTS_READY) < 4:
        print("提示: 其余部分(2/3/4)内容将在后续轮次补齐后追加。")


if __name__ == "__main__":
    main()
