"""
双曲线边类 - 优化版本
"""
from typing import Dict, List
from OCC.Core.TopoDS import TopoDS_Edge, TopoDS_Face
import math
import logging

from .base_edge import BaseEdge
from ...utils.constants import GeometryType

logger = logging.getLogger(__name__)


class Hyperbola(BaseEdge):
    """双曲线边类"""
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.EDGE_HYPERBOLA

    def _extract_geometry_features(self):
        """提取双曲线的几何特征（最小集）"""
        try:
            hyperbola = self.adaptor.Hyperbola()

            major_radius = hyperbola.MajorRadius()
            minor_radius = hyperbola.MinorRadius()

            # 计算离心率
            eccentricity = math.sqrt(1 + (minor_radius / major_radius) ** 2) if major_radius > 0 else 0.0

            self.major_radius = float(major_radius)
            self.minor_radius = float(minor_radius)
            self.eccentricity = float(eccentricity)
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.major_radius = -1
            self.minor_radius = -1
            self.eccentricity = -1
            self.error = True
    
    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.append(self.major_radius)
        vector.append(self.minor_radius)
        vector.append(self.eccentricity)
        return vector   