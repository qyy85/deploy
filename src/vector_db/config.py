"""
向量数据库配置模块

支持从多种来源加载配置：
- YAML 配置文件 (config.yaml)
- 环境变量
- DeployConfig 对象
"""

import json
import os
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class VectorDBConfig:
    """
    向量数据库配置
    
    Attributes:
        host: Milvus 服务器地址
        port: Milvus 服务器端口
        database_name: 数据库名称（独立存储库）
        collection_name: 集合名称（相当于数据库中的表）
        vector_dim: 特征向量维度
        index_type: 索引类型 (IVF_FLAT, IVF_SQ8, HNSW 等)
        metric_type: 距离度量类型 (L2, IP, COSINE)
        nlist: 聚类中心数量
        nprobe: 搜索时探测的聚类数量
    """
    host: str = "192.168.30.132"
    port: int = 19530
    database_name: str = "model_feat_rs"
    collection_name: str = "feat"
    vector_dim: int = 256
    index_type: str = "IVF_FLAT"
    metric_type: str = "L2"
    nlist: int = 128
    nprobe: int = 16
    
    @classmethod
    def from_env(cls) -> "VectorDBConfig":
        """
        从环境变量加载配置
        
        支持的环境变量:
            VECTOR_DB_CONTEXT: JSON 格式的配置
            MILVUS_HOST: 服务器地址
            MILVUS_PORT: 服务器端口
            MILVUS_DATABASE: 数据库名称
            MILVUS_COLLECTION: 集合名称
        
        Returns:
            VectorDBConfig 实例
        """
        config = cls()
        
        # 优先从 VECTOR_DB_CONTEXT 加载
        context = os.getenv("VECTOR_DB_CONTEXT")
        if context:
            try:
                ctx = json.loads(context)
                config.host = ctx.get("host", config.host)
                config.port = int(ctx.get("port", config.port))
                config.database_name = ctx.get("database", config.database_name)
                config.collection_name = ctx.get("collection", config.collection_name)
                config.vector_dim = int(ctx.get("vector_dim", config.vector_dim))
                config.index_type = ctx.get("index_type", config.index_type)
                config.metric_type = ctx.get("metric_type", config.metric_type)
                config.nlist = int(ctx.get("nlist", config.nlist))
                config.nprobe = int(ctx.get("nprobe", config.nprobe))
            except json.JSONDecodeError:
                logger.warning("无法解析 VECTOR_DB_CONTEXT，使用默认配置")
        
        # 单独的环境变量可以覆盖
        config.host = os.getenv("MILVUS_HOST", config.host)
        config.port = int(os.getenv("MILVUS_PORT", str(config.port)))
        config.database_name = os.getenv("MILVUS_DATABASE", config.database_name)
        config.collection_name = os.getenv("MILVUS_COLLECTION", config.collection_name)
        
        return config
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "VectorDBConfig":
        """
        从 YAML 配置文件加载配置
        
        Args:
            yaml_path: YAML 文件路径 (如 config.yaml)
        
        Returns:
            VectorDBConfig 实例
        """
        import yaml
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        config = cls()
        
        if "vector_db" in config_dict:
            vdb_config = config_dict["vector_db"]
            config.host = vdb_config.get("host", config.host)
            config.port = int(vdb_config.get("port", config.port))
            config.database_name = vdb_config.get("database_name", config.database_name)
            config.collection_name = vdb_config.get("collection_name", config.collection_name)
            config.vector_dim = int(vdb_config.get("vector_dim", config.vector_dim))
            config.index_type = vdb_config.get("index_type", config.index_type)
            config.metric_type = vdb_config.get("metric_type", config.metric_type)
            config.nlist = int(vdb_config.get("nlist", config.nlist))
            config.nprobe = int(vdb_config.get("nprobe", config.nprobe))
        
        return config
    
    @classmethod
    def from_deploy_config(cls, deploy_config) -> "VectorDBConfig":
        """
        从 DeployConfig 对象创建配置
        
        Args:
            deploy_config: config.DeployConfig 实例
        
        Returns:
            VectorDBConfig 实例
        """
        vdb = deploy_config.vector_db
        return cls(
            host=vdb.host,
            port=vdb.port,
            database_name=vdb.database_name,
            collection_name=vdb.collection_name,
            vector_dim=vdb.vector_dim,
            index_type=vdb.index_type,
            metric_type=vdb.metric_type,
            nlist=vdb.nlist,
            nprobe=vdb.nprobe,
        )
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> "VectorDBConfig":
        """
        从字典创建配置
        
        Args:
            config_dict: 配置字典
        
        Returns:
            VectorDBConfig 实例
        """
        return cls(
            host=config_dict.get("host", cls.host),
            port=int(config_dict.get("port", cls.port)),
            database_name=config_dict.get("database_name", cls.database_name),
            collection_name=config_dict.get("collection_name", cls.collection_name),
            vector_dim=int(config_dict.get("vector_dim", cls.vector_dim)),
            index_type=config_dict.get("index_type", cls.index_type),
            metric_type=config_dict.get("metric_type", cls.metric_type),
            nlist=int(config_dict.get("nlist", cls.nlist)),
            nprobe=int(config_dict.get("nprobe", cls.nprobe)),
        )
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            配置字典
        """
        return {
            "host": self.host,
            "port": self.port,
            "database_name": self.database_name,
            "collection_name": self.collection_name,
            "vector_dim": self.vector_dim,
            "index_type": self.index_type,
            "metric_type": self.metric_type,
            "nlist": self.nlist,
            "nprobe": self.nprobe,
        }
    
    def __str__(self) -> str:
        return (
            f"VectorDBConfig(\n"
            f"  host={self.host},\n"
            f"  port={self.port},\n"
            f"  database_name={self.database_name},\n"
            f"  collection_name={self.collection_name},\n"
            f"  vector_dim={self.vector_dim},\n"
            f"  index_type={self.index_type},\n"
            f"  metric_type={self.metric_type}\n"
            f")"
        )


def load_config(
    yaml_path: Optional[str] = None,
    use_env: bool = True,
) -> VectorDBConfig:
    """
    智能加载配置
    
    优先级（从高到低）:
        1. 指定的 YAML 文件
        2. 默认 config.yaml（如果存在）
        3. 环境变量
        4. 默认值
    
    Args:
        yaml_path: YAML 配置文件路径
        use_env: 是否使用环境变量覆盖
    
    Returns:
        VectorDBConfig 实例
    """
    from pathlib import Path
    
    config = None
    
    # 尝试从 YAML 加载
    if yaml_path:
        config_file = Path(yaml_path)
        if config_file.exists():
            logger.info(f"从配置文件加载: {yaml_path}")
            config = VectorDBConfig.from_yaml(str(config_file))
    
    # 尝试默认 config.yaml
    if config is None:
        default_yaml = Path(__file__).parent.parent / "config.yaml"
        if default_yaml.exists():
            logger.info(f"从默认配置文件加载: {default_yaml}")
            config = VectorDBConfig.from_yaml(str(default_yaml))
    
    # 使用环境变量或默认值
    if config is None:
        if use_env:
            logger.info("从环境变量加载配置")
            config = VectorDBConfig.from_env()
        else:
            logger.info("使用默认配置")
            config = VectorDBConfig()
    
    return config

