# -*- coding: utf-8 -*-
"""
面的抽象基类
定义所有面类型的基础特征提取逻辑
"""
from abc import ABC, abstractmethod
from typing import Dict
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.Geom import Geom_SurfaceOfLinearExtrusion, Geom_SurfaceOfRevolution
from OCC.Core.BRep import BRep_Tool
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop
import logging
from typing import List
from ...utils.constants import Orientation

logger = logging.getLogger(__name__)


class BaseFace(ABC):
    """面的抽象基类 - 所有面类型的统一基础"""

    def __init__(self, face: TopoDS_Face, face_id: int, config: Dict):
        """初始化面对象

        Args:
            face: 面对象
            face_id: 面ID
            config: 配置信息
        """
        self.face = face
        self.id = face_id
        self.config = config
        self.adaptor = BRepAdaptor_Surface(face)

        # 初始化类特征属性
        self.type = None
        self.uv_bounds = None
        self.area = None
        self.center = None
        self.tolerance = None
        self.natural_restriction = None
        self.orientation = None
        # 统一错误标志：任一特征提取失败时置为 True
        self.error = False

    def get_feature_vector(self):
        vector = []
        vector.extend(self.uv_bounds)
        vector.extend(self.center)
        vector.append(self.area)
        vector.append(self.tolerance)
        vector.append(self.natural_restriction)
        vector.append(self.orientation)
        return vector

    def extract_all_features(self):
        """提取所有特征（统一接口）"""
        # 1. 提取基础特征（存储到类属性中）
        self._extract_base_features()

        # 2. 提取几何特征（存储到类属性中）
        self._extract_geometry_features()

        # 3. 返回类本身
        return self
    
    def _extract_base_features(self):
        """提取基类特征（所有面类型统一提取）

        包括：
        - 标识信息: id, type
        - 参数域: uv_bounds
        - 度量信息: area, center
        - 精度信息: tolerance
        - 拓扑信息: natural_restriction, orientation
        """
        self.get_type_name()
        # 参数域信息
        self._extract_parameter_domain()

        # 度量信息
        self._extract_metric_features()

        # 精度信息
        self._extract_precision_features()

        # 拓扑信息
        self._extract_topology_features()
    
    def _extract_parameter_domain(self):
        """提取参数域信息"""
        try:
            u_min = self.adaptor.FirstUParameter()
            u_max = self.adaptor.LastUParameter()
            v_min = self.adaptor.FirstVParameter()
            v_max = self.adaptor.LastVParameter()
            self.uv_bounds = [float(u_min), float(u_max), float(v_min), float(v_max)]
        except Exception as e:
            logger.error(f"提取UV边界失败,error: {e}")
            self.uv_bounds = -1
            self.error = True
    
    def _extract_metric_features(self):
        """提取度量信息（面积和中心）"""
        # 1. 面积
        try:
            props = GProp_GProps()
            brepgprop.SurfaceProperties(self.face, props)
            self.area = float(props.Mass())
        except Exception as e:
            logger.error(f"计算面积失败,error: {e}")
            self.area = -1
            self.error = True

        # 2. 中心坐标（UV参数中心）
        self._calculate_uv_center()

    
    def _calculate_uv_center(self):
        """计算UV参数中心（保证在曲面上）"""
        try:
            u_min = self.adaptor.FirstUParameter()
            u_max = self.adaptor.LastUParameter()
            v_min = self.adaptor.FirstVParameter()
            v_max = self.adaptor.LastVParameter()
            u_center = (u_min + u_max) / 2.0
            v_center = (v_min + v_max) / 2.0
            
            # 映射到3D空间
            point = self.adaptor.Value(u_center, v_center)
            self.center = [float(point.X()), float(point.Y()), float(point.Z())]
            
        except Exception as e:
            logger.error(f"计算UV中心失败,error: {e}")
            self.center = -1
            self.error = True
    
    def _extract_precision_features(self):
        """提取精度信息"""
        try:
            self.tolerance = float(BRep_Tool.Tolerance(self.face))
        except Exception as e:
            logger.error(f"提取公差失败,error: {e}")
            self.tolerance = -1
            self.error = True
    
    def _extract_topology_features(self):
        """提取拓扑信息"""
        try:
            self.natural_restriction = int(bool(BRep_Tool.NaturalRestriction(self.face)))
            self.orientation = Orientation.from_topabs(self.face.Orientation())
        except Exception as e:
            logger.error(f"提取拓扑信息失败,error: {e}")
            self.natural_restriction = -1
            self.orientation = -1
            self.error = True
    
    @abstractmethod
    def get_type_name(self):
        """获取几何类型名称（子类实现，存储到 self.type 中）"""
        pass
    
    @abstractmethod
    def _extract_geometry_features(self):
        """提取几何特征（子类实现，存储到 self.geometry_features 中）"""
        pass

