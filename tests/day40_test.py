# Day 40 Tests: Final Project - 完整AI学习平台
#
# answer.py 必须实现（接口约定）:
# - LearningPlatform 类（整合前39天核心能力的最小闭环）:
#     .register(student_id) -> None
#     .submit(student_id, day, code) -> dict 记录  {"id":..,"day":..,"passed":bool,...}
#       判定规则：code含"def "视为可运行并通过（模拟判题）
#     .review(record) -> dict  {"suggestion": str, ...} 根据是否通过给出建议
#     .report(student_id) -> dict {"submissions": int, "average_score": float}
# - export_report(report, path) -> None  写JSON文件
# - README_TEMPLATE -> str  文档模板，包含 "## Features" 与 "## Quick Start"
import json
import os

import pytest

try:
    import answer
except ModuleNotFoundError as e:
    if getattr(e, "name", "") == "answer":
        answer = None
    else:
        raise
except Exception:
    raise


def test_answer_module_imports():
    """answer exists -> import errors are FAIL; only skip when repo has no submission"""
    if answer is None:
        pytest.skip("no answer.py under review (TestEngine injects it during real grading)")


def _require(name):
    if answer is None:
        pytest.skip("no answer.py under review")
    obj = getattr(answer, name, None)
    if obj is None:
        pytest.fail(f"必须实现 {name}")
    return obj


@pytest.mark.skill("capstone.platform", "documentation")
class TestCoreWorkflow:
    def _platform(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        cls = getattr(answer, "LearningPlatform", None)
        if cls is None:
            pytest.fail("必须实现 LearningPlatform 类")
        plat = cls()
        plat.register("stu-1")
        return plat

    def test_register_and_submit(self):
        plat = self._platform()
        rec = plat.submit("stu-1", 1, "def solve():\n    return 42\n")
        assert isinstance(rec, dict)
        assert int(rec.get("day", -1)) == 1

    def test_pass_and_fail_paths(self):
        """基础功能: 通过/不通过两种路径"""
        plat = self._platform()
        ok = plat.submit("stu-1", 2, "def good():\n    pass")
        bad = plat.submit("stu-1", 3, "# 只有注释，没有实现")
        assert bool(ok.get("passed")) is True
        assert bool(bad.get("passed")) is False

    def test_report_statistics(self):
        """任务要求检查: 汇总报告"""
        plat = self._platform()
        for day in range(1, 5):
            plat.submit("stu-1", day, "def f():\n    pass" if day % 2 else "pass")
        report = plat.report("stu-1")
        assert int(report.get("submissions", 0)) == 4
        avg = float(report.get("average_score", -1))
        # 2/4通过 → 平均分50左右（实现可用自己的分数体系，但必须>0）
        assert 0 <= avg <= 100


@pytest.mark.skill("capstone.platform", "documentation")
class TestReview:
    def test_review_gives_suggestion(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        plat_cls = getattr(answer, "LearningPlatform", None)
        if plat_cls is None:
            pytest.fail("必须实现 LearningPlatform 类")
        plat = plat_cls()
        plat.register("s")
        rec = plat.submit("s", 1, "no impl")
        review = plat.review(rec)
        text = str(review)
        assert ("suggestion" in review) or len(text) > 5, f"review缺少建议: {review}"

    def test_review_differs_by_result(self):
        """AI集成点: 通过与失败的建议应不同"""
        if answer is None:
            pytest.skip("no answer.py under review")
        plat_cls = getattr(answer, "LearningPlatform", None)
        plat = plat_cls()
        plat.register("s")
        r_ok = plat.review(plat.submit("s", 1, "def a():\n    pass"))
        r_bad = plat.review(plat.submit("s", 2, "todo"))
        assert str(r_ok) != str(r_bad), "通过/失败的建议不应相同"


@pytest.mark.skill("capstone.platform", "documentation")
class TestDeployment:
    def test_export_report_json(self, tmp_path):
        if answer is None:
            pytest.skip("no answer.py under review")
        export = getattr(answer, "export_report", None)
        if export is None:
            pytest.fail("必须实现 export_report()")
        path = str(tmp_path / "report.json")
        export({"student": "s1", "score": 88.0}, path)
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["student"] == "s1"

    def test_documentation_template(self):
        """文档要求检查"""
        if answer is None:
            pytest.skip("no answer.py under review")
        template = getattr(answer, "README_TEMPLATE", None)
        if not template or not isinstance(template, str):
            pytest.fail("必须定义 README_TEMPLATE 字符串常量")
        assert "## Features" in template and "## Quick Start" in template


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
