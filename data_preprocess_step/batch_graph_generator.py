#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成异构图脚本
从CAD数据源目录批量处理STEP文件，生成异构图并按类别存储
"""
import os
import sys
import logging
import time
import json
import traceback
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Callable
import argparse
from tqdm import tqdm

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_preprocess.graph_builder import GraphBuilder
import dgl


def process_step_to_graph(step_path: str) -> Tuple[Optional[dgl.DGLGraph], Dict]:
    """
    处理单个 STEP 文件，返回 DGL 图和元数据
    
    这是一个简单的工具函数，适用于部署和快速测试
    
    Args:
        step_path: STEP 文件路径
        
    Returns:
        (dgl_graph, metadata): DGL 图和元数据字典
    """
    step_file = Path(step_path)
    
    if not step_file.exists():
        return None, {
            "source_file": str(step_path),
            "file_name": step_file.name,
            "status": "error",
            "error": f"文件不存在: {step_path}"
        }
    
    try:
        graph_builder = GraphBuilder()
        hetero_graph = graph_builder.from_step(str(step_file))
        dgl_graph = hetero_graph.build_dgl_graph()
        
        metadata = {
            "source_file": str(step_file),
            "file_name": step_file.name,
            "status": "success",
            "num_nodes": sum(dgl_graph.num_nodes(ntype) for ntype in dgl_graph.ntypes),
            "num_edges": sum(dgl_graph.num_edges(etype) for etype in dgl_graph.canonical_etypes),
            "node_types": list(dgl_graph.ntypes),
            "edge_types": [et[1] for et in dgl_graph.canonical_etypes],
        }
        
        return dgl_graph, metadata
        
    except Exception as e:
        return None, {
            "source_file": str(step_path),
            "file_name": step_file.name,
            "status": "error",
            "error": str(e)
        }


def process_step_files_batch(
    file_paths: List[str], 
    max_workers: int = 4,
    show_progress: bool = True,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[Tuple[Optional[dgl.DGLGraph], Dict]]:
    """
    批量处理 STEP 文件列表（不按类别）
    
    Args:
        file_paths: STEP 文件路径列表
        max_workers: 最大并行进程数
        show_progress: 是否显示进度条
        progress_callback: 进度回调函数，接收 (current, total, message) 参数
        
    Returns:
        [(dgl_graph, metadata), ...]: 结果列表，顺序与输入一致
    """
    if not file_paths:
        return []
    
    # 单文件直接处理
    if len(file_paths) == 1:
        if progress_callback:
            progress_callback(0, 1, "开始处理单个文件...")
        result = process_step_to_graph(file_paths[0])
        if progress_callback:
            progress_callback(1, 1, "处理完成")
        return [result]
    
    # 多文件并行处理
    results = [None] * len(file_paths)
    total_files = len(file_paths)
    completed_count = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 提交任务，保留索引
        future_to_idx = {
            executor.submit(process_step_to_graph, path): idx 
            for idx, path in enumerate(file_paths)
        }
        
        # 创建迭代器
        futures = as_completed(future_to_idx)
        if show_progress and not progress_callback:
            try:
                futures = tqdm(futures, total=len(file_paths), desc="处理STEP文件")
            except:
                pass
        
        # 收集结果
        for future in futures:
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
                completed_count += 1
                if progress_callback:
                    file_name = Path(file_paths[idx]).name
                    progress_callback(completed_count, total_files, f"正在处理: {file_name} ({completed_count}/{total_files})")
            except Exception as e:
                results[idx] = (None, {
                    "source_file": file_paths[idx],
                    "status": "error",
                    "error": str(e)
                })
                completed_count += 1
                if progress_callback:
                    file_name = Path(file_paths[idx]).name
                    progress_callback(completed_count, total_files, f"处理失败: {file_name} ({completed_count}/{total_files})")
    
    return results


# 模块级别的处理函数，用于多进程调用
def process_single_file_worker(args: Tuple[str, str, str]) -> Tuple[bool, str, Optional[str]]:
    """
    处理单个STEP文件的工作函数（供多进程调用）

    Args:
        args: (step_file_path, category, target_dir) 元组

    Returns:
        Tuple[success, message, error]: (是否成功, 消息, 错误信息)
    """
    step_file_path, category, target_dir = args
    step_file = Path(step_file_path)
    target_dir = Path(target_dir)

    try:
        # 检查文件是否已存在
        target_file = target_dir / category / f"{step_file.stem}.bin"
        if target_file.exists():
            return True, f"文件已存在，跳过: {target_file}", None

        # 在每个进程中创建独立的实例
        graph_builder = GraphBuilder()

        # 构建异构图（from_step内部已包含分析逻辑）
        graph = graph_builder.from_step(str(step_file))
        graph.build_dgl_graph()
        # 保存图
        graph.save_graph(str(target_file))

        # 从图中获取统计信息用于元数据
        num_nodes = len(graph.nodes)
        num_edges = len(graph.edges)

        # 收集节点和边的类型信息
        node_types = set()
        edge_types = set()

        for node in graph.nodes.values():
            node_types.add(getattr(node, 'type', 'Unknown'))

        for edge in graph.edges:
            edge_types.add(getattr(edge, 'type', 'Unknown'))

        # 保存元数据
        metadata_file = target_dir / category / f"{step_file.stem}_metadata.json"
        metadata = {
            'source_file': str(step_file),
            'category': category,
            'processing_time': time.time(),
            'num_nodes': num_nodes,
            'num_edges': num_edges,
            'num_faces': sum(1 for node in graph.nodes.values() if hasattr(node, 'node_type') and node.node_type == 'face'),
            'node_types': list(node_types),
            'edge_types': list(edge_types)
        }

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return True, f"成功处理: {step_file.name} -> {target_file}", None

    except Exception as e:
        error_msg = f"处理文件失败 {step_file}: {str(e)}"
        return False, error_msg, str(e)


class BatchGraphGenerator:
    """批量异构图生成器"""

    def __init__(self, source_dir: str, target_dir: str, max_workers: int = 4):
        """
        初始化批量生成器

        Args:
            source_dir: 源数据目录
            target_dir: 目标存储目录
            max_workers: 最大并行工作进程数
        """
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.max_workers = max_workers

        # 注意：在多进程模式下，每个子进程会单独创建 GraphBuilder 实例
        # 这里不再初始化，避免序列化问题

        # 统计信息
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'skipped_files': 0,
            'start_time': None,
            'end_time': None,
            'categories': {},
            'errors': []
        }

        # 设置日志
        self.setup_logging()

    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('batch_graph_generation.log', encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger(__name__)

    def discover_step_files(self) -> Dict[str, List[Path]]:
        """
        发现所有STEP文件，按类别分组

        Returns:
            Dict[category, List[Path]]: 类别到文件路径列表的映射
        """
        self.logger.info(f"正在扫描源目录: {self.source_dir}")

        category_files = {}

        # 遍历源目录下的所有子目录（类别）
        for category_dir in self.source_dir.iterdir():
            if not category_dir.is_dir():
                continue

            category_name = category_dir.name
            step_dir = category_dir / "STEP"

            if not step_dir.exists():
                # self.logger.warning(f"类别 {category_name} 没有STEP子目录，跳过")
                # continue
                step_dir = category_dir

            # 查找所有STEP文件
            step_files = list(step_dir.glob("*.stp")) + list(step_dir.glob("*.step")) + list(step_dir.glob("*.STP")) + list(step_dir.glob("*.STEP"))


            if step_files:
                category_files[category_name] = step_files
                self.stats['categories'][category_name] = {
                    'total': len(step_files),
                    'processed': 0,
                    'failed': 0,
                    'skipped': 0
                }
                self.logger.info(f"发现类别 '{category_name}': {len(step_files)} 个文件")
            else:
                self.logger.warning(f"类别 '{category_name}' 的STEP目录为空")

        total_files = sum(len(files) for files in category_files.values())
        self.stats['total_files'] = total_files
        self.logger.info(f"总共发现 {total_files} 个STEP文件，分布在 {len(category_files)} 个类别中")

        return category_files

    def ensure_target_directories(self, categories: List[str]):
        """
        确保目标目录结构存在

        Args:
            categories: 类别列表
        """
        self.logger.info("正在创建目标目录结构...")

        for category in categories:
            category_dir = self.target_dir / category
            category_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"创建目录: {category_dir}")

    def process_category(self, category: str, files: List[Path]) -> Dict:
        """
        处理单个类别的所有文件

        Args:
            category: 类别名称
            files: 该类别的文件列表

        Returns:
            Dict: 处理结果统计
        """
        self.logger.info(f"开始处理类别: {category} ({len(files)} 个文件)")

        category_stats = {
            'total': len(files),
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }

        # 准备任务参数列表
        task_args = [
            (str(file_path), category, str(self.target_dir))
            for file_path in files
        ]

        # 使用进程池并行处理，添加进度条
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(process_single_file_worker, args): Path(args[0])
                for args in task_args
            }

            # 创建进度条
            with tqdm(total=len(files), desc=f"处理 {category}",
                     unit="文件", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:

                # 收集结果
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]

                    try:
                        success, message, error = future.result()

                        if success:
                            if "跳过" in message:
                                category_stats['skipped'] += 1
                                pbar.set_postfix({"状态": "跳过"})
                            else:
                                category_stats['processed'] += 1
                                pbar.set_postfix({"状态": "成功"})
                            self.logger.debug(message)
                        else:
                            category_stats['failed'] += 1
                            category_stats['errors'].append(error)
                            pbar.set_postfix({"状态": "失败"})
                            self.logger.error(message)

                    except Exception as e:
                        category_stats['failed'] += 1
                        error_msg = f"处理文件时发生异常 {file_path}: {str(e)}"
                        category_stats['errors'].append(error_msg)
                        pbar.set_postfix({"状态": "异常"})
                        self.logger.error(error_msg)

                    # 更新进度条
                    pbar.update(1)

        self.logger.info(f"类别 '{category}' 处理完成: 成功 {category_stats['processed']}, "
                        f"失败 {category_stats['failed']}, 跳过 {category_stats['skipped']}")

        return category_stats

    def run(self) -> Dict:
        """
        运行批量处理

        Returns:
            Dict: 处理结果统计
        """
        self.stats['start_time'] = time.time()
        self.logger.info("="*80)
        self.logger.info("开始批量生成异构图")
        self.logger.info(f"源目录: {self.source_dir}")
        self.logger.info(f"目标目录: {self.target_dir}")
        self.logger.info(f"最大并行进程数: {self.max_workers}")
        self.logger.info("="*80)

        try:
            # 发现所有STEP文件
            category_files = self.discover_step_files()

            if not category_files:
                self.logger.warning("没有发现任何STEP文件")
                return self.stats

            # 确保目标目录存在
            self.ensure_target_directories(list(category_files.keys()))

            # 创建总体进度条
            total_categories = len(category_files)
            with tqdm(total=total_categories, desc="批量处理进度",
                     unit="类别", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as category_pbar:

                # 处理每个类别
                for category, files in category_files.items():
                    category_stats = self.process_category(category, files)
                    self.stats['categories'][category] = category_stats

                    # 更新总体统计
                    self.stats['processed_files'] += category_stats['processed']
                    self.stats['failed_files'] += category_stats['failed']
                    self.stats['skipped_files'] += category_stats['skipped']

                    # 更新类别进度条
                    category_pbar.set_postfix({
                        "当前类别": category,
                        "成功": category_stats['processed'],
                        "失败": category_stats['failed']
                    })
                    category_pbar.update(1)

            self.stats['end_time'] = time.time()
            self.print_summary()

        except Exception as e:
            self.logger.error(f"批量处理过程中发生错误: {str(e)}")
            self.logger.debug(traceback.format_exc())
            self.stats['errors'].append(str(e))

        return self.stats

    def print_summary(self):
        """打印处理摘要"""
        duration = self.stats['end_time'] - self.stats['start_time']

        self.logger.info("="*80)
        self.logger.info("批量处理完成!")
        self.logger.info("="*80)
        self.logger.info(f"总处理时间: {duration:.2f} 秒")
        self.logger.info(f"总文件数: {self.stats['total_files']}")
        self.logger.info(f"成功处理: {self.stats['processed_files']}")
        self.logger.info(f"处理失败: {self.stats['failed_files']}")
        self.logger.info(f"跳过文件: {self.stats['skipped_files']}")

        if self.stats['total_files'] > 0:
            success_rate = (self.stats['processed_files'] / self.stats['total_files']) * 100
            self.logger.info(f"成功率: {success_rate:.1f}%")

        self.logger.info("\n各类别处理详情:")
        for category, stats in self.stats['categories'].items():
            total = stats['total']
            processed = stats['processed']
            failed = stats['failed']
            skipped = stats['skipped']
            self.logger.info(f"  {category:15s}: 总计 {total:3d}, 成功 {processed:3d}, "
                           f"失败 {failed:3d}, 跳过 {skipped:3d}")

        if self.stats['failed_files'] > 0:
            self.logger.warning(f"\n共有 {self.stats['failed_files']} 个文件处理失败，详见日志文件")

        self.logger.info("="*80)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='批量生成异构图 - 从CAD STEP文件生成异构图',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        示例用法:
        %(prog)s /home/km/model/CAD_Brep/CAD_1_15_Classes /data
        %(prog)s /path/to/source /path/to/target --workers 8
        %(prog)s /path/to/source /path/to/target --workers 1 --verbose
        """
    )

    parser.add_argument(
        'source_dir',
        help='源数据目录路径（包含分类子目录）'
    )

    parser.add_argument(
        'target_dir',
        help='目标存储目录路径'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='并行处理进程数 (默认: 4)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='启用详细日志输出'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 验证源目录
    if not os.path.exists(args.source_dir):
        print(f"错误: 源目录不存在: {args.source_dir}")
        sys.exit(1)

    # 创建批量生成器
    generator = BatchGraphGenerator(
        source_dir=args.source_dir,
        target_dir=args.target_dir,
        max_workers=args.workers
    )

    # 运行批量处理
    try:
        stats = generator.run()

        # 保存统计信息
        stats_file = Path(args.target_dir) / "batch_processing_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n统计信息已保存到: {stats_file}")

        # 根据处理结果设置退出码
        if stats['failed_files'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()