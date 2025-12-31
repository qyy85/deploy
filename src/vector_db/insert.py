"""
向量数据库插入操作模块

负责将模型特征向量插入到 Milvus 向量数据库。
支持从模型文件路径加载、提取特征并插入。
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import numpy as np
from pymilvus import Collection

from .client import VectorDBClient

logger = logging.getLogger(__name__)


class VectorDBInsert:
    """
    向量数据库插入操作类
    
    负责：
    - 批量插入特征向量
    - 从模型文件提取特征并插入（可选）
    
    使用示例:
        >>> client = VectorDBClient()
        >>> client.connect()
        >>> client.create_collection()
        >>> 
        >>> inserter = VectorDBInsert(client)
        >>> inserter.insert(
        ...     part_ids=["101"],
        ...     vectors=[[0.1, 0.2, ...]],
        ...     part_names=["轴承座"],
        ... )
    """
    
    def __init__(self, client: VectorDBClient):
        """
        初始化插入操作类
        
        Args:
            client: VectorDBClient 实例（必须已连接并创建集合）
        """
        self.client = client
        self._collection: Optional[Collection] = None
    
    @property
    def collection(self) -> Collection:
        """获取集合对象"""
        if self._collection is None:
            self._collection = self.client.get_collection()
            if self._collection is None:
                raise RuntimeError("集合未创建，请先调用 client.create_collection()")
        return self._collection
    
    def insert(
        self,
        part_ids: List[str],
        vectors: Union[List[List[float]], np.ndarray],
        # 业务字段（来自接口）
        part_cls_ids: Optional[List[int]] = None,
        part_names: Optional[List[str]] = None,
        part_codes: Optional[List[str]] = None,
        part_versions: Optional[List[str]] = None,
        # model_info 字段
        model_file_names: Optional[List[str]] = None,
        model_types: Optional[List[str]] = None,
        model_urls: Optional[List[str]] = None,
        # AI 推理结果
        class_ids: Optional[List[int]] = None,
        class_names: Optional[List[str]] = None,
        confidences: Optional[List[float]] = None,
        # 系统字段
        create_times: Optional[List[int]] = None,
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """
        批量插入特征向量
        
        Args:
            part_ids: 零件ID列表
            vectors: 特征向量列表 (每个向量256维)
            part_cls_ids: 零件分类ID列表
            part_names: 零件名称列表
            part_codes: 零件编码列表
            part_versions: 零件版本列表
            model_file_names: 模型文件名列表
            model_types: 模型类型列表
            model_urls: 模型URL列表
            class_ids: AI预测类别ID列表
            class_names: AI预测类别名称列表
            confidences: AI预测置信度列表
            create_times: 创建时间戳列表
            metadata_list: 扩展元数据列表
            
        Returns:
            插入的part_id列表
        """
        n = len(part_ids)
        
        # 转换向量格式
        if isinstance(vectors, np.ndarray):
            vectors = vectors.tolist()
        
        # 设置默认值
        current_time = int(time.time())
        
        part_cls_ids = part_cls_ids or [0] * n
        part_names = part_names or [""] * n
        part_codes = part_codes or [""] * n
        part_versions = part_versions or [""] * n
        model_file_names = model_file_names or [""] * n
        model_types = model_types or [""] * n
        model_urls = model_urls or [""] * n
        class_ids = class_ids or [0] * n
        class_names = class_names or [""] * n
        confidences = confidences or [0.0] * n
        create_times = create_times or [current_time] * n
        metadata_list = metadata_list or [{}] * n
        
        # 序列化元数据
        metadata_strs = [json.dumps(m, ensure_ascii=False) for m in metadata_list]
        
        # 构建插入数据（顺序必须与 Schema 定义一致）
        data = [
            part_ids,
            vectors,
            part_cls_ids,
            part_names,
            part_codes,
            part_versions,
            model_file_names,
            model_types,
            model_urls,
            class_ids,
            class_names,
            confidences,
            create_times,
            metadata_strs,
        ]
        
        # 执行插入
        self.collection.insert(data)
        self.collection.flush()
        
        logger.info(f"✓ 已插入 {n} 条记录")
        return part_ids
    
    def insert_from_model_files(
        self,
        model_paths: List[str],
        part_ids: Optional[List[str]] = None,
        part_cls_ids: Optional[List[int]] = None,
        part_names: Optional[List[str]] = None,
        part_codes: Optional[List[str]] = None,
        part_versions: Optional[List[str]] = None,
        model_types: Optional[List[str]] = None,
        model_urls: Optional[List[str]] = None,
        inference_engine=None,
        graph_builder=None,
    ) -> List[str]:
        """
        从模型文件路径加载、提取特征并插入
        
        注意：此方法需要 inference_engine 和 graph_builder 参数。
        如果未提供，需要先提取特征再调用 insert() 方法。
        
        Args:
            model_paths: 模型文件路径列表（STEP 或 XML 文件）
            part_ids: 零件ID列表（可选，默认使用文件名）
            part_cls_ids: 零件分类ID列表
            part_names: 零件名称列表
            part_codes: 零件编码列表
            part_versions: 零件版本列表
            model_types: 模型类型列表
            model_urls: 模型URL列表
            inference_engine: 推理引擎实例（ModelInference）
            graph_builder: 图构建器实例
            
        Returns:
            插入的part_id列表
        """
        if inference_engine is None or graph_builder is None:
            raise ValueError(
                "insert_from_model_files 需要 inference_engine 和 graph_builder 参数。"
                "请先提取特征，然后使用 insert() 方法。"
            )
        
        # TODO: 实现从模型文件提取特征并插入的逻辑
        # 1. 加载模型文件
        # 2. 构建图
        # 3. 推理提取特征和分类结果
        # 4. 调用 insert()
        
        raise NotImplementedError("此功能需要实现模型文件加载和特征提取逻辑")
    
    def delete_by_ids(self, part_ids: List[str]) -> int:
        """
        批量删除记录
        
        Args:
            part_ids: 要删除的零件ID列表
            
        Returns:
            删除的记录数
        """
        # 构建删除表达式
        ids_str = ", ".join([f'"{pid}"' for pid in part_ids])
        expr = f"part_id in [{ids_str}]"
        
        result = self.collection.delete(expr)
        self.collection.flush()
        
        deleted_count = result.delete_count if hasattr(result, 'delete_count') else len(part_ids)
        logger.info(f"✓ 已删除 {deleted_count} 条记录")
        return deleted_count

