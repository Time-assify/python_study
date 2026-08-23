# -*- coding: utf-8 -*-
"""合成任务正确实现（pipeline集成测试专用，与正式课程无关）"""
import re


def safe_divide(a, b):
    if b == 0:
        raise ZeroDivisionError("除数不能为0")
    return a / b


_WS_RE = re.compile(r"\s+")


def normalize_name(s):
    collapsed = _WS_RE.sub(" ", s.strip())
    return " ".join(w.capitalize() for w in collapsed.split(" ")) if collapsed else ""


class Accumulator:
    def __init__(self):
        self._total = 0.0

    def add(self, x):
        self._total += x
        return self._total

    def total(self):
        return self._total

    def reset(self):
        self._total = 0.0
