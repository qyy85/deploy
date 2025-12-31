import torch
import dgl
from typing import List, Dict, Tuple

def data_collate(batch):
    """批量合并异构图数据，自动处理有标签/无标签情况"""
    if not batch:
        return {}
    
    # 检测是否有标签
    has_labels = ("label" in batch[0])
    has_sample_name = ("sample_name" in batch[0])

    if len(batch) == 1:
        sample = batch[0]
        result = {"graph": sample["graph"]}
        if has_labels:
            result["label"] = sample["label"]
        if has_sample_name:
            result["sample_name"] = sample["sample_name"]
        return result
    
    try:
        # 提取并标准化图
        graphs = [sample["graph"] for sample in batch]
        standardized_graphs = standardize_hetero_graphs(graphs)
        batched_graph = dgl.batch(standardized_graphs)
        
        result = {"graph": batched_graph}
        
        # 处理标签
        if has_labels:
            labels = [sample["label"] for sample in batch]
            result["label"] = torch.cat(labels, dim=0)
        
        if has_sample_name:
            sample_names = [sample["sample_name"] for sample in batch]
            result["sample_name"] = sample_names
        
        return result
        
    except Exception as e:
        print(f"批量合并失败: {e}")
        return {}

def standardize_hetero_graphs( graphs: List[dgl.DGLGraph]) -> List[dgl.DGLGraph]:
        """
        标准化异构图，使所有图具有相同的节点类型和边类型
        
        策略：
        1. 收集所有图的节点类型和边类型的并集
        2. 为每个图添加缺失的节点类型（空节点）
        3. 确保所有图具有相同的图结构模式
        """
        if not graphs:
            return graphs
        
        # 1. 收集所有节点类型和边类型
        all_ntypes = set()
        all_etypes = set()
        
        for g in graphs:
            all_ntypes.update(g.ntypes)
            all_etypes.update(g.canonical_etypes)
        
        all_ntypes = sorted(list(all_ntypes))
        all_etypes = sorted(list(all_etypes))
        
        # 2. 标准化每个图
        standardized_graphs = []
        
        for i, g in enumerate(graphs):
            try:
                new_g = _add_missing_types(g, all_ntypes, all_etypes)
                standardized_graphs.append(new_g)
            except Exception as e:
                print(f"图 {i} 标准化失败: {e}")
        
        return standardized_graphs
    
def _add_missing_types(graph: dgl.DGLGraph, 
                        target_ntypes: List[str], 
                        target_etypes: List[Tuple]) -> dgl.DGLGraph:
        """为单个图添加缺失的节点类型和边类型"""
        
        # 构建新的边字典
        edge_dict = {}
        
        # 1. 复制原有的边
        for etype in graph.canonical_etypes:
            if etype in target_etypes:
                u, v = graph.edges(etype=etype)
                edge_dict[etype] = (u, v)
        
        # 2. 为缺失的边类型添加空边
        for etype in target_etypes:
            if etype not in edge_dict:
                # 创建空边：源节点到目标节点的空连接
                edge_dict[etype] = (torch.tensor([], dtype=torch.int64), 
                                torch.tensor([], dtype=torch.int64))
        
        # 3. 计算每种节点类型的数量
        num_nodes_dict = {}
        for ntype in target_ntypes:
            if ntype in graph.ntypes:
                num_nodes_dict[ntype] = graph.num_nodes(ntype)
            else:
                # 为缺失的节点类型添加一个虚拟节点
                num_nodes_dict[ntype] = 0
        # 4. 创建新图
        new_g = dgl.heterograph(edge_dict, num_nodes_dict)
        # 5. 复制特征
        _copy_features(graph, new_g, target_ntypes, target_etypes)
        return new_g

   
def _copy_features(old_g: dgl.DGLGraph, 
                    new_g: dgl.DGLGraph,
                    target_ntypes: List[str], 
                    target_etypes: List[Tuple]):
        """复制节点和边特征到新图"""
        
        # 复制节点特征
        for ntype in target_ntypes:
            if ntype in old_g.ntypes:
                # 复制现有特征
                for feat_name, feat_data in old_g.nodes[ntype].data.items():
                    new_g.nodes[ntype].data[feat_name] = feat_data
            else:
                # 为新节点类型创建零特征（如果需要的话）
                # 这里可以根据需要添加默认特征
                pass
        
        # 复制边特征
        for etype in target_etypes:
            if etype in old_g.canonical_etypes:
                # 复制现有特征
                for feat_name, feat_data in old_g.edges[etype].data.items():
                    new_g.edges[etype].data[feat_name] = feat_data

