# -*- coding: utf-8 -*-
"""
贝塞尔曲面类
"""
from typing import Dict
from OCC.Core.TopoDS import TopoDS_Face
import logging

from .base_face import BaseFace
from ...utils.constants import GeometryType

logger = logging.getLogger(__name__)


class BezierFace(BaseFace):
    """贝塞尔曲面类"""
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.FACE_BEZIER

    def _extract_geometry_features(self):
        """提取贝塞尔曲面的几何特征"""
        try:
            bezier = self.adaptor.Bezier()

            self.u_degree = int(bezier.UDegree())
            self.v_degree = int(bezier.VDegree())
            self.num_u_poles = int(bezier.NbUPoles())
            self.num_v_poles = int(bezier.NbVPoles())
            self.is_rational = bool(bezier.IsURational() or bezier.IsVRational())
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.u_degree = -1
            self.v_degree = -1
            self.num_u_poles = -1
            self.num_v_poles = -1
            self.is_rational = -1
            self.error = True

    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.extend([self.u_degree, self.v_degree, self.num_u_poles, self.num_v_poles, self.is_rational])
        return vector