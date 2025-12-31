from abc import ABC, abstractmethod
from typing import List
from data_preprocess.feature_config import FeatureConfig

class Edge(ABC):
    """边抽象基类"""
    
    def __init__(self, src_node_id: str, dst_node_id: str, edge_type: str):
        self.src_node_id = src_node_id
        self.dst_node_id = dst_node_id  
        self.edge_type = edge_type
        # self.features: List[float] = []
        self.raw_params: List[dict] = []
    
    @abstractmethod
    def extract_features(self, params: List[dict]) -> List[float]:
        """从XML参数中提取边特征"""
        pass
    
    def get_feature_dim(self) -> int:
        """获取该边类型的特征维度"""
        return FeatureConfig.get_edge_feature_dim(self.edge_type)
    
    def get_feature_vector(self) -> List[float]:
        """动态生成特征向量"""
        pass

# 具体边类实现
class ArcEdge(Edge):
    """弧形边"""
    
    def __init__(self, src_node_id: str, dst_node_id: str):
        super().__init__(src_node_id, dst_node_id, "arc")
        self.connect_type = -1
        self.inner_outer = 0
        self.radius = 0
        self.angle = 0
    
    def extract_features(self, params: List[dict]) -> List[float]:
        """提取弧形边特征"""
        param_dict = {p.get('name', ''): p for p in params}
        
        # 连接类型 (arc = 0)
        self.connect_type = 0
        
        # 内外
        inner_outer = param_dict.get("内外", {})
        if inner_outer.get('type') in ('Double', 'Int'):
            self.inner_outer = float(inner_outer.get('value', 0))
        else:
            self.inner_outer = -1
            
        # 圆角半径
        radius = param_dict.get("圆角半径", {})
        if radius.get('type') in ('Double', 'Int'):
            self.radius = float(radius.get('value', 0))
        else:
            self.radius = -1
            
        # 过渡面夹角
        angle = param_dict.get("过渡面夹角", {})
        if angle.get('type') in ('Double', 'Int'):
            self.angle = float(angle.get('value', 0))
        else:
            self.angle = -1
            
        # self.features = features
        # return features
    def get_feature_vector(self) -> List[float]:
        """动态生成特征向量"""
        return [self.connect_type, self.inner_outer, self.radius, self.angle]

    def get_angle_feature_vector(self) -> List[float]:
        """获取角度特征向量"""
        return [self.angle]

class StraightEdge(Edge):
    """直线边"""
    
    def __init__(self, src_node_id: str, dst_node_id: str):
        super().__init__(src_node_id, dst_node_id, "straight")
        self.connect_type = -1
        self.angle = -1
    
    def extract_features(self, params: List[dict]) -> List[float]:
        """提取直线边特征"""
        # features = []
        param_dict = {p.get('name', ''): p for p in params}
        
        # 连接类型 (straight = 1)
        self.connect_type = 1
        
        # 面与面之间夹角
        angle = param_dict.get("面与面之间夹角", {})
        if angle.get('type') in ('Double', 'Int'):
            self.angle = float(angle.get('value', 0))
        else:
            self.angle = -1
            
        # self.features = features
        # return features
    def get_feature_vector(self) -> List[float]:
        """动态生成特征向量"""
        return [self.connect_type, self.angle]
    
    def get_angle_feature_vector(self) -> List[float]:
        """获取角度特征向量"""
        return [self.angle]

class EdgeFactory:
    """边工厂类"""
    
    _edge_classes = {
        'arc': ArcEdge,
        'straight': StraightEdge
    }
    
    @classmethod
    def create_edge(cls, edge_type: str, src_id: str, dst_id: str) -> Edge:
        """根据类型创建边"""
        if edge_type not in cls._edge_classes:
            print(f"Warning: Unknown edge type '{edge_type}', using StraightEdge as default")
            return StraightEdge(src_id, dst_id)
        
        return cls._edge_classes[edge_type](src_id, dst_id)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的边类型列表"""
        return list(cls._edge_classes.keys())