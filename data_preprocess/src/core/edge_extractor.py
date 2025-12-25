"""
边特征提取器 
"""
from typing import Dict, List, Any, Optional
from OCC.Core.TopoDS import TopoDS_Edge, TopoDS_Face
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.GeomAbs import (
    GeomAbs_Line, GeomAbs_Circle, GeomAbs_Ellipse, GeomAbs_Parabola,
    GeomAbs_Hyperbola, GeomAbs_BSplineCurve, GeomAbs_BezierCurve,
    GeomAbs_OffsetCurve, GeomAbs_OtherCurve
)
import logging

from .geometric_edges import (
    Line, Circle, Ellipse, Parabola, Hyperbola,
    BSpline, Bezier, OtherCurve
)

logger = logging.getLogger(__name__)


class EdgeExtractor:
    """边特征提取器 - 重构版本"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.face_objects_cache = {}
    
    def set_face_objects(self, face_objects: list[TopoDS_Face]):
        """设置面对象映射（用于连续性计算）"""
        self.face_objects_cache = face_objects
    
    def extract_edge_object(self, edge: TopoDS_Edge, edge_id: int, 
                            connected_face_ids: List[int]):
        """提取边特征
        
        Args:
            edge: 边对象
            edge_id: 边ID
            connected_face_ids: 连接的面ID列表
            
        Returns:
            边特征对象
        """
        try:
            # 获取曲线类型
            adaptor = BRepAdaptor_Curve(edge)
            curve_type = adaptor.GetType()
            
            # 创建几何边对象并提取特征
            edge_obj = self._create_edge_object(
                edge, edge_id, curve_type, 
                connected_face_ids, self.face_objects_cache
            )
            
            # 提取所有特征
            return edge_obj.extract_all_features()
            
        except Exception as e:
            logger.error(f"创建边对象失败,error: {e}")
            # 返回一个默认的OtherCurve对象作为降级处理
            return OtherCurve(edge, edge_id, self.config, "Unknown", connected_face_ids, self.face_objects_cache)
    
    
    def _create_edge_object(self, edge: TopoDS_Edge, edge_id: int, 
                           curve_type, connected_faces: List[int],
                           face_objects: list[TopoDS_Face]):
        """根据曲线类型创建边对象"""
        type_map = {
            GeomAbs_Line: Line,
            GeomAbs_Circle: Circle,
            GeomAbs_Ellipse: Ellipse,
            GeomAbs_Parabola: Parabola,
            GeomAbs_Hyperbola: Hyperbola,
            GeomAbs_BSplineCurve: BSpline,
            GeomAbs_BezierCurve: Bezier,
        }
        
        edge_class = type_map.get(curve_type)
        
        if edge_class:
            # 创建具体几何边对象
            return edge_class(edge, edge_id, self.config, connected_faces, face_objects)
        else:
            # OtherCurve 或 OffsetCurve
            curve_name = "OffsetCurve" if curve_type == GeomAbs_OffsetCurve else "OtherCurve"
            return OtherCurve(edge, edge_id, self.config, curve_name, connected_faces, face_objects)
