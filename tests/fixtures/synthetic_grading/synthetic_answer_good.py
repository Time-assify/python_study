# -*- coding: utf-8 -*-
"""合成任务的正确实现（仅用于验证TestEngine判题链路，与正式课程无关）"""
import re


def safe_divide(a, b):
    if b == 0:
        raise ZeroDivisionError("除数不能为0")
    return a / b


_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def parse_numbers(text):
    return [float(m) for m in _NUMBER_RE.findall(text)]


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
