"""
面特征提取器 - 重构版本
基于新的 BaseFace 架构
"""
from typing import Dict
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.GeomAbs import (
    GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone, GeomAbs_Sphere,
    GeomAbs_Torus, GeomAbs_BezierSurface, GeomAbs_BSplineSurface,
    GeomAbs_SurfaceOfRevolution, GeomAbs_SurfaceOfExtrusion, GeomAbs_OffsetSurface,
    GeomAbs_OtherSurface
)
from OCC.Core.Geom import Geom_RectangularTrimmedSurface
import logging

from .geometric_faces import (
    PlaneFace, CylindricalFace, ConicalFace, SphericalFace, ToroidalFace,
    BSplineFace, BezierFace, RevolutionFace, ExtrusionFace, OffsetFace, OtherSurface
)

logger = logging.getLogger(__name__)


class FaceExtractor:
    """面特征提取器 - 重构版本"""
    
    def __init__(self, config: Dict):
        """初始化提取器
        
        Args:
            config: 配置信息
        """
        self.config = config.get('face_extraction', {})
    
    def extract_face_object(self, face: TopoDS_Face, face_id: int):
        """提取单个面的特征
        
        Args:
            face: 面对象
            face_id: 面ID
            
        Returns:
            面特征对象
        """
        try:
            # 使用BRepAdaptor_Surface进行操作
            adaptor = BRepAdaptor_Surface(face)
            surface_type = adaptor.GetType()
            
            # 根据曲面类型创建对应的几何面对象并提取特征
            face_obj = self._create_face_object(face, face_id, surface_type)
            return face_obj.extract_all_features()
            
        except Exception as e:
            logger.error(f"创建面对象失败,error: {e}")
            # 返回一个默认的OtherSurface对象作为降级处理
            return OtherSurface(face, face_id, self.config, "Unknown")
    
    def _create_face_object(self, face: TopoDS_Face, face_id: int, surface_type):
        """根据曲面类型创建对应的几何面对象"""
        
        if surface_type == GeomAbs_Plane:
            return PlaneFace(face, face_id, self.config)
        
        elif surface_type == GeomAbs_Cylinder:
            return CylindricalFace(face, face_id, self.config)
        
        elif surface_type == GeomAbs_Cone:
            return ConicalFace(face, face_id, self.config)
        
        elif surface_type == GeomAbs_Sphere:
            return SphericalFace(face, face_id, self.config)
        
        elif surface_type == GeomAbs_Torus:
            return ToroidalFace(face, face_id, self.config)
        
        elif surface_type == GeomAbs_BSplineSurface:
            return BSplineFace(face, face_id, self.config)
        
        elif surface_type == GeomAbs_BezierSurface:
            return BezierFace(face, face_id, self.config)
        
        elif surface_type == GeomAbs_SurfaceOfRevolution:
            return RevolutionFace(face, face_id, self.config)
        
        elif surface_type == GeomAbs_SurfaceOfExtrusion:
            return ExtrusionFace(face, face_id, self.config)
        
        elif surface_type == GeomAbs_OffsetSurface:
            # 偏移曲面
            return OffsetFace(face, face_id, self.config)
        
        elif surface_type == GeomAbs_OtherSurface:
            # 尝试识别具体类型
            return self._handle_other_surface(face, face_id, "OtherSurface")
        
        else:
            return OtherSurface(face, face_id, self.config, "Unknown")
    
    def _handle_other_surface(self, face: TopoDS_Face, face_id: int, surface_type_name: str):
        """处理 GeomAbs_OtherSurface 类型"""
        try:
            # 其他未实现的类型，使用 OtherSurface
            logger.warning(f"未实现专门提取器的OtherSurface类型: {surface_type_name} (面ID: {face_id})")
            return OtherSurface(face, face_id, self.config, surface_type_name)
            
        except Exception as e:
            logger.exception(f"处理 OtherSurface 时出错 (面ID: {face_id}): {e}")
            return OtherSurface(face, face_id, self.config, "Unknown")