# -*- coding: utf-8 -*-
"""
圆锥面类
"""
from typing import Dict
from OCC.Core.TopoDS import TopoDS_Face
import logging

from .base_face import BaseFace
from ...utils.constants import GeometryType, MathConstants, ExtractionConfig

logger = logging.getLogger(__name__)


class ConicalFace(BaseFace):
    """圆锥面类"""
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.FACE_CONE

    def _extract_geometry_features(self):
        """提取圆锥面的几何特征（方向和尺寸）"""
        try:
            cone = self.adaptor.Cone()

            # 轴方向
            axis_direction = cone.Axis().Direction()

            # 半锥角
            semi_angle = cone.SemiAngle()

            # 参考半径
            ref_radius = cone.RefRadius()

            # 高度和角度范围（从UV计算）
            u_first = self.adaptor.FirstUParameter()
            u_last = self.adaptor.LastUParameter()
            v_first = self.adaptor.FirstVParameter()
            v_last = self.adaptor.LastVParameter()

            # 角度范围
            angular_range = float(u_last - u_first)

            # 高度（通过V参数端点的实际3D距离计算）
            try:
                p1 = self.adaptor.Value(u_first, v_first)
                p2 = self.adaptor.Value(u_first, v_last)
                height = p1.Distance(p2)
            except:
                height = abs(v_last - v_first)  # 降级方案

            self.axis_direction = [float(axis_direction.X()), float(axis_direction.Y()), float(axis_direction.Z())]
            self.semi_angle = float(semi_angle)
            self.ref_radius = float(ref_radius)
            self.height = float(height)
            self.angular_range = angular_range
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.axis_direction = -1
            self.semi_angle = -1
            self.ref_radius = -1
            self.height = -1
            self.angular_range = -1
            self.error = True
        
    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.extend(self.axis_direction)
        vector.append(self.semi_angle)
        vector.append(self.ref_radius)
        vector.append(self.height)
        vector.append(self.angular_range)
        return vector