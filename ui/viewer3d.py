"""
3D查看器组件
基于 opencascade.js 和 Three.js 实现STEP文件的Web显示

支持的文件格式:
- ISO-10303-21 (STEP)标准文件
- 编码: ISO-8859-1, ASCII, UTF-8
"""
import logging
import hashlib
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# 全局字典存储文件ID到文件路径的映射
_file_cache = {}


def register_file(file_path: str) -> str:
    """
    注册文件并生成唯一ID
    
    Args:
        file_path: STEP文件路径
        
    Returns:
        文件ID
    """
    # 使用文件路径和时间戳生成唯一ID
    file_id = hashlib.md5(f"{file_path}_{time.time()}".encode()).hexdigest()[:16]
    _file_cache[file_id] = file_path
    return file_id


def get_file_path(file_id: str) -> str:
    """
    根据文件ID获取文件路径
    
    Args:
        file_id: 文件ID
        
    Returns:
        文件路径，如果不存在返回None
    """
    return _file_cache.get(file_id)


def create_step_viewer_html(file_path: str = None) -> str:
    """
    创建基于iframe的STEP文件3D查看器
    
    Args:
        file_path: STEP文件路径（可选）
        
    Returns:
        包含iframe的HTML字符串
    """
    
    # 如果没有文件，显示空状态
    if not file_path:
        return create_empty_step_viewer()
    
    # 验证文件存在
    if not Path(file_path).exists():
        return f"""
        <div style="padding: 2rem; text-align: center; color: #ef4444;">
            <p>❌ 文件不存在</p>
            <p style="font-size: 0.9rem; color: #cbd5e1;">{file_path}</p>
        </div>
        """
    
    try:
        # 注册文件并获取ID
        file_id = register_file(file_path)
        logger.info(f"已注册3D查看器文件: {file_path} -> {file_id}")
        
        # 创建iframe，指向独立的查看器页面
        viewer_html = f"""
        <iframe 
            src="/viewer?file={file_id}" 
            style="width: 100%; height: 500px; border: 2px solid #475569; border-radius: 12px; background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%);"
            frameborder="0"
            allowfullscreen>
        </iframe>
        """
        
        return viewer_html
        
    except Exception as e:
        logger.error(f"创建3D查看器失败: {e}")
        return f"""
        <div style="padding: 2rem; text-align: center; color: #ef4444;">
            <p>❌ 无法创建3D查看器</p>
            <p style="font-size: 0.9rem; color: #cbd5e1;">{str(e)}</p>
        </div>
        """


def create_empty_step_viewer() -> str:
    """创建空的STEP查看器占位符"""
    return """
    <div style="width: 100%; height: 500px; background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; border: 2px solid #475569; box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.2);">
        <div style="text-align: center; color: #cbd5e1;">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin: 0 auto; opacity: 0.7;">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                <polyline points="3.27,6.96 12,12.01 20.73,6.96"/>
                <line x1="12" y1="22.08" x2="12" y2="12"/>
            </svg>
            <p style="margin-top: 1rem; font-size: 1.1rem; color: #f1f5f9;">上传STEP文件后显示3D预览</p>
            <p style="margin-top: 0.5rem; font-size: 0.9rem; color: #cbd5e1;">支持 .step, .stp 格式</p>
        </div>
    </div>
    """

