# -*- coding: utf-8 -*-
"""
旋转曲面类
"""
from typing import Dict
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Core.BRep import BRep_Tool
from OCC.Core.Geom import Geom_SurfaceOfRevolution
import logging

from .base_face import BaseFace
from ...utils.constants import GeometryType, ExtractionConfig

logger = logging.getLogger(__name__)


class RevolutionFace(BaseFace):
    """旋转曲面类"""
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.FACE_REVOLUTION

    def _extract_geometry_features(self):
        """提取旋转曲面的几何特征（基面轴方向和角度范围）"""
        try:
            # 获取几何曲面并下转型为旋转曲面
            geom_surface = BRep_Tool.Surface(self.face)
            revolution_surface = Geom_SurfaceOfRevolution.DownCast(geom_surface)

            if revolution_surface is not None :
                # 旋转轴方向
                axis = revolution_surface.Axis()
                direction = axis.Direction()

                self.axis_direction = [
                    float(direction.X()),
                    float(direction.Y()),
                    float(direction.Z()),
                ]

                # 角度范围（从U参数范围估算）
                u_first = self.adaptor.FirstUParameter()
                u_last = self.adaptor.LastUParameter()
                self.angular_range = float(u_last - u_first)
            else:
                logger.error("旋转曲面下转失败或为空")
                self.axis_direction = -1
                self.angular_range = -1
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.axis_direction = -1
            self.angular_range = -1
            self.error = True
            
    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.extend(self.axis_direction)
        vector.append(self.angular_range)
        return vector