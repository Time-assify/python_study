# -*- coding: utf-8 -*-
"""合成任务的缺陷实现（用于验证TestEngine能区分good/bad，与正式课程无关）"""
import re


def safe_divide(a, b):
    if b == 0:
        return None  # BUG: 应抛ZeroDivisionError
    return a // b  # BUG: 整除而非真除


_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")  # BUG: 丢失负号


def parse_numbers(text):
    return [float(m) for m in _NUMBER_RE.findall(text)]


class Accumulator:
    def __init__(self):
        self._total = 0.0

    def add(self, x):
        self._total = x  # BUG: 覆盖而非累加
        return self._total

    def total(self):
        return self._total

    def reset(self):
        pass  # BUG: 未清零
