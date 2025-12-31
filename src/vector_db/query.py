"""
向量数据库查询操作模块

负责从 Milvus 向量数据库查询特征向量。
支持按条件过滤、按ID查询、批量查询等。
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple

import numpy as np
from pymilvus import Collection

from .client import VectorDBClient

logger = logging.getLogger(__name__)


class VectorDBQuery:
    """
    向量数据库查询操作类
    
    负责：
    - 按条件查询向量（用于自定义相似度计算）
    - 按ID查询
    - Milvus ANN 搜索（可选）
    
    使用示例:
        >>> client = VectorDBClient()
        >>> client.connect()
        >>> client.create_collection()
        >>> 
        >>> querier = VectorDBQuery(client)
        >>> records = querier.query_by_filter('part_cls_id == 1')
        >>> for r in records:
        ...     vector = r['vector']
        ...     # 自定义相似度计算
    """
    
    def __init__(self, client: VectorDBClient):
        """
        初始化查询操作类
        
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
    
    def get_by_id(self, part_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取记录
        
        Args:
            part_id: 零件ID
            
        Returns:
            记录数据，不存在则返回 None
        """
        expr = f'part_id == "{part_id}"'
        results = self.collection.query(
            expr=expr,
            output_fields=[
                "part_id", "vector", 
                "part_cls_id", "part_name", "part_code", "part_version",
                "model_file_name", "model_type", "model_url",
                "class_id", "class_name", "confidence", 
                "create_time", "metadata"
            ]
        )
        
        if results:
            record = results[0]
            # 解析元数据
            if "metadata" in record and record["metadata"]:
                try:
                    record["metadata"] = json.loads(record["metadata"])
                except json.JSONDecodeError:
                    pass
            return record
        return None
    
    def query_by_filter(
        self,
        filter_expr: str,
        include_vector: bool = True,
        output_fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        按条件查询记录（用于自定义相似度计算场景）
        
        此方法不使用向量索引，直接按业务字段过滤，返回符合条件的所有记录及其向量。
        适用于：先过滤后在应用层自定义计算相似度的场景。
        
        Args:
            filter_expr: 过滤表达式，支持 Milvus 表达式语法，例如:
                - 'part_cls_id == 1'
                - 'part_cls_id in [1, 2, 3]'
                - 'part_name like "轴承%"'
                - 'class_id >= 0 and confidence > 0.8'
            include_vector: 是否返回向量数据（默认True）
            output_fields: 自定义返回字段，默认返回所有字段
            limit: 最大返回记录数，默认无限制
            
        Returns:
            符合条件的记录列表，每条记录包含字段数据和向量
            
        Example:
            >>> # 查询某分类下的所有零件及其向量
            >>> records = querier.query_by_filter('part_cls_id == 1')
            >>> for r in records:
            ...     vector = r['vector']
            ...     # 自定义相似度计算
            ...     similarity = my_custom_similarity(query_vector, vector)
        """
        # 默认输出字段
        if output_fields is None:
            output_fields = [
                "part_id", "part_cls_id", "part_name", "part_code", "part_version",
                "model_file_name", "model_type", "model_url",
                "class_id", "class_name", "confidence",
                "create_time", "metadata"
            ]
        
        # 是否包含向量
        if include_vector and "vector" not in output_fields:
            output_fields = ["vector"] + output_fields
        
        # 执行查询
        query_params = {
            "expr": filter_expr,
            "output_fields": output_fields,
        }
        if limit is not None:
            query_params["limit"] = limit
        
        results = self.collection.query(**query_params)
        
        # 解析元数据
        for record in results:
            if "metadata" in record and record["metadata"]:
                try:
                    record["metadata"] = json.loads(record["metadata"])
                except json.JSONDecodeError:
                    pass
        
        logger.info(f"✓ 查询到 {len(results)} 条符合条件的记录")
        return results
    
    def query_vectors_by_filter(
        self,
        filter_expr: str,
        limit: Optional[int] = None,
    ) -> Tuple[List[str], np.ndarray]:
        """
        按条件查询并只返回向量（轻量版，用于批量相似度计算）
        
        Args:
            filter_expr: 过滤表达式
            limit: 最大返回记录数
            
        Returns:
            (part_ids, vectors) 元组:
                - part_ids: 零件ID列表
                - vectors: numpy 数组，shape = (n, vector_dim)
        """
        query_params = {
            "expr": filter_expr,
            "output_fields": ["part_id", "vector"],
        }
        if limit is not None:
            query_params["limit"] = limit
        
        results = self.collection.query(**query_params)
        
        if not results:
            return [], np.array([])
        
        part_ids = [r["part_id"] for r in results]
        vectors = np.array([r["vector"] for r in results], dtype=np.float32)
        
        logger.info(f"✓ 查询到 {len(part_ids)} 条向量")
        return part_ids, vectors
    
    def search(
        self,
        query_vector: Union[List[float], np.ndarray],
        top_k: int = 10,
        filter_expr: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        使用 Milvus ANN 搜索相似向量（需要向量索引）
        
        注意：此方法需要创建向量索引。如果使用自定义相似度计算，
        请使用 query_by_filter() 方法。
        
        Args:
            query_vector: 查询向量 (256维)
            top_k: 返回结果数量
            filter_expr: 过滤表达式 (如 "class_id == 1")
            output_fields: 返回的字段列表
            
        Returns:
            搜索结果列表，每个结果包含 id, distance, 及指定的输出字段
        """
        # 转换向量格式
        if isinstance(query_vector, np.ndarray):
            query_vector = query_vector.tolist()
        
        # 默认输出字段
        if output_fields is None:
            output_fields = [
                "part_id", "part_cls_id", "part_name", "part_code", "part_version",
                "model_file_name", "model_type", "model_url",
                "class_id", "class_name", "confidence"
            ]
        
        # 搜索参数
        search_params = {
            "metric_type": self.client.config.metric_type,
            "params": {"nprobe": self.client.config.nprobe}
        }
        
        # 执行搜索
        results = self.collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=output_fields,
        )
        
        # 解析结果
        search_results = []
        for hits in results:
            for hit in hits:
                result = {
                    "part_id": hit.id,
                    "distance": hit.distance,
                    "score": 1.0 / (1.0 + hit.distance),  # 将距离转换为相似度分数
                }
                # 添加额外字段
                for field in output_fields:
                    if field != "part_id" and hasattr(hit, "entity"):
                        result[field] = hit.entity.get(field)
                search_results.append(result)
        
        return search_results
    
    def search_batch(
        self,
        query_vectors: Union[List[List[float]], np.ndarray],
        top_k: int = 10,
        filter_expr: Optional[str] = None,
    ) -> List[List[Dict[str, Any]]]:
        """
        批量搜索相似向量（需要向量索引）
        
        Args:
            query_vectors: 查询向量列表
            top_k: 每个查询返回的结果数量
            filter_expr: 过滤表达式
            
        Returns:
            每个查询的搜索结果列表
        """
        # 转换向量格式
        if isinstance(query_vectors, np.ndarray):
            query_vectors = query_vectors.tolist()
        
        output_fields = [
            "part_id", "part_cls_id", "part_name", "part_code", "part_version",
            "model_file_name", "model_type", "model_url",
            "class_id", "class_name", "confidence"
        ]
        
        search_params = {
            "metric_type": self.client.config.metric_type,
            "params": {"nprobe": self.client.config.nprobe}
        }
        
        results = self.collection.search(
            data=query_vectors,
            anns_field="vector",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=output_fields,
        )
        
        all_results = []
        for hits in results:
            search_results = []
            for hit in hits:
                result = {
                    "part_id": hit.id,
                    "distance": hit.distance,
                    "score": 1.0 / (1.0 + hit.distance),
                }
                for field in output_fields:
                    if field != "part_id" and hasattr(hit, "entity"):
                        result[field] = hit.entity.get(field)
                search_results.append(result)
            all_results.append(search_results)
        
        return all_results
    
    def count(self) -> int:
        """获取集合中的记录数"""
        return self.collection.num_entities

