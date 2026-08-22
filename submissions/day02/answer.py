"""Day 02: 高级Python - 装饰器和生成器"""

# 1. 基本装饰器
def my_decorator(func):
    """简单装饰器"""
    def wrapper(*args, **kwargs):
        print("调用前...")
        result = func(*args, **kwargs)
        print("调用后...")
        return result
    return wrapper

@my_decorator
def say_hello(name):
    print(f"Hello, {name}!")

# 2. 带参数的装饰器
def repeat(times):
    """重复执行装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = None
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def greet():
    print("Hi!")

# 3. 类装饰器
class CountCalls:
    """统计函数调用次数"""
    def __init__(self, func):
        self.func = func
        self.count = 0
    
    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"调用次数: {self.count}")
        return self.func(*args, **kwargs)

@CountCalls
def add(a, b):
    return a + b

# 4. 生成器
def fibonacci(n):
    """斐波那契数列生成器"""
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

# 5. 生成器表达式
squares = (x**2 for x in range(10))

# 6. 上下文管理器
class Timer:
    """计时器上下文管理器"""
    def __enter__(self):
        import time
        self.start = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.elapsed = time.time() - self.start
        print(f"耗时: {self.elapsed:.4f}秒")

# 测试
if __name__ == "__main__":
    say_hello("World")
    print()
    
    greet()
    print()
    
    result = add(1, 2)
    print(f"结果: {result}")
    print()
    
    fib_list = list(fibonacci(10))
    print(f"斐波那契: {fib_list}")
    print()
    
    print(f"平方数: {list(squares)}")
    print()
    
    with Timer():
        sum(range(1000000))