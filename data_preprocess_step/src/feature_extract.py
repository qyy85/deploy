"""
几何特征分析器
统筹整个特征提取过程
"""
from typing import Dict, List
from datetime import datetime
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Face, TopoDS_Edge
from OCC.Core.TopExp import TopExp_Explorer, topexp
from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCC.Core.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCC.Core.ShapeFix import ShapeFix_Face
from OCC.Core.BRepLib import breplib_BuildCurves3d

from .step_loader import STEPLoader
from .id_manager import IDManager
from .core.edge_extractor import EdgeExtractor
from .core.face_extractor import FaceExtractor

import logging

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """几何特征分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.id_manager = IDManager()
        self.edge_extractor = EdgeExtractor({})
        self.face_extractor = FaceExtractor({})
        self.loader = STEPLoader()
        
    def analyze_file(self, step_file: str) -> Dict:
        """分析STEP文件并提取特征
        
        Args:
            step_file: STEP文件路径
            scale_to_unit_box: 是否缩放到单位立方体
            
        Returns:
            提取的特征数据
        """
        # 加载STEP文件
        shape = self.loader.load(step_file)
        # 分析形状
        result = self.__analyze_shape(shape, step_file)
        return result
    
    def __analyze_shape(self, shape: TopoDS_Shape, step_file: str = "") -> Dict:
        """分析形状并提取特征
        
        Args:
            shape: 形状对象
            step_file: STEP文件路径（用于元数据）
            
        Returns:
            提取的特征数据
        """
        # 重置ID管理器
        self.id_manager.reset()
        
        # 先提取面对象
        faces_objects = self.extract_faces_objects(shape)
        # 再提取边对象
        edges_objects = self.extract_edges_objects(shape, faces_objects)

        # 构建结果
        result = {
            # "metadata": self.build_metadata(step_file, len(edges_objects), len(faces_objects)),
            "edges": edges_objects,
            "nodes": faces_objects
        }
        
        return result
    
    def _build_edge_face_mapping(self, shape: TopoDS_Shape) -> TopTools_IndexedDataMapOfShapeListOfShape:
        """使用OpenCASCADE的MapShapesAndAncestors直接构建边到面的映射
        
        Args:
            shape: 形状对象
            
        Returns:
            边到面列表的映射
        """
        edge_face_map = TopTools_IndexedDataMapOfShapeListOfShape()
        topexp.MapShapesAndAncestors(shape, TopAbs_EDGE, TopAbs_FACE, edge_face_map)
        return edge_face_map
    
    def _get_connected_faces_from_edge(self, edge: TopoDS_Edge, edge_face_map: TopTools_IndexedDataMapOfShapeListOfShape) -> List[TopoDS_Face]:
        """从边对象直接获取连接的面对象列表
        
        Args:
            edge: 边对象
            edge_face_map: 边到面的映射
            
        Returns:
            连接的面对象列表
        """
        connected_faces = []
        
        if edge_face_map.Contains(edge):
            face_list = edge_face_map.FindFromKey(edge)
            
            # 使用First和Last方法获取面（对于大多数情况，边连接1-2个面）
            if face_list.Size() > 0:
                connected_faces.append(face_list.First())
                if face_list.Size() > 1:
                    connected_faces.append(face_list.Last())
        
        return connected_faces
    
    def extract_edges_objects(self, shape: TopoDS_Shape, faces_objects: List[TopoDS_Face]) -> List[TopoDS_Edge]:
        """提取所有边的特征
        
        Args:
            shape: 形状对象
            face_id_map: 面对象hash到面ID的映射字典（来自id_manager.face_map）
            
        Returns:
            边特征列表
        """
        # 构建边到面的直接映射
        edge_face_map = self._build_edge_face_mapping(shape)
        edges_obj = []
        edge_explorer = TopExp_Explorer(shape, TopAbs_EDGE)
        processed_edges = set()
        
        while edge_explorer.More():
            edge = edge_explorer.Current()
            edge_id = self.id_manager.get_edge_id(edge)
            
            # 避免重复处理同一条边
            if edge_id not in processed_edges:
                # 直接从边获取连接的面对象
                connected_faces = self._get_connected_faces_from_edge(edge, edge_face_map)
                self.edge_extractor.set_face_objects(connected_faces)
                # 将面对象转换为面ID列表，确保所有面都有ID
                connected_face_ids = []
                for face in connected_faces:
                    # 确保面ID存在，如果不存在会自动创建
                    face_id = self.id_manager.get_face_id(face, is_edge_extraction=True)
                    connected_face_ids.append(face_id)
                
                edge = self.edge_extractor.extract_edge_object(
                    edge, edge_id, connected_face_ids
                )
                if edge.type == 'Unknown':
                    logger.warning(f"未知边类型，(边ID: {edge_id})")
                    continue
                edges_obj.append(edge)
                processed_edges.add(edge_id)
            
            edge_explorer.Next()
        
        return edges_obj
    
    def extract_faces_objects(self, shape: TopoDS_Shape) -> List[TopoDS_Face]:
        """提取所有面的特征
        
        Args:
            shape: 形状对象
            
        Returns:
            面特征列表
        """
        faces_objects = []
        face_explorer = TopExp_Explorer(shape, TopAbs_FACE)
        processed_faces = set()
        
        while face_explorer.More():
            face = face_explorer.Current()
            face_id = self.id_manager.get_face_id(face)
            
            # 避免重复处理同一个面
            if face_id not in processed_faces:
                # 在特征提取前对面进行修复
                # healed_face = self._heal_face(face)
                face_obj = self.face_extractor.extract_face_object(face, face_id)
                if face_obj.type == 'Unknown':
                    logger.warning(f"未知面类型，(面ID: {face_id})")
                    continue
                if face_obj.error:
                    continue
                faces_objects.append(face_obj)
                processed_faces.add(face_id)
            
            face_explorer.Next()
        
        return faces_objects
    
    def _heal_face(self, face: TopoDS_Face) -> TopoDS_Face:
        """面级修复：修复单个面的几何/拓扑问题
        
        Args:
            face: 原始面对象
            
        Returns:
            修复后的面对象（若失败则返回原始面）
        """
        try:
            # 使用ShapeFix_Face进行面修复
            face_fixer = ShapeFix_Face(face)
            face_fixer.Perform()
            healed_face = face_fixer.Face()
            
            # 如果修复成功且得到有效面，则使用修复后的面
            if not healed_face.IsNull():
                # 重建3D曲线
                breplib_BuildCurves3d(healed_face)
                return healed_face
            else:
                logger.debug(f"面修复失败，使用原始面")
                return face
                
        except Exception as e:
            logger.debug(f"面修复过程中出错: {e}，使用原始面")
            return face
    
    def build_metadata(self, step_file: str, total_edges: int, total_faces: int) -> Dict:
        """构建元数据
        
        Args:
            step_file: STEP文件路径
            total_edges: 边总数
            total_faces: 面总数
            
        Returns:
            元数据字典
        """
        metadata = {
            "extractor_version": "1.0.0",
            "pythonocc_version": "7.9.0",
            "step_file": step_file,
            "extraction_time": datetime.now().isoformat(),
            "total_edges": total_edges,
            "total_faces": total_faces
        }
        
        return metadata