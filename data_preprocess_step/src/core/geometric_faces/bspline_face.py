# -*- coding: utf-8 -*-
"""
B样条曲面类 - 优化版本
"""
from typing import Dict
from OCC.Core.TopoDS import TopoDS_Face
import logging

from .base_face import BaseFace
from ...utils.constants import GeometryType

logger = logging.getLogger(__name__)


class BSplineFace(BaseFace):
    """B样条曲面类"""
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.FACE_BSPLINE

    def _extract_geometry_features(self):
        """提取B样条曲面的几何特征（精简版）"""
        try:
            bspline = self.adaptor.BSpline()

            self.u_degree = int(bspline.UDegree())
            self.v_degree = int(bspline.VDegree())
            self.num_u_poles = int(bspline.NbUPoles())
            self.num_v_poles = int(bspline.NbVPoles())
            self.is_rational = bool(bspline.IsURational() or bspline.IsVRational())
            self.is_u_periodic = bool(bspline.IsUPeriodic())
            self.is_v_periodic = bool(bspline.IsVPeriodic())
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.u_degree = -1
            self.v_degree = -1
            self.num_u_poles = -1
            self.num_v_poles = -1
            self.is_rational = -1
            self.is_u_periodic = -1
            self.is_v_periodic = -1
            self.error = True

    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.extend([self.u_degree, self.v_degree, self.num_u_poles, self.num_v_poles, self.is_rational, self.is_u_periodic, self.is_v_periodic])
        return vector