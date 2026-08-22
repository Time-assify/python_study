# Phase 2 Tests: PyTorch (Day 8-18)
import pytest


class TestTensorConcepts:
    """Tensor概念测试"""
    
    def test_tensor_creation(self):
        """测试Tensor创建"""
        # 模拟tensor操作概念
        tensor = [1, 2, 3, 4, 5]
        assert len(tensor) == 5
        assert tensor[0] == 1
    
    def test_tensor_operations(self):
        """测试Tensor操作"""
        # 模拟数学运算
        a = [1, 2, 3]
        b = [4, 5, 6]
        c = [a[i] + b[i] for i in range(3)]
        assert c == [5, 7, 9]
    
    def test_tensor_reshape(self):
        """测试Tensor变形"""
        # 模拟reshape操作
        tensor = [1, 2, 3, 4, 5, 6]
        reshaped = [[1, 2, 3], [4, 5, 6]]
        assert len(reshaped) == 2
        assert len(reshaped[0]) == 3


class TestAutogradConcepts:
    """Autograd概念测试"""
    
    def test_gradient_basic(self):
        """测试梯度基本概念"""
        # y = x^2, dy/dx = 2x
        x = 3
        y = x ** 2
        gradient = 2 * x
        assert gradient == 6
    
    def test_gradient_chain_rule(self):
        """测试链式法则"""
        # y = (x + 1)^2, dy/dx = 2(x + 1)
        x = 2
        y = (x + 1) ** 2
        gradient = 2 * (x + 1)
        assert gradient == 6


class TestNNModuleConcepts:
    """nn.Module概念测试"""
    
    def test_linear_layer(self):
        """测试线性层概念"""
        # y = xW + b
        x = [1, 2, 3]
        W = [[1, 0], [0, 1], [1, 1]]
        b = [0, 0]
        
        # 简单矩阵乘法
        y = [sum(x[i] * W[i][j] for i in range(3)) + b[j] for j in range(2)]
        assert y == [4, 5]
    
    def test_activation_relu(self):
        """测试ReLU激活函数"""
        def relu(x):
            return max(0, x)
        
        assert relu(-5) == 0
        assert relu(0) == 0
        assert relu(5) == 5
    
    def test_activation_sigmoid(self):
        """测试Sigmoid激活函数"""
        import math
        
        def sigmoid(x):
            return 1 / (1 + math.exp(-x))
        
        assert 0 < sigmoid(0) < 1
        assert sigmoid(0) == pytest.approx(0.5, abs=0.01)


class TestDatasetConcepts:
    """Dataset概念测试"""
    
    def test_dataset_interface(self):
        """测试Dataset接口"""
        class SimpleDataset:
            def __init__(self, data):
                self.data = data
            
            def __len__(self):
                return len(self.data)
            
            def __getitem__(self, idx):
                return self.data[idx]
        
        dataset = SimpleDataset([1, 2, 3, 4, 5])
        assert len(dataset) == 5
        assert dataset[2] == 3


class TestOptimizerConcepts:
    """优化器概念测试"""
    
    def test_sgd_update(self):
        """测试SGD更新规则"""
        # w = w - lr * gradient
        w = 1.0
        lr = 0.1
        gradient = 2.0
        
        w_new = w - lr * gradient
        assert w_new == 0.8
    
    def test_learning_rate_effect(self):
        """测试学习率影响"""
        w = 1.0
        gradient = 2.0
        
        w_large_lr = w - 0.5 * gradient
        w_small_lr = w - 0.01 * gradient
        
        assert w_large_lr < w_small_lr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])