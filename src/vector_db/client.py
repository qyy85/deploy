"""
Milvus 向量数据库客户端

负责连接管理和集合（Collection）的创建与管理。
"""

import logging
from typing import Optional

from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
    MilvusException,
    db,
)

from .config import VectorDBConfig

logger = logging.getLogger(__name__)


class VectorDBClient:
    """
    Milvus 向量数据库客户端
    
    负责：
    - 连接管理（连接、断开）
    - 数据库管理（创建、切换）
    - 集合管理（创建、删除、检查）
    
    使用示例:
        >>> client = VectorDBClient()
        >>> client.connect()
        >>> client.create_collection()
        >>> collection = client.get_collection()
        >>> client.close()
    """
    
    def __init__(self, config: Optional[VectorDBConfig] = None):
        """
        初始化向量数据库客户端
        
        Args:
            config: 数据库配置，默认从环境变量加载
        """
        self.config = config or VectorDBConfig.from_env()
        self.collection: Optional[Collection] = None
        self._connected = False
        self._alias = "default"
    
    def connect(self) -> bool:
        """
        连接到 Milvus 服务器并切换到指定数据库
        
        Returns:
            是否连接成功
        """
        try:
            connections.connect(
                alias=self._alias,
                host=self.config.host,
                port=self.config.port,
            )
            self._connected = True
            logger.info(f"✓ 已连接到 Milvus: {self.config.host}:{self.config.port}")
            
            # 创建数据库（如果不存在）
            self._ensure_database()
            
            return True
        except MilvusException as e:
            logger.error(f"✗ 连接 Milvus 失败: {e}")
            return False
    
    def _ensure_database(self):
        """确保数据库存在，如果不存在则创建"""
        database_name = self.config.database_name
        
        # 获取现有数据库列表
        existing_dbs = db.list_database()
        
        if database_name not in existing_dbs:
            # 创建新数据库
            db.create_database(database_name)
            logger.info(f"✓ 已创建数据库: {database_name}")
        else:
            logger.info(f"✓ 数据库已存在: {database_name}")
        
        # 切换到目标数据库
        db.using_database(database_name)
        logger.info(f"✓ 已切换到数据库: {database_name}")
    
    def close(self):
        """关闭连接"""
        if self._connected:
            connections.disconnect(self._alias)
            self._connected = False
            logger.info("已断开 Milvus 连接")
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    def collection_exists(self, name: Optional[str] = None) -> bool:
        """检查集合是否存在"""
        collection_name = name or self.config.collection_name
        return utility.has_collection(collection_name)
    
    def create_collection(self, drop_if_exists: bool = False) -> Collection:
        """
        创建特征向量集合
        
        Schema（参考接口 pushPartsList 的 JSON 结构）:
            业务字段:
                - part_id: 零件唯一标识 (VARCHAR, primary key)
                - part_cls_id: 零件分类ID (INT64)
                - part_name: 零件名称 (VARCHAR)
                - part_code: 零件编码 (VARCHAR)
                - part_version: 零件版本 (VARCHAR)
            
            模型信息 (model_info):
                - model_file_name: 模型文件名 (VARCHAR)
                - model_type: 模型类型 (VARCHAR)
                - model_url: 模型URL (VARCHAR)
            
            AI推理结果:
                - vector: 特征向量 (FLOAT_VECTOR, 256维)
                - class_id: 预测类别ID (INT64)
                - class_name: 预测类别名称 (VARCHAR)
                - confidence: 预测置信度 (FLOAT)
            
            系统字段:
                - create_time: 创建时间戳 (INT64)
                - metadata: 扩展元数据 JSON (VARCHAR)
        
        Args:
            drop_if_exists: 是否删除已存在的集合
            
        Returns:
            创建的集合对象
        """
        collection_name = self.config.collection_name
        
        # 检查并处理已存在的集合
        if self.collection_exists():
            if drop_if_exists:
                utility.drop_collection(collection_name)
                logger.info(f"已删除现有集合: {collection_name}")
            else:
                logger.info(f"集合已存在: {collection_name}")
                self.collection = Collection(collection_name)
                self._load_collection()
                return self.collection
        
        # 定义字段 Schema（参考接口 pushPartsList 的 JSON 结构）
        fields = [
            # 主键：零件ID（接口中为整数，这里用字符串存储以兼容各种ID格式）
            FieldSchema(
                name="part_id",
                dtype=DataType.VARCHAR,
                max_length=64,
                is_primary=True,
                description="零件唯一标识"
            ),
            # 特征向量（AI模型提取）
            FieldSchema(
                name="vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.config.vector_dim,
                description="模型特征向量"
            ),
            # === 来自接口的业务字段 ===
            FieldSchema(
                name="part_cls_id",
                dtype=DataType.INT64,
                description="零件分类ID"
            ),
            FieldSchema(
                name="part_name",
                dtype=DataType.VARCHAR,
                max_length=256,
                description="零件名称"
            ),
            FieldSchema(
                name="part_code",
                dtype=DataType.VARCHAR,
                max_length=128,
                description="零件编码"
            ),
            FieldSchema(
                name="part_version",
                dtype=DataType.VARCHAR,
                max_length=64,
                description="零件版本"
            ),
            # === model_info 子对象字段 ===
            FieldSchema(
                name="model_file_name",
                dtype=DataType.VARCHAR,
                max_length=512,
                description="模型文件名"
            ),
            FieldSchema(
                name="model_type",
                dtype=DataType.VARCHAR,
                max_length=64,
                description="模型类型"
            ),
            FieldSchema(
                name="model_url",
                dtype=DataType.VARCHAR,
                max_length=1024,
                description="模型URL"
            ),
            # === AI 推理结果字段 ===
            FieldSchema(
                name="class_id",
                dtype=DataType.INT64,
                description="预测类别ID"
            ),
            FieldSchema(
                name="class_name",
                dtype=DataType.VARCHAR,
                max_length=128,
                description="预测类别名称"
            ),
            FieldSchema(
                name="confidence",
                dtype=DataType.FLOAT,
                description="预测置信度"
            ),
            # === 系统字段 ===
            FieldSchema(
                name="create_time",
                dtype=DataType.INT64,
                description="创建时间戳"
            ),
            FieldSchema(
                name="metadata",
                dtype=DataType.VARCHAR,
                max_length=4096,
                description="扩展元数据JSON"
            ),
        ]
        
        # 创建集合 Schema
        schema = CollectionSchema(
            fields=fields,
            description="3D模型特征向量集合，用于零件相似性搜索"
        )
        
        # 创建集合
        self.collection = Collection(
            name=collection_name,
            schema=schema,
            using=self._alias,
        )
        logger.info(f"✓ 已创建集合: {collection_name}")
        
        # 注意：当前业务场景使用自定义相似度计算，不需要向量索引
        # 如需启用 Milvus ANN 搜索，取消下行注释
        self._create_index()
        
        # 加载集合到内存
        self._load_collection()
        
        return self.collection
    
    def _create_index(self):
        """创建向量索引（保留实现，默认不调用）"""
        index_params = {
            "metric_type": self.config.metric_type,
            "index_type": self.config.index_type,
            "params": {"nlist": self.config.nlist}
        }
        
        self.collection.create_index(
            field_name="vector",
            index_params=index_params
        )
        logger.info(f"✓ 已创建向量索引: {self.config.index_type}")
    
    def _load_collection(self):
        """加载集合到内存"""
        if self.collection:
            self.collection.load()
            logger.info("✓ 集合已加载到内存")
    
    def get_collection(self) -> Optional[Collection]:
        """获取集合对象"""
        if self.collection is None and self.collection_exists():
            self.collection = Collection(self.config.collection_name)
            self._load_collection()
        return self.collection
    
    def drop_collection(self):
        """删除集合（表）"""
        if self.collection_exists():
            utility.drop_collection(self.config.collection_name)
            self.collection = None
            logger.info(f"✓ 已删除集合: {self.config.collection_name}")
    
    def drop_database(self):
        """删除整个数据库（包含所有集合）"""
        database_name = self.config.database_name
        
        # 先切换到默认数据库
        db.using_database("default")
        
        existing_dbs = db.list_database()
        if database_name in existing_dbs:
            db.drop_database(database_name)
            self.collection = None
            logger.info(f"✓ 已删除数据库: {database_name}")
        else:
            logger.warning(f"数据库不存在: {database_name}")
    
    def list_databases(self):
        """列出所有数据库"""
        return db.list_database()
    
    def list_collections(self):
        """列出当前数据库中的所有集合"""
        return utility.list_collections()
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()

