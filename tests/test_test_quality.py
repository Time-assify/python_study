"""测试质量自动扫描器

扫描 tests/day*_test.py，禁止:
- 恒真断言: assert True / assert X or True / assert True or X /
  assert 1 / assert "abc" 等可静态判真的表达式
- pass-only / 占位名测试
- 无正当理由的 skip（白名单：
  1) 仓库无待评测answer.py（正式评测由TestEngine注入）
  2) 第三方库未安装（环境问题，非学生代码问题））
- 重型训练模式（download=True/num_workers/数据集下载/.cuda()/range>100）

重型检查范围由 tasks/dayXX.json["skills"] 动态决定（P1-3），
不再硬编码天数。

同时验证: 每个day文件必须导入answer且具备fail-not-skip机制。
"""
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent

ALLOWED_SKIP_MARKERS = ("环境问题", "no answer.py under review")

# 含这些关键字的skill → 启用重型训练模式检查
HEAVY_SKILL_KEYWORDS = (
    "pytorch", "cv", "detection", "onnx", "torchvision",
    "transformer", "huggingface",
)

FORBIDDEN_TORCH_PATTERNS = (
    "download=True",
    "num_workers",
    "CIFAR10(",
    "MNIST(",
    ".cuda()",
)

DAY_FILES = sorted((ROOT / "tests").glob("day??_test.py"))


def _load(day_file: Path):
    return ast.parse(day_file.read_text(encoding="utf-8"))


def _task_skills(day: int):
    task_path = ROOT / "tasks" / f"day{day:02d}.json"
    if not task_path.exists():
        return []
    return json.loads(task_path.read_text(encoding="utf-8")).get("skills", [])


def _is_heavy_day(day: int) -> bool:
    """P1-3: 依据skills判断是否启用重型训练模式检查"""
    for skill in _task_skills(day):
        lowered = skill.lower()
        if any(k in lowered for k in HEAVY_SKILL_KEYWORDS):
            return True
    return False


def _test_functions(tree):
    """yield所有 test_* 函数节点（含类内方法）"""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                node.name.startswith("test_"):
            yield node


def _is_empty_body(func) -> bool:
    """测试体只有docstring/pass/...则视为空测试"""
    body = list(func.body)
    if body and isinstance(body[0], ast.Expr) and \
            isinstance(body[0].value, ast.Constant) and \
            isinstance(body[0].value.value, str):
        body = body[1:]  # 去掉docstring
    return len(body) == 1 and isinstance(body[0], ast.Pass)


def _const_truthiness(node):
    """若node是字面常量/字面集合，返回其真值；否则返回None

    P2: 除ast.Constant外，覆盖List/Tuple/Set/Dict字面量——
    非空集合静态恒真（assert [1] / assert {"a": 1}），空集合恒假。
    """
    # 字面集合（非Constant节点）
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return len(node.elts) > 0
    if isinstance(node, ast.Dict):
        return len(node.keys) > 0

    if not isinstance(node, ast.Constant):
        return None
    value = node.value
    if value is None or isinstance(value, type(...)):  # None / Ellipsis
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return len(value) > 0
    if isinstance(value, (tuple, list, set, dict, frozenset)):
        return len(value) > 0
    return None


def _is_trivially_true(expr):
    """P0-4: 静态判定assert条件恒真

    覆盖:
    - ast.Constant(True) 及一切真值常量: assert 1 / assert "abc"
    - BoolOp(Or): 任一operand恒真 → 整体恒真
    - BoolOp(And): 全部operand恒真 → 整体恒真
    - UnaryOp(Not): 包裹恒假常量 → 恒真 (assert not False)
    """
    truth = _const_truthiness(expr)
    if truth is True:
        return True
    if truth is False:
        return False

    if isinstance(expr, ast.BoolOp):
        values = [(_const_truthiness(op), op) for op in expr.values]
        if isinstance(expr.op, ast.Or):
            # 任一operand静态为True，或任一operand递归恒真
            return any(t is True or _is_trivially_true(op) for t, op in values)
        # And: 全部恒真才整体恒真
        return all(t is True for t, _ in values) and \
            all(_is_trivially_true(op) for _, op in values)

    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        inner = _const_truthiness(expr.operand)
        if inner is False:
            return True
        return False

    return False


def find_trivial_asserts(tree):
    """返回tree中所有恒真断言的行号列表"""
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert) and _is_trivially_true(node.test):
            hits.append(node.lineno)
    return hits


class TestNoTautologicalAssertions:
    """P0-4: 禁止一切可静态判真的assert"""

    def test_no_tautological_assertions(self):
        offenders = []
        for f in DAY_FILES:
            tree = _load(f)
            for lineno in find_trivial_asserts(tree):
                offenders.append(f"{f.name}:{lineno}")
        assert not offenders, f"发现恒真断言: {offenders}"

    def test_no_assert_true(self):
        for f in DAY_FILES:
            tree = _load(f)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assert):
                    if isinstance(node.test, ast.Constant) and \
                            node.test.value is True:
                        raise AssertionError(
                            f"{f.name}:{node.lineno} 出现 assert True"
                        )


class TestNoPlaceholderTests:
    def test_no_pass_only_tests(self):
        for f in DAY_FILES:
            tree = _load(f)
            for func in _test_functions(tree):
                assert not _is_empty_body(func), (
                    f"{f.name}:{func.lineno} 测试 {func.name} 是pass-only占位"
                )

    def test_no_placeholder_names(self):
        banned = re.compile(r"placeholder|todo|fixme|dummy_test", re.IGNORECASE)
        for f in DAY_FILES:
            tree = _load(f)
            for func in _test_functions(tree):
                assert not banned.search(func.name), (
                    f"{f.name} 占位测试名: {func.name}"
                )


class TestSkipPolicy:
    """skip必须带白名单理由；禁止无条件skip标记"""

    def test_no_unconditional_skip_marker(self):
        for f in DAY_FILES:
            src = f.read_text(encoding="utf-8")
            assert "@pytest.mark.skip\n" not in src and \
                "@pytest.mark.skip(" not in src, (
                    f"{f.name} 存在无条件 @pytest.mark.skip"
                )

    def test_every_skip_has_allowed_reason(self):
        reason_re = re.compile(
            r"pytest\.skip\(\s*[\"']([^\"']*)[\"']\s*\)"
        )
        kwreason_re = re.compile(r"skipif\([^)]*reason\s*=\s*[\"']([^\"']*)[\"']")
        for f in DAY_FILES:
            src = f.read_text(encoding="utf-8")
            for m in reason_re.finditer(src):
                assert any(k in m.group(1) for k in ALLOWED_SKIP_MARKERS), (
                    f"{f.name}: 非白名单skip理由 -> {m.group(1)!r}"
                )
            for m in kwreason_re.finditer(src):
                assert any(k in m.group(1) for k in ALLOWED_SKIP_MARKERS), (
                    f"{f.name}: 非白名单skipif理由 -> {m.group(1)!r}"
                )


class TestEveryDayImportsAnswer:
    def test_imports_answer_and_fail_mechanism(self):
        for f in DAY_FILES:
            src = f.read_text(encoding="utf-8")
            assert "import answer" in src, f"{f.name} 未导入answer"
            assert "pytest.fail" in src or "_require" in src, (
                f"{f.name} 缺少fail-not-skip机制"
            )
            # 学生代码存在但导入失败必须FAIL（raise穿透），而非吞异常
            assert re.search(r"except Exception:\s*\n\s*raise", src), (
                f"{f.name} 缺少 except Exception: raise（学生代码错误必须暴露）"
            )


class TestPyTorchTestDiscipline:
    """P1-3: skill驱动 — pytorch/cv/detection/onnx相关day禁止重型训练"""

    def test_no_heavy_patterns_in_heavy_days(self):
        for f in DAY_FILES:
            day = int(f.stem[3:5])
            if not _is_heavy_day(day):
                continue
            src = f.read_text(encoding="utf-8")
            for pat in FORBIDDEN_TORCH_PATTERNS:
                assert pat not in src, (
                    f"{f.name} 禁止使用 {pat!r}（避免长时间训练/下载）"
                )

    def test_training_iterations_bounded(self):
        """显式range迭代上限不得超过100步"""
        bound = re.compile(r"for\s+_?\w*\s+in\s+range\((\d+)\)")
        for f in DAY_FILES:
            day = int(f.stem[3:5])
            if not _is_heavy_day(day):
                continue
            for m in bound.finditer(f.read_text(encoding="utf-8")):
                n = int(m.group(1))
                assert n <= 100, (
                    f"{f.name} 训练循环range({n})超过100步上限"
                )
