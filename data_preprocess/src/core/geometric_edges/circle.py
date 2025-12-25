"""
圆弧边类
"""
from typing import Dict, List
from OCC.Core.TopoDS import TopoDS_Edge, TopoDS_Face
import logging

from .base_edge import BaseEdge
from ...utils.constants import GeometryType, MathConstants

logger = logging.getLogger(__name__)


class Circle(BaseEdge):
    """圆弧边类"""
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.EDGE_CIRCLE

    def _extract_geometry_features(self):
        """提取圆弧的几何特征（最小集）"""
        try:
            circle = self.adaptor.Circle()
            first = self.adaptor.FirstParameter()
            last = self.adaptor.LastParameter()

            radius = circle.Radius()
            angle_span = last - first

            self.radius = float(radius)
            self.angle_span = float(angle_span)
            self.is_full_circle = abs(angle_span - MathConstants.TWO_PI) < MathConstants.FULL_CIRCLE_TOLERANCE
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.radius = -1
            self.angle_span = -1
            self.is_full_circle = -1
            self.error = True
    
    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.append(self.radius)
        vector.append(self.angle_span)
        vector.append(self.is_full_circle)
        return vector   