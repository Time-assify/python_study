# Day 06 Tests: NumPy/Pandas数据处理
#
# answer.py 必须实现（接口约定）:
# - clean_dataframe(df) -> DataFrame      删除含NaN的行 + 去除重复行
# - minmax_normalize(df, column) -> Series  列归一化到[0,1]；常数列返回全0.5
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

try:
    import pandas as pd
    import numpy as np
except ImportError:
    pd = None
    np = None

requires_pandas = pytest.mark.skipif(pd is None, reason="pandas未安装（环境问题）")


def test_answer_module_imports():
    """answer exists -> import errors are FAIL; only skip when repo has no submission"""
    if answer is None:
        pytest.skip("no answer.py under review (TestEngine injects it during real grading)")


@requires_pandas
@pytest.mark.skill("numpy", "pandas", "data.cleaning")
class TestDataCleaning:
    def _require(self, name):
        if answer is None:
            pytest.skip("no answer.py under review")
        fn = getattr(answer, name, None)
        if fn is None:
            pytest.fail(f"必须实现 {name}()")
        return fn

    def _sample_df(self):
        return pd.DataFrame({
            "a": [1.0, 2.0, 2.0, None, 5.0],
            "b": ["x", "y", "y", "z", "w"],
        })

    def test_clean_drops_nan_rows(self):
        clean = self._require("clean_dataframe")
        result = clean(self._sample_df())
        assert len(result) == 3, f"应删除NaN行后剩3行，得到{len(result)}"
        assert not result.isna().any().any(), "结果中不应有NaN"

    def test_clean_removes_duplicates(self):
        """边界条件: 完全重复行只保留一条"""
        clean = self._require("clean_dataframe")
        df = pd.DataFrame({"a": [1, 1, 1], "b": ["k", "k", "k"]})
        result = clean(df)
        assert len(result) == 1, f"重复行未去重: {len(result)}"

    def test_normalize_range(self):
        norm = self._require("minmax_normalize")
        df = pd.DataFrame({"v": [0.0, 5.0, 10.0]})
        out = norm(df, "v")
        vals = np.asarray(out, dtype=float)
        assert abs(vals.min() - 0.0) < 1e-9 and abs(vals.max() - 1.0) < 1e-9

    def test_normalize_constant_column(self):
        """边界条件+错误处理: 常数列避免除零"""
        norm = self._require("minmax_normalize")
        df = pd.DataFrame({"v": [7.0, 7.0, 7.0]})
        out = norm(df, "v")
        vals = np.asarray(out, dtype=float)
        assert np.allclose(vals, 0.5), f"常数列应返回全0.5，得到{vals}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
