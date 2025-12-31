"""
BREP图数据集模块

BREPGraphDataset: 从XML文件列表构建图数据集，可直接用于DataLoader
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Callable
from data_preprocess import GraphBuilder
import torch
from torch.utils.data import Dataset
from torch import FloatTensor
import dgl
from concurrent.futures import ProcessPoolExecutor, as_completed


def process_xml_to_graph(xml_path: str) -> Tuple[Optional[dgl.DGLGraph], Dict]:
    """
    处理单个 XML 文件，返回 DGL 图和元数据
    
    Args:
        xml_path: XML 文件路径
        
    Returns:
        (dgl_graph, metadata): DGL 图和元数据字典
    """
    xml_file = Path(xml_path)
    
    if not xml_file.exists():
        return None, {
            "source_file": str(xml_path),
            "file_name": xml_file.name,
            "status": "error",
            "error": f"文件不存在: {xml_path}"
        }
    
    try:
        # 读取 XML 文件内容
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # 使用 GraphBuilder 从 XML 构建图
        graph_builder = GraphBuilder()
        hetero_graph = graph_builder.from_xml(xml_content)
        dgl_graph = hetero_graph.build_dgl_graph()
        
        metadata = {
            "source_file": str(xml_file),
            "file_name": xml_file.name,
            "status": "success",
            "num_nodes": sum(dgl_graph.num_nodes(ntype) for ntype in dgl_graph.ntypes),
            "num_edges": sum(dgl_graph.num_edges(etype) for etype in dgl_graph.canonical_etypes),
            "node_types": list(dgl_graph.ntypes),
            "edge_types": [et[1] for et in dgl_graph.canonical_etypes],
        }
        
        return dgl_graph, metadata
        
    except Exception as e:
        return None, {
            "source_file": str(xml_path),
            "file_name": xml_file.name,
            "status": "error",
            "error": str(e)
        }


def process_xml_files_batch(
    file_paths: List[str], 
    max_workers: int = 4,
    show_progress: bool = True,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[Tuple[Optional[dgl.DGLGraph], Dict]]:
    """
    批量处理 XML 文件列表
    
    Args:
        file_paths: XML 文件路径列表
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
        result = process_xml_to_graph(file_paths[0])
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
            executor.submit(process_xml_to_graph, path): idx 
            for idx, path in enumerate(file_paths)
        }
        
        # 创建迭代器
        futures = as_completed(future_to_idx)
        if show_progress and not progress_callback:
            try:
                from tqdm import tqdm
                futures = tqdm(futures, total=len(file_paths), desc="处理XML文件")
            except ImportError:
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


class BREPGraphDataset(Dataset):
    """
    BREP图数据集 - 从 XML 文件构建图
    
    使用多进程批量处理 XML 文件
    
    用法:
        dataset = BREPGraphDataset(file_paths=["a.xml", "b.xml", "c.xml"])
        dataloader = DataLoader(dataset, batch_size=4, collate_fn=dataset.collate_fn)
    """
    
    def __init__(
        self,
        file_paths: List[Union[str, Path]],
        transform=None,
        convert_float32: bool = True,
        max_workers: int = 4,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ):
        """
        初始化数据集
        
        Args:
            file_paths: 文件路径列表（支持 .xml）
            transform: 数据变换函数
            convert_float32: 是否转换为float32
            max_workers: XML文件处理的最大并行进程数
            progress_callback: 进度回调函数，接收 (current, total, message) 参数
        """
        self.file_paths = [Path(p) for p in file_paths]
        self.transform = transform
        self.convert_float32 = convert_float32
        self.max_workers = max_workers
        self.progress_callback = progress_callback
        
        # 数据存储
        self.data = []
        self.edge_types_dim = {}
        self.node_dim = {}
        
        # 加载所有数据
        self._load_all()
        self.edge_types_dim, self.node_dim = self._compute_dims()
    
    def _load_all(self):
        """加载所有XML文件（多进程批量处理）"""
        # 过滤有效的 XML 文件
        xml_files = []
        for fp in self.file_paths:
            suffix = fp.suffix.lower()
            if suffix == '.xml':
                xml_files.append(fp)
            else:
                print(f"⚠ 不支持的文件格式，跳过: {fp}")
        
        if not xml_files:
            print("⚠ 没有有效的XML文件")
            if self.progress_callback:
                self.progress_callback(0, 0, "没有有效的XML文件")
            return
        
        total_files = len(xml_files)
        print(f"📂 批量处理 {total_files} 个XML文件（{self.max_workers}进程）...")
        
        if self.progress_callback:
            self.progress_callback(0, total_files, f"开始处理 {total_files} 个文件...")
        
        # 调用多进程批量处理，传入进度回调
        results = process_xml_files_batch(
            [str(fp) for fp in xml_files],
            max_workers=self.max_workers,
            show_progress=False,  # 不使用tqdm，使用自定义回调
            progress_callback=self.progress_callback
        )
        
        # 处理结果
        processed_count = 0
        for idx, ((graph, metadata), file_path) in enumerate(zip(results, xml_files)):
            if graph is None:
                if self.progress_callback:
                    self.progress_callback(idx + 1, total_files, f"跳过无效文件: {file_path.name}")
                continue
            
            if self._is_empty_graph(graph):
                if self.progress_callback:
                    self.progress_callback(idx + 1, total_files, f"跳过空图: {file_path.name}")
                continue
            
            if self.convert_float32:
                graph = self._to_float32(graph)
            
            self.data.append({
                "graph": graph,
                "file_name": file_path.name,  # 保存完整文件名（含扩展名）
                "metadata": metadata
            })
            processed_count += 1
            
            if self.progress_callback:
                self.progress_callback(idx + 1, total_files, f"已处理 {processed_count}/{total_files} 个文件")
        
        print(f"✓ 成功加载 {len(self.data)}/{total_files} 个图")
    
    def _is_empty_graph(self, graph: dgl.DGLGraph) -> bool:
        """检查是否为空图"""
        if isinstance(graph, dgl.DGLHeteroGraph):
            return sum(graph.num_edges(etype) for etype in graph.canonical_etypes) == 0
        return graph.num_edges() == 0
    
    def _to_float32(self, graph: dgl.DGLGraph) -> dgl.DGLGraph:
        """转换为float32"""
        for ntype in graph.ntypes:
            if 'x' in graph.nodes[ntype].data:
                graph.nodes[ntype].data['x'] = graph.nodes[ntype].data['x'].type(FloatTensor)
        for etype in graph.canonical_etypes:
            if 'x' in graph.edges[etype].data:
                graph.edges[etype].data['x'] = graph.edges[etype].data['x'].type(FloatTensor)
        return graph
    
    def _compute_dims(self) -> Tuple[Dict, Dict]:
        """计算边类型和节点类型的特征维度"""
        edge_types_dim = {}
        node_dim = {}
        
        for sample in self.data:
            graph = sample["graph"]
            
            for etype in graph.canonical_etypes:
                if etype not in edge_types_dim:
                    stype, _, _ = etype
                    edge_feat = graph.edges[etype].data.get('x')
                    node_feat = graph.nodes[stype].data.get('x')
                    if edge_feat is not None and node_feat is not None:
                        edge_types_dim[etype] = (edge_feat.shape[1], node_feat.shape[1])
            
            for ntype in graph.ntypes:
                if ntype not in node_dim:
                    feat = graph.nodes[ntype].data.get('x')
                    if feat is not None:
                        node_dim[ntype] = feat.shape[1]
        
        return edge_types_dim, node_dim
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict:
        sample = self.data[idx].copy()
        if self.transform and sample.get("graph") is not None:
            sample = self.transform(sample)
        return sample
    
    def get_graphs(self) -> List[dgl.DGLGraph]:
        """获取所有图对象"""
        return [sample["graph"] for sample in self.data]
    
    @staticmethod
    def get_graph_info(graph: dgl.DGLGraph) -> Dict:
        """获取图的详细信息"""
        info = {
            "num_node_types": len(graph.ntypes),
            "num_edge_types": len(graph.canonical_etypes),
            "node_types": {},
            "edge_types": {},
            "total_nodes": 0,
            "total_edges": 0,
        }
        
        for ntype in graph.ntypes:
            num_nodes = graph.num_nodes(ntype)
            feat = graph.nodes[ntype].data.get('x')
            info["node_types"][ntype] = {
                "count": num_nodes,
                "feature_dim": feat.shape[-1] if feat is not None and num_nodes > 0 else 0
            }
            info["total_nodes"] += num_nodes
        
        for etype in graph.canonical_etypes:
            num_edges = graph.num_edges(etype)
            feat = graph.edges[etype].data.get('x')
            info["edge_types"][str(etype)] = {
                "count": num_edges,
                "feature_dim": feat.shape[-1] if feat is not None and num_edges > 0 else 0
            }
            info["total_edges"] += num_edges
        
        return info


def load_single_graph(file_path: Union[str, Path]) -> Tuple[Optional[dgl.DGLGraph], Dict]:
    """
    加载单个XML文件的便捷函数
    
    Args:
        file_path: XML文件路径（.xml）
        
    Returns:
        (graph, metadata): DGL图和元数据
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()
    
    metadata = {
        "source_file": str(file_path),
        "file_name": file_path.name,
        "status": "processing"
    }
    
    if not file_path.exists():
        metadata["status"] = "error"
        metadata["error"] = f"文件不存在: {file_path}"
        return None, metadata
    
    if suffix != '.xml':
        metadata["status"] = "error"
        metadata["error"] = f"不支持的文件格式: {suffix}，仅支持 .xml"
        return None, metadata
    
    try:
        graph, meta = process_xml_to_graph(str(file_path))
        metadata.update(meta)
        return graph, metadata
    except Exception as e:
        metadata["status"] = "error"
        metadata["error"] = str(e)
        return None, metadata
