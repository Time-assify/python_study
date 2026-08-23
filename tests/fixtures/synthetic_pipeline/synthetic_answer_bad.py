# -*- coding: utf-8 -*-
"""合成任务缺陷实现（pipeline集成测试专用，与正式课程无关）"""
import re


def safe_divide(a, b):
    if b == 0:
        return None  # BUG: 应抛ZeroDivisionError
    return a // b  # BUG: 整除


def normalize_name(s):  # BUG: 未折叠空格、未大小写规范化
    return s.strip()


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
