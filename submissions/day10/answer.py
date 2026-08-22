"""Day 10: nn.Module神经网络 - 多层感知机"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class SimpleMLP(nn.Module):
    """简单多层感知机"""
    
    def __init__(self, input_size, hidden_size, output_size):
        super(SimpleMLP, self).__init__()
        
        # 定义层
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, output_size)
        
        # 定义Dropout
        self.dropout = nn.Dropout(0.2)
    
    def forward(self, x):
        # 第一层 + ReLU + Dropout
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        
        # 第二层 + ReLU + Dropout
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        # 输出层
        x = self.fc3(x)
        return x


class CNNClassifier(nn.Module):
    """简单CNN分类器"""
    
    def __init__(self, num_classes=10):
        super(CNNClassifier, self).__init__()
        
        # 卷积层
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        
        # 全连接层
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, num_classes)
        
        # BatchNorm
        self.bn1 = nn.BatchNorm2d(32)
        self.bn2 = nn.BatchNorm2d(64)
    
    def forward(self, x):
        # 卷积块1
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        
        # 卷积块2
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        
        # 展平
        x = x.view(-1, 64 * 7 * 7)
        
        # 全连接层
        x = F.relu(self.fc1(x))
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.fc2(x)
        
        return x


def train_example():
    """训练示例"""
    # 创建模型
    model = SimpleMLP(784, 256, 10)
    
    # 定义损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    # 生成虚拟数据
    batch_size = 32
    X = torch.randn(batch_size, 784)  # 28x28图像展平
    y = torch.randint(0, 10, (batch_size,))
    
    # 训练循环
    model.train()
    for epoch in range(5):
        # 前向传播
        outputs = model(X)
        loss = criterion(outputs, y)
        
        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        print(f"Epoch {epoch+1}/5, Loss: {loss.item():.4f}")
    
    return model


if __name__ == "__main__":
    print("PyTorch nn.Module教程\n")
    
    # 创建简单MLP
    mlp = SimpleMLP(784, 256, 10)
    print("MLP模型:")
    print(mlp)
    print(f"\n参数数量: {sum(p.numel() for p in mlp.parameters()):,}")
    
    # 训练示例
    print("\n训练示例:")
    trained_model = train_example()
    
    # 测试推理
    model.eval()
    test_input = torch.randn(1, 784)
    with torch.no_grad():
        output = trained_model(test_input)
    print(f"\n推理输出形状: {output.shape}")