# Phase 3 Tests: Deep Learning (Day 19-30)
import pytest


class TestResNetConcepts:
    """ResNet概念测试"""
    
    def test_residual_connection(self):
        """测试残差连接"""
        # F(x) + x
        def residual_block(x):
            # 模拟恒等映射 + 残差
            identity = x
            residual = x * 0.1  # 模拟小的变换
            return identity + residual
        
        x = 5
        y = residual_block(x)
        assert y == 5.5
    
    def test_skip_connection_gradient(self):
        """测试跳跃连接梯度流动"""
        # 梯度可以直接通过跳跃连接流动
        gradient_output = 1.0
        gradient_skip = gradient_output  # 梯度无衰减
        assert gradient_skip == 1.0


class TestCNNConcepts:
    """CNN概念测试"""
    
    def test_convolution_operation(self):
        """测试卷积操作"""
        # 简单的1D卷积
        def conv1d(input_data, kernel, stride=1):
            output = []
            for i in range(0, len(input_data) - len(kernel) + 1, stride):
                conv_sum = sum(input_data[i+j] * kernel[j] for j in range(len(kernel)))
                output.append(conv_sum)
            return output
        
        input_data = [1, 2, 3, 4, 5]
        kernel = [1, 0, -1]
        output = conv1d(input_data, kernel)
        assert len(output) == 3
        assert output[0] == 1*1 + 2*0 + 3*(-1)  # = -2
        assert output[1] == 2*1 + 3*0 + 4*(-1)  # = -2
        assert output[2] == 3*1 + 4*0 + 5*(-1)  # = -2
    
    def test_pooling_operation(self):
        """测试池化操作"""
        # 最大池化
        def max_pool(input_data, pool_size=2):
            output = []
            for i in range(0, len(input_data), pool_size):
                output.append(max(input_data[i:i+pool_size]))
            return output
        
        input_data = [1, 3, 2, 4, 5, 6]
        output = max_pool(input_data)
        assert output == [3, 4, 6]


class TestBatchNormConcepts:
    """BatchNorm概念测试"""
    
    def test_batch_norm_formula(self):
        """测试批归一化公式"""
        import math
        
        def batch_norm(x, gamma=1, beta=0, eps=1e-5):
            mean = sum(x) / len(x)
            variance = sum((xi - mean) ** 2 for xi in x) / len(x)
            normalized = [(xi - mean) / math.sqrt(variance + eps) for xi in x]
            return [gamma * xi + beta for xi in normalized]
        
        x = [1, 2, 3, 4, 5]
        result = batch_norm(x)
        assert len(result) == 5


class TestTransferLearningConcepts:
    """迁移学习概念测试"""
    
    def test_feature_extraction(self):
        """测试特征提取概念"""
        # 冻结的特征提取器
        class FeatureExtractor:
            def __init__(self):
                self.frozen = True
            
            def extract(self, x):
                return [x[i] * 0.5 for i in range(len(x))]
        
        extractor = FeatureExtractor()
        features = extractor.extract([1, 2, 3])
        assert features == [0.5, 1.0, 1.5]


class TestTransformerConcepts:
    """Transformer概念测试"""
    
    def test_self_attention(self):
        """测试自注意力机制"""
        import math
        
        def attention(Q, K, V):
            d_k = len(Q)
            scores = sum(Q[i] * K[i] for i in range(d_k)) / math.sqrt(d_k)
            weights = math.exp(scores)
            return [V[i] * weights for i in range(len(V))]
        
        Q = [1, 0, 1]
        K = [1, 0, 1]
        V = [1, 2, 3]
        output = attention(Q, K, V)
        assert len(output) == 3
    
    def test_positional_encoding(self):
        """测试位置编码"""
        import math
        
        def positional_encoding(pos, d_model):
            pe = []
            for i in range(0, d_model, 2):
                pe.append(math.sin(pos / (10000 ** (i / d_model))))
                pe.append(math.cos(pos / (10000 ** (i / d_model))))
            return pe
        
        pe = positional_encoding(0, 4)
        assert len(pe) == 4


class TestYOLOConcepts:
    """YOLO概念测试"""
    
    def test_grid_division(self):
        """测试网格划分"""
        image_size = 416
        grid_size = 13
        cell_size = image_size // grid_size
        assert cell_size == 32
    
    def test_nms_basic(self):
        """测试非极大值抑制概念"""
        def iou(box1, box2):
            # 简化的IoU计算
            x1 = max(box1[0], box2[0])
            y1 = max(box1[1], box2[1])
            x2 = min(box1[2], box2[2])
            y2 = min(box1[3], box2[3])
            
            intersection = max(0, x2 - x1) * max(0, y2 - y1)
            area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
            area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
            union = area1 + area2 - intersection
            
            return intersection / union if union > 0 else 0
        
        box1 = [0, 0, 10, 10]
        box2 = [5, 5, 15, 15]
        assert 0 < iou(box1, box2) < 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])