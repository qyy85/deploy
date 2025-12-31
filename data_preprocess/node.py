from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from data_preprocess.feature_config import FeatureConfig
from sklearn.preprocessing import StandardScaler
from typing_extensions import override
from functools import singledispatch

class Node(ABC):
    """节点抽象基类 - 基于属性字段的设计"""
    
    def __init__(self, node_id: str, node_type: str):
        self.node_id = node_id
        self.node_type = node_type
        self.raw_params: List[dict] = []
        
        # 主要特征属性（所有节点共有）
        self.face_type_idx: int = 0
        self.inner_outer: int = 0
        self.origin_x: float = 0.0
        self.origin_y: float = 0.0
        self.origin_z: float = 0.0
        self.normal_x: float = 0.0
        self.normal_y: float = 0.0
        self.normal_z: float = 0.0
        self.area: float = 0.0
    
    @abstractmethod
    def extract_features(self, params: List[dict]) -> None:
        """从XML参数中提取特征到属性字段"""
        pass
    
    @abstractmethod
    def get_feature_vector(self) -> List[float]:
        """动态生成特征向量（用于机器学习）"""
        pass 
    
    def get_feature_dim(self) -> int:
        """获取该节点类型的特征维度"""
        return FeatureConfig.get_node_feature_dim(self.node_type)
    
    def get_main_features_dict(self) -> Dict[str, Any]:
        """获取主要特征字典"""
        return {
            'face_type_idx': self.face_type_idx,
            'inner_outer': self.inner_outer,
            'origin': [self.origin_x, self.origin_y, self.origin_z],
            'normal': [self.normal_x, self.normal_y, self.normal_z],
            'area': self.area
        }
    
    def get_all_features_dict(self) -> Dict[str, Any]:
        """获取所有特征的字典表示"""
        return {
            'main': self.get_main_features_dict(),
            'specific': self.get_specific_features_dict(),
            'node_type': self.node_type,
            'node_id': self.node_id
        }
    
    def parse_vector(self, vector_str: str) -> List[float]:
        """解析Vector字符串为浮点数列表"""
        try:
            if vector_str.startswith('[') and vector_str.endswith(']'):
                vector_str = vector_str[1:-1]
            
            if ',' in vector_str:
                parts = vector_str.split(',')
            else:
                parts = vector_str.split()
            
            return [float(part.strip()) for part in parts]
        except Exception as e:
            print(f"Error parsing vector '{vector_str}': {e}")
            return [0.0, 0.0, 0.0]
    
    def extract_main_features(self, params: List[dict]) -> None:
        """提取主要特征到属性字段"""
        param_dict = {p.get('name', ''): p for p in params}
        
        # 处理面类型
        if params:
            node_types = ['extrude', 'plane', 'straight line face', 'B_surface', 
                         'cylinder', 'fillet', 'torus', 'cone', 'sphere']
            self.face_type_idx = node_types.index(self.node_type) if self.node_type in node_types else 0
        else:
            raise ValueError(f"Node type {self.node_type} not found in node_types")
        
        # 内外表面
        surface_param = param_dict.get("内外表面", {})
        if surface_param.get('type') in ('Double', 'Int'):
            self.inner_outer = int(surface_param.get('value', 0))
        else:
            raise ValueError(f"no known feature for {surface_param.get('type')}")
            
        # 原点 (3D)
        origin_param = param_dict.get("原点", {})
        if origin_param.get('type') == 'Vector':
            origin_values = self.parse_vector(origin_param.get('value', '[0,0,0]'))
            self.origin_x, self.origin_y, self.origin_z = origin_values[:3]
        else:
            raise ValueError(f"no known feature for {origin_param.get('type')}")
            
        # 法向量 (3D)  
        normal_param = param_dict.get("法向量", {})
        if normal_param.get('type') == 'Vector':
            normal_values = self.parse_vector(normal_param.get('value', '[0,0,1]'))
            self.normal_x, self.normal_y, self.normal_z = normal_values[:3]
        else:
            raise ValueError(f"no known feature for {normal_param.get('type')}")
            
        # 面积
        area_param = param_dict.get("面积", {})
        if area_param.get('type') in ('Double', 'Int'):
            self.area = float(area_param.get('value', 0))
        else:
            raise ValueError(f"no known feature for {area_param.get('type')}")
    
    def get_main_feature_vector(self) -> List[float]:
        """获取主要特征向量"""
        return [
            self.face_type_idx,
            self.inner_outer,
            self.origin_x, self.origin_y, self.origin_z,
            self.normal_x, self.normal_y, self.normal_z,
            self.area
        ]
    
    def get_origin_feature_vector(self) -> List[float]:
        """获取原点特征向量"""
        return [self.origin_x, self.origin_y, self.origin_z]
    
    def get_normal_feature_vector(self) -> List[float]:
        """获取法向量特征向量"""
        return [self.normal_x, self.normal_y, self.normal_z]
    
    def get_area_feature_vector(self) -> List[float]:
        """获取面积特征向量"""
        return [self.area]
    
    def scale_origin_rigid(self,centroid:List[float],max_distance:float):
        self.origin_x = (self.origin_x - centroid[0]) / max_distance
        self.origin_y = (self.origin_y - centroid[1]) / max_distance
        self.origin_z = (self.origin_z - centroid[2]) / max_distance

    def scale_origin_standard(self,scaler:StandardScaler):
        self.origin_coord = scaler.transform([self.get_origin_feature_vector()])[0]
        self.origin_x = self.origin_coord[0]
        self.origin_y = self.origin_coord[1]
        self.origin_z = self.origin_coord[2]

    def scale_area_standard(self,scaler:StandardScaler):
        self.area = scaler.transform([[self.area]])[0][0]


# 具体节点类实现
class CylinderNode(Node):
    """圆柱面节点"""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "cylinder")
        # 圆柱面特有属性
        self.radius: float = 0.0
        self.height: float = 0.0
        self.axis_angle: float = 0.0
    
    def extract_features(self, params: List[dict]) -> None:
        """提取圆柱面特征到属性字段"""
        # 提取主要特征
        self.extract_main_features(params)
        
        # 提取圆柱面特有特征
        param_dict = {p.get('name', ''): p for p in params}
        
        # 圆柱面半径
        radius_param = param_dict.get('圆柱面半径', {})
        if radius_param.get('type') in ('Double', 'Int'):
            self.radius = float(radius_param.get('value', 0))
        
        # 高度
        height_param = param_dict.get('高度', {})
        if height_param.get('type') in ('Double', 'Int'):
            self.height = float(height_param.get('value', 0))
        
        # 相对面轴线包角
        angle_param = param_dict.get('相对面轴线包角', {})
        if angle_param.get('type') in ('Double', 'Int'):
            self.axis_angle = float(angle_param.get('value', 0))
    
    def get_feature_vector(self) -> List[float]:
        """动态生成特征向量"""
        main_features = self.get_main_feature_vector()
        specific_features = [self.radius, self.height, self.axis_angle]
        return main_features + specific_features


class PlaneNode(Node):
    """平面节点"""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "plane")
        # 平面节点当前没有特有属性
    
    def extract_features(self, params: List[dict]) -> None:
        """提取平面特征"""
        # 平面只有主要特征
        self.extract_main_features(params)
    
    def get_feature_vector(self) -> List[float]:
        """动态生成特征向量"""
        return self.get_main_feature_vector()

class FilletNode(Node):
    """倒圆角节点"""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "fillet")
        # 倒圆角特有属性
        self.fillet_radius: float = 0.0
        self.arc_degree: float = 0.0
        self.chamfer_angle: float = 0.0
        self.chamfer_width: float = 0.0
    
    def extract_features(self, params: List[dict]) -> None:
        """提取倒圆角特征"""
        self.extract_main_features(params)
        
        param_dict = {p.get('name', ''): p for p in params}
        
        # 倒圆半径
        radius_param = param_dict.get('倒圆半径', {})
        if radius_param.get('type') in ('Double', 'Int'):
            self.fillet_radius = float(radius_param.get('value', 0))
        
        # 弧度
        arc_param = param_dict.get('弧度', {})
        if arc_param.get('type') in ('Double', 'Int'):
            self.arc_degree = float(arc_param.get('value', 0))
        
        # 倒角面夹角
        angle_param = param_dict.get('倒角面夹角', {})
        if angle_param.get('type') in ('Double', 'Int'):
            self.chamfer_angle = float(angle_param.get('value', 0))
        
        # 倒角面宽度
        width_param = param_dict.get('倒角面宽度', {})
        if width_param.get('type') in ('Double', 'Int'):
            self.chamfer_width = float(width_param.get('value', 0))
    
    def get_feature_vector(self) -> List[float]:
        """动态生成特征向量"""
        main_features = self.get_main_feature_vector()
        specific_features = [self.fillet_radius, self.arc_degree, self.chamfer_angle, self.chamfer_width]
        return main_features + specific_features


class TorusNode(Node):
    """圆环面节点"""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "torus")
        # 圆环面特有属性
        self.minor_diameter: float = 0.0
        self.major_diameter: float = 0.0
        self.arc_degree: float = 0.0
        self.minor_sweep_angle: float = 0.0
        self.axis_angle: float = 0.0
    
    def extract_features(self, params: List[dict]) -> None:
        """提取圆环面特征"""
        self.extract_main_features(params)
        
        param_dict = {p.get('name', ''): p for p in params}
        
        # 圆环面小径
        minor_param = param_dict.get('圆环面小径', {})
        if minor_param.get('type') in ('Double', 'Int'):
            self.minor_diameter = float(minor_param.get('value', 0))
        
        # 圆环面中径
        major_param = param_dict.get('圆环面中径', {})
        if major_param.get('type') in ('Double', 'Int'):
            self.major_diameter = float(major_param.get('value', 0))
        
        # 弧度
        arc_param = param_dict.get('弧度', {})
        if arc_param.get('type') in ('Double', 'Int'):
            self.arc_degree = float(arc_param.get('value', 0))
        
        # 小径绕中径上张角
        sweep_param = param_dict.get('小径绕中径上张角', {})
        if sweep_param.get('type') in ('Double', 'Int'):
            self.minor_sweep_angle = float(sweep_param.get('value', 0))
        
        # 相对圆环面轴线张角
        axis_param = param_dict.get('相对圆环面轴线张角', {})
        if axis_param.get('type') in ('Double', 'Int'):
            self.axis_angle = float(axis_param.get('value', 0))
    
    def get_feature_vector(self) -> List[float]:
        """动态生成特征向量"""
        main_features = self.get_main_feature_vector()
        specific_features = [self.minor_diameter, self.major_diameter, self.arc_degree, 
                           self.minor_sweep_angle, self.axis_angle]
        return main_features + specific_features


class ConeNode(Node):
    """圆锥面节点"""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "cone")
        # 圆锥面特有属性
        self.radius: float = 0.0
        self.half_angle: float = 0.0
        self.height: float = 0.0
        self.axis_angle: float = 0.0
    
    def extract_features(self, params: List[dict]) -> None:
        """提取圆锥面特征"""
        self.extract_main_features(params)
        
        param_dict = {p.get('name', ''): p for p in params}
        
        # 圆锥面半径
        radius_param = param_dict.get('圆锥面半径', {})
        if radius_param.get('type') in ('Double', 'Int'):
            self.radius = float(radius_param.get('value', 0))
        
        # 圆锥半锥角
        half_angle_param = param_dict.get('圆锥半锥角', {})
        if half_angle_param.get('type') in ('Double', 'Int'):
            self.half_angle = float(half_angle_param.get('value', 0))
        
        # 高度
        height_param = param_dict.get('高度', {})
        if height_param.get('type') in ('Double', 'Int'):
            self.height = float(height_param.get('value', 0))
        
        # 相对面轴线包角
        axis_param = param_dict.get('相对面轴线包角', {})
        if axis_param.get('type') in ('Double', 'Int'):
            self.axis_angle = float(axis_param.get('value', 0))
    
    def get_feature_vector(self) -> List[float]:
        """动态生成特征向量"""
        main_features = self.get_main_feature_vector()
        specific_features = [self.radius, self.half_angle, self.height, self.axis_angle]
        return main_features + specific_features


class SphereNode(Node):
    """球面节点"""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "sphere")
        # 球面特有属性
        self.radius: float = 0.0
        self.arc_degree: float = 0.0
    
    def extract_features(self, params: List[dict]) -> None:
        """提取球面特征"""
        self.extract_main_features(params)
        
        param_dict = {p.get('name', ''): p for p in params}
        
        # 球半径
        radius_param = param_dict.get('球半径', {})
        if radius_param.get('type') in ('Double', 'Int'):
            self.radius = float(radius_param.get('value', 0))
        
        # 弧度
        arc_param = param_dict.get('弧度', {})
        if arc_param.get('type') in ('Double', 'Int'):
            self.arc_degree = float(arc_param.get('value', 0))
    
    def get_feature_vector(self) -> List[float]:
        """动态生成特征向量"""
        main_features = self.get_main_feature_vector()
        specific_features = [self.radius, self.arc_degree]
        return main_features + specific_features


class ExtrudeNode(Node):
    """拉伸面节点"""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "extrude")
        # 拉伸面当前没有特有属性
    
    def extract_features(self, params: List[dict]) -> None:
        """提取拉伸面特征"""
        self.extract_main_features(params)
    
    def get_feature_vector(self) -> List[float]:
        """动态生成特征向量"""
        return self.get_main_feature_vector()


class StraightLineFaceNode(Node):
    """直线面节点"""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "straight line face")
        # 直线面当前没有特有属性
    
    def extract_features(self, params: List[dict]) -> None:
        """提取直线面特征"""
        self.extract_main_features(params)
    
    def get_feature_vector(self) -> List[float]:
        """动态生成特征向量"""
        return self.get_main_feature_vector()


class BSurfaceNode(Node):
    """B样条曲面节点"""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "B_surface")
        # B样条曲面当前没有特有属性
    
    def extract_features(self, params: List[dict]) -> None:
        """提取B样条曲面特征"""
        self.extract_main_features(params)
    
    def get_feature_vector(self) -> List[float]:
        """动态生成特征向量"""
        return self.get_main_feature_vector()


# 工厂类
class NodeFactory:
    """节点工厂类"""
    
    _node_classes = {
        'cylinder': CylinderNode,
        'plane': PlaneNode,
        'fillet': FilletNode,
        'torus': TorusNode,
        'cone': ConeNode,
        'sphere': SphereNode,
        'extrude': ExtrudeNode,
        'straight line face': StraightLineFaceNode,
        'B_surface': BSurfaceNode
    }
    
    @classmethod
    def create_node(cls, node_type: str, node_id: str) -> Node:
        """根据类型创建节点"""
        if node_type not in cls._node_classes:
            print(f"Warning: Unknown node type '{node_type}', using PlaneNode as default")
            return PlaneNode(node_id)
        
        return cls._node_classes[node_type](node_id)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的节点类型列表"""
        return list(cls._node_classes.keys())