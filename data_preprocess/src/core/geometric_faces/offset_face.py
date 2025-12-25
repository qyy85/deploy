# -*- coding: utf-8 -*-
"""
偏移曲面类
"""
from typing import Dict
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Core.BRep import BRep_Tool
from OCC.Core.Geom import Geom_OffsetSurface
import logging

from .base_face import BaseFace
from ...utils.constants import GeometryType

logger = logging.getLogger(__name__)


class OffsetFace(BaseFace):
    """偏移曲面类"""

    def get_type_name(self):
        """获取几何类型名称"""
        self.type = GeometryType.FACE_OFFSET

    def _extract_geometry_features(self):
        """提取偏移曲面几何特征（偏移量与是否反向）"""
        try:
            geom_surface = BRep_Tool.Surface(self.face)
            offset_surface = Geom_OffsetSurface.DownCast(geom_surface)

            if offset_surface is not None:
                # 偏移量
                self.offset_value = float(offset_surface.Offset())
            else:
                logger.error("偏移曲面下转失败或为空")
                self.offset_value = -1.0
                self.error = True
        except Exception as e:
            logger.error(f"提取{self.type}几何特征失败,error: {e}")
            self.offset_value = -1.0
            self.error = True

    def get_feature_vector(self):
        vector = super().get_feature_vector()
        vector.append(self.offset_value)
        return vector


