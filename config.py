"""
部署配置模块
"""

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ModelConfig:
    """模型配置"""
    # 模型路径（二选一）
    model_path: str = "pt/model.pt"  # 导出的模型
    checkpoint_path: Optional[str] = None  # 原始检查点
    
    # 模型参数
    graph_emb_dim: int = 256
    device: str = "cpu"  # "cpu" or "cuda"
    batch_size: int = 8  # 批量推理大小


@dataclass
class ClassMapping:
    """类别映射配置"""
    # 父类映射
    parent_classes: Dict[str, str] = field(default_factory=lambda: {
        "zhengti": "整体式",
        "zhuzao": "铸造式", 
        "huanxing": "环形式"
    })
    
    # 子类映射
    child_classes: Dict[str, str] = field(default_factory=lambda: {
        "che": "车削",
        "li": "里",
        "liwo": "螺窝",
        "wo": "窝",
        "wuzhou": "无轴"
    })
    
    # 完整类别映射 (用于分类器)
    # 格式: "父类" -> 类别ID
    full_class_map: Dict[str, int] = field(default_factory=lambda: {
        "huanxing": 0,
        "zhuzao": 1,
        "zhengti": 2,
    })
    
    def get_class_name(self, class_id: int) -> str:
        """根据类别ID获取中文名称"""
        reverse_map = {v: k for k, v in self.full_class_map.items()}
        if class_id not in reverse_map:
            return f"未知类别({class_id})"
        
        # 直接使用父类名称（不再需要分割路径）
        parent = reverse_map[class_id]
        parent_cn = self.parent_classes.get(parent, parent)
        return parent_cn
    
    def get_all_class_names(self) -> List[str]:
        """获取所有类别的中文名称"""
        return [self.get_class_name(i) for i in range(len(self.full_class_map))]


@dataclass
class VectorDBConfig:
    """
    向量数据库配置
    
    注意: 此配置类与 src/vector_db.py 中的 VectorDBConfig 保持同步
    可通过 src.vector_db.VectorDBConfig.from_deploy_config(config) 转换
    """
    db_type: str = "milvus"  # 向量数据库类型
    host: str = "192.168.30.132"
    port: int = 19530
    database_name: str = "model_feat_rs"  # 数据库名称（独立存储库）
    collection_name: str = "feat"   # 集合名称（相当于数据库中的表）
    vector_dim: int = 256  # 特征向量维度
    index_type: str = "IVF_FLAT"  # 索引类型: IVF_FLAT, IVF_SQ8, HNSW
    metric_type: str = "L2"  # 距离度量: L2, IP (内积), COSINE
    nlist: int = 128  # 聚类中心数量
    nprobe: int = 16  # 搜索时探测的聚类数量


@dataclass  
class UIConfig:
    """UI配置"""
    title: str = "🔬 3D BREP 模型智能分类系统"
    description: str = "上传STEP格式的三维模型，自动提取BREP拓扑结构并进行分类预测"
    theme: str = "dark"  # "dark" or "light"
    enable_3d_preview: bool = True
    enable_batch_processing: bool = True
    max_batch_size: int = 20
    server_port: int = 7860
    share: bool = False


@dataclass
class DeployConfig:
    """总部署配置"""
    model: ModelConfig = field(default_factory=ModelConfig)
    class_mapping: ClassMapping = field(default_factory=ClassMapping)
    ui: UIConfig = field(default_factory=UIConfig)
    vector_db: VectorDBConfig = field(default_factory=VectorDBConfig)
    
    temp_dir: str = "/tmp/brep_deploy"
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "DeployConfig":
        """从YAML文件加载配置"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        config = cls()
        
        if "model" in config_dict:
            config.model = ModelConfig(**config_dict["model"])
        if "class_mapping" in config_dict:
            config.class_mapping = ClassMapping(**config_dict["class_mapping"])
        if "ui" in config_dict:
            config.ui = UIConfig(**config_dict["ui"])
        if "vector_db" in config_dict:
            config.vector_db = VectorDBConfig(**config_dict["vector_db"])
        if "temp_dir" in config_dict:
            config.temp_dir = config_dict["temp_dir"]
            
        return config
    
    def to_yaml(self, yaml_path: str):
        """保存配置到YAML文件"""
        config_dict = {
            "model": {
                "model_path": self.model.model_path,
                "checkpoint_path": self.model.checkpoint_path,
                "graph_emb_dim": self.model.graph_emb_dim,
                "device": self.model.device,
                "batch_size": self.model.batch_size,
            },
            "class_mapping": {
                "parent_classes": self.class_mapping.parent_classes,
                "child_classes": self.class_mapping.child_classes,
                "full_class_map": self.class_mapping.full_class_map,
            },
            "ui": {
                "title": self.ui.title,
                "description": self.ui.description,
                "theme": self.ui.theme,
                "enable_3d_preview": self.ui.enable_3d_preview,
                "enable_batch_processing": self.ui.enable_batch_processing,
                "max_batch_size": self.ui.max_batch_size,
                "server_port": self.ui.server_port,
                "share": self.ui.share,
            },
            "vector_db": {
                "db_type": self.vector_db.db_type,
                "host": self.vector_db.host,
                "port": self.vector_db.port,
                "database_name": self.vector_db.database_name,
                "collection_name": self.vector_db.collection_name,
                "vector_dim": self.vector_db.vector_dim,
                "index_type": self.vector_db.index_type,
                "metric_type": self.vector_db.metric_type,
                "nlist": self.vector_db.nlist,
                "nprobe": self.vector_db.nprobe,
            },
            "temp_dir": self.temp_dir,
        }
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)


# 默认配置
DEFAULT_CONFIG = DeployConfig()
