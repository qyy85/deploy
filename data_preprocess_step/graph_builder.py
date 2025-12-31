import dgl
from typing import Dict, Optional, Any, Union
from .src.graph import HeterogeneousGraph
from .src.feature_extract import FeatureExtractor

class GraphBuilder:
    """图构建器类 - 协调整个图构建过程"""
    
    def __init__(self):
        self.graph: Optional[HeterogeneousGraph] = None
        self.feature_extractor = FeatureExtractor()
        
    def from_step(self, step_path: str) -> 'GraphBuilder':
        """从XML内容构建图"""
        # 解析XML
        parsed_data = self.feature_extractor.analyze_file(step_path)
        # 创建新图
        self.graph = HeterogeneousGraph()
        
        # 创建节点
        for node in parsed_data['nodes']:
            self.graph.add_node(node)
        
        # 创建边
        for edge in parsed_data['edges']:
            self.graph.add_edge(edge)
        
        return self.graph
        
    def build_heterogeneous_graph(self) -> dgl.DGLGraph:
        """构建异构图"""
        if self.graph is None:
            raise ValueError("请先调用 from_step() 解析数据")
        
        return self.graph.build_dgl_graph()
    
    def get_graph(self) -> HeterogeneousGraph:
        """获取内部图对象"""
        return self.graph
    

    