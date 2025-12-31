import dgl
from typing import Dict, Optional, Any, Union
from data_preprocess.node import NodeFactory
from data_preprocess.edge import EdgeFactory
from data_preprocess.graph import HeterogeneousGraph
from pathlib import Path
import numpy as np
from sklearn.preprocessing import StandardScaler,MaxAbsScaler 
import torch
from .xml_parser import XMLParser

class GraphBuilder:
    """图构建器类 - 协调整个图构建过程"""
    
    def __init__(self):
        self.xml_parser = XMLParser()
        self.graph: Optional[HeterogeneousGraph] = None
        
    def from_xml(self, xml_content: str) -> 'GraphBuilder':
        """从XML内容构建图"""
        # 解析XML
        parsed_data = self.xml_parser.parse(xml_content)
        
        # 创建新图
        self.graph = HeterogeneousGraph()
        
        # 创建节点
        for node_data in parsed_data['nodes']:
            node = NodeFactory.create_node(node_data['type'], node_data['id'])
            node.extract_features(node_data['params'])
            node.raw_params = node_data['params']
            self.graph.add_node(node)
        
        # 创建边
        for edge_data in parsed_data['edges']:
            edge = EdgeFactory.create_edge(
                edge_data['type'],
                edge_data['src_id'], 
                edge_data['dst_id']
            )
            edge.extract_features(edge_data['params'])
            edge.raw_params = edge_data['params']
            self.graph.add_edge(edge)
        
        return self.graph
    
    def build_heterogeneous_graph(self) -> dgl.DGLGraph:
        """构建异构图"""
        if self.graph is None:
            raise ValueError("请先调用 from_xml() 解析数据")
        
        return self.graph.build_dgl_graph()
    
    def build_homogeneous_graph(self) -> dgl.DGLGraph:
        """构建同构图"""
        if self.graph is None:
            raise ValueError("请先调用 from_xml() 解析数据")
        self.graph.to_homogeneous()
        return self.graph
    
    def get_graph(self) -> HeterogeneousGraph:
        """获取内部图对象"""
        return self.graph
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图统计信息"""
        if self.graph is None:
            return {}
        return self.graph.get_statistics()

    def _rigid_scaling(self,coords, method:str = 'L2'):
        """平移+均匀缩放保持空间关系"""
        centroid = np.mean(coords, axis=0)    # 计算点云质心
        translated = coords - centroid         # 平移至质心为原点
        
        # 计算整体缩放因子（最大欧氏距离）
        # max_distance_ = np.max(np.linalg.norm(translated, axis=1))
        if method == 'L2':
            # L2范数 - 欧氏距离: √(x² + y² + z²)
            max_distance = np.max(np.linalg.norm(translated, axis=1))
        elif method == 'manhattan':
            # L1范数 - 曼哈顿距离: |x| + |y| + |z|
            max_distance = np.max(np.sum(np.abs(translated), axis=1))
        else:
            raise ValueError(f"不支持的距离度量方法: {method}")    # 均匀缩放
        
        return centroid, max_distance
    
    def _standardScaler(self,datas):
        '''
        标准化数据
        datas: 数据列表
        return: 标准化器
        '''
        scaler = StandardScaler()
        scaler.fit(datas)
        return scaler
    
    def _MaxAbsScaler(self,datas):
        scaler = MaxAbsScaler()
        datas_scaled = scaler.fit_transform(datas)
        return datas_scaled
    
    def scale_rigid_single(self,graph:dgl.DGLGraph):
        node_coords = []
        area = []
        for node in graph.nodes.values():
            node_coords.append(node.get_origin_feature_vector())
            area.append(node.get_area_feature_vector())
        centroid, max_distance = self._rigid_scaling(node_coords)
        scaler = self._standardScaler(area)
        for node in graph.nodes.values():
            node.scale_origin_rigid(centroid,max_distance)
            node.scale_area_standard(scaler)
        return graph

    def scale_rigid(self,graphs:list[dgl.DGLGraph]):
        node_coords = []
        area = []
        for graph in graphs:
            for node in graph.nodes.values():
                node_coords.append(node.get_origin_feature_vector())
                area.append(node.get_area_feature_vector())
        centroid, max_distance = self._rigid_scaling(node_coords)
        scaler = self._standardScaler(area)

        for graph in graphs:
            for node in graph.nodes.values():
                node.scale_origin_rigid(centroid,max_distance)
                node.scale_area_standard(scaler)
        return graphs

    def scale_standard_single(self,graph:dgl.DGLGraph):
        node_coords = []
        area = []
        for node in graph.nodes.values():
            node_coords.append(node.get_origin_feature_vector())
            area.append(node.get_area_feature_vector())
        scaler_area = self._standardScaler(area)
        scaler_origin = self._standardScaler(node_coords)
        for node in graph.nodes.values():
            node.scale_origin_standard(scaler_origin)
            node.scale_area_standard(scaler_area)
        return graph

    def scale_standard(self,graphs:list[dgl.DGLGraph]):
        node_coords = []
        area = []
        for graph in graphs:
            for node in graph.nodes.values():
                node_coords.append(node.get_origin_feature_vector())
                area.append(node.get_area_feature_vector())
        scaler_area = self._standardScaler(area)
        scaler_origin = self._standardScaler(node_coords)
        for graph in graphs:
            for node in graph.nodes.values():
                node.scale_origin_standard(scaler_origin)
                node.scale_area_standard(scaler_area)
        return graphs
    
    def scale_MaxAbsScaler_single(self,graph:dgl.DGLGraph):
        scaler_node_feat = self._MaxAbsScaler(graph.ndata["x"].numpy())
        scaler_edge_feat = self._MaxAbsScaler(graph.edata["x"].numpy())
        graph.ndata["x"] = torch.from_numpy(scaler_node_feat)
        graph.edata["x"] = torch.from_numpy(scaler_edge_feat)
        return graph   





   
    