# Day 05 Tests: API客户端开发
#
# answer.py 必须实现（接口约定）:
# - build_url(base, path, params=None) -> str      拼接URL并附加查询参数
# - APIClient(base_url)                            类：get(path)/post(path, json=None)，
#                                                  底层用requests，网络错误包装为APIError
# - APIError(Exception)                            自定义异常类
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
    import requests
except ImportError:
    requests = None


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


@pytest.mark.skill("python.requests", "api.client")
class TestBuildUrl:
    def test_simple_path(self):
        build_url = _require("build_url")
        url = build_url("http://api.example.com", "/users")
        assert url.startswith("http://api.example.com"), f"错误URL: {url}"
        assert "/users" in url

    def test_with_params(self):
        build_url = _require("build_url")
        url = build_url("http://api.example.com", "/search", {"q": "ml", "page": 1})
        assert "q=ml" in url and "page=1" in url, f"缺少查询参数: {url}"

    def test_params_none_no_query(self):
        """边界条件: params为None时不应有 '?' """
        build_url = _require("build_url")
        url = build_url("http://api.example.com", "/ping")
        assert "?" not in url


@pytest.mark.skill("python.requests", "api.client")
class TestAPIClient:
    def test_api_error_is_exception(self):
        APIError = _require("APIError")
        assert issubclass(APIError, Exception), "APIError必须是Exception子类"

    def test_client_has_get_post(self):
        client_cls = _require("APIClient")
        for m in ("get", "post"):
            if not callable(getattr(client_cls, m, None)):
                pytest.fail(f"APIClient必须实现 {m}() 方法")

    def test_error_wrapping(self):
        """错误处理: 连接失败时抛出APIError而不是requests异常"""
        if requests is None:
            pytest.skip("requests未安装（环境问题）")
        client_cls = _require("APIClient")
        APIError = answer.APIError
        client = client_cls("http://127.0.0.1:1")  # 不可达端口
        with pytest.raises(APIError):
            client.get("/anything")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
