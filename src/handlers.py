"""
文件处理模块

包含单文件处理和批量处理的逻辑
"""

import time
import traceback
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from torch.utils.data import DataLoader

logger = logging.getLogger(__name__)

from config import DeployConfig, DEFAULT_CONFIG
from .brep_and_graph import load_single_graph, BREPGraphDataset
from .common import data_collate
from ui.components import (
    create_empty_prediction_html,
    create_empty_confidence_html,
    create_empty_probs_html,
    format_prediction_result,
    format_batch_results,
    create_progress_html,
    create_empty_progress_html
)


class FileHandler:
    """文件处理器"""
    
    def __init__(
        self, 
        config: DeployConfig,
        classifier=None,
        is_ready: bool = False
    ):
        """
        初始化处理器
        
        Args:
            config: 部署配置
            classifier: 分类器实例
            is_ready: 分类器是否就绪
        """
        self.config = config
        self.classifier = classifier
        self.is_ready = is_ready
    
    def update_classifier(self, classifier, is_ready: bool):
        """更新分类器状态"""
        self.classifier = classifier
        self.is_ready = is_ready
    
    def process_single_file(
        self, 
        file_obj
    ) -> Tuple[str, str, str, str]:
        """
        处理单个文件
        
        Args:
            file_obj: Gradio文件对象
            
        Returns:
            (class_html, confidence_html, probs_html, viewer_html)
        """
        from ui.viewer3d import create_empty_step_viewer
        
        if file_obj is None:
            return (
                create_empty_prediction_html(),
                create_empty_confidence_html(),
                create_empty_probs_html(),
                create_empty_step_viewer()
            )
        
        start_time = time.time()
        
        try:
            file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
            print(f"📂 处理文件: {file_path}")
            
            # 步骤1: 加载/构建图
            graph, metadata = load_single_graph(file_path)
            
            if graph is None:
                error_msg = metadata.get("error", "未知错误")
                raise RuntimeError(f"图构建失败: {error_msg}")
            
            # 步骤2: 分类预测
            if self.classifier is not None and self.is_ready:
                result = self.classifier.predict(graph=graph)
                
                class_html, confidence_html, probs_html = format_prediction_result(
                    predicted_class=result["predicted_class"],
                    confidence=result["confidence"],
                    probabilities=result["probabilities"],
                    inference_time=result["inference_time"]
                )
            else:
                # 演示模式
                demo_result = self._generate_demo_prediction()
                class_html, confidence_html, probs_html = format_prediction_result(
                    **demo_result
                )
            
            # 生成3D查看器
            from ui.viewer3d import create_step_viewer_html
            viewer_html = create_step_viewer_html(file_path)
            
            total_time = time.time() - start_time
            print(f"✓ 处理完成，耗时: {total_time*1000:.1f}ms")
            
            return class_html, confidence_html, probs_html, viewer_html
            
        except Exception as e:
            error_msg = str(e)
            traceback.print_exc()
            
            error_html = f"""
            <div style="text-align: center; padding: 2rem; color: #ff4d4f;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin: 0 auto;">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="15" y1="9" x2="9" y2="15"/>
                    <line x1="9" y1="9" x2="15" y2="15"/>
                </svg>
                <p style="margin-top: 1rem;">处理失败</p>
                <p style="color: #8b949e; font-size: 0.9rem; margin-top: 0.5rem;">{error_msg}</p>
            </div>
            """
            
            from ui.viewer3d import create_empty_step_viewer
            return (
                error_html,
                create_empty_confidence_html(),
                create_empty_probs_html(),
                create_empty_step_viewer()
            )
    
    def process_batch_files(
        self, 
        file_objs: List
    ):
        """
        批量处理文件（使用多进程加载 + DataLoader批量推理）
        使用生成器逐步更新进度
        
        Args:
            file_objs: Gradio文件对象列表
            
        Yields:
            (进度HTML, 表格数据) - 逐步更新进度
        """
        if not file_objs:
            yield create_empty_progress_html(), []
            return
        
        # 从配置读取批次大小
        batch_size = self.config.model.batch_size
        
        # 提取文件路径
        file_paths = [
            file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
            for file_obj in file_objs
        ]
        
        total_files = len(file_paths)
        start_time = time.time()
        
        # 阶段1: 图数据构建
        # 更新进度：开始加载
        yield create_progress_html(
            stage1_progress=0,
            stage1_text=f"开始构建图数据，共 {total_files} 个文件...",
            stage2_progress=0,
            stage2_text="等待图数据构建完成..."
        ), []
        
        # 使用真实的进度回调
        progress_queue = []
        current_progress = [0]  # 使用列表以便在回调中修改
        
        def progress_callback(current: int, total: int, message: str):
            """进度回调函数"""
            if total > 0:
                progress_pct = int((current / total) * 100)
                current_progress[0] = progress_pct
                progress_queue.append((progress_pct, message))
        
        # 使用 BREPGraphDataset 多进程批量加载图
        try:
            # 在后台线程中加载，主线程监控进度队列
            dataset = None
            load_error = None
            
            def load_in_background():
                nonlocal dataset, load_error
                try:
                    dataset = BREPGraphDataset(
                        file_paths=file_paths, 
                        max_workers=4,
                        progress_callback=progress_callback
                    )
                except Exception as e:
                    load_error = e
            
            import threading
            load_thread = threading.Thread(target=load_in_background)
            load_thread.start()
            
            # 监控进度队列并更新UI
            while load_thread.is_alive():
                # 检查进度队列
                while progress_queue:
                    progress_pct, message = progress_queue.pop(0)
                    yield create_progress_html(
                        stage1_progress=progress_pct,
                        stage1_text=message,
                        stage2_progress=0,
                        stage2_text="等待图数据构建完成..."
                    ), []
                
                # 如果没有新进度，也定期更新当前进度
                import time as time_module
                time_module.sleep(0.3)  # 每0.3秒检查一次
            
            # 处理剩余的进度更新
            while progress_queue:
                progress_pct, message = progress_queue.pop(0)
                yield create_progress_html(
                    stage1_progress=progress_pct,
                    stage1_text=message,
                    stage2_progress=0,
                    stage2_text="等待图数据构建完成..."
                ), []
            
            load_thread.join()
            
            if load_error:
                raise load_error
            
            # 更新进度：加载完成
            loaded_count = len(dataset)
            stage1_text = f"完成！成功加载 {loaded_count}/{total_files} 个图"
            yield create_progress_html(
                stage1_progress=100,
                stage1_text=stage1_text,
                stage2_progress=0,
                stage2_text="准备开始推理..."
            ), []
            
        except Exception as e:
            print(f"⚠ 批量加载失败: {e}")
            error_html = create_progress_html(
                stage1_progress=0,
                stage1_text=f"加载失败: {str(e)}",
                stage2_progress=0,
                stage2_text="未开始"
            )
            yield error_html, []
            return
        
        if len(dataset) == 0:
            print("⚠ 没有成功加载的图")
            error_html = create_progress_html(
                stage1_progress=0,
                stage1_text="没有成功加载的图",
                stage2_progress=0,
                stage2_text="未开始"
            )
            yield error_html, []
            return
        
        load_time = time.time() - start_time
        print(f"✓ 图加载完成，耗时: {load_time:.2f}s，共 {len(dataset)} 个图")
        
        # 创建 DataLoader
        dataloader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=False,
            collate_fn=data_collate
        )
        
        # 阶段2: 模型推理处理
        total_batches = len(dataloader)
        results = []
        processed_count = 0
        
        for batch_idx, batch in enumerate(dataloader):
            batched_graph = batch["graph"]
            file_names_batch = batch.get("file_name", [])
            
            # 确保 file_names_batch 是列表
            if not isinstance(file_names_batch, list):
                file_names_batch = [file_names_batch]
            
            # 更新阶段2进度
            stage2_progress = (batch_idx + 1) / total_batches * 100 if total_batches > 0 else 0
            processed_count += len(file_names_batch)
            stage2_text = f"正在处理批次 {batch_idx + 1}/{total_batches} (已处理 {processed_count} 个文件)"
            
            # 逐步更新进度
            yield create_progress_html(
                stage1_progress=100,
                stage1_text=stage1_text,
                stage2_progress=stage2_progress,
                stage2_text=stage2_text
            ), format_batch_results(results) if results else []
            
            try:
                if self.classifier is not None and self.is_ready:
                    # 批量推理
                    batch_results = self.classifier.predict_batch(batched_graph)
                    
                    for i, result in enumerate(batch_results):
                        # 直接使用 file_name（样本名）
                        filename = file_names_batch[i] if i < len(file_names_batch) else f"unknown_{i}"
                        result["filename"] = filename
                        result["status"] = "success"
                        results.append(result)
                else:
                    # 演示模式
                    for i, file_name in enumerate(file_names_batch):
                        demo_result = self._generate_demo_prediction()
                        filename = file_name if file_name else f"unknown_{i}"
                        demo_result["filename"] = filename
                        demo_result["status"] = "success"
                        results.append(demo_result)
                        
            except Exception as e:
                print(f"⚠ 批次推理失败: {e}")
                for i, file_name in enumerate(file_names_batch):
                    filename = file_name if file_name else f"unknown_{i}"
                    results.append({
                        "filename": filename,
                        "predicted_class": "-",
                        "confidence": 0,
                        "status": "error",
                        "inference_time": 0
                    })
        
        total_time = time.time() - start_time
        print(f"✓ 批量处理完成，总耗时: {total_time:.2f}s")
        
        # 最终进度
        final_html = create_progress_html(
            stage1_progress=100,
            stage1_text=stage1_text,
            stage2_progress=100,
            stage2_text=f"完成！共处理 {len(results)} 个文件，总耗时 {total_time:.1f}s"
        )
        
        yield final_html, format_batch_results(results)
    
    def _generate_demo_prediction(self) -> Dict:
        """生成演示预测结果"""
        import random
        
        all_classes = self.config.class_mapping.get_all_class_names()
        if not all_classes:
            all_classes = ["整体式-螺窝", "铸造式-车削", "环形式-无轴"]
        
        predicted_class = random.choice(all_classes)
        confidence = random.uniform(0.7, 0.98)
        
        probabilities = {}
        remaining = 1.0 - confidence
        
        for cls in all_classes:
            if cls == predicted_class:
                probabilities[cls] = confidence
            else:
                prob = random.uniform(0, remaining / len(all_classes))
                probabilities[cls] = prob
                remaining -= prob
        
        return {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "probabilities": probabilities,
            "inference_time": 0.05
        }

