"""Day 03: 面向对象设计 - ML框架基类"""
from abc import ABC, abstractmethod
from typing import Any, List, Tuple
import numpy as np


# 1. 抽象基类 - 模型
class BaseModel(ABC):
    """模型基类"""
    
    def __init__(self):
        self.is_trained = False
        self.parameters = {}
    
    @abstractmethod
    def forward(self, X: np.ndarray) -> np.ndarray:
        """前向传播"""
        pass
    
    @abstractmethod
    def backward(self, gradient: np.ndarray) -> np.ndarray:
        """反向传播"""
        pass
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        if not self.is_trained:
            raise RuntimeError("模型未训练")
        return self.forward(X)


# 2. 损失函数基类
class BaseLoss(ABC):
    """损失函数基类"""
    
    @abstractmethod
    def compute(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """计算损失"""
        pass
    
    @abstractmethod
    def gradient(self, y_pred: np.ndarray, y_true: np.ndarray) -> np.ndarray:
        """计算梯度"""
        pass


# 3. 优化器基类
class BaseOptimizer(ABC):
    """优化器基类"""
    
    def __init__(self, learning_rate: float = 0.01):
        self.learning_rate = learning_rate
    
    @abstractmethod
    def update(self, params: dict, gradients: dict) -> dict:
        """更新参数"""
        pass


# 4. 具体实现 - 线性回归
class LinearModel(BaseModel):
    """线性回归模型"""
    
    def __init__(self, input_dim: int):
        super().__init__()
        self.weights = np.random.randn(input_dim) * 0.01
        self.bias = 0.0
    
    def forward(self, X: np.ndarray) -> np.ndarray:
        return np.dot(X, self.weights) + self.bias
    
    def backward(self, gradient: np.ndarray) -> np.ndarray:
        return gradient


class MSELoss(BaseLoss):
    """均方误差损失"""
    
    def compute(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        return np.mean((y_pred - y_true) ** 2)
    
    def gradient(self, y_pred: np.ndarray, y_true: np.ndarray) -> np.ndarray:
        return 2 * (y_pred - y_true) / len(y_true)


class SGDOptimizer(BaseOptimizer):
    """随机梯度下降优化器"""
    
    def update(self, params: dict, gradients: dict) -> dict:
        for key in params:
            params[key] -= self.learning_rate * gradients.get(key, 0)
        return params


# 5. 训练器
class Trainer:
    """训练器"""
    
    def __init__(self, model: BaseModel, loss: BaseLoss, optimizer: BaseOptimizer):
        self.model = model
        self.loss = loss
        self.optimizer = optimizer
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 100):
        """训练模型"""
        for epoch in range(epochs):
            # 前向传播
            y_pred = self.model.forward(X)
            
            # 计算损失
            loss = self.loss.compute(y_pred, y)
            
            # 计算梯度
            gradient = self.loss.gradient(y_pred, y)
            
            # 更新参数
            self.model.weights -= self.optimizer.learning_rate * np.dot(X.T, gradient) / len(y)
            self.model.bias -= self.optimizer.learning_rate * np.mean(gradient)
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch + 1}/{epochs}, Loss: {loss:.4f}")
        
        self.model.is_trained = True


# 测试
if __name__ == "__main__":
    # 生成示例数据
    np.random.seed(42)
    X = np.random.randn(100, 1)
    y = 2 * X.squeeze() + 1 + np.random.randn(100) * 0.1
    
    # 创建模型
    model = LinearModel(input_dim=1)
    loss = MSELoss()
    optimizer = SGDOptimizer(learning_rate=0.1)
    
    # 训练
    trainer = Trainer(model, loss, optimizer)
    trainer.train(X, y, epochs=100)
    
    # 预测
    test_X = np.array([[0], [1], [2]])
    predictions = model.predict(test_X)
    print(f"\n预测结果: {predictions}")