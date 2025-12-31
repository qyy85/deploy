"""
贝塞尔曲线边类 - 优化版本
"""
from typing import Dict, List
from OCC.Core.TopoDS import TopoDS_Edge, TopoDS_Face
import logging

from .base_edge import BaseEdge
from ...utils.constants import GeometryType

logger = logging.getLogger(__name__)


class Bezier(BaseEdge):
    """贝塞尔曲线边类"""
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.EDGE_BEZIER

    def _extract_geometry_features(self):
        """提取贝塞尔曲线的几何特征（最小集）"""
        try:
            bezier = self.adaptor.Bezier()

            self.degree = int(bezier.Degree())
            self.num_poles = int(bezier.NbPoles())
            self.is_rational = bool(bezier.IsRational())
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.degree = -1
            self.num_poles = -1
            self.is_rational = -1
            self.error = True

    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.append(self.degree)
        vector.append(self.num_poles)
        vector.append(self.is_rational)
        return vector   