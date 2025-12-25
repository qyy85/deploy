"""
ID管理器
用于为边和面生成唯一ID

使用OpenCASCADE的TopTools_IndexedMapOfShape来确保相同的拓扑结构
（即使是不同的Python包装对象）获得相同的ID。
"""
from OCC.Core.TopoDS import TopoDS_Edge, TopoDS_Face
from OCC.Core.TopTools import TopTools_IndexedMapOfShape
import logging

logger = logging.getLogger(__name__)


class IDManager:
    """ID管理器类
    
    使用TopTools_IndexedMapOfShape来唯一标识边和面。
    该方法基于底层TShape指针比较（通过IsSame()），
    而不是Python对象指针，确保相同的拓扑结构获得相同的ID。
    """
    
    def __init__(self):
        """初始化ID管理器"""
        # 使用OpenCASCADE的IndexedMap来存储和索引形状
        # IndexedMap内部使用IsSame()比较，基于底层TShape指针
        self._edge_map = TopTools_IndexedMapOfShape()
        self._face_map = TopTools_IndexedMapOfShape()
    
    def get_edge_id(self, edge: TopoDS_Edge) -> int:
        """为边生成或获取ID
        
        使用TopTools_IndexedMapOfShape确保相同的边（即使不同Python对象）
        获得相同的ID。
        
        Args:
            edge: 边对象
            
        Returns:
            边的ID（整数，从0开始）
        """
        # FindIndex返回1-based索引，如果不存在返回0
        index = self._edge_map.FindIndex(edge)
        
        if index == 0:
            # 不存在，添加到map中
            # Add返回新添加元素的1-based索引
            index = self._edge_map.Add(edge)
            logger.debug(f"创建新边ID: {index - 1}, 总边数: {self._edge_map.Size()}")
        
        # 转换为0-based索引
        return index - 1
    
    def get_face_id(self, face: TopoDS_Face, is_edge_extraction: bool = False) -> int:
        """为面生成或获取ID
        
        使用TopTools_IndexedMapOfShape确保相同的面（即使不同Python对象）
        获得相同的ID。
        
        Args:
            face: 面对象
            is_edge_extraction: 是否在边提取过程中调用
            
        Returns:
            面的ID（整数，从0开始）
        """
        # FindIndex返回1-based索引，如果不存在返回0
        index = self._face_map.FindIndex(face)
        
        if index == 0:
            # 不存在，添加到map中
            index = self._face_map.Add(face)
            
            # 只有在边提取过程中发现新面时才发出警告
            if is_edge_extraction:
                logger.warning(f"创建面ID: {index - 1}, 总面数: {self._face_map.Size()}")
        
        # 转换为0-based索引
        return index - 1
    
    @property
    def edge_count(self) -> int:
        """获取已注册的边数量"""
        return self._edge_map.Size()
    
    @property
    def face_count(self) -> int:
        """获取已注册的面数量"""
        return self._face_map.Size()
    
    def reset(self):
        """重置所有计数器和映射"""
        self._edge_map.Clear()
        self._face_map.Clear()
