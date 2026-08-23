# Day 03 Tests: 面向对象设计
#
# answer.py 必须实现（接口约定）:
# - BaseModel(ABC)                 抽象基类：声明抽象方法 fit(X, y) 和 predict(X)
# - LinearModel(BaseModel)         具体子类：可实现简单规则即可（如返回全零）
# - OptimizerBase(ABC)             抽象基类：声明抽象方法 step(params)
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


class TestAbstractBaseClass:
    """基础功能: 抽象基类"""

    def test_base_model_is_abstract(self):
        from abc import ABC
        base = _require("BaseModel")
        assert issubclass(base, ABC), "BaseModel必须继承abc.ABC"

    def test_base_model_cannot_instantiate(self):
        """错误处理: 抽象类不可实例化"""
        base = _require("BaseModel")
        with pytest.raises(TypeError):
            base()

    def test_abstract_methods_declared(self):
        base = _require("BaseModel")
        abstract_names = set()
        for klass in base.__mro__:
            for attr, val in vars(klass).items():
                if getattr(val, "__isabstractmethod__", False):
                    abstract_names.add(attr)
        assert {"fit", "predict"} <= abstract_names, f"缺少抽象方法: {abstract_names}"


class TestInheritance:
    """继承与多态"""

    def test_linear_model_subclasses_base(self):
        base = _require("BaseModel")
        linear = _require("LinearModel")
        assert issubclass(linear, base), "LinearModel必须继承BaseModel"

    def test_linear_model_can_instantiate(self):
        """边界条件: 具体子类可实例化并实现fit/predict"""
        linear = _require("LinearModel")
        model = linear()
        model.fit([[1.0], [2.0]], [1, 2])
        preds = model.predict([[3.0]])
        assert preds is not None, "predict应有返回值"

    def test_polymorphism(self):
        """多态: 不同子类通过统一接口调用"""
        base = _require("BaseModel")
        linear = _require("LinearModel")

        class Dummy(base):
            def fit(self, X, y):
                return self

            def predict(self, X):
                return [0] * len(X)

        models = [linear(), Dummy()]
        for m in models:
            out = m.predict([[1.0]])
            assert out is not None, f"{type(m).__name__} 未实现统一predict接口"


class TestOptimizerBase:
    def test_optimizer_base_abstract(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        opt = getattr(answer, "OptimizerBase", None)
        if opt is None:
            pytest.fail("必须实现 OptimizerBase")
        with pytest.raises(TypeError):
            opt()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
