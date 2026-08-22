# Phase 4 Tests: AI Agent (Day 31-40)
import pytest


class TestLLMClientConcepts:
    """LLM客户端概念测试"""
    
    def test_api_message_format(self):
        """测试API消息格式"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
    
    def test_streaming_response(self):
        """测试流式响应概念"""
        def stream_response():
            for chunk in ["Hello", " ", "World"]:
                yield chunk
        
        response = "".join(stream_response())
        assert response == "Hello World"


class TestPromptEngineeringConcepts:
    """提示工程概念测试"""
    
    def test_few_shot_prompting(self):
        """测试少样本提示"""
        examples = [
            {"input": "good", "output": "positive"},
            {"input": "bad", "output": "negative"}
        ]
        prompt = "Classify the sentiment:\n"
        for ex in examples:
            prompt += f"Input: {ex['input']}\nOutput: {ex['output']}\n"
        
        assert "positive" in prompt
        assert "negative" in prompt
    
    def test_chain_of_thought(self):
        """测试思维链推理"""
        prompt = """Let's solve this step by step:
        Step 1: Understand the problem
        Step 2: Break it down
        Step 3: Solve each part
        """
        assert "Step 1" in prompt
        assert "Step 2" in prompt


class TestRAGConcepts:
    """RAG概念测试"""
    
    def test_document_chunking(self):
        """测试文档分块"""
        def chunk_document(text, chunk_size=100):
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        doc = "This is a test document. " * 20
        chunks = chunk_document(doc, 50)
        assert len(chunks) > 1
    
    def test_similarity_search(self):
        """测试相似度搜索"""
        def cosine_similarity(vec1, vec2):
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a ** 2 for a in vec1) ** 0.5
            norm2 = sum(b ** 2 for b in vec2) ** 0.5
            return dot_product / (norm1 * norm2) if norm1 * norm2 > 0 else 0
        
        vec1 = [1, 0, 1]
        vec2 = [1, 0, 1]
        vec3 = [0, 1, 0]
        
        assert cosine_similarity(vec1, vec2) == pytest.approx(1.0)
        assert cosine_similarity(vec1, vec3) == pytest.approx(0.0)


class TestAgentConcepts:
    """Agent概念测试"""
    
    def test_observe_think_act(self):
        """测试观察-思考-行动循环"""
        class SimpleAgent:
            def __init__(self):
                self.memory = []
            
            def observe(self, observation):
                self.memory.append(observation)
            
            def think(self):
                return f"Based on {len(self.memory)} observations"
            
            def act(self, action):
                return f"Executing: {action}"
        
        agent = SimpleAgent()
        agent.observe("obs1")
        agent.observe("obs2")
        
        thought = agent.think()
        assert "2 observations" in thought
        
        result = agent.act("move_forward")
        assert "move_forward" in result
    
    def test_tool_calling(self):
        """测试工具调用概念"""
        tools = {
            "search": lambda q: f"Results for: {q}",
            "calculate": lambda expr: eval(expr)
        }
        
        result = tools["search"]("python")
        assert "python" in result
        
        result = tools["calculate"]("2 + 2")
        assert result == 4


class TestCodeAgentConcepts:
    """Code Agent概念测试"""
    
    def test_code_generation(self):
        """测试代码生成概念"""
        def generate_function(name, params):
            return f"def {name}({', '.join(params)}):\n    pass"
        
        code = generate_function("add", ["a", "b"])
        assert "def add(a, b):" in code
    
    def test_code_review(self):
        """测试代码审查概念"""
        def review_code(code):
            issues = []
            if "eval(" in code:
                issues.append("Security: avoid eval()")
            if "import *" in code:
                issues.append("Style: avoid wildcard imports")
            return issues
        
        code = "from module import *"
        issues = review_code(code)
        assert len(issues) > 0


class TestSystemIntegration:
    """系统整合概念测试"""
    
    def test_workflow_management(self):
        """测试工作流管理"""
        class Workflow:
            def __init__(self):
                self.steps = []
            
            def add_step(self, name, func):
                self.steps.append((name, func))
            
            def execute(self, initial_data):
                result = initial_data
                for name, func in self.steps:
                    result = func(result)
                return result
        
        workflow = Workflow()
        workflow.add_step("double", lambda x: x * 2)
        workflow.add_step("add_ten", lambda x: x + 10)
        
        result = workflow.execute(5)
        assert result == 20
    
    def test_error_handling(self):
        """测试错误处理"""
        def safe_execute(func, *args, **kwargs):
            try:
                return True, func(*args, **kwargs)
            except Exception as e:
                return False, str(e)
        
        success, result = safe_execute(lambda x: x / 0, 1)
        assert not success
        assert "division by zero" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])