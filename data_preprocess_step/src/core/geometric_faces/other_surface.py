# -*- coding: utf-8 -*-
"""
其他曲面类 - OtherSurface
仅提取基础特征，不提取几何特征
"""
from typing import Dict
from OCC.Core.TopoDS import TopoDS_Face
import logging

from .base_face import BaseFace
from ...utils.constants import GeometryType

logger = logging.getLogger(__name__)


class OtherSurface(BaseFace):
    """其他曲面类 - 仅提取基础特征"""
    
    def __init__(self, face: TopoDS_Face, face_id: int, config: Dict,
                 surface_type_name: str = "OtherSurface"):
        """初始化
        
        Args:
            surface_type_name: 曲面类型名称（用于标识具体类型）
        """
        super().__init__(face, face_id, config)
        self.surface_type_name = surface_type_name
    
    def get_type_name(self):
        """获取几何类型名称"""
        self.type = self.surface_type_name

    def _extract_geometry_features(self):
        """不提取几何特征"""
        pass

    def get_feature_vector(self):
        vector = super().get_feature_vector()
        return vector