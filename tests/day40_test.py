# Day 40 Tests: Final Project - AI学习平台闭环（Capstone）
#
# answer.py 必须实现（接口约定）:
# - LearningPlatform 类（整合注册→提交→统计→review→画像→推荐→报告的最小闭环）:
#     register_student(student_id) -> None
#     submit_result(student_id, day, test_score, errors) -> dict 记录
#         errors: list[dict]（至少含error_type键）或 list[str]（错误类型名）
#     add_review(student_id, review) -> dict    review为dict，建议含suggestion键
#     get_profile(student_id) -> dict  至少含:
#         submissions: int          已保存提交数
#         average_score: float      平均分
#         error_statistics: dict    {error_type: 次数} 跨提交累计
#         reviews: list             已保存的review列表
#     recommend_next_task(student_id) -> str
#         根据当前画像（最薄弱错误）给出下一步任务建议；
#         画像不同 → 建议内容不同
#     generate_report(student_id) -> dict  至少含 submissions/average_score/
#                                          error_statistics/reviews/recommendation
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
    obj = getattr(answer, name, None)
    if obj is None:
        pytest.fail(f"必须实现 {name}")
    return obj


def _platform():
    if answer is None:
        pytest.skip("no answer.py under review")
    cls = getattr(answer, "LearningPlatform", None)
    if cls is None:
        pytest.fail("必须实现 LearningPlatform 类")
    plat = cls()
    plat.register_student("stu-1")
    return plat


@pytest.mark.skill("capstone.platform", "documentation")
class TestRegistration:
    def test_register_student(self):
        """1. 注册学生"""
        plat = _platform()
        assert plat is not None
        # 新学生初始画像：0次提交
        profile = plat.get_profile("stu-1")
        assert int(profile.get("submissions", -1)) == 0, (
            f"新学生submissions应为0: {profile}"
        )


@pytest.mark.skill("capstone.platform", "documentation")
class TestSubmissionsAndStats:
    def test_two_submissions_saved(self):
        """2. 保存两次不同提交"""
        plat = _platform()
        r1 = plat.submit_result("stu-1", 1, 80.0,
                                [{"error_type": "TensorShapeError"}])
        r2 = plat.submit_result("stu-1", 2, 60.0,
                                [{"error_type": "TensorShapeError"},
                                 {"error_type": "ImportError"}])
        assert isinstance(r1, dict) and isinstance(r2, dict)
        profile = plat.get_profile("stu-1")
        assert int(profile["submissions"]) == 2, (
            f"两次提交后submissions应为2: {profile}"
        )

    def test_average_score_over_history(self):
        """3. 生成历史统计: 平均分跨提交计算"""
        plat = _platform()
        plat.submit_result("stu-1", 1, 80.0, [])
        plat.submit_result("stu-1", 2, 60.0, [])
        avg = float(plat.get_profile("stu-1")["average_score"])
        assert abs(avg - 70.0) < 1e-6, f"平均分应为70，得到{avg}"

    def test_errors_accumulated_across_submissions(self):
        """4. 错误被累计: error_statistics跨提交聚合"""
        plat = _platform()
        plat.submit_result("stu-1", 1, 80.0,
                           [{"error_type": "TensorShapeError"}])
        plat.submit_result("stu-1", 2, 60.0,
                           [{"error_type": "TensorShapeError"},
                            {"error_type": "ImportError"}])
        stats = plat.get_profile("stu-1")["error_statistics"]
        assert int(stats.get("TensorShapeError", 0)) == 2, (
            f"TensorShapeError应累计2次: {stats}"
        )
        assert int(stats.get("ImportError", 0)) == 1


@pytest.mark.skill("capstone.platform", "documentation")
class TestReviews:
    def test_review_saved_and_visible(self):
        """5. review被保存且可在画像中看到"""
        plat = _platform()
        saved = plat.add_review("stu-1", {"suggestion": "练习Conv2d尺寸计算"})
        assert isinstance(saved, dict)
        profile = plat.get_profile("stu-1")
        reviews_text = str(profile.get("reviews", []))
        assert "练习Conv2d尺寸计算" in reviews_text, (
            f"review应保存在画像中: {reviews_text}"
        )


@pytest.mark.skill("capstone.platform", "documentation")
class TestProfileEvolution:
    def test_profile_changes_with_new_submission(self):
        """6. profile随提交变化: 平均分随第三次提交改变"""
        plat = _platform()
        plat.submit_result("stu-1", 1, 80.0, [])
        before = float(plat.get_profile("stu-1")["average_score"])
        plat.submit_result("stu-1", 2, 40.0, [])
        after = float(plat.get_profile("stu-1")["average_score"])
        assert abs(before - 80.0) < 1e-6 and abs(after - 60.0) < 1e-6, (
            f"平均分应从80变为60: {before}->{after}"
        )

    def test_recommendation_varies_by_profile(self):
        """7. 下一任务建议根据profile变化: 最薄弱错误不同→建议不同"""
        plat_a = _platform()
        # A: TensorShapeError主导
        plat_a.register_student("stu-a")
        for d in range(3):
            plat_a.submit_result("stu-a", d + 1, 50.0,
                                 [{"error_type": "TensorShapeError"}])
        rec_a = str(plat_a.recommend_next_task("stu-a"))

        plat_b = _platform()
        # B: ImportError主导
        plat_b.register_student("stu-b")
        for d in range(3):
            plat_b.submit_result("stu-b", d + 1, 50.0,
                                 [{"error_type": "ImportError"}])
        rec_b = str(plat_b.recommend_next_task("stu-b"))

        low_a, low_b = rec_a.lower(), rec_b.lower()
        assert ("tensor" in low_a) or ("shape" in low_a) or ("维度" in rec_a), (
            f"A的薄弱项是shape，建议应相关: {rec_a}"
        )
        assert ("import" in low_b) or ("module" in low_b) or ("导入" in rec_b), (
            f"B的薄弱项是导入，建议应相关: {rec_b}"
        )
        assert rec_a != rec_b, "不同画像必须产生不同建议"


@pytest.mark.skill("capstone.platform", "documentation")
class TestReportExport:
    def test_generate_report_contains_all_sections(self):
        """8. report生成: 包含统计/review/建议全部字段"""
        plat = _platform()
        plat.submit_result("stu-1", 1, 90.0, [{"error_type": "SyntaxError"}])
        plat.add_review("stu-1", {"suggestion": "复习缩进规则"})
        report = plat.generate_report("stu-1")
        text = str(report)
        for key in ("submissions", "average_score", "error_statistics",
                    "recommendation"):
            assert key in report or key in text, f"report缺少{key}: {report}"

    def test_export_report_json(self, tmp_path):
        """report导出为JSON文件"""
        if answer is None:
            pytest.skip("no answer.py under review")
        export = getattr(answer, "export_report", None)
        if export is None:
            pytest.fail("必须实现 export_report()")
        plat = _platform()
        plat.submit_result("stu-1", 1, 88.0, [])
        report = plat.generate_report("stu-1")
        path = tmp_path / "report.json"
        export(report, str(path))
        assert os.path.exists(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data == report or set(data) & {"average_score", "submissions"}

    def test_documentation_template(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        template = getattr(answer, "README_TEMPLATE", None)
        if not template or not isinstance(template, str):
            pytest.fail("必须定义 README_TEMPLATE 字符串常量")
        assert "## Features" in template and "## Quick Start" in template


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
