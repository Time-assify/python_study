# Day 29 Tests: FastAPI服务部署
#
# answer.py 必须实现（接口约定）:
# - create_app() -> FastAPI 应用，包含:
#   GET  /health            -> {"status": "ok"}
#   POST /predict           body {"features": [num,...]} -> {"prediction": int}
#   POST /predict_batch     body {"items": [[...],[...]]} -> {"predictions": [int,...]}
#   预测规则自定（如 features求和>0 → 1 否则 0）
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
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None

requires_fastapi = pytest.mark.skipif(TestClient is None, reason="fastapi未安装（环境问题）")


def test_answer_module_imports():
    """answer exists -> import errors are FAIL; only skip when repo has no submission"""
    if answer is None:
        pytest.skip("no answer.py under review (TestEngine injects it during real grading)")


def _require(name):
    if answer is None:
        pytest.skip("no answer.py under review")
    fn = getattr(answer, name, None)
    if fn is None:
        pytest.fail(f"必须实现 {name}()")
    return fn


@pytest.fixture()
def client():
    create_app = _require("create_app")
    return TestClient(create_app())


@requires_fastapi
class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200, f"/health应返回200: {r.status_code}"
        assert r.json().get("status") == "ok"


@requires_fastapi
class TestPredict:
    def test_predict_positive(self, client):
        """基础功能"""
        r = client.post("/predict", json={"features": [1.0, 2.0, 3.0]})
        assert r.status_code == 200
        body = r.json()
        assert "prediction" in body, f"响应缺少prediction字段: {body}"

    def test_rule_consistency(self, client):
        """边界条件: 正负输入给出不同预测"""
        pos = client.post("/predict", json={"features": [5.0]}).json()["prediction"]
        neg = client.post("/predict", json={"features": [-5.0]}).json()["prediction"]
        assert pos != neg, "正/负特征应产生不同预测结果"

    def test_predict_validation_error(self, client):
        """错误处理: 缺少features应422"""
        r = client.post("/predict", json={"wrong_key": 1})
        assert r.status_code == 422

    def test_batch(self, client):
        """批量接口"""
        r = client.post("/predict_batch", json={"items": [[1.0], [-1.0], [2.0]]})
        assert r.status_code == 200
        preds = r.json().get("predictions")
        assert isinstance(preds, list) and len(preds) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
