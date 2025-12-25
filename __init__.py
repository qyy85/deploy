"""
3D BREP Model Classification Deployment Module
===============================================

本模块提供完整的3D模型分类部署解决方案：
- BREP图提取：从STEP文件构建异构图
- ONNX推理：高效模型推理
- Web UI：现代化交互界面

使用方法：
    python -m deploy.app --config deploy/config.yaml
"""

from .config import DeployConfig

__version__ = "1.0.0"
__all__ = ["DeployConfig"]

