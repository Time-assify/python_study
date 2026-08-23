"""测试质量自动扫描器

扫描 tests/day*_test.py，禁止:
- assert True / placeholder / pass-only 测试体
- 无正当理由的 skip（仅允许两类白名单：
  1) 仓库无待评测answer.py（正式评测由TestEngine注入）
  2) 第三方库未安装（环境问题，非学生代码问题））
- PyTorch测试重训练模式（download=True/num_workers/大数据集下载/.cuda()）

同时验证: 每个day文件必须导入answer且具备fail-not-skip机制。
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent

ALLOWED_SKIP_MARKERS = ("环境问题", "no answer.py under review")

TORCH_DAYS = set(range(8, 26)) - {25}  # 25为transformers日
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


class TestNoPlaceholderTests:
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
    """torch相关day只允许轻量验证，禁止重型训练/数据下载"""

    def test_no_heavy_patterns_in_torch_days(self):
        for f in DAY_FILES:
            day = int(f.stem[3:5])
            if day not in TORCH_DAYS:
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
            if day not in TORCH_DAYS:
                continue
            for m in bound.finditer(f.read_text(encoding="utf-8")):
                n = int(m.group(1))
                assert n <= 100, (
                    f"{f.name} 训练循环range({n})超过100步上限"
                )
