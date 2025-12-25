"""
UI组件模块

提供可复用的Gradio UI组件
"""

import gradio as gr
from typing import Dict, List, Optional, Tuple, Any
import gradio as gr
import json


def create_file_upload_component() -> gr.File:
    """
    创建文件上传组件
    
    Returns:
        Gradio File组件
    """
    return gr.File(
        label="📁 上传3D模型文件",
        file_types=[".step", ".stp", ".STEP", ".STP", ".bin"],
        file_count="single",
        elem_classes=["upload-area"]
    )


def create_batch_upload_component() -> gr.File:
    """
    创建批量上传组件
    
    Returns:
        Gradio File组件（支持多文件）
    """
    return gr.File(
        label="📁 批量上传3D模型文件",
        file_types=[".step", ".stp", ".STEP", ".STP", ".bin"],
        file_count="multiple",
        elem_classes=["upload-area"]
    )


def create_result_display() -> Tuple[gr.HTML, gr.HTML, gr.HTML]:
    """
    创建结果展示组件
    
    Returns:
        (predicted_class, confidence, probabilities) 组件元组
    """
    predicted_class = gr.HTML(
        value=create_empty_prediction_html(),
        label="预测类别",
        elem_classes=["result-card"]
    )
    
    confidence = gr.HTML(
        value=create_empty_confidence_html(),
        label="置信度"
    )
    
    probabilities = gr.HTML(
        value=create_empty_probs_html(),
        label="概率分布"
    )
    
    return predicted_class, confidence, probabilities




# 3D查看器功能已移除


def create_batch_processor() -> Tuple[gr.HTML, gr.Dataframe]:
    """
    创建批量处理结果表格和进度显示
    
    Returns:
        (进度显示组件, 结果表格组件)
    """
    progress_display = gr.HTML(
        value=create_empty_progress_html(),
        label="📊 处理进度",
        visible=True
    )
    
    batch_table = gr.Dataframe(
        headers=["文件名", "预测类别", "置信度", "状态", "处理时间"],
        datatype=["str", "str", "number", "str", "str"],
        label="📊 批量处理结果",
        interactive=False,
        elem_classes=["batch-table"],
        wrap=True,  # 允许文本换行
        max_height=600,  # 设置最大高度
        overflow_row_behaviour="paginate",  # 超出时使用分页
    )
    
    return progress_display, batch_table


def create_empty_progress_html() -> str:
    """创建空的进度显示HTML"""
    return """
    <div class="progress-container" style="padding: 1rem; background: linear-gradient(135deg, rgba(41, 53, 72, 0.7) 0%, rgba(30, 41, 59, 0.7) 100%); border-radius: 8px; margin-bottom: 1rem; border: 1px solid #475569;">
        <div style="margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: #f1f5f9; font-weight: 600;">图数据构建</span>
                <span style="color: #cbd5e1; font-size: 0.9rem;">等待开始...</span>
            </div>
            <div style="width: 100%; height: 8px; background: #334155; border-radius: 4px; overflow: hidden;">
                <div class="progress-bar-stage1" style="width: 0%; height: 100%; background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%); transition: width 0.3s ease;"></div>
            </div>
        </div>
        <div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: #f1f5f9; font-weight: 600;">模型推理</span>
                <span style="color: #cbd5e1; font-size: 0.9rem;">等待开始...</span>
            </div>
            <div style="width: 100%; height: 8px; background: #334155; border-radius: 4px; overflow: hidden;">
                <div class="progress-bar-stage2" style="width: 0%; height: 100%; background: linear-gradient(90deg, #10b981 0%, #34d399 100%); transition: width 0.3s ease;"></div>
            </div>
        </div>
    </div>
    """


def create_progress_html(stage1_progress: float, stage1_text: str, stage2_progress: float, stage2_text: str) -> str:
    """
    创建进度显示HTML
    
    Args:
        stage1_progress: 阶段1进度 (0-100)
        stage1_text: 阶段1状态文本
        stage2_progress: 阶段2进度 (0-100)
        stage2_text: 阶段2状态文本
        
    Returns:
        HTML字符串
    """
    stage1_pct = min(100, max(0, stage1_progress))
    stage2_pct = min(100, max(0, stage2_progress))
    
    stage1_color = "#3b82f6" if stage1_pct < 100 else "#10b981"
    stage2_color = "#10b981"
    
    return f"""
    <div class="progress-container" style="padding: 1rem; background: linear-gradient(135deg, rgba(41, 53, 72, 0.7) 0%, rgba(30, 41, 59, 0.7) 100%); border-radius: 8px; margin-bottom: 1rem; border: 1px solid #475569;">
        <div style="margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: #f1f5f9; font-weight: 600;">图数据构建</span>
                <span style="color: #cbd5e1; font-size: 0.9rem;">{stage1_text}</span>
            </div>
            <div style="width: 100%; height: 8px; background: #334155; border-radius: 4px; overflow: hidden;">
                <div class="progress-bar-stage1" style="width: {stage1_pct}%; height: 100%; background: linear-gradient(90deg, {stage1_color} 0%, #60a5fa 100%); transition: width 0.3s ease;"></div>
            </div>
        </div>
        <div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: #f1f5f9; font-weight: 600;">模型推理</span>
                <span style="color: #cbd5e1; font-size: 0.9rem;">{stage2_text}</span>
            </div>
            <div style="width: 100%; height: 8px; background: #334155; border-radius: 4px; overflow: hidden;">
                <div class="progress-bar-stage2" style="width: {stage2_pct}%; height: 100%; background: linear-gradient(90deg, {stage2_color} 0%, #34d399 100%); transition: width 0.3s ease;"></div>
            </div>
        </div>
    </div>
    """


def create_graph_info_display() -> gr.HTML:
    """
    创建图结构信息展示组件
    
    Returns:
        Gradio HTML组件
    """
    return gr.HTML(
        value=create_empty_graph_info(),
        label="📋 图结构信息"
    )


def create_empty_prediction_html() -> str:
    """创建空的预测结果HTML"""
    return """
    <div style="background: linear-gradient(135deg, rgba(41, 53, 72, 0.7) 0%, rgba(30, 41, 59, 0.7) 100%); 
                border: 2px solid #475569; 
                border-radius: 12px; 
                padding: 2rem 1.5rem; 
                text-align: center; 
                min-height: 280px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);">
        <div style="width: 64px; height: 64px; margin: 0 auto 1rem auto; 
                    background: #1e293b; 
                    border-radius: 50%; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center;
                    border: 2px solid #475569;">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
        </div>
        <p style="color: #cbd5e1; font-size: 0.95rem; margin: 0;">等待上传文件</p>
    </div>
    """


def create_empty_confidence_html() -> str:
    """创建空的置信度HTML"""
    return """
    <div style="background: linear-gradient(135deg, rgba(41, 53, 72, 0.7) 0%, rgba(30, 41, 59, 0.7) 100%); 
                border: 2px solid #475569; 
                border-radius: 12px; 
                padding: 1.5rem; 
                min-height: 280px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);">
        <h4 style="color: #f1f5f9; margin: 0 0 1.5rem 0; font-size: 1rem; font-weight: 600; text-align: center;">
            置信度分析
        </h4>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
            <span style="color: #f1f5f9; font-weight: 600; font-size: 0.95rem;">置信度</span>
            <span style="color: #cbd5e1; font-family: monospace; font-size: 0.9rem;">--%</span>
        </div>
        <div style="width: 100%; 
                    height: 10px; 
                    background: #334155; 
                    border-radius: 5px; 
                    overflow: hidden;">
            <div style="width: 0%; 
                        height: 100%; 
                        background: #475569; 
                        transition: width 0.3s ease;"></div>
        </div>
        <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 1rem; text-align: center;">
            等待模型预测结果
        </p>
    </div>
    """


def create_empty_probs_html() -> str:
    """创建空的概率分布HTML"""
    return """
    <div style="background: linear-gradient(135deg, rgba(41, 53, 72, 0.7) 0%, rgba(30, 41, 59, 0.7) 100%); 
                border: 2px solid #475569; 
                border-radius: 12px; 
                padding: 1.5rem;
                min-height: 280px;
                display: flex;
                flex-direction: column;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);">
        <h4 style="color: #f1f5f9; margin: 0 0 1rem 0; font-size: 1rem; font-weight: 600;">
            📊 类别概率分布
        </h4>
        <div style="flex: 1; display: flex; align-items: center; justify-content: center; text-align: center; color: #cbd5e1; font-size: 0.9rem;">
            <div>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="2" style="margin: 0 auto 0.5rem auto; opacity: 0.5;">
                    <line x1="18" y1="20" x2="18" y2="10"/>
                    <line x1="12" y1="20" x2="12" y2="4"/>
                    <line x1="6" y1="20" x2="6" y2="14"/>
                </svg>
                <p>等待分类结果</p>
            </div>
        </div>
    </div>
    """


def create_empty_graph_info() -> str:
    """创建空的图信息HTML"""
    return """
    <div class="graph-info-panel" style="padding: 1rem; color: #cbd5e1; text-align: center;">
        <p>等待图提取...</p>
    </div>
    """


def format_prediction_result(
    predicted_class: str,
    confidence: float,
    probabilities: Dict[str, float],
    inference_time: float = 0.0
) -> Tuple[str, str, str]:
    """
    格式化预测结果为HTML
    
    Args:
        predicted_class: 预测类别
        confidence: 置信度
        probabilities: 概率分布
        inference_time: 推理时间（秒）
        
    Returns:
        (class_html, confidence_html, probs_html)
    """
    # 预测类别HTML - 柔和现代风格
    class_html = f"""
    <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(16, 185, 129, 0.12) 100%); 
                border: 2px solid #3b82f6; 
                border-radius: 12px; 
                padding: 2rem 1.5rem; 
                text-align: center; 
                min-height: 280px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                box-shadow: 0 6px 20px rgba(59, 130, 246, 0.25);">
        <div style="font-size: 0.75rem; 
                    color: #cbd5e1; 
                    text-transform: uppercase; 
                    letter-spacing: 1.5px; 
                    margin-bottom: 0.8rem;
                    font-weight: 500;">
            预测类别
        </div>
        <div style="font-size: 1.6rem; 
                    font-weight: 700; 
                    color: #60a5fa;
                    margin-bottom: 0.8rem;
                    text-shadow: 0 2px 8px rgba(96, 165, 250, 0.4);
                    line-height: 1.4;">
            {predicted_class}
        </div>
        <div style="display: inline-block;
                    background: rgba(30, 41, 59, 0.8); 
                    color: #cbd5e1; 
                    font-size: 0.85rem;
                    font-family: monospace;
                    padding: 0.4rem 1rem;
                    border-radius: 6px;
                    border: 1px solid #475569;
                    margin: 0 auto;">
            ⚡ {inference_time*1000:.1f}ms
        </div>
    </div>
    """
    
    # 置信度HTML - 现代配色方案
    confidence_pct = confidence * 100
    if confidence > 0.8:
        confidence_color = "#10b981"
        confidence_emoji = "✓"
        confidence_label = "高"
    elif confidence > 0.5:
        confidence_color = "#60a5fa"
        confidence_emoji = "○"
        confidence_label = "中"
    else:
        confidence_color = "#f59e0b"
        confidence_emoji = "!"
        confidence_label = "低"
    
    confidence_html = f"""
    <div style="background: linear-gradient(135deg, rgba(41, 53, 72, 0.7) 0%, rgba(30, 41, 59, 0.7) 100%); 
                border: 2px solid #475569; 
                border-radius: 12px; 
                padding: 1.5rem; 
                min-height: 280px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);">
        <h4 style="color: #f1f5f9; margin: 0 0 1.5rem 0; font-size: 1rem; font-weight: 600; text-align: center;">
            置信度分析
        </h4>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
            <span style="color: #f1f5f9; font-weight: 600; font-size: 0.95rem;">置信度</span>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="color: {confidence_color}; 
                            font-family: monospace; 
                            font-weight: 700;
                            font-size: 1.1rem;">
                    {confidence_pct:.1f}%
                </span>
                <span style="background: {confidence_color}; 
                            color: #1e293b; 
                            padding: 0.2rem 0.6rem; 
                            border-radius: 4px; 
                            font-size: 0.75rem;
                            font-weight: 600;">
                    {confidence_label}
                </span>
            </div>
        </div>
        <div style="width: 100%; 
                    height: 10px; 
                    background: #334155; 
                    border-radius: 5px; 
                    overflow: hidden;">
            <div style="width: {confidence_pct}%; 
                        height: 100%; 
                        background: {confidence_color}; 
                        transition: width 0.5s ease;
                        box-shadow: 0 0 8px {confidence_color};"></div>
        </div>
    </div>
    """
    
    # 概率分布HTML - 现代渐变配色
    sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    
    # 现代配色：蓝色系+绿色强调
    colors = ["#60a5fa", "#10b981", "#8b5cf6", "#f59e0b", "#6b7280"]
    
    probs_items = ""
    for idx, (class_name, prob) in enumerate(sorted_probs[:5]):  # 只显示前5个
        prob_pct = prob * 100
        is_top = idx == 0
        color = colors[min(idx, len(colors)-1)]
        
        probs_items += f"""
        <div style="margin-bottom: {'1rem' if idx < 4 else '0'};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <span style="background: {color}; 
                                color: #1e293b; 
                                min-width: 24px; 
                                height: 24px; 
                                border-radius: 4px; 
                                display: flex; 
                                align-items: center; 
                                justify-content: center; 
                                font-size: 0.75rem;
                                font-weight: 600;
                                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);">
                        {idx + 1}
                    </span>
                    <span style="color: {'#f8fafc' if is_top else '#f1f5f9'}; 
                                font-size: 0.9rem;
                                font-weight: {'600' if is_top else '400'};">
                        {class_name}
                    </span>
                </div>
                <span style="color: {color}; 
                            font-family: monospace; 
                            font-size: 0.85rem;
                            font-weight: 600;">
                    {prob_pct:.1f}%
                </span>
            </div>
            <div style="width: 100%; 
                        height: {'10px' if is_top else '8px'}; 
                        background: #334155; 
                        border-radius: 4px; 
                        overflow: hidden;">
                <div style="width: {prob_pct}%; 
                            height: 100%; 
                            background: {color}; 
                            transition: width 0.5s ease;
                            box-shadow: 0 0 6px {color};"></div>
            </div>
        </div>
        """
    
    probs_html = f"""
    <div style="background: linear-gradient(135deg, rgba(41, 53, 72, 0.7) 0%, rgba(30, 41, 59, 0.7) 100%); 
                border: 2px solid #475569; 
                border-radius: 12px; 
                padding: 1.5rem;
                min-height: 280px;
                display: flex;
                flex-direction: column;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);">
        <h4 style="color: #f1f5f9; margin: 0 0 1rem 0; font-size: 1rem; font-weight: 600;">
            📊 类别概率分布 <span style="color: #cbd5e1; font-size: 0.85rem; font-weight: 400;">(Top {min(5, len(sorted_probs))})</span>
        </h4>
        <div style="flex: 1; display: flex; flex-direction: column; justify-content: center;">
            {probs_items}
        </div>
    </div>
    """
    
    return class_html, confidence_html, probs_html


def format_graph_info(graph_info: Dict) -> str:
    """
    格式化图信息为HTML
    
    Args:
        graph_info: 图信息字典
        
    Returns:
        HTML字符串
    """
    node_types_str = ", ".join(graph_info.get("node_types", []))
    edge_types_str = ", ".join([str(et) for et in graph_info.get("edge_types", [])])
    
    return f"""
    <div class="graph-info-panel">
        <h4 style="color: #f1f5f9; margin-bottom: 1rem;">📋 图结构信息</h4>
        
        <div class="graph-info-item">
            <span class="graph-info-label">总节点数</span>
            <span class="graph-info-value">{graph_info.get('total_nodes', 0)}</span>
        </div>
        
        <div class="graph-info-item">
            <span class="graph-info-label">总边数</span>
            <span class="graph-info-value">{graph_info.get('total_edges', 0)}</span>
        </div>
        
        <div class="graph-info-item">
            <span class="graph-info-label">节点类型数</span>
            <span class="graph-info-value">{graph_info.get('num_node_types', 0)}</span>
        </div>
        
        <div class="graph-info-item">
            <span class="graph-info-label">边类型数</span>
            <span class="graph-info-value">{graph_info.get('num_edge_types', 0)}</span>
        </div>
        
        <div style="margin-top: 1rem;">
            <p style="color: #cbd5e1; font-size: 0.85rem; margin-bottom: 0.5rem;">节点类型:</p>
            <p style="color: #60a5fa; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; word-break: break-all;">
                {node_types_str or "无"}
            </p>
        </div>
        
        <div style="margin-top: 0.5rem;">
            <p style="color: #cbd5e1; font-size: 0.85rem; margin-bottom: 0.5rem;">边类型:</p>
            <p style="color: #10b981; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; word-break: break-all;">
                {edge_types_str or "无"}
            </p>
        </div>
    </div>
    """


def format_batch_results(results: List[Dict]) -> List[List]:
    """
    格式化批量处理结果为表格数据
    
    Args:
        results: 结果列表
        
    Returns:
        表格数据
    """
    table_data = []
    
    for result in results:
        # 确保文件名正确提取（优先使用原始文件名）
        filename = result.get("filename", "未知")
        # 如果文件名包含路径，只取文件名部分
        if isinstance(filename, str):
            from pathlib import Path
            filename = Path(filename).name
        
        predicted_class = result.get("predicted_class", "-")
        confidence = result.get("confidence", 0)
        status = result.get("status", "unknown")
        inference_time = result.get("inference_time", 0)
        process_time = f"{inference_time*1000:.1f}ms"
        
        # 状态映射
        status_display = {
            "success": "✅ 成功",
            "error": "❌ 失败",
            "processing": "⏳ 处理中"
        }.get(status, status)
        
        table_data.append([
            filename,
            predicted_class,
            f"{confidence*100:.1f}%",
            status_display,
            process_time
        ])
    
    return table_data


def create_header() -> gr.HTML:
    """创建应用头部"""
    return gr.HTML("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 class="app-title">🔬 3D BREP 模型智能分类系统</h1>
        <p class="app-subtitle">
            基于图神经网络的三维CAD模型自动分类 | 支持STEP格式
        </p>
    </div>
    """)


def create_footer() -> gr.HTML:
    """创建应用页脚"""
    return gr.HTML("""
    <div class="app-footer">
        <p>3D BREP Model Classification System v1.0</p>
        <p style="margin-top: 0.5rem;">
            Powered by PyTorch • DGL • ONNX Runtime • Gradio
        </p>
    </div>
    """)

