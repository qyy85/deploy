# -*- coding: utf-8 -*-
"""
拉伸曲面类
"""
from typing import Dict
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Core.BRep import BRep_Tool
from OCC.Core.Geom import Geom_SurfaceOfLinearExtrusion
import logging

from .base_face import BaseFace
from ...utils.constants import GeometryType

logger = logging.getLogger(__name__)


class ExtrusionFace(BaseFace):
    """拉伸曲面类"""
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.FACE_EXTRUSION

    def _extract_geometry_features(self):
        """提取拉伸曲面的几何特征（基线曲线与方向、以及长度）"""
        try:
            # 获取几何曲面并下转型为线性拉伸曲面
            geom_surface = BRep_Tool.Surface(self.face)
            extrusion_surface = Geom_SurfaceOfLinearExtrusion.DownCast(geom_surface)

            if extrusion_surface is not None:
                # 基线曲线与方向
                basis_curve = extrusion_surface.BasisCurve()
                direction = extrusion_surface.Direction()

                # 方向向量
                self.extrusion_direction = [
                    float(direction.X()),
                    float(direction.Y()),
                    float(direction.Z()),
                ]

                # 拉伸长度（从V参数范围估算）
                v_first = self.adaptor.FirstVParameter()
                v_last = self.adaptor.LastVParameter()
                self.extrusion_length = float(abs(v_last - v_first))

                # 可选：记录基线曲线是否存在（避免将复杂对象放入特征向量）
                self.has_basis_curve = 1
            else:
                logger.error("线性拉伸曲面下转失败或为空")
                self.extrusion_direction = -1
                self.extrusion_length = -1
                self.has_basis_curve = 0
                self.error = True
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.extrusion_direction = -1
            self.extrusion_length = -1
            self.has_basis_curve = 0
            self.error = True

    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.extend(self.extrusion_direction)
        vector.append(self.extrusion_length)
        return vector