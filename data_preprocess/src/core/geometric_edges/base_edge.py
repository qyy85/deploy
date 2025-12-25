"""
边的抽象基类
定义所有边类型的基础特征提取逻辑
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from OCC.Core.TopoDS import TopoDS_Edge, TopoDS_Face
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRep import BRep_Tool
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop
import logging

from ...utils.constants import (
    EdgeRole, Continuity, Orientation,
    MathConstants
)

logger = logging.getLogger(__name__)


class BaseEdge(ABC):
    """边的抽象基类 - 所有边类型的统一基础"""
    
    def __init__(self, edge: TopoDS_Edge, edge_id: int, config: Dict,
                 connected_faces: List[int] = None,
                 face_objects: list[TopoDS_Face] = None):
        """初始化边对象

        Args:
            edge: 边对象
            edge_id: 边ID
            config: 配置信息
            connected_faces: 连接的面ID列表
            face_objects: 面ID到面对象的映射（用于连续性计算）
        """
        self.edge = edge
        self.edge_id = edge_id
        self.config = config
        self.connected_faces = connected_faces
        self.src_node_id = connected_faces[0]
        self.dst_node_id = connected_faces[-1]
        self.face_objects = face_objects or []
        self.adaptor = BRepAdaptor_Curve(edge)

        # 初始化类特征属性
        self.type = None
        self.parameter_range = None
        self.tolerance = None
        self.same_parameter = None
        self.same_range = None
        self.edge_role = None
        self.continuity = None
        self.is_closed = None
        self.is_degenerated = None
        self.orientation = None
        self.length = None
        # 统一错误标志：任一特征提取失败时置为 True
        self.error = False
    
    def get_feature_vector(self):
        vector = []
        vector.extend(self.parameter_range)
        vector.append(self.tolerance)
        vector.append(self.same_parameter)
        vector.append(self.same_range)
        vector.append(self.edge_role)
        vector.append(self.continuity)
        vector.append(self.is_closed)
        vector.append(self.is_degenerated)
        vector.append(self.orientation)
        vector.append(self.length)
        return vector
        
    def extract_all_features(self):
        """提取所有特征（统一接口）"""
        # 1. 提取基础特征（存储到类属性中）
        self._extract_base_features()

        # 2. 提取几何特征（存储到类属性中）
        self._extract_geometry_features()

        # 3. 返回类本身
        return self
    
    def _extract_base_features(self):
        """提取基础特征（所有边类型统一提取）

        包括：
        - 标识信息: id, type
        - 参数信息: parameter_range
        - 精度信息: tolerance, same_parameter, same_range
        - 连接关系: connected_faces, edge_role
        - 连续性: continuity
        - 拓扑属性: is_closed, is_degenerated, orientation
        - 度量信息: length
        """
        # 设置类型名称
        self.get_type_name()

        # 参数信息
        self._extract_parameter_features()

        # 精度信息
        self._extract_precision_features()

        # 拓扑特征
        self._extract_topology_features()
    
    def _extract_parameter_features(self):
        """提取参数信息"""
        try:
            first = self.adaptor.FirstParameter()
            last = self.adaptor.LastParameter()
            self.parameter_range = [float(first), float(last)]
        except Exception as e:
            logger.error(f"提取参数范围失败,error: {e}")
            self.parameter_range = -1
            self.error = True
    
    def _extract_precision_features(self):
        """提取精度信息"""
        try:
            self.tolerance = float(BRep_Tool.Tolerance(self.edge))
            self.same_parameter = bool(BRep_Tool.SameParameter(self.edge))
            self.same_range = bool(BRep_Tool.SameRange(self.edge))
        except Exception as e:
            logger.error(f"提取精度信息失败,error: {e}")
            self.tolerance = -1
            self.same_parameter = -1
            self.same_range = -1
            self.error = True
    
    def _extract_topology_features(self):
        """提取拓扑特征（所有边类型，包括 OtherCurve）"""
        # 1. 连接关系
        self.edge_role = EdgeRole.from_num_faces(len(self.connected_faces))

        # 2. 连续性（仅当连接2个或以上面时）
        self.continuity = self._calculate_continuity()

        # 3. 拓扑属性
        try:
            self.is_closed = bool(BRep_Tool.IsClosed(self.edge))
            self.is_degenerated = bool(BRep_Tool.Degenerated(self.edge))
            self.orientation = Orientation.from_topabs(self.edge.Orientation())
        except Exception as e:
            logger.error(f"提取拓扑属性失败,error: {e}")
            self.is_closed = -1
            self.is_degenerated = -1
            self.orientation = -1
            self.error = True

        # 4. 长度（可能失败，尤其是 OtherCurve）
        self.length = self._calculate_length()
    
    def _calculate_continuity(self) -> int:
        """计算连续性编码"""
        # 必须有至少2个连接面才能计算连续性
        if len(self.face_objects) < 2:
            return Continuity.NONE
        
        try:
            # 获取前两个连接面的对象
            face1 = self.face_objects[0]
            face2 = self.face_objects[1]
            
            if face1 is None or face2 is None:
                logger.warning(f"无法获取面对象 (边ID: {self.edge_id})")
                return Continuity.NONE
            
            # 使用 BRep_Tool 计算连续性
            geomabs_continuity = BRep_Tool.Continuity(self.edge, face1, face2)
            
            # 转换为整数编码
            return Continuity.from_geomabs(geomabs_continuity)
            
        except Exception as e:
            logger.error(f"计算连续性失败,error: {e}")
            self.error = True
            return Continuity.NONE
    
    def _calculate_length(self):
        """计算边长度"""
        try:
            props = GProp_GProps()
            brepgprop.LinearProperties(self.edge, props)
            return float(props.Mass())
        except Exception as e:
            logger.error(f"计算长度失败,error: {e}")
            self.error = True
            return -1
    
    @abstractmethod
    def get_type_name(self):
        """获取几何类型名称（子类实现，存储到 self.type 中）"""
        pass

    @abstractmethod
    def _extract_geometry_features(self):
        """提取几何特征（子类实现，存储为类属性）"""
        pass
    

