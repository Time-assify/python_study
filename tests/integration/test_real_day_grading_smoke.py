"""P1-1: 真实判题Smoke测试

GitHub Actions绿色不能证明 TestEngine + answer.py + dayXX_test.py 判题链路可用，
因为无answer时day测试会skip。

本文件为代表性Days（1/8/13/20/31/39/40）提供最小good/bad submission，
运行真实 TestEngine.run_submission()，验证:
- good.score > bad.score
- bad 至少有1个失败/错误测试

后续逐步扩展到全部40天。
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.evaluator.test_engine import TestEngine  # noqa: E402


GOOD_ANSWERS = {
    1: '''"""Day01 good"""
import logging
import os


def create_project_structure(project_name):
    dirs = {}
    root = os.path.abspath(project_name)
    dirs["root"] = root
    os.makedirs(root, exist_ok=True)
    for k in ("src", "tests", "configs", "data", "logs"):
        d = os.path.join(root, k)
        os.makedirs(d, exist_ok=True)
        dirs[k] = d
        if k == "src":
            open(os.path.join(d, "__init__.py"), "w", encoding="utf-8").close()
    return dirs


def create_config_file(config_path):
    with open(config_path, "w", encoding="utf-8") as f:
        f.write("project:\\n  name: ml-project\\nconfig:\\n  version: 1\\n")
    return True


def setup_logger(log_file, level=logging.INFO):
    lg = logging.getLogger("ml_platform_d01")
    lg.setLevel(level)
    lg.handlers.clear()
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    lg.addHandler(fh)
    return lg
''',
    8: '''"""Day08 good"""
import torch


def create_tensor(data):
    return torch.tensor(data, dtype=torch.float32)


def reshape_tensor(t, shape):
    return t.reshape(*shape)


def tensor_stats(t):
    t = torch.as_tensor(t, dtype=torch.float32)
    return float(t.mean()), float(t.std(unbiased=False))


def index_last(t):
    return t.reshape(-1)[-1]
''',
    13: '''"""Day13 good"""
import torch
import torch.nn as nn


class SimpleCNN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Linear(16 * 14 * 14, num_classes)

    def forward(self, x):
        x = self.features(x)
        return self.classifier(x.flatten(1))


def count_conv_layers(model):
    return sum(isinstance(m, nn.Conv2d) for m in model.modules())
''',
    20: '''"""Day20 good"""
import numpy as np
import torch
import torch.nn as nn


class CIFARNet(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        )
        self.classifier = nn.Linear(32 * 8 * 8, num_classes)

    def forward(self, x):
        return self.classifier(self.features(x).flatten(1))


def accuracy(outputs, labels):
    outputs = torch.as_tensor(outputs)
    labels = torch.as_tensor(labels)
    if outputs.shape[0] != labels.shape[0]:
        raise ValueError("outputs与labels长度不一致")
    preds = outputs.argmax(dim=-1)
    return (preds == labels).float().mean().item()


def confusion_matrix(preds, labels, num_classes):
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for p, l in zip(np.asarray(preds), np.asarray(labels)):
        cm[int(l), int(p)] += 1
    return cm
''',
    31: '''"""Day31 good - 全部mock，不访问真实API"""


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self, api_key=None, transport=None):
        self.api_key = api_key
        self.transport = transport

    def is_available(self):
        return self.api_key is not None

    def _ensure_ready(self):
        if not self.is_available():
            raise LLMError("未配置api_key")
        if self.transport is None:
            raise LLMError("未配置transport")

    def chat(self, messages, **kwargs):
        self._ensure_ready()
        chunks = list(self.transport(messages))
        return "".join(chunks)

    def chat_stream(self, messages):
        self._ensure_ready()
        yield from self.transport(messages)


def retry_call(fn, retries=2, exceptions=(Exception,)):
    attempt = 0
    while True:
        try:
            return fn()
        except exceptions:
            attempt += 1
            if attempt > retries:
                raise


def parse_response(text):
    start = text.find("{")
    end = text.rfind("}") + 1
    import json
    if start != -1 and end > start:
        return json.loads(text[start:end])
    return None


def chunk_text(text, max_chars):
    if max_chars < 1:
        raise ValueError("max_chars必须>=1")
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
''',
    39: '''"""Day39 good"""
import functools


class Pipeline:
    def __init__(self, steps):
        self.steps = list(steps)

    def run(self, x):
        for step in self.steps:
            x = step(x)
        return x


def retry_step(func=None, retries=2):
    """支持 @retry_step 与 @retry_step(retries=n)/retry_step(fn, retries=n)"""
    def decorate(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                try:
                    return fn(*args, **kwargs)
                except Exception:
                    attempt += 1
                    if attempt > retries:
                        raise
        return wrapper

    if callable(func):
        return decorate(func)
    return decorate


class EventBus:
    def __init__(self):
        self._subs = {}

    def subscribe(self, topic, fn):
        self._subs.setdefault(topic, []).append(fn)

    def publish(self, topic, data):
        for fn in self._subs.get(topic, []):
            fn(data)


def health_check(services):
    failures = []
    for name, probe in services.items():
        try:
            probe()
        except Exception:
            failures.append(name)
    return {"all_ok": not failures, "failures": failures}
''',
    40: '''"""Day40 good - 学习平台闭环Capstone"""
import json


class LearningPlatform:
    def __init__(self):
        self.students = {}

    def register_student(self, student_id):
        self.students[student_id] = {
            "records": [], "reviews": [], "error_statistics": {},
        }

    def submit_result(self, student_id, day, test_score, errors):
        st = self.students[student_id]
        norm = []
        for e in errors or []:
            if isinstance(e, dict):
                etype = e.get("error_type", "Unknown")
            else:
                etype = str(e)
            norm.append({"error_type": etype})
            stats = st["error_statistics"]
            stats[etype] = stats.get(etype, 0) + 1
        record = {"day": day, "test_score": test_score, "errors": norm}
        st["records"].append(record)
        return dict(record)

    def add_review(self, student_id, review):
        st = self.students[student_id]
        entry = dict(review)
        st["reviews"].append(entry)
        return entry

    def get_profile(self, student_id):
        st = self.students[student_id]
        scores = [r["test_score"] for r in st["records"]]
        avg = sum(scores) / len(scores) if scores else 0.0
        return {
            "submissions": len(st["records"]),
            "average_score": avg,
            "error_statistics": dict(st["error_statistics"]),
            "reviews": list(st["reviews"]),
        }

    _TOPICS = {
        "TensorShapeError": "复习PyTorch Tensor维度与Conv2d尺寸计算",
        "ImportError": "复习Python模块导入与包管理",
        "SyntaxError": "巩固Python基础语法与缩进规则",
        "LogicError": "练习边界条件与断言调试",
        "RuntimeError": "学习阅读traceback定位根因",
    }

    def recommend_next_task(self, student_id):
        stats = self.students[student_id]["error_statistics"]
        if not stats:
            return "从Day01开始按计划学习"
        weakest = max(stats.items(), key=lambda kv: kv[1])[0]
        for key, topic in self._TOPICS.items():
            if key.lower() in weakest.lower():
                return f"针对{weakest}：{topic}"
        return f"针对{weakest}做专项练习"

    def generate_report(self, student_id):
        profile = self.get_profile(student_id)
        profile["recommendation"] = self.recommend_next_task(student_id)
        return profile


def export_report(report, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


README_TEMPLATE = "# AI学习平台\\n## Features\\n- 判题\\n- 画像\\n## Quick Start\\n- python main.py\\n"
''',
}

BAD_ANSWERS = {
    1: '"""bad: 缺少大部分接口"""\ndef create_config_file(path):\n    return False\n',
    8: '''"""bad: dtype错误"""
import torch
def create_tensor(data):
    return torch.tensor(data, dtype=torch.float64)
''',
    13: '''"""bad: 无池化层"""
import torch.nn as nn
class SimpleCNN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.features = nn.Conv2d(1, 16, 3, padding=1)
        self.fc = nn.Linear(16 * 28 * 28, num_classes)
    def forward(self, x):
        return self.fc(self.features(x).flatten(1))
''',
    20: '''"""bad: accuracy不做长度校验"""
import numpy as np
import torch.nn as nn
class CIFARNet(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2))
        self.classifier = nn.Linear(16 * 16 * 16, num_classes)
    def forward(self, x):
        return self.classifier(self.features(x).flatten(1))
def accuracy(outputs, labels):
    preds = outputs.argmax(dim=-1)
    return (preds == labels).float().mean().item()
''',
    31: '''"""bad: 缺stream/retry"""
class LLMError(Exception):
    pass
class LLMClient:
    def __init__(self, api_key=None, transport=None):
        self.api_key = api_key
        self.transport = transport
    def is_available(self):
        return self.api_key is not None
    def chat(self, messages, **kw):
        if not self.is_available():
            raise LLMError("no key")
        return "".join(self.transport(messages))
def parse_response(text):
    import json
    s = text.find("{"); e = text.rfind("}") + 1
    return json.loads(text[s:e]) if s != -1 else None
def chunk_text(t, n):
    if n < 1:
        raise ValueError()
    return [t[i:i+n] for i in range(0, len(t), n)]
''',
    39: '''"""bad: Pipeline不链接"""
class Pipeline:
    def __init__(self, steps):
        self.steps = list(steps)
    def run(self, x):
        return self.steps[0](x) if self.steps else x
''',
    40: '''"""bad: 平台缺少推荐/画像闭环"""
class LearningPlatform:
    def register_student(self, sid):
        self.students = {sid: {"records": []}}
    def submit_result(self, sid, day, score, errors):
        self.students[sid]["records"].append(score)
        return {"day": day}
''',
}

REPRESENTATIVE_DAYS = sorted(GOOD_ANSWERS.keys())


@pytest.fixture(scope="module")
def engine():
    return TestEngine(timeout=60)


def _grade(engine, tmp_path, day: int, code: str):
    p = tmp_path / "answer.py"
    p.write_text(code, encoding="utf-8")
    return engine.run_submission(day, str(p))


class TestRepresentativeGrading:
    @pytest.mark.parametrize("day", REPRESENTATIVE_DAYS)
    def test_good_beats_bad(self, engine, tmp_path_factory, day):
        tmp_path = tmp_path_factory.mktemp(f"d{day}")
        good = _grade(engine, tmp_path, day, GOOD_ANSWERS[day])
        bad = _grade(engine, tmp_path, day, BAD_ANSWERS[day])

        # good提交不允许出现error级故障（允许个别failed但不允许崩溃）
        assert good.errors == 0, (
            f"Day{day} good提交不应有error: "
            f"{[t.message[:80] for t in good.test_results if t.status == 'error']}"
        )
        # bad必须至少有1个失败/错误
        assert bad.failed + bad.errors >= 1, (
            f"Day{day} bad提交应至少失败1项，实际failed={bad.failed}"
        )
        # 分数严格区分
        assert good.score > bad.score, (
            f"Day{day}: good({good.score:.1f}) 应优于 bad({bad.score:.1f})"
        )

    def test_summary_report(self, engine, tmp_path_factory):
        """输出验收所需的分数对照表"""
        rows = []
        for day in REPRESENTATIVE_DAYS:
            tmp_path = tmp_path_factory.mktemp(f"sum{day}")
            g = _grade(engine, tmp_path, day, GOOD_ANSWERS[day])
            b = _grade(engine, tmp_path, day, BAD_ANSWERS[day])
            rows.append(f"Day{day:02d}: good={g.score:6.1f}  bad={b.score:6.1f}")
        print("\n=== Grading Smoke Report ===")
        for r in rows:
            print(r)
        assert len(rows) == len(REPRESENTATIVE_DAYS)
