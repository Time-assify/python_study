# Phase 1 Tests: Python Engineering (Day 1-7)
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "submissions" / "day01"))


class TestDay01:
    """Day 01: Python工程环境"""
    
    def test_import_answer(self):
        """测试导入answer模块"""
        import answer
        assert hasattr(answer, "create_project_structure")
        assert hasattr(answer, "create_config_file")
        assert hasattr(answer, "setup_logger")


class TestProjectStructureConcepts:
    """项目结构概念测试"""
    
    def test_structure_has_src(self):
        """测试结构包含src目录"""
        structure = {"root": "project", "src": "project/src", "tests": "project/tests"}
        assert "src" in structure
    
    def test_structure_has_tests(self):
        """测试结构包含tests目录"""
        structure = {"root": "project", "src": "project/src", "tests": "project/tests"}
        assert "tests" in structure


class TestDecoratorConcepts:
    """装饰器概念测试"""
    
    def test_decorator_basic(self):
        """测试装饰器基本用法"""
        def my_decorator(func):
            def wrapper():
                return func()
            return wrapper
        
        @my_decorator
        def say_hello():
            return "hello"
        
        assert say_hello() == "hello"
    
    def test_decorator_with_args(self):
        """测试带参数的装饰器"""
        def repeat(times):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    result = ""
                    for _ in range(times):
                        result += func(*args, **kwargs)
                    return result
                return wrapper
            return decorator
        
        @repeat(3)
        def say_hi():
            return "hi"
        
        assert say_hi() == "hihihi"


class TestGeneratorConcepts:
    """生成器概念测试"""
    
    def test_generator_basic(self):
        """测试生成器基本用法"""
        def my_generator():
            yield 1
            yield 2
            yield 3
        
        gen = my_generator()
        assert next(gen) == 1
        assert next(gen) == 2
        assert next(gen) == 3
    
    def test_generator_expression(self):
        """测试生成器表达式"""
        gen = (x * 2 for x in range(5))
        assert list(gen) == [0, 2, 4, 6, 8]


class TestOOPConcepts:
    """面向对象概念测试"""
    
    def test_class_inheritance(self):
        """测试类继承"""
        class Base:
            def base_method(self):
                return "base"
        
        class Child(Base):
            def child_method(self):
                return "child"
        
        obj = Child()
        assert obj.base_method() == "base"
        assert obj.child_method() == "child"
    
    def test_abstract_class(self):
        """测试抽象类概念"""
        from abc import ABC, abstractmethod
        
        class Shape(ABC):
            @abstractmethod
            def area(self):
                pass
        
        class Circle(Shape):
            def __init__(self, radius):
                self.radius = radius
            
            def area(self):
                return 3.14 * self.radius ** 2
        
        circle = Circle(5)
        assert circle.area() == 78.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])