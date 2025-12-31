from typing import Dict, List, Optional, Any, Set
from .core.geometric_faces.base_face import BaseFace as Node
from .core.geometric_edges.base_edge import BaseEdge as Edge
from collections import defaultdict
import dgl
import torch

# 图类实现
class HeterogeneousGraph:
    """异构图类 - 支持转换为同构图"""
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}  # node_id -> Node对象
        self.edges: List[Edge] = []
        self.dgl_graph: Optional[dgl.DGLGraph] = None
        self._node_id_mapping = {}  # 内部ID映射
    def save_graph(self, save_path: str):
        """保存图"""
        dgl.save_graphs(save_path, self.dgl_graph)
    
    def add_node(self, node: Node):
        """添加节点"""
        self.nodes[node.id] = node
        
    def add_edge(self, edge: Edge):
        """添加边"""
        # 验证端点存在
        if edge.src_node_id in self.nodes and edge.dst_node_id in self.nodes:
            self.edges.append(edge)
        else:
            print(f"Warning: 尝试添加边，但端点不存在: {edge.src_node_id} -> {edge.dst_node_id}")
    
    def build_dgl_graph(self) -> dgl.DGLGraph:
        """构建异构DGL图"""
        if not self.nodes:
            raise ValueError("图中没有节点，无法构建DGL图")
            
        # 按节点类型分组
        self.nodes_by_type = defaultdict(list)
        nodes_feat_by_type = defaultdict(list)
        node_type_id_mapping = defaultdict(dict)  # {node_type: {original_id: dgl_id}}
        
        for node in self.nodes.values():
            self.nodes_by_type[node.type].append(node)
        
        # 为每种节点类型创建局部ID映射
        for ntype, node_list in self.nodes_by_type.items():
            for i, node in enumerate(node_list):
                node_type_id_mapping[ntype][node.id] = i
                nodes_feat_by_type[ntype].append(node.get_feature_vector())
        
        # 按边类型分组并构建图数据结构
        self.hetero_graph_data = {}
        edge_features_by_type = defaultdict(list)
        
        for edge in self.edges:
            src_node = self.nodes[edge.src_node_id]
            dst_node = self.nodes[edge.dst_node_id]
            
            canonical_etype = (src_node.type, edge.type, dst_node.type)
            
            # 获取在DGL中的局部ID
            src_dgl_id = node_type_id_mapping[src_node.type][edge.src_node_id]
            dst_dgl_id = node_type_id_mapping[dst_node.type][edge.dst_node_id]
            
            if canonical_etype not in self.hetero_graph_data:
                self.hetero_graph_data[canonical_etype] = ([], [])
            
            self.hetero_graph_data[canonical_etype][0].append(src_dgl_id)
            self.hetero_graph_data[canonical_etype][1].append(dst_dgl_id)
            edge_features_by_type[canonical_etype].append(edge.get_feature_vector())
        
        # 转换为tensor
        for canonical_etype in self.hetero_graph_data:
            src_list, dst_list = self.hetero_graph_data[canonical_etype]
            self.hetero_graph_data[canonical_etype] = (
                torch.tensor(src_list, dtype=torch.long),
                torch.tensor(dst_list, dtype=torch.long)
            )
        
        # 创建异构图
        self.dgl_graph = dgl.heterograph(self.hetero_graph_data)
        
        # 添加节点特征
        for ntype, node_feat in nodes_feat_by_type.items():
            if node_feat:
                self.dgl_graph.nodes[ntype].data['x'] = torch.tensor(
                    node_feat, dtype=torch.float32
                )
        
        # 添加边特征
        for canonical_etype, edge_feat_list in edge_features_by_type.items():
            if edge_feat_list:
                self.dgl_graph.edges[canonical_etype].data['x'] = torch.tensor(
                    edge_feat_list, dtype=torch.float32
                )
        
        return self.dgl_graph
    
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图的统计信息"""
        stats = {
            'num_nodes': len(self.nodes),
            'num_edges': len(self.edges),
            'node_types': {},
            'edge_types': {}
        }
        
        # 统计节点类型分布
        for node in self.nodes.values():
            if node.type not in stats['node_types']:
                stats['node_types'][node.type] = 0
            stats['node_types'][node.type] += 1
        
        # 统计边类型分布
        for edge in self.edges:
            if edge.edge_type not in stats['edge_types']:
                stats['edge_types'][edge.type] = 0
            stats['edge_types'][edge.type] += 1
        
        return stats
    def save(self, path):
        dgl.save_graphs(path, self.dgl_graph)