#!/usr/bin/env python3
"""
3D BREP 模型智能分类系统 - Web应用

功能特性：
- 上传STEP格式的三维模型
- 自动提取BREP拓扑图结构
- 使用PyTorch/DGL图神经网络进行分类
- 3D模型预览
- 批量处理支持

启动方式：
    cd /root/workspace/deploy
    python app.py --config config.yaml
    或使用启动脚本：
    ./run.sh
"""

import sys
import traceback
from pathlib import Path
import gradio as gr
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse

# 添加项目根目录到路径 (deploy目录)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import DeployConfig, DEFAULT_CONFIG
from src.handlers import FileHandler
from ui.layouts import create_app_ui
from ui.themes import create_custom_theme, CUSTOM_CSS
from src.inference import ModelInference


class ModelClassificationApp:
    """3D模型分类Web应用"""
    
    def __init__(self, config: DeployConfig = None):
        """
        初始化应用
        
        Args:
            config: 部署配置对象
        """
        self.config = config or DEFAULT_CONFIG
        self.classifier = None
        self.is_ready = False
        
        # 初始化组件
        self._init_classifier()
        
        # 初始化处理器
        self.handler = FileHandler(
            config=self.config,
            classifier=self.classifier,
            is_ready=self.is_ready
        )
    
    def _init_classifier(self):
        """初始化分类器"""
        print("🔧 正在初始化推理组件...")
        
        try:
            model_path = Path(self.config.model.model_path)
            
            if not model_path.exists():
                print(f"⚠ 模型文件不存在: {model_path}")
                print("  系统将以演示模式运行")
                return
            
            # 构建类别映射
            class_mapping = {}
            for path, idx in self.config.class_mapping.full_class_map.items():
                class_mapping[idx] = self.config.class_mapping.get_class_name(idx)
            
            
            self.classifier = ModelInference(
                model_path=str(model_path),
                class_mapping=class_mapping,
                device=self.config.model.device
            )
            self.is_ready = self.classifier.is_ready()
            print("✓ 推理引擎已初始化")
            
        except Exception as e:
            print(f"⚠ 推理引擎初始化失败: {e}")
            traceback.print_exc()
    
    def create_ui(self):
        """创建UI界面"""
        # 创建主题和CSS
        theme = create_custom_theme()
        
        # Gradio 6.x: theme和css在create_app_ui内部处理
        app = create_app_ui(
            config=self.config,
            is_ready=self.is_ready,
            single_process_fn=self.handler.process_single_file,
            batch_process_fn=self.handler.process_batch_files,
            theme=theme,
            css=CUSTOM_CSS
        )
        
        return app
    
    def launch(self, **kwargs):
        """启动Web应用"""
        gradio_app = self.create_ui()
        
        # 创建 FastAPI 应用
        fastapi_app = FastAPI()
        
        # 挂载静态文件目录
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            fastapi_app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        # 添加3D查看器路由
        from ui.viewer3d import get_file_path
        
        @fastapi_app.get("/viewer", response_class=HTMLResponse)
        async def viewer_page():
            """提供3D查看器页面"""
            viewer_template = static_dir / "viewer_template.html"
            if not viewer_template.exists():
                raise HTTPException(status_code=404, detail="Viewer template not found")
            
            with open(viewer_template, 'r', encoding='utf-8') as f:
                return f.read()
        
        @fastapi_app.get("/api/step-content/{file_id}", response_class=PlainTextResponse)
        async def get_step_content(file_id: str):
            """提供STEP文件内容"""
            file_path = get_file_path(file_id)
            
            if not file_path:
                raise HTTPException(status_code=404, detail="File not found")
            
            if not Path(file_path).exists():
                raise HTTPException(status_code=404, detail="File does not exist")
            
            try:
                # 使用ISO-8859-1编码读取STEP文件
                with open(file_path, 'r', encoding='iso-8859-1') as f:
                    content = f.read()
                return content
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
        
        # 将 Gradio 应用挂载到 FastAPI
        app = gr.mount_gradio_app(fastapi_app, gradio_app, path="/")
        
        # 启动配置
        server_port = self.config.ui.server_port
        share = self.config.ui.share
        
        print(f"""
╔═══════════════════════════════════════════════════════════════╗
║           3D BREP 模型智能分类系统                              ║
╠═══════════════════════════════════════════════════════════════╣
║  本地访问: http://localhost:{server_port}                          ║
║  远程访问: http://0.0.0.0:{server_port} 或使用IP地址            ║
║  分类器状态: {'已就绪' if self.is_ready else '演示模式'}                                   ║
║  静态文件: /static/ (FastAPI挂载)                              ║
╚═══════════════════════════════════════════════════════════════╝
        """)
        
        # 使用 uvicorn 启动 FastAPI 应用
        import uvicorn
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=server_port,
            log_level="info"
        )


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="3D BREP 模型智能分类系统")
    parser.add_argument("--config", type=str, default="config.yaml", help="配置文件路径")
    parser.add_argument("--port", type=int, default=7860, help="服务端口")
    parser.add_argument("--share", action="store_true", help="生成公网链接")
    parser.add_argument("--device", type=str, default="cuda", choices=["cpu", "cuda"], help="推理设备")
    
    args = parser.parse_args()
    
    # 加载配置
    if args.config and Path(args.config).exists():
        config = DeployConfig.from_yaml(args.config)
    else:
        config = DEFAULT_CONFIG
    
    # 应用命令行参数
    config.ui.server_port = args.port
    config.ui.share = args.share
    config.model.device = args.device
    
    # 启动应用
    app = ModelClassificationApp(config)
    app.launch()


if __name__ == "__main__":
    main()
