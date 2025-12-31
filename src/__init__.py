"""
核心功能模块
"""

from .brep_and_graph import (
    BREPGraphDataset,
    load_single_graph,
)
from .inference import ModelInference
# 模块化向量数据库接口
from .vector_db import (
    VectorDBConfig,
    load_config as load_vector_db_config,
    VectorDBClient,
    VectorDBInsert,
    VectorDBQuery,
)

__all__ = [
    "BREPGraphDataset",
    "load_single_graph",
    "ModelInference",
    # 向量数据库模块
    "VectorDBClient",
    "VectorDBInsert",
    "VectorDBQuery",
    "VectorDBConfig",
    "load_vector_db_config",
]
