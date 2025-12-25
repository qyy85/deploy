# -*- coding: utf-8 -*-
"""
环面类
"""
from typing import Dict
from OCC.Core.TopoDS import TopoDS_Face
import logging

from .base_face import BaseFace
from ...utils.constants import GeometryType, ExtractionConfig

logger = logging.getLogger(__name__)


class ToroidalFace(BaseFace):
    """环面类"""
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.FACE_TORUS

    def _extract_geometry_features(self):
        """提取环面的几何特征（方向和半径）"""
        try:
            torus = self.adaptor.Torus()

            # 轴方向
            axis_direction = torus.Axis().Direction()

            # 大半径和小半径
            major_radius = torus.MajorRadius()
            minor_radius = torus.MinorRadius()

            # 角度范围（从UV计算）
            u_first = self.adaptor.FirstUParameter()
            u_last = self.adaptor.LastUParameter()
            angular_range = float(u_last - u_first)

            self.axis_direction = [float(axis_direction.X()), float(axis_direction.Y()), float(axis_direction.Z())]
            self.major_radius = float(major_radius)
            self.minor_radius = float(minor_radius)
            self.angular_range = angular_range
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.axis_direction = -1
            self.major_radius = -1
            self.minor_radius = -1
            self.angular_range = -1
            self.error = True
            
    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.extend(self.axis_direction)
        vector.append(self.major_radius)
        vector.append(self.minor_radius)
        vector.append(self.angular_range)
        return vector