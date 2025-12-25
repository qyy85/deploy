"""
UI布局模块

定义Gradio界面的布局结构
"""

import gradio as gr
from typing import Callable

from config import DeployConfig
from .components import (
    create_header,
    create_footer,
    create_empty_prediction_html,
    create_empty_confidence_html,
    create_empty_probs_html,
    create_progress_html,
    create_empty_progress_html,
)


def create_single_tab(
    process_fn: Callable,
) -> dict:
    """
    创建单文件处理Tab
    
    Args:
        process_fn: 处理函数
        
    Returns:
        包含组件引用的字典
    """
    with gr.TabItem("🔍 单文件分类", id="single"):
        # 顶部文件上传区域
        gr.Markdown("""
        <div style="padding: 1rem 0; border-bottom: 1px solid #475569; margin-bottom: 1.5rem;">
            <h3 style="color: #f1f5f9; margin: 0 0 0.5rem 0; font-size: 1.2rem;">📁 上传STEP模型文件</h3>
            <p style="color: #cbd5e1; margin: 0; font-size: 0.9rem;">支持 .step, .stp 格式文件，系统将自动提取BREP特征并进行分类</p>
        </div>
        """)
        
        # 文件上传区域 - 全宽显示
        file_input = gr.File(
            label="",
            file_types=[".step", ".stp", ".STEP", ".STP"],
            file_count="single",
            elem_classes=["upload-area"],
            show_label=False
        )
        
        # 3D预览区域 - 全宽显示
        gr.Markdown("""
        <div style="margin: 2rem 0 0.8rem 0;">
            <h4 style="color: #f1f5f9; margin: 0; font-size: 1.1rem;">
                <span style="background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%); 
                             -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                             font-weight: 600;">🔷 3D模型预览</span>
            </h4>
        </div>
        """)
        
        from ui.viewer3d import create_empty_step_viewer
        viewer_output = gr.HTML(
            value=create_empty_step_viewer(),
            show_label=False
        )
        
        # 分类结果区域 - 三栏布局
        gr.Markdown("""
        <div style="margin: 2rem 0 0.8rem 0;">
            <h4 style="color: #f1f5f9; margin: 0; font-size: 1.1rem;">
                <span style="background: linear-gradient(135deg, #10b981 0%, #34d399 100%); 
                             -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                             font-weight: 600;">📊 分类结果</span>
            </h4>
        </div>
        """)
        
        with gr.Row(equal_height=True):
            # 预测类别
            with gr.Column(scale=1):
                class_output = gr.HTML(
                    value=create_empty_prediction_html(),
                    show_label=False
                )
            
            # 置信度
            with gr.Column(scale=1):
                confidence_output = gr.HTML(
                    value=create_empty_confidence_html(),
                    show_label=False
                )
            
            # 概率分布
            with gr.Column(scale=1):
                probs_output = gr.HTML(
                    value=create_empty_probs_html(),
                    show_label=False
                )
        
        # 底部操作按钮
        with gr.Row():
            clear_btn = gr.Button(
                "🔄 清空重置",
                variant="secondary",
                size="lg",
                elem_classes=["toolbar-btn"]
            )
        
        # 绑定事件
        file_input.change(
            fn=process_fn,
            inputs=[file_input],
            outputs=[
                class_output,
                confidence_output,
                probs_output,
                viewer_output
            ]
        )
        
        from ui.viewer3d import create_empty_step_viewer
        clear_btn.click(
            fn=lambda: (
                None,
                create_empty_prediction_html(),
                create_empty_confidence_html(),
                create_empty_probs_html(),
                create_empty_step_viewer()
            ),
            inputs=[],
            outputs=[
                file_input,
                class_output,
                confidence_output,
                probs_output,
                viewer_output
            ]
        )
    
    return {
        "file_input": file_input,
        "class_output": class_output,
        "confidence_output": confidence_output,
        "probs_output": probs_output,
        "viewer_output": viewer_output,
        "clear_btn": clear_btn
    }


def create_batch_tab(
    process_fn: Callable,
) -> dict:
    """
    创建批量处理Tab
    
    Args:
        process_fn: 处理函数
        
    Returns:
        包含组件引用的字典
    """
    with gr.TabItem("📚 批量处理", id="batch"):
        gr.Markdown("""
        ### 📚 批量模型分类
        
        支持同时上传多个STEP文件进行批量分类处理。
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                batch_input = gr.File(
                    label="📁 批量上传文件",
                    file_types=[".step", ".stp", ".STEP", ".STP"],
                    file_count="multiple",
                    elem_classes=["upload-area"]
                )
                
                with gr.Row():
                    batch_process_btn = gr.Button(
                        "🚀 开始批量处理",
                        variant="primary"
                    )
                    batch_clear_btn = gr.Button(
                        "🔄 清空",
                        variant="secondary"
                    )
            
            with gr.Column(scale=2):
                batch_progress = gr.HTML(
                    value=create_empty_progress_html(),
                    label="📊 处理进度",
                    visible=True
                )
                
                batch_results = gr.Dataframe(
                    headers=["文件名", "预测类别", "置信度", "状态", "处理时间"],
                    datatype=["str", "str", "str", "str", "str"],
                    label="📊 批量处理结果",
                    interactive=False,
                    elem_classes=["batch-table"]
                )
        
        # 绑定事件
        batch_process_btn.click(
            fn=process_fn,
            inputs=[batch_input],
            outputs=[batch_progress, batch_results]
        )
        
        batch_clear_btn.click(
            fn=lambda: (None, create_empty_progress_html(), []),
            inputs=[],
            outputs=[batch_input, batch_progress, batch_results]
        )
    
    return {
        "batch_input": batch_input,
        "batch_process_btn": batch_process_btn,
        "batch_clear_btn": batch_clear_btn,
        "batch_progress": batch_progress,
        "batch_results": batch_results
    }


def create_system_tab(
    config: DeployConfig,
    is_ready: bool
) -> None:
    """
    创建系统信息Tab
    
    Args:
        config: 部署配置
        is_ready: 分类器是否就绪
    """
    with gr.TabItem("⚙️ 系统信息", id="system"):
        gr.Markdown("### ⚙️ 系统状态")
        
        with gr.Row():
            with gr.Column():
                classifier_status = "✅ 已就绪" if is_ready else "⚠️ 演示模式"
                
                gr.Markdown(f"""
                | 组件 | 状态 |
                |------|------|
                | 分类器 | {classifier_status} |
                | 推理设备 | {config.model.device.upper()} |
                | 模型路径 | `{config.model.model_path}` |
                | 批次大小 | {config.model.batch_size} |
                """)
            
            with gr.Column():
                gr.Markdown("### 📋 支持的类别")
                
                class_list = ""
                for parent, parent_cn in config.class_mapping.parent_classes.items():
                    class_list += f"\n**{parent_cn}** ({parent})\n"
                    for child, child_cn in config.class_mapping.child_classes.items():
                        key = f"{parent}/{child}"
                        if key in config.class_mapping.full_class_map:
                            class_list += f"  - {child_cn} ({child})\n"
                
                gr.Markdown(class_list if class_list else "未配置类别映射")
        
        gr.Markdown("""
        ---
        ### 📖 使用说明
        
        1. **单文件分类**: 上传单个STEP格式的三维模型文件
        2. **批量处理**: 同时上传多个文件，批量获取分类结果
        3. **支持格式**: `.step`, `.stp`, `.STEP`
        """)


def create_app_ui(
    config: DeployConfig,
    is_ready: bool,
    single_process_fn: Callable,
    batch_process_fn: Callable,
    theme: gr.Theme = None,
    css: str = None
) -> gr.Blocks:
    """
    创建完整的应用UI
    
    Args:
        config: 部署配置
        is_ready: 分类器是否就绪
        single_process_fn: 单文件处理函数
        batch_process_fn: 批量处理函数
        theme: Gradio主题（可选）
        css: 自定义CSS（可选）
        
    Returns:
        Gradio Blocks应用
    """
    # Gradio 6.x: 使用 theme 和 css 参数 (会显示警告，但能确保样式生效)
    with gr.Blocks(
        title=config.ui.title,
        theme=theme,
        css=css
    ) as app:
        
        create_header()
        
        with gr.Tabs() as tabs:
            create_single_tab(single_process_fn)
            create_batch_tab(batch_process_fn)
            create_system_tab(config, is_ready)
        
        create_footer()
    
    return app

