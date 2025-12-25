"""
常量定义模块
定义所有枚举编码和常量值
"""
import math
from OCC.Core.GeomAbs import (
    GeomAbs_C0, GeomAbs_G1, GeomAbs_C1,
    GeomAbs_G2, GeomAbs_C2, GeomAbs_C3, GeomAbs_CN
)
from OCC.Core.TopAbs import (
    TopAbs_FORWARD, TopAbs_REVERSED,
    TopAbs_INTERNAL, TopAbs_EXTERNAL
)


# ============== 数学常量 ==============
class MathConstants:
    """数学常量"""
    PI = math.pi
    TWO_PI = 2 * math.pi
    HALF_PI = math.pi / 2
    
    # 角度转换
    RAD_TO_DEG = 180.0 / math.pi
    DEG_TO_RAD = math.pi / 180.0
    
    # 容差
    ANGLE_TOLERANCE = 1e-6
    LENGTH_TOLERANCE = 1e-10
    FULL_CIRCLE_TOLERANCE = 0.01  # 判断是否完整圆的容差


# ============== 边角色编码 ==============
class EdgeRole:
    """边角色编码"""
    FREE = 0           # 自由边（不连接任何面）
    BOUNDARY = 1       # 边界边（连接1个面）
    INTERIOR = 2       # 内部边（连接2个面）
    NON_MANIFOLD = 3   # 非流形边（连接3个及以上面）
    
    @staticmethod
    def from_num_faces(num_faces: int) -> int:
        """根据连接面数量判断边角色"""
        if num_faces == 0:
            return EdgeRole.FREE
        elif num_faces == 1:
            return EdgeRole.BOUNDARY
        elif num_faces == 2:
            return EdgeRole.INTERIOR
        else:
            return EdgeRole.NON_MANIFOLD
    
    @staticmethod
    def to_name(role: int) -> str:
        """将角色编码转换为名称（用于调试）"""
        names = {
            0: "free",
            1: "boundary",
            2: "interior",
            3: "non_manifold"
        }
        return names.get(role, "unknown")


# ============== 连续性编码 ==============
class Continuity:
    """连续性类型编码"""
    NONE = -1   # 无连续性（边界边或自由边）
    C0 = 0      # 位置连续（尖锐边）
    G1 = 1      # 几何切线连续
    C1 = 2      # 参数切线连续
    G2 = 3      # 几何曲率连续
    C2 = 4      # 参数曲率连续
    C3 = 5      # 三阶连续
    CN = 6      # N阶连续（无限光滑）
    
    # pythonocc 枚举值到整数编码的映射
    GEOMABS_TO_CODE = {
        GeomAbs_C0: 0,
        GeomAbs_G1: 1,
        GeomAbs_C1: 2,
        GeomAbs_G2: 3,
        GeomAbs_C2: 4,
        GeomAbs_C3: 5,
        GeomAbs_CN: 6,
    }
    
    @staticmethod
    def from_geomabs(geomabs_continuity) -> int:
        """将 pythonocc 的连续性枚举转换为整数编码"""
        return Continuity.GEOMABS_TO_CODE.get(geomabs_continuity, Continuity.NONE)
    
    @staticmethod
    def to_name(continuity: int) -> str:
        """将连续性编码转换为名称（用于调试）"""
        names = {
            -1: "None",
            0: "C0",
            1: "G1",
            2: "C1",
            3: "G2",
            4: "C2",
            5: "C3",
            6: "CN"
        }
        return names.get(continuity, "Unknown")
    
    @staticmethod
    def is_smooth(continuity: int) -> bool:
        """判断是否光滑（>= G1）"""
        return continuity >= Continuity.G1
    
    @staticmethod
    def is_sharp(continuity: int) -> bool:
        """判断是否尖锐（= C0）"""
        return continuity == Continuity.C0


# ============== 方向编码 ==============
class Orientation:
    """方向编码"""
    FORWARD = 0
    REVERSED = 1
    INTERNAL = 2
    EXTERNAL = 3
    
    # pythonocc 枚举值到整数编码的映射
    TOPABS_TO_CODE = {
        TopAbs_FORWARD: 0,
        TopAbs_REVERSED: 1,
        TopAbs_INTERNAL: 2,
        TopAbs_EXTERNAL: 3,
    }
    
    @staticmethod
    def from_topabs(topabs_orientation) -> int:
        """将 pythonocc 的方向枚举转换为整数编码"""
        return Orientation.TOPABS_TO_CODE.get(topabs_orientation, Orientation.FORWARD)
    
    @staticmethod
    def to_name(orientation: int) -> str:
        """将方向编码转换为名称（用于调试）"""
        names = {
            0: "FORWARD",
            1: "REVERSED",
            2: "INTERNAL",
            3: "EXTERNAL"
        }
        return names.get(orientation, "Unknown")


# ============== 几何类型名称 ==============
class GeometryType:
    """几何类型名称常量"""
    
    # 边类型
    EDGE_LINE = "Line"
    EDGE_CIRCLE = "Circle"
    EDGE_ELLIPSE = "Ellipse"
    EDGE_PARABOLA = "Parabola"
    EDGE_HYPERBOLA = "Hyperbola"
    EDGE_BSPLINE = "BSplineCurve"
    EDGE_BEZIER = "BezierCurve"
    EDGE_OFFSET = "OffsetCurve"
    EDGE_OTHER = "OtherCurve"
    
    # 面类型
    FACE_PLANE = "Plane"
    FACE_CYLINDER = "Cylinder"
    FACE_CONE = "Cone"
    FACE_SPHERE = "Sphere"
    FACE_TORUS = "Torus"
    FACE_BSPLINE = "BSplineSurface"
    FACE_BEZIER = "BezierSurface"
    FACE_REVOLUTION = "SurfaceOfRevolution"
    FACE_EXTRUSION = "SurfaceOfExtrusion"
    FACE_OFFSET = "OffsetSurface"
    FACE_OTHER = "OtherSurface"


# ============== 特征提取配置常量 ==============
class ExtractionConfig:
    """特征提取配置常量"""
    
    # 默认容差
    DEFAULT_TOLERANCE = 1e-7
    
    # 长度计算失败时的默认值
    FAILED_LENGTH = -1.0
    
    # 几何特征提取失败时的标识
    FAILED_EXTRACTION = -1
    
    # 完整圆判断阈值
    FULL_CIRCLE_THRESHOLD = MathConstants.FULL_CIRCLE_TOLERANCE
    
    # 完整球/圆柱判断阈值
    FULL_RANGE_THRESHOLD = MathConstants.FULL_CIRCLE_TOLERANCE

