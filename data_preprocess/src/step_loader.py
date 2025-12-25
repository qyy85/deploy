"""
STEP文件加载器
用于加载STEP文件并提取拓扑元素
"""
from typing import List
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Edge, TopoDS_Face
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.ShapeFix import ShapeFix_Shape
from OCC.Core.BRepLib import breplib_BuildCurves3d
from OCC.Core.BRepTools import breptools_Clean
import logging
# from utils.brep_utils import scale_solid_to_unit_box

logger = logging.getLogger(__name__)


class STEPLoader:
    """STEP文件加载器"""
    
    def __init__(self, scale_body: bool = True):
        """初始化加载器
        
        Args:
            file_path: STEP文件路径
            scale_to_unit_box: 是否缩放到单位立方体 [-1, 1]^3
        """
        self.shape = None
        self.scale_body = scale_body
    
    def _heal_shape(self, shape: TopoDS_Shape) -> TopoDS_Shape:
        """形状级修复：修复几何/拓扑问题并重建3D曲线后清理。

        Args:
            shape: 原始形状

        Returns:
            修复后的形状（若失败则返回原始形状）
        """
        try:
            fixer = ShapeFix_Shape(shape)
            fixer.Perform()
            healed = fixer.Shape()

            # 重建3D曲线并清理
            breplib_BuildCurves3d(healed)
            breptools_Clean(healed)
            return healed
        except Exception as e:
            logger.warning(f"形状级修复失败, error: {e}")
            return shape

    def load(self, step_path) -> TopoDS_Shape:
        """加载STEP文件并返回形状
        
        Returns:
            加载的形状对象（可能已缩放到单位立方体）
            
        Raises:
            FileNotFoundError: 文件不存在
            RuntimeError: 文件加载失败
        """
        try:
            # 创建STEP读取器
            reader = STEPControl_Reader()
            
            # 读取文件
            status = reader.ReadFile(step_path)
            if status != IFSelect_RetDone:
                raise RuntimeError(f"Failed to read STEP file: {step_path}")
            
            # 转换为形状
            reader.TransferRoots()
            shape = reader.OneShape()
            
            if shape is None or shape.IsNull():
                raise RuntimeError(f"No valid shape found in STEP file: {step_path}")
            
            # 形状级修复
            # shape = self._heal_shape(shape)
            
            # # 如果需要缩放到单位立方体
            # if self.scale_body:
            #     # 使用用户提供的occwl实现进行缩放
            #     return scale_solid_to_unit_box(shape)
            return shape
            
        except Exception as e:
            raise RuntimeError(f"Error loading STEP file {step_path}: {str(e)}")