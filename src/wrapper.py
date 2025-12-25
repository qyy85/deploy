"""
模型包装器

将编码器和分类器组合为单一模块，用于导出和推理。
"""

import torch
import torch.nn as nn
import dgl


class ClassifierWrapper(nn.Module):
    """
    分类器包装器
    
    将编码器和分类器组合为单一模块
    """
    
    def __init__(self, encoder: nn.Module, classifier: nn.Module):
        super().__init__()
        self.encoder = encoder
        self.classifier = classifier
    
    def forward(self, batched_graph: dgl.DGLGraph) -> torch.Tensor:
        """
        前向传播
        
        Args:
            batched_graph: 批量DGL图
            
        Returns:
            logits: 分类logits [batch_size, num_classes]
        """
        # 图编码
        graph_embedding = self.encoder(batched_graph)
        # 分类
        logits = self.classifier(graph_embedding)
        return logits
    
    def predict(self, batched_graph: dgl.DGLGraph) -> torch.Tensor:
        """预测类别"""
        logits = self.forward(batched_graph)
        return torch.argmax(logits, dim=-1)
    
    def predict_proba(self, batched_graph: dgl.DGLGraph) -> torch.Tensor:
        """预测概率"""
        logits = self.forward(batched_graph)
        return torch.softmax(logits, dim=-1)

