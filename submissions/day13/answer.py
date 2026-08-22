"""Day 13: CNN卷积神经网络 - 图像分类"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class SimpleCNN(nn.Module):
    """简单CNN模型"""
    
    def __init__(self, num_classes=10):
        super(SimpleCNN, self).__init__()
        
        # 卷积层
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1)
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        
        # 池化层
        self.pool = nn.MaxPool2d(2, 2)
        
        # 全连接层
        self.fc1 = nn.Linear(64 * 4 * 4, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, num_classes)
        
        # Dropout
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x):
        # 卷积块1
        x = self.pool(F.relu(self.conv1(x)))  # 32x32 -> 16x16x16
        
        # 卷积块2
        x = self.pool(F.relu(self.conv2(x)))  # 16x16 -> 8x8x32
        
        # 卷积块3
        x = self.pool(F.relu(self.conv3(x)))  # 8x8 -> 4x4x64
        
        # 展平
        x = x.view(-1, 64 * 4 * 4)
        
        # 全连接层
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        
        return x


class ResidualBlock(nn.Module):
    """残差块"""
    
    def __init__(self, channels):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)
    
    def forward(self, x):
        residual = x
        
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        
        out += residual  # 跳跃连接
        out = F.relu(out)
        
        return out


class ResNet(nn.Module):
    """简单ResNet"""
    
    def __init__(self, num_classes=10):
        super(ResNet, self).__init__()
        
        # 初始卷积
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        
        # 残差块
        self.res1 = ResidualBlock(32)
        self.res2 = ResidualBlock(32)
        self.res3 = ResidualBlock(32)
        
        # 池化
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        
        # 全连接
        self.fc = nn.Linear(32, num_classes)
    
    def forward(self, x):
        # 初始卷积
        x = F.relu(self.bn1(self.conv1(x)))
        
        # 残差块
        x = self.res1(x)
        x = self.res2(x)
        x = self.res3(x)
        
        # 全局平均池化
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        
        # 分类
        x = self.fc(x)
        
        return x


def count_parameters(model):
    """统计模型参数"""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable


if __name__ == "__main__":
    print("CNN卷积神经网络教程\n")
    
    # 创建模型
    cnn = SimpleCNN(num_classes=10)
    print("SimpleCNN模型:")
    print(cnn)
    
    total, trainable = count_parameters(cnn)
    print(f"\n总参数: {total:,}")
    print(f"可训练参数: {trainable:,}")
    
    # 测试前向传播
    x = torch.randn(1, 3, 32, 32)  # batch=1, channels=3, 32x32
    output = cnn(x)
    print(f"\n输入形状: {x.shape}")
    print(f"输出形状: {output.shape}")
    
    # ResNet示例
    print("\n" + "="*50)
    resnet = ResNet(num_classes=10)
    print("\nResNet模型:")
    print(resnet)
    
    output = resnet(x)
    print(f"\nResNet输出形状: {output.shape}")