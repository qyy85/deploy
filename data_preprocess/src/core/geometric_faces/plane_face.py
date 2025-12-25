# -*- coding: utf-8 -*-
"""
平面类 - 优化版本
"""
from typing import Dict
from OCC.Core.TopoDS import TopoDS_Face
import logging

from .base_face import BaseFace
from ...utils.constants import GeometryType, ExtractionConfig

logger = logging.getLogger(__name__)


class PlaneFace(BaseFace):
    """平面类"""
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.FACE_PLANE

    def _extract_geometry_features(self):
        """提取平面的几何特征（仅方向信息）"""
        try:
            plane = self.adaptor.Plane()

            # 法向量和坐标轴方向
            normal = plane.Axis().Direction()
            x_axis = plane.XAxis().Direction()
            y_axis = plane.YAxis().Direction()

            self.normal = [float(normal.X()), float(normal.Y()), float(normal.Z())]
            self.x_axis = [float(x_axis.X()), float(x_axis.Y()), float(x_axis.Z())]
            self.y_axis = [float(y_axis.X()), float(y_axis.Y()), float(y_axis.Z())]
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.normal = -1
            self.x_axis = -1
            self.y_axis = -1
            self.error = True

    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.extend(self.normal)
        vector.extend(self.x_axis)
        vector.extend(self.y_axis)
        return vector