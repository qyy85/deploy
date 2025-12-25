# 3D查看器离线部署指南

## 📌 概述

3D查看器默认使用CDN加载JavaScript库，适合有网络的环境。如果需要在**完全离线的环境**中部署，需要预先下载并配置本地JS库。

---

## ⚡ 快速决策

### 你的环境是否需要离线部署？

```
是否有网络连接？
├─ 有 → 使用默认配置（CDN模式）✅ 最简单
└─ 没有
   └─ 是否需要3D预览？
      ├─ 不需要 → 禁用3D查看器 ✅ 推荐
      └─ 需要 → 配置离线模式 ⚙️ 复杂
```

---

## 方案1: 禁用3D查看器（推荐）

**适用场景**: 离线环境 + 只需要分类功能

### 修改配置

编辑 `config.yaml`:

```yaml
ui:
  title: "3D BREP 模型智能分类系统"
  server_port: 7860
  share: false
  enable_3d_viewer: false  # 添加此行
```

编辑 `config.py` 的 `UIConfig` 类:

```python
@dataclass
class UIConfig:
    title: str = "3D BREP 模型智能分类系统"
    server_port: int = 7860
    share: bool = False
    enable_3d_viewer: bool = True  # 添加此字段
```

修改 `ui/layouts.py` 的 `create_single_tab`:

```python
# 根据配置决定是否显示3D查看器
config = AppConfig.load()

if config.ui.enable_3d_viewer:
    from ui.viewer3d import create_empty_step_viewer
    viewer_output = gr.HTML(
        value=create_empty_step_viewer(),
        label="🔷 3D模型预览"
    )
else:
    # 显示提示信息
    viewer_output = gr.HTML(
        value='<div style="padding: 2rem; text-align: center; color: #8b949e;">3D预览已禁用（离线模式）</div>',
        label="🔷 3D模型预览"
    )
```

**优点**:
- ✅ 无需下载额外文件
- ✅ 配置简单
- ✅ 分类功能完全正常

**缺点**:
- ❌ 无法查看3D模型

---

## 方案2: 离线部署3D查看器（高级）

**适用场景**: 离线环境 + 必须要3D预览

### 步骤概览

```
1. 有网环境下载JS库 → 2. 拷贝到离线服务器 → 3. 修改代码路径 → 4. 配置静态服务
```

### 详细步骤

#### 1️⃣ 在有网络的环境中下载依赖

创建下载脚本:

```bash
cd /root/workspace/deploy
mkdir -p static/libs
cd static/libs

# 创建下载脚本
cat > download.sh << 'EOF'
#!/bin/bash
set -e

echo "📦 下载Three.js和opencascade.js..."

# 确保安装了Node.js和npm
if ! command -v npm &> /dev/null; then
    echo "❌ 需要先安装 Node.js 和 npm"
    exit 1
fi

# 1. 下载 Three.js
echo "1️⃣ 下载 Three.js..."
npm pack three@0.150.0
tar -xzf three-*.tgz
mkdir -p three
cp package/build/three.module.js three/
cp -r package/examples/jsm three/
rm -rf package three-*.tgz

# 2. 下载 opencascade.js
echo "2️⃣ 下载 opencascade.js..."
npm pack opencascade.js@2.0.0-beta.2
tar -xzf opencascade.js-*.tgz
mkdir -p opencascade
cp -r package/dist/* opencascade/
rm -rf package opencascade.js-*.tgz

echo ""
echo "✅ 下载完成！"
echo "📁 目录结构:"
tree -L 2
echo ""
echo "📦 总大小: $(du -sh . | cut -f1)"
echo ""
echo "🚀 下一步: 将 static/libs 目录打包拷贝到离线服务器"
EOF

chmod +x download.sh
./download.sh
```

#### 2️⃣ 打包并传输到离线环境

```bash
# 在有网络的环境
cd /root/workspace/deploy
tar -czf 3d-viewer-libs.tar.gz static/libs/

# 传输到离线服务器（使用U盘、SCP等方式）
# 例如: scp 3d-viewer-libs.tar.gz user@offline-server:/path/to/deploy/
```

#### 3️⃣ 在离线环境解压

```bash
# 在离线服务器
cd /root/workspace/deploy
tar -xzf 3d-viewer-libs.tar.gz
```

#### 4️⃣ 修改代码使用本地路径

编辑 `ui/viewer3d.py`，修改导入部分:

```python
# 原来的CDN导入（在线模式）
# import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.150.0/+esm';

# 改为本地导入（离线模式）
# import * as THREE from '/static/libs/three/three.module.js';
```

完整修改示例:

```python
def create_step_viewer_html(file_path: str = None) -> str:
    # ... 前面代码不变 ...
    
    # 判断是在线还是离线模式
    import os
    use_local_libs = os.path.exists('/root/workspace/deploy/static/libs/three')
    
    if use_local_libs:
        # 离线模式：使用本地库
        three_import = "import * as THREE from '/static/libs/three/three.module.js';"
        controls_import = "import { OrbitControls } from '/static/libs/three/jsm/controls/OrbitControls.js';"
        occ_import = "const { default: initOpenCascade } = await import('/static/libs/opencascade/opencascade.wasm.module.js');"
    else:
        # 在线模式：使用CDN
        three_import = "import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.150.0/+esm';"
        controls_import = "import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.150.0/examples/jsm/controls/OrbitControls.js';"
        occ_import = "const { default: initOpenCascade } = await import('https://cdn.jsdelivr.net/npm/opencascade.js@2.0.0-beta.2/dist/opencascade.wasm.module.js');"
    
    viewer_html = f"""
    <div id="{viewer_id}">
        <!-- ... HTML不变 ... -->
        
        <script type="module">
            // 使用动态导入
            {three_import}
            {controls_import}
            
            (async function() {{
                try {{
                    {occ_import}
                    
                    // ... 其余代码不变 ...
                }} catch (error) {{
                    console.error('加载失败:', error);
                }}
            }})();
        </script>
    </div>
    """
    return viewer_html
```

#### 5️⃣ 配置Gradio静态文件服务

在 `app.py` 中添加静态文件支持:

```python
import gradio as gr
from pathlib import Path

# 配置静态文件路径
static_dir = Path(__file__).parent / "static"

# 启动时挂载静态文件
demo = create_app()
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    # Gradio会自动提供 /file= 路由来访问文件
    # 但需要确保static目录在正确位置
)
```

或者使用FastAPI手动挂载:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import gradio as gr

app = FastAPI()

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 挂载Gradio应用
gradio_app = create_app()
app = gr.mount_gradio_app(app, gradio_app, path="/")
```

---

## 📊 两种方案对比

| 特性 | 方案1: 禁用 | 方案2: 离线部署 |
|------|-----------|---------------|
| 配置复杂度 | ⭐ 简单 | ⭐⭐⭐⭐⭐ 复杂 |
| 额外下载 | 0 MB | 35 MB |
| 代码修改 | 最小 | 中等 |
| 3D预览 | ❌ | ✅ |
| 分类功能 | ✅ | ✅ |
| 维护成本 | 低 | 中高 |

---

## 🛠️ 故障排查

### 问题1: 本地库路径404

**原因**: Gradio没有正确提供静态文件服务

**解决**:
1. 检查 `static/libs` 目录是否存在
2. 确认文件路径正确
3. 使用浏览器开发者工具查看网络请求

### 问题2: CORS错误

**原因**: JavaScript模块跨域限制

**解决**:
```python
# 在 app.py 中设置CORS
demo.launch(
    server_name="0.0.0.0",
    allowed_paths=["static"],  # 允许访问static目录
)
```

### 问题3: WASM加载失败

**原因**: WASM文件MIME类型不正确

**解决**:
确保服务器正确设置MIME类型:
- `.wasm` → `application/wasm`
- `.js` → `application/javascript`

---

## 💡 最佳实践

### 推荐配置

```yaml
# 对于大多数离线部署场景
ui:
  enable_3d_viewer: false  # 禁用3D查看器
  
# 核心分类功能不受影响：
# ✅ BREP特征提取
# ✅ 图神经网络推理
# ✅ 结果展示
```

### 何时使用离线部署？

**建议禁用** (方案1):
- ✅ 内网环境，无法访问公网
- ✅ 主要关注分类精度
- ✅ 用户已有其他CAD软件查看模型

**建议离线部署** (方案2):
- ✅ 必须提供完整的一体化体验
- ✅ 有专业运维支持
- ✅ 用户明确要求3D预览功能

---

## 📦 依赖文件清单

```
static/libs/
├── three/
│   ├── three.module.js         (1.2 MB)   - Three.js核心
│   └── jsm/
│       └── controls/
│           └── OrbitControls.js (20 KB)    - 相机控制
└── opencascade/
    ├── opencascade.wasm.module.js (500 KB) - JS胶水代码
    └── opencascade.wasm.wasm      (30 MB)  - WASM主模块
```

**总大小**: 约 **32 MB**

---

## 📞 技术支持

如有问题，请查看:
1. [3D查看器集成文档](3D_VIEWER_INTEGRATION.md)
2. [更新日志](../CHANGELOG.md)
3. GitHub Issues

---

## 🔄 版本兼容性

| 库 | 版本 | 备注 |
|----|------|------|
| three.js | 0.150.0 | 稳定版本 |
| opencascade.js | 2.0.0-beta.2 | 最新稳定版 |

**更新库版本**: 重新运行下载脚本即可

