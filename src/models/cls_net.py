import torch
import torch.nn as nn
import torch.nn.functional as F

class ClassifyNet(nn.Module):
    """
    分类器网络
    """
    def __init__(self, input_dim, num_classes, dropout=0.3, use_batch_norm=True, reduction_ratio=4):
        super().__init__()
        self.use_batch_norm = use_batch_norm
        self.reduction_ratio = reduction_ratio
        
        # LayerNorm: 输入特征归一化
        self.layer_norm1 = nn.LayerNorm(input_dim)
        
        # ★ 新增：通道注意力模块（Squeeze-and-Excitation风格）
        # 压缩维度到 input_dim // reduction_ratio，减少参数量
        # self.channel_attention = nn.Sequential(
        #     nn.Linear(input_dim, input_dim // reduction_ratio, bias=False),
        #     nn.ReLU(inplace=True),
        #     nn.Linear(input_dim // reduction_ratio, input_dim, bias=False),
        #     nn.Sigmoid()
        # )
        
        # 第一层：特征适配层（保持维度）
        self.linear1 = nn.Linear(input_dim, input_dim, bias=True)
        self.bn1 = nn.BatchNorm1d(input_dim) if use_batch_norm else nn.Identity()
        self.dp1 = nn.Dropout(p=dropout)
        
        # 输出层：分类决策
        self.linear4 = nn.Linear(input_dim, num_classes, bias=True)
        
        # 权重初始化
        for m in self.modules():
            self.weights_init(m)    

    def weights_init(self, m):
        """权重初始化：Kaiming初始化适合ReLU"""
        if isinstance(m, nn.Linear):
            torch.nn.init.kaiming_uniform_(m.weight.data, nonlinearity='relu')
            if m.bias is not None:
                m.bias.data.fill_(0.0)

    def forward(self, x):   
        # 输入归一化
        x_norm = self.layer_norm1(x)
        
        # ★ 通道注意力：自适应调整特征重要性
        # 学习每个特征维度的权重 (batch_size, input_dim)
        # attention_weights = self.channel_attention(x_norm)
        # 逐元素相乘，重新加权特征
        # x_attended = x_norm * attention_weights
        x_attended = x_norm
        # 特征适配层
        x = self.linear1(x_attended)
        x = self.bn1(x)
        x = F.relu(x, inplace=True)
        x = self.dp1(x)
        
        # 输出层：分类决策（无激活函数，输出logits）
        logits = self.linear4(x)
        return logits