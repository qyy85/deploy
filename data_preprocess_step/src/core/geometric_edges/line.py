"""
直线边类
"""
from typing import Dict, List
from OCC.Core.TopoDS import TopoDS_Edge, TopoDS_Face
import logging

from .base_edge import BaseEdge
from ...utils.constants import GeometryType

logger = logging.getLogger(__name__)


class Line(BaseEdge):
    """直线边类"""
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.EDGE_LINE

    def _extract_geometry_features(self):
        """提取直线的几何特征（仅方向）"""
        try:
            line = self.adaptor.Line()
            direction = line.Direction()

            self.direction = [float(direction.X()), float(direction.Y()), float(direction.Z())]
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.direction = -1
            self.error = True
    
    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.extend(self.direction)
        return vector   
    