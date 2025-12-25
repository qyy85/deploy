"""
其他曲线类 - OtherCurve/OffsetCurve
仅提取基础特征，不提取几何特征
"""
from typing import Dict, List
from OCC.Core.TopoDS import TopoDS_Edge, TopoDS_Face
import logging

from .base_edge import BaseEdge
from ...utils.constants import GeometryType

logger = logging.getLogger(__name__)


class OtherCurve(BaseEdge):
    """其他曲线类 - 仅提取基础特征"""
    
    def __init__(self, edge: TopoDS_Edge, edge_id: int, config: Dict,
                 curve_type_name: str = "OtherCurve",
                 connected_faces: List[int] = None,
                 face_objects: Dict[int, TopoDS_Face] = None):
        """初始化
        
        Args:
            curve_type_name: 曲线类型名称（OtherCurve 或 OffsetCurve）
        """
        super().__init__(edge, edge_id, config, connected_faces, face_objects)
        self.curve_type_name = curve_type_name
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = self.curve_type_name

    def _extract_geometry_features(self):
        """不提取几何特征"""
        pass
    
    def get_feature_vector(self):
        vector = super().get_feature_vector()
        return vector
