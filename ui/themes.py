"""
自定义UI主题

设计理念：
- 深色工业风格，专业现代感
- 科技蓝+能量橙强调色
- 毛玻璃效果和微交互
"""

import gradio as gr


def create_custom_theme() -> gr.Theme:
    """
    创建自定义Gradio主题
    
    Returns:
        Gradio主题对象
    """
    return gr.themes.Base(
        # 主色调
        primary_hue=gr.themes.Color(
            c50="#e6f7ff",
            c100="#bae7ff",
            c200="#91d5ff",
            c300="#69c0ff",
            c400="#40a9ff",
            c500="#1890ff",
            c600="#096dd9",
            c700="#0050b3",
            c800="#003a8c",
            c900="#002766",
            c950="#001529"
        ),
        # 次要色调
        secondary_hue=gr.themes.Color(
            c50="#fff7e6",
            c100="#ffe7ba",
            c200="#ffd591",
            c300="#ffc069",
            c400="#ffa940",
            c500="#fa8c16",
            c600="#d46b08",
            c700="#ad4e00",
            c800="#873800",
            c900="#612500",
            c950="#3d1600"
        ),
        # 中性色
        neutral_hue=gr.themes.Color(
            c50="#fafafa",
            c100="#f5f5f5",
            c200="#e8e8e8",
            c300="#d9d9d9",
            c400="#bfbfbf",
            c500="#8c8c8c",
            c600="#595959",
            c700="#434343",
            c800="#262626",
            c900="#1f1f1f",
            c950="#141414"
        ),
        font=[
            gr.themes.GoogleFont("DM Sans"),
            gr.themes.GoogleFont("JetBrains Mono"),
            "ui-sans-serif",
            "system-ui",
            "sans-serif"
        ],
        font_mono=[
            gr.themes.GoogleFont("JetBrains Mono"),
            "ui-monospace",
            "monospace"
        ],
        radius_size=gr.themes.sizes.radius_md,
        spacing_size=gr.themes.sizes.spacing_md,
    ).set(
        # 柔和深色背景 - 更舒适的配色
        background_fill_primary="#1e293b",  # 柔和深蓝灰
        background_fill_primary_dark="#1e293b",
        background_fill_secondary="#293548",
        background_fill_secondary_dark="#293548",
        body_background_fill="#1e293b",
        body_background_fill_dark="#1e293b",
        
        # 区块样式 - 明显的层次感
        block_background_fill="#293548",  # 卡片背景
        block_background_fill_dark="#293548",
        block_border_color="#475569",  # 更明显的边框
        block_border_color_dark="#475569",
        block_border_width="1px",
        block_label_background_fill="#334155",
        block_label_background_fill_dark="#334155",
        block_label_text_color="#f1f5f9",
        block_label_text_color_dark="#f1f5f9",
        block_radius="12px",
        block_shadow="0 4px 12px rgba(0, 0, 0, 0.2)",
        
        # 按钮样式 - 明亮蓝色
        button_primary_background_fill="linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
        button_primary_background_fill_dark="linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
        button_primary_background_fill_hover="linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)",
        button_primary_background_fill_hover_dark="linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)",
        button_primary_text_color="#ffffff",
        button_primary_text_color_dark="#ffffff",
        button_primary_border_color="transparent",
        button_primary_border_color_dark="transparent",
        
        # 输入框样式 - 更柔和
        input_background_fill="#334155",
        input_background_fill_dark="#334155",
        input_border_color="#475569",
        input_border_color_dark="#475569",
        input_border_color_focus="#3b82f6",
        input_border_color_focus_dark="#3b82f6",
        input_placeholder_color="#94a3b8",
        input_placeholder_color_dark="#94a3b8",
        
        # 文本颜色 - 更清晰
        body_text_color="#f1f5f9",
        body_text_color_dark="#f1f5f9",
        body_text_color_subdued="#cbd5e1",
        body_text_color_subdued_dark="#cbd5e1",
        
        # 链接颜色 - 明亮
        link_text_color="#60a5fa",
        link_text_color_dark="#60a5fa",
        link_text_color_hover="#3b82f6",
        link_text_color_hover_dark="#3b82f6",
        
        # 阴影 - 更柔和
        shadow_drop="0 4px 6px -1px rgba(0, 0, 0, 0.15)",
        shadow_drop_lg="0 10px 15px -3px rgba(0, 0, 0, 0.25)",
    )


# 自定义CSS样式
CUSTOM_CSS = """
/* ========== 最高优先级深色背景 - 优化协调性 ========== */

/* 清除所有默认白色背景 */
*, *::before, *::after {
    scrollbar-color: #475569 #1e293b;
}

/* 1. 页面根元素 - 柔和深蓝灰背景 */
body, html {
    background: #1e293b !important;
    background-color: #1e293b !important;
}

/* 2. Gradio主容器 - 全宽显示，不居中 */
.gradio-container,
.gradio-container-5-0-0,
.gradio-container-6-0-0,
[class*="gradio-container"] {
    background: #1e293b !important;
    background-color: #1e293b !important;
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 1.5rem 2.5rem !important;
}

/* 3. 主内容区域 */
main, .main, .app, #root, .gradio-app {
    background: #1e293b !important;
    background-color: #1e293b !important;
}

/* 4. Tabs和Tab面板 */
.tabs, .tab-nav, .tabitem,
[role="tablist"], [role="tabpanel"], [role="tab"] {
    background: #1e293b !important;
    background-color: #1e293b !important;
}

/* 5. 所有Block容器 */
.block, .form, .panel, .box, .container {
    background: #1e293b !important;
    background-color: #1e293b !important;
}

/* 6. Column、Row、Wrap - 不居中 */
[class*="column"], [class*="row"], 
[class*="wrap"], [class*="contain"],
.gr-column, .gr-row {
    background: transparent !important;
    background-color: transparent !important;
}

/* 强制Row左对齐，不居中 */
div[class*="row"], .gr-row {
    justify-content: flex-start !important;
    align-items: stretch !important;
}

/* 强制Column填充宽度 */
div[class*="column"], .gr-column {
    width: 100% !important;
}

/* 7. 强制覆盖任何白色背景的内联样式 */
[style*="background: white"],
[style*="background-color: white"],
[style*="background: #fff"],
[style*="background-color: #fff"],
[style*="background: rgb(255, 255, 255)"],
[style*="background-color: rgb(255, 255, 255)"] {
    background: #1e293b !important;
    background-color: #1e293b !important;
}

/* 8. Gradio内部组件背景 */
.svelte-1b19cri, .svelte-*, [class^="svelte-"] {
    background-color: transparent !important;
}

/* 9. 确保所有div默认透明，除非特别指定 */
div:not([class*="block"]):not([class*="card"]):not([class*="viewer"]) {
    background-color: transparent;
}

/* ========== 组件样式 - 优化配色协调 ========== */

/* 标题样式 - 科技蓝+翡翠绿渐变 */
.app-title {
    background: linear-gradient(135deg, #60a5fa 0%, #10b981 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    text-align: center;
    margin-bottom: 0.5rem !important;
    letter-spacing: -0.02em;
}

.app-subtitle {
    color: #cbd5e1 !important;
    text-align: center;
    font-size: 1.1rem !important;
    margin-bottom: 2rem !important;
}

/* Markdown内容颜色 - 更清晰 */
.markdown-body, .prose, .gr-markdown {
    color: #f1f5f9 !important;
    background-color: transparent !important;
}

.markdown-body h1, .markdown-body h2, .markdown-body h3,
.markdown-body h4, .markdown-body h5, .markdown-body h6 {
    color: #f8fafc !important;
    border-bottom-color: #475569 !important;
}

.markdown-body p, .markdown-body li {
    color: #f1f5f9 !important;
}

.markdown-body code {
    background-color: #334155 !important;
    color: #60a5fa !important;
    border: 1px solid #475569 !important;
}

.markdown-body table {
    border-color: #475569 !important;
}

.markdown-body th, .markdown-body td {
    border-color: #475569 !important;
    color: #f1f5f9 !important;
}

.markdown-body th {
    background-color: #334155 !important;
}

/* 文件上传区域 - 柔和视觉 */
.upload-area, [data-testid="file"] {
    border: 2px dashed #475569 !important;
    border-radius: 16px !important;
    padding: 2rem !important;
    background: linear-gradient(135deg, rgba(41, 53, 72, 0.6) 0%, rgba(30, 41, 59, 0.6) 100%) !important;
    backdrop-filter: blur(8px);
    transition: all 0.3s ease !important;
}

.upload-area:hover, [data-testid="file"]:hover {
    border-color: #3b82f6 !important;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(16, 185, 129, 0.1) 100%) !important;
    box-shadow: 0 0 24px rgba(59, 130, 246, 0.3) !important;
}

/* 文件上传内部文本 */
.file-preview, .upload-text {
    color: #f1f5f9 !important;
    background-color: transparent !important;
}

/* 结果卡片 - 柔和层次 */
.result-card {
    background: linear-gradient(135deg, rgba(41, 53, 72, 0.9) 0%, rgba(30, 41, 59, 0.9) 100%) !important;
    backdrop-filter: blur(12px);
    border: 1px solid #475569 !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
}

.result-card:hover {
    border-color: #3b82f6 !important;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(59, 130, 246, 0.25) !important;
}

/* 预测结果展示 - 现代蓝色渐变 */
.prediction-class {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: white !important;
    padding: 1rem 2rem !important;
    border-radius: 12px !important;
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    text-align: center !important;
    margin: 1rem 0 !important;
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
}

.confidence-meter {
    height: 8px !important;
    background: #334155 !important;
    border-radius: 4px !important;
    overflow: hidden !important;
    margin: 0.5rem 0 !important;
}

.confidence-fill {
    height: 100% !important;
    background: linear-gradient(90deg, #3b82f6 0%, #10b981 100%) !important;
    border-radius: 4px !important;
    transition: width 0.5s ease !important;
}

/* 概率分布条 - 柔和配色 */
.prob-bar-container {
    margin: 0.3rem 0 !important;
}

.prob-bar {
    height: 24px !important;
    background: #334155 !important;
    border-radius: 6px !important;
    overflow: hidden !important;
    position: relative !important;
    border: 1px solid #475569 !important;
}

.prob-bar-fill {
    height: 100% !important;
    background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%) !important;
    transition: width 0.5s ease !important;
    display: flex !important;
    align-items: center !important;
    padding-left: 8px !important;
}

.prob-bar-text {
    position: absolute !important;
    right: 8px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    color: #f1f5f9 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}

/* 图信息面板 - 柔和背景 */
.graph-info-panel {
    background: linear-gradient(135deg, rgba(41, 53, 72, 0.9) 0%, rgba(30, 41, 59, 0.85) 100%) !important;
    border: 1px solid #475569 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
}

.graph-info-item {
    display: flex !important;
    justify-content: space-between !important;
    padding: 0.5rem 0 !important;
    border-bottom: 1px solid #475569 !important;
}

.graph-info-label {
    color: #cbd5e1 !important;
}

.graph-info-value {
    color: #60a5fa !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* 3D预览区域 - 适度深色背景 */
.viewer-3d {
    background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%) !important;
    border: 2px solid #475569 !important;
    border-radius: 12px !important;
    min-height: 400px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.2) !important;
}

/* 批量处理表格 - 柔和配色 */
.batch-table {
    background: #293548 !important;
    border-radius: 12px !important;
    overflow: auto !important;
    max-height: 600px !important;
    border: 1px solid #475569 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
}

.batch-table table {
    width: 100% !important;
    border-collapse: collapse !important;
    background: #293548 !important;
}

.batch-table th {
    background: linear-gradient(180deg, #334155 0%, #293548 100%) !important;
    color: #f1f5f9 !important;
    font-weight: 600 !important;
    padding: 1rem !important;
    border-bottom: 2px solid #3b82f6 !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 10 !important;
}

.batch-table td {
    padding: 0.75rem 1rem !important;
    border-bottom: 1px solid #475569 !important;
    color: #f1f5f9 !important;
    background: #293548 !important;
}

.batch-table tr:hover td {
    background: #334155 !important;
}

.batch-table tbody tr:nth-child(even) td {
    background: #242f3f !important;
}

.batch-table tbody tr:nth-child(even):hover td {
    background: #334155 !important;
}

/* 状态标签 - 更现代的配色 */
.status-badge {
    padding: 0.25rem 0.75rem !important;
    border-radius: 9999px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}

.status-success {
    background: rgba(16, 185, 129, 0.15) !important;
    color: #10b981 !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
}

.status-error {
    background: rgba(239, 68, 68, 0.15) !important;
    color: #ef4444 !important;
    border: 1px solid rgba(239, 68, 68, 0.3) !important;
}

.status-processing {
    background: rgba(59, 130, 246, 0.15) !important;
    color: #3b82f6 !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
}

/* 动画效果 - 更柔和的发光 */
@keyframes pulse-glow {
    0%, 100% {
        box-shadow: 0 0 8px rgba(59, 130, 246, 0.3);
    }
    50% {
        box-shadow: 0 0 24px rgba(59, 130, 246, 0.6);
    }
}

.processing-indicator {
    animation: pulse-glow 2s infinite;
}

/* 工具栏按钮 - 柔和交互 */
.toolbar-btn {
    background: linear-gradient(135deg, rgba(41, 53, 72, 0.5) 0%, rgba(30, 41, 59, 0.5) 100%) !important;
    border: 1px solid #475569 !important;
    color: #f1f5f9 !important;
    padding: 0.5rem 1rem !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
    backdrop-filter: blur(8px);
}

.toolbar-btn:hover {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(16, 185, 129, 0.15) 100%) !important;
    border-color: #3b82f6 !important;
    color: #60a5fa !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25) !important;
}

/* 页脚 - 柔和边框 */
.app-footer {
    text-align: center !important;
    color: #94a3b8 !important;
    padding: 2rem 0 !important;
    font-size: 0.9rem !important;
    border-top: 1px solid #475569 !important;
    margin-top: 2rem !important;
}

/* 响应式调整 */
@media (max-width: 768px) {
    .app-title {
        font-size: 1.8rem !important;
    }
    
    .prediction-class {
        font-size: 1.2rem !important;
    }
}

/* Tab样式 - 柔和主题色 */
.tabs {
    background: transparent !important;
}

.tab-nav {
    background: linear-gradient(135deg, rgba(41, 53, 72, 0.7) 0%, rgba(30, 41, 59, 0.7) 100%) !important;
    border-radius: 12px !important;
    padding: 0.5rem !important;
    gap: 0.5rem !important;
    border: 1px solid #475569 !important;
    backdrop-filter: blur(8px);
}

.tab-nav button {
    background: transparent !important;
    border: none !important;
    color: #cbd5e1 !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}

.tab-nav button.selected {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.35) !important;
}

.tab-nav button:hover:not(.selected) {
    background: rgba(51, 65, 85, 0.6) !important;
    color: #f1f5f9 !important;
}
"""

