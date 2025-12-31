"""
特征配置类
定义各种节点和边的特征维度和映射
"""

from dataclasses import dataclass
from typing import Dict

@dataclass
class FeatureConfig:
    """特征配置类"""
    
    # 主要特征维度映射 (所有节点共有)
    MAIN_FEATURES = {
        "面类型": 1,      # 分类特征，用索引
        "内外表面": 1,     # 0/1特征  
        "原点": 3,        # 3D坐标
        "法向量": 3,       # 3D向量
        "面积": 1         # 标量值
    }
    
    # 各节点类型特有特征
    NODE_SPECIFIC_FEATURES = {
        'cylinder': {
            "圆柱面半径": 1, "高度": 1, "相对面轴线包角": 1
        },
        'fillet': {
            "倒圆半径": 1, "弧度": 1, "倒角面夹角": 1, "倒角面宽度": 1
        },
        'torus': {
            "圆环面小径": 1, "圆环面中径": 1, "弧度": 1, 
            "小径绕中径上张角": 1, "相对圆环面轴线张角": 1
        },
        'cone': {
            "圆锥面半径": 1, "圆锥半锥角": 1, "高度": 1, "相对面轴线包角": 1
        },
        'sphere': {
            "球半径": 1, "弧度": 1
        }
    }
    
    # 边特征
    EDGE_FEATURES = {
        'arc': {
            "连接类型": 1, "内外": 1, "圆角半径": 1, "过渡面夹角": 1
        },
        'straight': {
            "连接类型": 1, "面与面之间夹角": 1
        }
    }
    ALL_NODE_TYPES = ['plane', 'extrude', 'straight line face', 'B_surface', 'cylinder', 'fillet', 'torus', 'cone', 'sphere']
    
    @classmethod
    def get_node_feature_dim(cls, node_type: str) -> int:
        """获取节点特征总维度"""
        main_dim = sum(cls.MAIN_FEATURES.values())  # 9维
        specific_dim = sum(cls.NODE_SPECIFIC_FEATURES.get(node_type, {}).values())
        return main_dim + specific_dim
    
    @classmethod
    def get_edge_feature_dim(cls, edge_type: str) -> int:
        """获取边特征维度"""
        return sum(cls.EDGE_FEATURES.get(edge_type, {}).values())
    
    @classmethod
    def get_main_feature_dim(cls) -> int:
        """获取主要特征维度（所有节点共有）"""
        return sum(cls.MAIN_FEATURES.values())  # 9维
    
    @classmethod
    def get_all_node_types(cls) -> list:
        """获取所有支持的节点类型"""
        return cls.ALL_NODE_TYPES
    
    @classmethod
    def get_all_edge_types(cls) -> list:
        """获取所有支持的边类型"""
        return list(cls.EDGE_FEATURES.keys())