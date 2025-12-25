"""
抛物线边类
"""
from typing import Dict, List
from OCC.Core.TopoDS import TopoDS_Edge, TopoDS_Face
import logging

from .base_edge import BaseEdge
from ...utils.constants import GeometryType

logger = logging.getLogger(__name__)


class Parabola(BaseEdge):
    """抛物线边类"""
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.EDGE_PARABOLA

    def _extract_geometry_features(self):
        """提取抛物线的几何特征"""
        try:
            parabola = self.adaptor.Parabola()

            self.focal_length = float(parabola.Focal())
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.focal_length = -1
            self.error = True
    
    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.append(self.focal_length)
        return vector   