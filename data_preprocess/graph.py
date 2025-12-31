from typing import Dict, List, Optional, Any, Set
from data_preprocess.node import Node, NodeFactory
from data_preprocess.edge import Edge, EdgeFactory
from data_preprocess.feature_config import FeatureConfig
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
        self.nodes[node.node_id] = node
        
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
            self.nodes_by_type[node.node_type].append(node)
        
        # 为每种节点类型创建局部ID映射
        for ntype, node_list in self.nodes_by_type.items():
            for i, node in enumerate(node_list):
                node_type_id_mapping[ntype][node.node_id] = i
                nodes_feat_by_type[ntype].append(node.get_feature_vector())
        
        # 按边类型分组并构建图数据结构
        self.hetero_graph_data = {}
        edge_features_by_type = defaultdict(list)
        
        for edge in self.edges:
            src_node = self.nodes[edge.src_node_id]
            dst_node = self.nodes[edge.dst_node_id]
            
            canonical_etype = (src_node.node_type, edge.edge_type, dst_node.node_type)
            
            # 获取在DGL中的局部ID
            src_dgl_id = node_type_id_mapping[src_node.node_type][edge.src_node_id]
            dst_dgl_id = node_type_id_mapping[dst_node.node_type][edge.dst_node_id]
            
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
    
    def to_homogeneous(self) -> dgl.DGLGraph:
        """转换为同构图 - 基于特征对齐的方法"""
        if self.dgl_graph is None:
            self.build_dgl_graph()
        
        # 特征对齐 - 先对节点特征进行维度统一
        self._align_node_features()
        
        # 边特征对齐
        self._align_edge_features()
        
        homo_graph = dgl.to_homogeneous(self.dgl_graph, ndata=['x'], edata=['x'])
        
        return homo_graph
    
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
            if node.node_type not in stats['node_types']:
                stats['node_types'][node.node_type] = 0
            stats['node_types'][node.node_type] += 1
        
        # 统计边类型分布
        for edge in self.edges:
            if edge.edge_type not in stats['edge_types']:
                stats['edge_types'][edge.edge_type] = 0
            stats['edge_types'][edge.edge_type] += 1
        
        return stats
    
    def _collect_all_specific_features(self) -> List[str]:
        """收集所有节点类型的特有特征名称（去重）"""
        all_specific_features = set()
        
        # 从FeatureConfig中收集所有特有特征
        for node_type, features in FeatureConfig.NODE_SPECIFIC_FEATURES.items():
            all_specific_features.update(features.keys())
        
        return sorted(list(all_specific_features))  # 排序保证顺序一致性
    
    def _align_node_features(self):
        """对齐节点特征维度 - 基于原始代码的特征对齐逻辑"""
        
        print("开始节点特征对齐...")
        
        # 计算特征维度
        main_dim = FeatureConfig.get_main_feature_dim()  # 9维
        all_specific_features = self._collect_all_specific_features()
        specific_dim = len(all_specific_features)
        total_dim = main_dim + specific_dim
        
        # 为每种节点类型创建特征名称到索引的映射
        specific_feature_to_idx = {feat: i for i, feat in enumerate(all_specific_features)}
        
        # 处理每种节点类型的特征
        for ntype in self.dgl_graph.ntypes:
            print(f"\n处理节点类型: {ntype}")
            
            current_feat = self.dgl_graph.nodes[ntype].data['x']
            node_num = current_feat.shape[0]
            current_dim = current_feat.shape[1]
            
            print(f"当前特征形状: {current_feat.shape}")
            
            # 创建对齐后的特征矩阵
            aligned_feat = torch.zeros(node_num, total_dim)
            
            # 1. 填充主要特征（前9维）
            main_feat_dim = min(main_dim, current_dim)
            aligned_feat[:, :main_feat_dim] = current_feat[:, :main_feat_dim]
            # print(f"填充主要特征: 前{main_feat_dim}维")
            
            # 2. 填充特有特征
            if ntype in FeatureConfig.NODE_SPECIFIC_FEATURES:
                type_specific_features = list(FeatureConfig.NODE_SPECIFIC_FEATURES[ntype].keys())
                print(f"节点{ntype}的特有特征: {type_specific_features}")
                
                # 计算特有特征在原始特征向量中的起始位置
                feat_idx = main_dim  # 从主要特征之后开始
                
                for feat_name in type_specific_features:
                    if feat_name in specific_feature_to_idx:
                        # 找到该特征在全局特征向量中的位置
                        global_idx = main_dim + specific_feature_to_idx[feat_name]
                        
                        # 从原始特征向量中复制数据
                        if feat_idx < current_dim:
                            aligned_feat[:, global_idx] = current_feat[:, feat_idx]
                            print(f"  特征 '{feat_name}': 从位置{feat_idx} -> 全局位置{global_idx}")
                        feat_idx += 1
            
            # 更新图中的特征
            self.dgl_graph.nodes[ntype].data['x'] = aligned_feat
    
    def _align_edge_features(self):
        """对齐边特征维度"""
        
        print("\n开始边特征对齐...")
        
        # 边特征统一为4维：[连接类型, 参数1, 参数2, 参数3]
        # arc: [0, 内外, 圆角半径, 过渡面夹角]  
        # straight: [1, 0, 0, 面夹角]
        target_edge_dim = 4
        
        for canonical_etype in self.dgl_graph.canonical_etypes:
            if 'x' in self.dgl_graph.edges[canonical_etype].data:
                current_feat = self.dgl_graph.edges[canonical_etype].data['x']
                num_edges = current_feat.shape[0]
                current_dim = current_feat.shape[1]
                
                print(f"边类型 {canonical_etype}: 当前维度{current_dim} -> 目标维度{target_edge_dim}")
                
                if current_dim < target_edge_dim:
                    # 需要扩展维度
                    aligned_feat = torch.zeros(num_edges, target_edge_dim)
                    
                    # 根据边类型进行特征对齐
                    edge_type = canonical_etype[1]  # 获取边类型名称
                    
                    if edge_type == 'arc' and current_dim >= 4:
                        # arc边有4个特征，直接复制
                        aligned_feat[:, :4] = current_feat[:, :4]
                    elif edge_type == 'straight' and current_dim >= 2:
                        # straight边有2个特征，填充到4维
                        aligned_feat[:, 0] = current_feat[:, 0]
                        aligned_feat[:, 3] = current_feat[:, 1]
                    else:
                        # 其他情况，尽可能复制已有特征
                        copy_dim = min(current_dim, target_edge_dim)
                        aligned_feat[:, :copy_dim] = current_feat[:, :copy_dim]
                    
                    self.dgl_graph.edges[canonical_etype].data['x'] = aligned_feat
                    print(f"  对齐完成: {current_feat.shape} -> {aligned_feat.shape}")
