"""
BREP图数据集模块

BREPGraphDataset: 从STEP文件列表构建图数据集，可直接用于DataLoader
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Callable
from data_preprocess.batch_graph_generator import process_step_to_graph
import torch
from torch.utils.data import Dataset
from torch import FloatTensor
import dgl


class BREPGraphDataset(Dataset):
    """
    BREP图数据集 - 从 STEP 文件构建图
    
    使用多进程批量处理 STEP 文件
    
    用法:
        dataset = BREPGraphDataset(file_paths=["a.step", "b.stp", "c.STEP"])
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
            file_paths: 文件路径列表（支持 .step, .stp, .STEP）
            transform: 数据变换函数
            convert_float32: 是否转换为float32
            max_workers: STEP文件处理的最大并行进程数
            progress_callback: 进度回调函数，接收 (current, total, message) 参数
        """
        self.file_paths = [Path(p) for p in file_paths]
        self.transform = transform
        self.convert_float32 = convert_float32
        self.max_workers = max_workers
        self.progress_callback = progress_callback
        
        # 初始化批量处理函数
        self._batch_process_func = None
        self._init_batch_processor()
        
        # 数据存储
        self.data = []
        self.edge_types_dim = {}
        self.node_dim = {}
        
        # 加载所有数据
        self._load_all()
        self.edge_types_dim, self.node_dim = self._compute_dims()
    
    def _init_batch_processor(self):
        """初始化批量处理函数"""
        try:
            from data_preprocess.batch_graph_generator import process_step_files_batch
            self._batch_process_func = process_step_files_batch
            print("✓ 成功加载 STEP 批量处理模块")
        except ImportError as e:
            raise ImportError(f"无法导入 STEP 处理模块: {e}")
    
    def _load_all(self):
        """加载所有STEP文件（多进程批量处理）"""
        # 过滤有效的 STEP 文件
        step_files = []
        for fp in self.file_paths:
            suffix = fp.suffix.lower()
            if suffix in ['.step', '.stp']:
                step_files.append(fp)
            else:
                print(f"⚠ 不支持的文件格式，跳过: {fp}")
        
        if not step_files:
            print("⚠ 没有有效的STEP文件")
            if self.progress_callback:
                self.progress_callback(0, 0, "没有有效的STEP文件")
            return
        
        total_files = len(step_files)
        print(f"📂 批量处理 {total_files} 个STEP文件（{self.max_workers}进程）...")
        
        if self.progress_callback:
            self.progress_callback(0, total_files, f"开始处理 {total_files} 个文件...")
        
        # 调用多进程批量处理，传入进度回调
        results = self._batch_process_func(
            [str(fp) for fp in step_files],
            max_workers=self.max_workers,
            show_progress=False,  # 不使用tqdm，使用自定义回调
            progress_callback=self.progress_callback
        )
        
        # 处理结果
        processed_count = 0
        for idx, ((graph, metadata), file_path) in enumerate(zip(results, step_files)):
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
    加载单个STEP文件的便捷函数
    
    Args:
        file_path: STEP文件路径（.step, .stp, .STEP）
        
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
    
    if suffix not in ['.step', '.stp']:
        metadata["status"] = "error"
        metadata["error"] = f"不支持的文件格式: {suffix}，仅支持 .step, .stp, .STEP"
        return None, metadata
    
    try:
        graph, meta = process_step_to_graph(str(file_path))
        metadata.update(meta)
        return graph, metadata
    except Exception as e:
        metadata["status"] = "error"
        metadata["error"] = str(e)
        return None, metadata
