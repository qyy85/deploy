#!/usr/bin/env python3
"""
初始化 Milvus 向量数据库

使用方法:
    # 使用 config.yaml 中的配置（推荐）
    python init_vector_db.py
    
    # 指定配置文件
    python init_vector_db.py --config /path/to/config.yaml
    
    # 命令行参数覆盖配置文件
    python init_vector_db.py --host 192.168.30.132 --port 19530
    
    # 重新创建数据库和集合（删除现有数据）
    python init_vector_db.py --recreate
    
    # 使用自定义数据库和集合名称
    python init_vector_db.py --database my_db --collection my_features
    

配置优先级（从高到低）:
    1. 命令行参数
    2. config.yaml 文件
    3. 环境变量
    4. 默认值

环境变量:
    MILVUS_HOST: Milvus 服务器地址
    MILVUS_PORT: Milvus 服务器端口
    MILVUS_DATABASE: 数据库名称
    MILVUS_COLLECTION: 集合名称
    VECTOR_DB_CONTEXT: JSON 格式的配置 {"host": "...", "port": ..., "database": ...}
"""

import argparse
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.vector_db import (
    VectorDBClient,
    VectorDBConfig,
    load_config,
)


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def main():
    parser = argparse.ArgumentParser(
        description="初始化 Milvus 向量数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Milvus 服务器地址 (覆盖配置文件)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Milvus 服务器端口 (默认: 19530)"
    )
    parser.add_argument(
        "--database",
        type=str,
        default=None,
        help="数据库名称 (默认: classify_features)"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=None,
        help="集合名称 (默认: model_features)"
    )
    parser.add_argument(
        "--vector-dim",
        type=int,
        default=256,
        help="特征向量维度 (默认: 256)"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="删除现有集合并重新创建"
    )
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 使用统一的配置加载函数
    config = load_config(yaml_path=args.config)
    
    # 命令行参数覆盖（优先级最高）
    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    if args.database:
        config.database_name = args.database
    if args.collection:
        config.collection_name = args.collection
    if args.vector_dim:
        config.vector_dim = args.vector_dim
    
    print("=" * 60)
    print("Milvus 向量数据库初始化")
    print("=" * 60)
    print(f"\n配置信息:")
    print(f"  服务器地址: {config.host}:{config.port}")
    print(f"  数据库名称: {config.database_name}")
    print(f"  集合名称: {config.collection_name}")
    print(f"  向量维度: {config.vector_dim}")
    print(f"  索引类型: {config.index_type}")
    print(f"  距离度量: {config.metric_type}")
    print()
    
    try:
        # 创建数据库客户端
        client = VectorDBClient(config)
        
        # 连接服务器
        print("正在连接 Milvus 服务器...")
        if not client.connect():
            logger.error("无法连接到 Milvus 服务器")
            sys.exit(1)
        
        # 创建集合
        print(f"\n正在创建集合 '{config.collection_name}'...")
        client.create_collection(drop_if_exists=args.recreate)
        
        # 显示数据库和集合信息
        all_dbs = client.list_databases()
        collections = client.list_collections()
        collection = client.get_collection()
        num_entities = collection.num_entities if collection else 0
        
        print(f"\n数据库信息:")
        print(f"  当前数据库: {config.database_name}")
        print(f"  所有数据库: {all_dbs}")
        print(f"  当前数据库中的集合: {collections}")
        print(f"\n集合信息:")
        print(f"  集合名称: {config.collection_name}")
        print(f"  记录数: {num_entities}")
        
        # 显示最终状态
        collection = client.get_collection()
        final_count = collection.num_entities if collection else 0
        
        print("\n" + "=" * 60)
        print("✓ 初始化完成!")
        print("=" * 60)
        print(f"\n最终记录数: {final_count}")
        
        # 关闭连接
        client.close()
        
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

