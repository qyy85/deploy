# 🔬 3D BREP 模型智能分类系统 - 部署模块

基于图神经网络的三维CAD模型自动分类部署解决方案。

## ✨ 功能特性

- **🔄 BREP图提取**: 从STEP文件自动提取BREP拓扑结构，构建异构图
- **⚡ PyTorch推理**: 完整支持DGL图神经网络，支持CPU和GPU
- **🔷 3D模型预览**: 基于opencascade.js的实时STEP文件3D显示 ✅ **已本地化，完全离线可用**
- **🎨 现代化UI**: 基于Gradio的深色主题Web界面
- **📚 批量处理**: 支持多文件批量分类，实时进度显示
- **📊 结果分析**: 详细的置信度和概率分布展示

> 💡 **重要**: 3D查看器JavaScript库已安装到本地（81MB），**无需网络连接**即可使用！
> 详见：[INSTALLATION_STATUS.md](INSTALLATION_STATUS.md)

## 📁 目录结构

```
deploy/
├── __init__.py              # 模块入口
├── app.py                   # Web应用主程序
├── config.py                # 配置管理
├── config.yaml              # 默认配置文件
├── requirements.txt         # 依赖列表
├── run.sh                   # 启动脚本
├── README.md                # 本文档
├── core/                    # 核心功能模块
│   ├── brep_extractor.py    # BREP图提取器
│   ├── exporter.py          # 模型导出工具
│   └── inference.py         # PyTorch推理引擎
├── ui/                      # UI组件
│   ├── components.py        # UI组件
│   └── themes.py            # 主题样式
└── models/                  # 模型存放目录
    └── .gitkeep
```

## 📦 依赖清单

### Python依赖（必需）

**核心分类功能所需依赖：**

| 包名 | 版本 | 用途 | 安装方式 |
|------|------|------|---------|
| `torch` | ≥2.0.0 | 深度学习框架 | pip/conda |
| `dgl` | ≥1.1.0 | 图神经网络库 | pip |
| `gradio` | ≥5.0.0 | Web UI框架 | pip |
| `pythonocc-core` | ≥7.7.0 | STEP文件解析 | conda |
| `numpy` | ≥1.20.0 | 数值计算 | pip |
| `pyyaml` | ≥6.0 | 配置文件解析 | pip |

**完整依赖列表**: 见 `requirements.txt`

### JavaScript依赖（3D查看器，可选）

**如果需要3D预览功能：**

| 库名 | 版本 | 大小 | 用途 |
|------|------|------|------|
| `three.js` | 0.150.0 | ~1.5MB | 3D渲染引擎 |
| `opencascade.js` | 2.0.0-beta.2 | ~31MB | STEP解析引擎 |

⚠️ **离线环境建议**: 禁用3D查看器，只保留核心分类功能

---

## 🚀 快速开始（离线环境）

### 准备阶段（在有网络的环境中）

#### 1. 下载Python依赖包

```bash
# 方式1: 使用pip download（推荐）
mkdir -p /tmp/deploy_packages
pip download -r deploy/requirements.txt -d /tmp/deploy_packages

# 方式2: 使用conda pack（如果使用conda环境）
conda install conda-pack
conda pack -n your_env_name -o deploy_env.tar.gz
```

#### 2. 下载预训练模型

```bash
# 从训练服务器复制模型文件
cp experiments/classification/xxx/best_classifier.ckpt deploy/models/
```

#### 3. （可选）下载3D查看器依赖

**⚠️ 仅在需要3D预览时下载，否则跳过此步骤**

```bash
# 需要先安装 Node.js 和 npm
cd deploy/static/libs

# 下载Three.js
npm pack three@0.150.0
tar -xzf three-0.150.0.tgz
mkdir -p three
cp package/build/three.module.js three/
cp -r package/examples/jsm three/
rm -rf package three-*.tgz

# 下载opencascade.js
npm pack opencascade.js@2.0.0-beta.2
tar -xzf opencascade.js-*.tgz
mkdir -p opencascade
cp -r package/dist/* opencascade/
rm -rf package opencascade.js-*.tgz

echo "✅ JavaScript库下载完成"
ls -lh
```

#### 4. 打包传输文件

```bash
# 打包整个deploy目录
cd /path/to/project
tar -czf deploy_offline.tar.gz \
    deploy/requirements.txt \
    deploy/app.py \
    deploy/config.yaml \
    deploy/src/ \
    deploy/ui/ \
    deploy/data_preprocess/ \
    deploy/models/ \
    /tmp/deploy_packages/  # Python依赖包

# 如果包含3D查看器库
tar -czf deploy_with_3d.tar.gz \
    deploy/ \
    /tmp/deploy_packages/

echo "📦 打包完成: deploy_offline.tar.gz"
du -sh deploy_offline.tar.gz
```

---

### 离线安装步骤

#### 1. 传输文件到离线服务器

```bash
# 使用U盘、移动硬盘或其他方式传输
# - deploy_offline.tar.gz
# - Python安装包（如果系统没有Python）
```

#### 2. 解压文件

```bash
# 在离线服务器上
cd /opt  # 或其他安装目录
tar -xzf deploy_offline.tar.gz
cd deploy
```

#### 3. 创建Python虚拟环境

```bash
# 方式1: 使用venv（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 方式2: 使用conda
conda create -n deploy python=3.10
conda activate deploy
```

#### 4. 安装Python依赖（离线）

```bash
# 从本地目录安装
pip install --no-index --find-links=/tmp/deploy_packages -r requirements.txt

# 或者逐个安装（如果有问题）
cd /tmp/deploy_packages
pip install --no-index --find-links=. torch-*.whl
pip install --no-index --find-links=. dgl-*.whl
pip install --no-index --find-links=. gradio-*.whl
# ... 其他依赖

# 验证安装
python -c "import torch; import dgl; import gradio; print('✓ 核心依赖安装成功')"
```

#### 5. 配置3D查看器（可选）

**选项A: 禁用3D查看器**（推荐，完全离线）

编辑 `config.yaml`:
```yaml
ui:
  title: "3D BREP 模型智能分类系统"
  server_port: 7860
  share: false
  enable_3d_viewer: false  # 添加此行
```

**选项B: 使用本地JS库**（需要提前下载）

如果在准备阶段已下载JS库，修改 `ui/viewer3d.py`:

```python
# 在 create_step_viewer_html 函数开头添加
def create_step_viewer_html(file_path: str = None) -> str:
    # 强制使用本地库（离线模式）
    USE_LOCAL_LIBS = True  # 改为True
    
    if USE_LOCAL_LIBS:
        three_import = "import * as THREE from '/static/libs/three/three.module.js';"
        # ... 其他本地导入
    # ...
```

#### 6. 验证模型文件

```bash
# 检查模型是否存在
ls -lh models/
# 应该看到: best_classifier.ckpt 或 model.pt
```

---

### 启动应用

```bash
# 确保在虚拟环境中
source venv/bin/activate  # 或 conda activate deploy

# 启动Web服务
python app.py

# 或指定参数
python app.py --port 7860 --device cpu
```

访问: `http://localhost:7860`

### 验证安装

```bash
# 验证核心功能
python -c "
import torch
import dgl
import gradio as gr
from OCC.Core.STEPControl import STEPControl_Reader
print('✅ 所有核心依赖安装成功')
print(f'PyTorch版本: {torch.__version__}')
print(f'DGL版本: {dgl.__version__}')
print(f'Gradio版本: {gr.__version__}')
"

# 测试启动
python app.py --help
```

---

## 📚 详细文档

- **[离线安装完整指南](OFFLINE_INSTALL_GUIDE.md)** ⭐ **强烈推荐**
  - 系统要求
  - 依赖打包方法
  - 逐步安装指南
  - 故障排查

- **[完整依赖列表](requirements-full.txt)**
  - 所有Python包及版本
  - 特殊依赖安装说明

- **[3D查看器离线部署](docs/3D_VIEWER_OFFLINE_SETUP.md)**
  - JavaScript库下载
  - 本地化配置

## 📦 核心依赖版本

### Python包（通过pip/conda安装）

| 包名 | 版本要求 | 安装方式 | 大小 | 备注 |
|------|---------|---------|------|------|
| `torch` | ≥2.0.0 | pip/conda | ~800MB | CPU版；GPU版更大 |
| `dgl` | ≥1.1.0 | pip | ~50MB | 图神经网络 |
| `gradio` | ≥5.0.0 | pip | ~100MB | Web UI |
| `pythonocc-core` | ≥7.7.0 | **conda only** | ~500MB | ⚠️ 只能用conda安装 |
| `numpy` | ≥1.24.0 | pip | ~15MB | 数值计算 |
| `PyYAML` | ≥6.0 | pip | ~1MB | 配置文件 |
| `tqdm` | ≥4.65.0 | pip | ~1MB | 进度条 |

**完整列表**: 见 `requirements-full.txt`（约70个包，总计~3GB）

### JavaScript库（3D查看器，可选）

| 库名 | 版本 | 大小 | 安装方式 |
|------|------|------|---------|
| `three.js` | 0.150.0 | ~1.5MB | npm或CDN |
| `opencascade.js` | 2.0.0-beta.2 | ~31MB | npm或CDN |

**离线环境建议**: 禁用3D查看器（`enable_3d_viewer: false`）

---

## 🔧 特殊说明

### ⚠️ pythonocc-core 安装

**这是最重要的依赖**，只能通过conda安装：

```bash
# 在线安装
conda install -c conda-forge pythonocc-core=7.7.0

# 离线安装
# 步骤1（有网环境）: 打包conda环境
conda install conda-pack
conda pack -n your_env -o environment.tar.gz

# 步骤2（离线环境）: 解压使用
tar -xzf environment.tar.gz -C /path/to/env
source /path/to/env/bin/activate
conda-unpack
```

详细说明：[OFFLINE_INSTALL_GUIDE.md](OFFLINE_INSTALL_GUIDE.md)

### 📥 完整离线安装包准备

**在有网络的环境中执行**:

```bash
# 1. 创建conda环境并安装所有依赖
conda create -n deploy python=3.10 -y
conda activate deploy
conda install -c conda-forge pythonocc-core=7.7.0 -y
pip install torch dgl gradio  # 其他依赖...

# 2. 打包环境（最重要）
conda install conda-pack -y
conda pack -n deploy -o deploy_env.tar.gz

# 3. 打包项目代码
tar -czf deploy_code.tar.gz deploy/

# 4. 打包模型
tar -czf models.tar.gz models/

# 传输这3个文件到离线服务器即可
```

**文件清单**:
```
deploy_env.tar.gz     (2-5GB)  - Python完整环境
deploy_code.tar.gz    (<10MB)  - 项目代码
models.tar.gz         (50-200MB) - 训练好的模型
```

**离线服务器上安装**:
```bash
# 1. 解压环境
mkdir -p /opt/envs/deploy
tar -xzf deploy_env.tar.gz -C /opt/envs/deploy
source /opt/envs/deploy/bin/activate
conda-unpack

# 2. 解压代码和模型
tar -xzf deploy_code.tar.gz -C /opt/
tar -xzf models.tar.gz -C /opt/deploy/

# 3. 配置并启动
cd /opt/deploy
vi config.yaml  # 设置 enable_3d_viewer: false
python app.py
```

**完整文档**: [OFFLINE_INSTALL_GUIDE.md](OFFLINE_INSTALL_GUIDE.md) (70页详细指南)

---

## 📦 完整依赖版本列表

## ⚙️ 配置说明

### 配置文件 (`config.yaml`)

```yaml
# 模型配置
model:
  model_path: "deploy/models/model.pt"  # 导出的模型
  checkpoint_path: "path/to/checkpoint.ckpt"  # 原始检查点
  graph_emb_dim: 256
  device: "cpu"  # 或 "cuda"

# 类别映射
class_mapping:
  parent_classes:
    zhengti: "整体式"
    zhuzao: "铸造式"
    huanxing: "环形式"
  child_classes:
    che: "车削"
    li: "里"
    liwo: "螺窝"
    wo: "窝"
    wuzhou: "无轴"

# UI配置
ui:
  title: "3D BREP 模型智能分类系统"
  server_port: 7860
  share: false
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--config` | 配置文件路径 | `deploy/config.yaml` |
| `--port` | 服务端口 | `7860` |
| `--share` | 生成公网链接 | `false` |
| `--device` | 推理设备 (cpu/cuda) | `cpu` |

## 🌐 网络要求

| 功能 | 网络要求 | 说明 |
|------|---------|------|
| **分类功能** | ❌ 不需要 | 完全本地运行 |
| **3D查看器** | ⚠️ 需要（首次） | 从CDN加载JS库（约30MB），浏览器会缓存 |

**如果在完全离线环境部署，建议禁用3D查看器功能。**

## 📋 支持的文件格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| STEP | `.step`, `.stp` | ISO 10303 CAD交换格式 |
| BIN | `.bin` | 预处理的DGL图文件 |

## 🔧 API使用

### 程序化调用

```python
from deploy.app import ModelClassificationApp
from deploy.config import DeployConfig

# 加载配置
config = DeployConfig.from_yaml("deploy/config.yaml")

# 创建应用
app = ModelClassificationApp(config)

# 处理单个文件
result = app.process_single_file("path/to/model.step")

# 启动Web服务
app.launch(server_port=7860)
```

### 直接使用推理引擎

```python
from deploy.core.brep_extractor import BREPGraphExtractor
from deploy.core.inference import ModelInference

# 提取BREP图
extractor = BREPGraphExtractor()
graph, metadata = extractor.extract_from_step("model.step")

# 分类预测
classifier = ModelInference(
    checkpoint_path="checkpoint.ckpt",
    class_mapping={0: "类别A", 1: "类别B"}
)
result = classifier.predict(graph)

print(f"预测类别: {result['predicted_class']}")
print(f"置信度: {result['confidence']:.2%}")
```

## 🎨 UI界面预览

系统提供三个主要功能页面：

1. **单文件分类**: 上传单个STEP文件，查看预测结果和3D预览
2. **批量处理**: 批量上传多个文件，获取分类结果表格
3. **系统信息**: 查看系统状态、类别列表和使用说明

## ❓ 常见问题

### Q: 启动时提示"GraphBuilder不可用"?

A: 需要安装`data_preprocess`模块才能直接从STEP文件提取图。如果该模块不可用，可以：
1. 先使用其他工具将STEP转换为BIN文件
2. 直接上传BIN文件进行分类

### Q: 如何使用GPU加速?

A: 
1. 确保安装了CUDA版本的PyTorch
2. 启动时指定设备: `python -m deploy.app --device cuda`

### Q: 如何添加新的类别?

A: 修改`config.yaml`中的`class_mapping`配置，添加新的类别映射。

## 📄 许可证

本项目仅供学习研究使用。

## 🤝 贡献

欢迎提交Issue和Pull Request！
