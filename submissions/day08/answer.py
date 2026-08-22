"""Day 08: Tensor基础 - PyTorch Tensor操作"""

# 注意：这个示例需要安装PyTorch
# pip install torch

import torch

def tensor_basics():
    """Tensor基础操作"""
    print("=== Tensor创建 ===")
    
    # 从Python列表创建
    x = torch.tensor([1, 2, 3, 4, 5])
    print(f"从列表创建: {x}")
    
    # 创建零张量
    zeros = torch.zeros(3, 4)
    print(f"零张量:\n{zeros}")
    
    # 创建一
    ones = torch.ones(2, 3)
    print(f"一张量:\n{ones}")
    
    # 创建随机张量
    rand = torch.rand(3, 3)
    print(f"随机张量:\n{rand}")
    
    # 创建等差序列
    arange = torch.arange(0, 10, 2)
    print(f"等差序列: {arange}")
    
    return x


def tensor_operations():
    """Tensor运算"""
    print("\n=== Tensor运算 ===")
    
    a = torch.tensor([1.0, 2.0, 3.0])
    b = torch.tensor([4.0, 5.0, 6.0])
    
    # 基本运算
    print(f"加法: {a + b}")
    print(f"乘法: {a * b}")
    print(f"点积: {torch.dot(a, b)}")
    
    # 矩阵运算
    m1 = torch.randn(2, 3)
    m2 = torch.randn(3, 2)
    print(f"矩阵乘法:\n{torch.mm(m1, m2)}")
    
    return a, b


def tensor_indexing():
    """Tensor索引"""
    print("\n=== Tensor索引 ===")
    
    x = torch.arange(12).reshape(3, 4)
    print(f"原始张量:\n{x}")
    
    # 基本索引
    print(f"第一行: {x[0]}")
    print(f"第一列: {x[:, 0]}")
    print(f"子矩阵:\n{x[0:2, 1:3]}")
    
    # 条件索引
    mask = x > 5
    print(f"大于5的元素: {x[mask]}")
    
    return x


def tensor_reshape():
    """Tensor变形"""
    print("\n=== Tensor变形 ===")
    
    x = torch.arange(12)
    print(f"原始: {x}")
    print(f"形状: {x.shape}")
    
    # reshape
    y = x.reshape(3, 4)
    print(f"reshape(3,4):\n{y}")
    
    # view
    z = x.view(4, 3)
    print(f"view(4,3):\n{z}")
    
    # 转置
    t = y.t()
    print(f"转置:\n{t}")
    
    # 展平
    flat = y.flatten()
    print(f"展平: {flat}")
    
    return x


def gpu_operations():
    """GPU操作（如果可用）"""
    print("\n=== GPU操作 ===")
    
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"使用GPU: {torch.cuda.get_device_name(0)}")
        
        # 在GPU上创建张量
        x_gpu = torch.randn(3, 3).to(device)
        print(f"GPU张量:\n{x_gpu}")
        
        # GPU计算
        y_gpu = x_gpu * 2
        print(f"GPU计算结果:\n{y_gpu}")
    else:
        print("GPU不可用，使用CPU")
        x_cpu = torch.randn(3, 3)
        print(f"CPU张量:\n{x_cpu}")


if __name__ == "__main__":
    print("PyTorch Tensor基础教程\n")
    
    # 检查PyTorch版本
    print(f"PyTorch版本: {torch.__version__}")
    print(f"CUDA可用: {torch.cuda.is_available()}\n")
    
    tensor_basics()
    tensor_operations()
    tensor_indexing()
    tensor_reshape()
    gpu_operations()
    
    print("\n教程完成！")