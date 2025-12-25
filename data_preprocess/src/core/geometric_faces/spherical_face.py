# -*- coding: utf-8 -*-
"""
球面类 - 优化版本
"""
from typing import Dict
from OCC.Core.TopoDS import TopoDS_Face
import logging

from .base_face import BaseFace
from ...utils.constants import GeometryType, MathConstants, ExtractionConfig

logger = logging.getLogger(__name__)


class SphericalFace(BaseFace):
    """球面类"""
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.FACE_SPHERE

    def _extract_geometry_features(self):
        """提取球面的几何特征（仅尺寸和范围）"""
        try:
            sphere = self.adaptor.Sphere()

            # 半径
            radius = sphere.Radius()

            # UV范围
            u_first = self.adaptor.FirstUParameter()
            u_last = self.adaptor.LastUParameter()
            v_first = self.adaptor.FirstVParameter()
            v_last = self.adaptor.LastVParameter()

            u_range = float(u_last - u_first)
            v_range = float(v_last - v_first)

            # 判断是否完整球面
            is_full_sphere = (
                abs(u_range - MathConstants.TWO_PI) < MathConstants.FULL_CIRCLE_TOLERANCE and
                abs(v_range - MathConstants.PI) < MathConstants.FULL_CIRCLE_TOLERANCE
            )

            self.radius = float(radius)
            self.u_range = u_range
            self.v_range = v_range
            self.is_full_sphere = is_full_sphere
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.radius = -1
            self.u_range = -1
            self.v_range = -1
            self.is_full_sphere = -1
            self.error = True
            
    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.append(self.radius)
        vector.append(self.u_range)
        vector.append(self.v_range)
        vector.append(self.is_full_sphere)
        return vector