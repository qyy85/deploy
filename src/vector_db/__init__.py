"""
向量数据库模块

模块化设计，职责清晰：
- client: 客户端连接和集合管理
- insert: 插入操作
- query: 查询操作
- config: 配置管理
"""

from .config import VectorDBConfig, load_config
from .client import VectorDBClient
from .insert import VectorDBInsert
from .query import VectorDBQuery

__all__ = [
    "VectorDBConfig",
    "load_config",
    "VectorDBClient",
    "VectorDBInsert",
    "VectorDBQuery",
]

