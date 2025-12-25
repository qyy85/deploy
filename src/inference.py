"""
PyTorch推理引擎

使用PyTorch进行模型推理，支持DGL图神经网络。
支持两种加载模式：
- native: 原生 PyTorch 模式，使用 state_dict 方式加载（推荐）
  - 从 checkpoint 中加载 encoder_config, encoder_state_dict, classifier_config, classifier_state_dict
  - 重建模型结构并加载权重
- jit: TorchScript 模式，使用 torch.jit.load 加载
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import dgl

# 添加项目根目录到路径，确保能找到 src.models 等模块
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入模型类
from .wrapper import ClassifierWrapper
from .models import DGI, ClassifyNet


class ModelInference:
    """
    PyTorch模型推理引擎
    
    支持两种模式：
    - native: 使用 state_dict 方式加载（推荐）
      - 从 checkpoint 中重建 encoder 和 classifier
      - 更安全、更灵活，不依赖完整的类定义
    - jit: 使用 TorchScript 模式加载
    """
    
    def __init__(
        self,
        model_path: str,
        class_mapping: Optional[Dict[int, str]] = None,
        device: str = "cpu",
        mode: str = "native"
    ):
        """
        初始化推理引擎
        
        Args:
            model_path: 导出的模型路径 (.pt)
            class_mapping: 类别ID到名称的映射
            device: 推理设备 ("cpu" 或 "cuda")
            mode: 加载模式 "native" 或 "jit"
        """
        self.device = torch.device(device)
        self.class_mapping = class_mapping or {}
        self.model = None
        self.mode = mode
        self.num_classes = len(class_mapping) if class_mapping else None
        
        # 加载模型
        self._load_model(model_path)
    
    def _load_model(self, model_path: str):
        """加载模型（使用 state_dict 方式）"""
        model_path = Path(model_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        print(f"📦 加载模型: {model_path}")
        print(f"   模式: {self.mode}")
        
        try:
            if self.mode == "native":
                # 原生模式：使用 state_dict 方式加载
                # 加载检查点
                checkpoint = torch.load(str(model_path), map_location=self.device)
                
                # 检查 checkpoint 格式
                if isinstance(checkpoint, dict) and 'encoder_config' in checkpoint and 'classifier_config' in checkpoint:
                    # 新格式：包含配置和 state_dict
                    # 重建编码器
                    encoder = DGI(**checkpoint['encoder_config'])
                    encoder.load_state_dict(checkpoint['encoder_state_dict'])
                    
                    # 重建分类器
                    classifier = ClassifyNet(**checkpoint['classifier_config'])
                    classifier.load_state_dict(checkpoint['classifier_state_dict'])
                    
                    # 组合成包装器
                    self.model = ClassifierWrapper(encoder, classifier)
                else:
                    raise ValueError(f"不支持的模型格式。期望包含 'encoder_config' 和 'classifier_config' 的字典，或 ClassifierWrapper 对象")
                
                # 设置为评估模式
                self.model.eval()
                self.model.to(self.device)
                print(f"✓ 模型加载成功 (state_dict 方式)，设备: {self.device}")
                
            elif self.mode == "jit":
                # JIT 模式：使用 torch.jit.load
                self.model = torch.jit.load(str(model_path), map_location=self.device)
                self.model.eval()
                self.model.to(self.device)
                print(f"✓ 模型加载成功 (TorchScript)，设备: {self.device}")
                
            else:
                raise ValueError(f"不支持的加载模式: {self.mode}")
                
        except Exception as e:
            raise RuntimeError(f"加载模型失败: {e}")
    
    @torch.no_grad()
    def predict(self, graph: dgl.DGLGraph) -> Dict:
        """
        执行单个图预测
        
        Args:
            graph: DGL异构图
            
        Returns:
            预测结果字典
        """
        start_time = time.time()
        
        # 移动图到设备
        graph = graph.to(self.device)
        
        # 推理（native 和 jit 模式统一调用方式）
        logits = self.model(graph)
        
        # 计算概率
        probabilities = torch.softmax(logits, dim=-1)
        
        # 解析结果
        predicted_class_id = int(torch.argmax(logits, dim=-1).item())
        confidence = float(torch.max(probabilities).item())
        
        # 构建概率分布
        prob_dist = {}
        probs_np = probabilities.cpu().numpy().flatten()
        for i, prob in enumerate(probs_np):
            class_name = self.class_mapping.get(i, f"Class_{i}")
            prob_dist[class_name] = float(prob)
        
        total_time = time.time() - start_time
        
        return {
            "predicted_class_id": predicted_class_id,
            "predicted_class": self.class_mapping.get(
                predicted_class_id, 
                f"Class_{predicted_class_id}"
            ),
            "confidence": confidence,
            "probabilities": prob_dist,
            "inference_time": total_time
        }
    
    @torch.no_grad()
    def predict_batch(self, batched_graph: dgl.DGLGraph) -> List[Dict]:
        """
        批量预测（接受已batch的图）
        
        Args:
            batched_graph: 已batch的DGL图
            
        Returns:
            预测结果列表
        """
        start_time = time.time()
        
        # 移动图到设备
        batched_graph = batched_graph.to(self.device)
        
        # 推理
        logits = self.model(batched_graph)
        probabilities = torch.softmax(logits, dim=-1)
        
        # 解析结果
        results = []
        probs_np = probabilities.cpu().numpy()
        
        for i in range(len(probs_np)):
            predicted_class_id = int(np.argmax(probs_np[i]))
            confidence = float(np.max(probs_np[i]))
            
            prob_dist = {
                self.class_mapping.get(j, f"Class_{j}"): float(prob)
                for j, prob in enumerate(probs_np[i])
            }
            
            results.append({
                "predicted_class_id": predicted_class_id,
                "predicted_class": self.class_mapping.get(
                    predicted_class_id,
                    f"Class_{predicted_class_id}"
                ),
                "confidence": confidence,
                "probabilities": prob_dist
            })
        
        total_time = time.time() - start_time
        avg_time = total_time / len(results) if results else 0
        
        for result in results:
            result["inference_time"] = avg_time
        
        return results
    
    def get_top_k(self, graph: dgl.DGLGraph, k: int = 3) -> List[Tuple[str, float]]:
        """获取Top-K预测结果"""
        result = self.predict(graph)
        sorted_probs = sorted(
            result["probabilities"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_probs[:k]
    
    def is_ready(self) -> bool:
        """检查推理引擎是否就绪"""
        return self.model is not None
