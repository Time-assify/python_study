# Day 07 Tests: Mini ML Framework（线性回归）
#
# answer.py 必须实现（接口约定）:
# - mse_loss(y_true, y_pred) -> float
# - LinearRegression 类: fit(X, y, lr=0.05, iters=800) / predict(X) -> ndarray
#   X为(n,1)数组，内部用梯度下降
import numpy as np
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


class TestLossFunction:
    def test_mse_known_value(self):
        mse = _require("mse_loss")
        val = mse(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 3.0]))
        assert abs(val) < 1e-9, "相同输入MSE应为0"

    def test_mse_value(self):
        mse = _require("mse_loss")
        val = mse(np.array([0.0, 0.0]), np.array([1.0, 3.0]))
        assert abs(val - 5.0) < 1e-9, f"MSE应为5.0，得到{val}"


class TestLinearRegression:
    def test_class_exists_with_api(self):
        cls = _require("LinearRegression")
        model = cls()
        for m in ("fit", "predict"):
            if not callable(getattr(model, m, None)):
                pytest.fail(f"LinearRegression必须实现 {m}()")

    def test_fit_perfect_linear(self):
        """基础功能: y=2x+1 拟合后预测接近"""
        cls = _require("LinearRegression")
        rng = np.random.RandomState(0)
        X = rng.uniform(-2, 2, size=(60, 1))
        y = (2 * X[:, 0] + 1).reshape(-1)
        model = cls()
        model.fit(X, y)
        preds = model.predict(X)
        err = float(np.mean(np.abs(preds - y)))
        assert err < 0.25, f"拟合误差过大: {err:.4f}（检查学习率/迭代次数）"

    def test_predict_shape(self):
        """边界条件: 预测输出形状与输入行数一致"""
        cls = _require("LinearRegression")
        model = cls()
        model.fit(np.array([[1.0], [2.0]]), np.array([3.0, 5.0]))
        preds = model.predict(np.array([[4.0], [5.0], [6.0]]))
        assert np.asarray(preds).shape[0] == 3

    def test_shape_mismatch_raises(self):
        """错误处理: X列数与训练不一致应报错(ValueError/RuntimeError均可)"""
        cls = _require("LinearRegression")
        model = cls()
        model.fit(np.array([[1.0], [2.0]]), np.array([3.0, 5.0]))
        with pytest.raises((ValueError, RuntimeError, IndexError)):
            model.predict(np.array([[1.0, 9.9], [2.0, 8.8]]))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
