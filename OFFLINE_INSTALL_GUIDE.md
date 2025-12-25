# 离线安装完整指南

本指南详细说明如何在**完全无网络的环境**中部署3D BREP模型分类系统。

---

## 📋 目录

1. [系统要求](#系统要求)
2. [准备阶段（有网络环境）](#准备阶段)
3. [传输文件](#传输文件)
4. [离线安装步骤](#离线安装步骤)
5. [验证和启动](#验证和启动)
6. [故障排查](#故障排查)

---

## 系统要求

### 硬件要求
- CPU: 4核心及以上
- 内存: 16GB RAM（最低8GB）
- 硬盘: 50GB可用空间
- GPU: 可选，NVIDIA显卡（4GB+显存）

### 软件要求
- 操作系统: Linux (推荐 Ubuntu 20.04/22.04) / Windows 10+ / macOS
- Python: 3.10 或 3.11
- Conda: Miniconda或Anaconda（推荐）

---

## 准备阶段

### 在有网络的环境中完成以下步骤

#### 📦 步骤1: 安装基础工具

```bash
# 1. 安装Miniconda（如果没有）
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 2. 安装Node.js（仅在需要3D查看器时）
# 从 https://nodejs.org/ 下载对应平台的安装包
```

#### 📥 步骤2: 创建并准备Conda环境

```bash
# 创建新环境
conda create -n deploy python=3.10 -y
conda activate deploy

# 安装核心依赖
conda install -c conda-forge pythonocc-core=7.7.0 -y

# 安装PyTorch（根据CUDA版本选择）
# CPU版本
conda install pytorch torchvision torchaudio cpuonly -c pytorch -y

# 或GPU版本（CUDA 11.8）
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y

# 安装DGL
pip install dgl -f https://data.dgl.ai/wheels/repo.html

# 安装其他依赖
pip install -r requirements-full.txt
```

#### 📦 步骤3: 打包Conda环境

**方式A: 使用conda-pack（推荐）**

```bash
# 安装conda-pack
conda install conda-pack -y

# 打包环境
conda pack -n deploy -o deploy_env.tar.gz

# 查看大小
ls -lh deploy_env.tar.gz
# 预期大小: 2-5GB（取决于是否包含GPU版本PyTorch）
```

**方式B: 导出环境规格**

```bash
# 导出明确的包列表
conda list --explicit > deploy_env_spec.txt

# 同时下载所有包到本地
mkdir -p conda_packages
conda install --download-only -c conda-forge -c pytorch \
    --override-channels \
    --prefix ./conda_packages \
    $(cat deploy_env_spec.txt | grep -v "^#" | grep -v "^@")
```

**方式C: 下载独立的wheel文件**

```bash
# 创建下载目录
mkdir -p python_packages

# 下载所有pip依赖
pip download -r requirements-full.txt -d python_packages/

# 下载PyTorch（CPU版本，约800MB）
pip download torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu -d python_packages/

# 下载DGL
pip download dgl -f https://data.dgl.ai/wheels/repo.html -d python_packages/

# 查看下载的包
ls -lh python_packages/
du -sh python_packages/
```

#### 📥 步骤4: 下载项目代码和模型

```bash
# 1. 克隆或打包项目代码
cd /path/to/project
tar -czf deploy_code.tar.gz deploy/

# 2. 复制训练好的模型
cp experiments/classification/best_model/best_classifier.ckpt deploy/models/

# 3. 打包模型文件
tar -czf deploy_models.tar.gz deploy/models/
```

#### 🎨 步骤5: （可选）下载3D查看器依赖

**⚠️ 仅在需要3D预览功能时执行**

```bash
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
tar -xzf opencascade.js-2.0.0-beta.2.tgz
mkdir -p opencascade
cp -r package/dist/* opencascade/
rm -rf package opencascade.js-*.tgz

# 打包
cd ../..
tar -czf 3d_libs.tar.gz static/libs/

echo "✅ 3D查看器库已打包"
```

#### 📦 步骤6: 整理所有文件

创建一个总目录，包含所有需要传输的文件：

```bash
mkdir -p offline_deploy_package
cd offline_deploy_package

# 复制/移动所有打包文件
cp ../deploy_env.tar.gz .           # Conda环境（2-5GB）
cp ../deploy_code.tar.gz .          # 项目代码（<10MB）
cp ../deploy_models.tar.gz .        # 模型文件（大小取决于模型）
cp ../3d_libs.tar.gz .              # 3D库（可选，32MB）
cp ../requirements-full.txt .       # 依赖列表

# 创建安装说明
cat > README_OFFLINE.txt << 'EOF'
离线安装包文件清单
==================

必需文件:
1. deploy_env.tar.gz      - Python环境（2-5GB）
2. deploy_code.tar.gz     - 项目代码
3. deploy_models.tar.gz   - 训练好的模型
4. requirements-full.txt  - 依赖列表

可选文件:
5. 3d_libs.tar.gz        - 3D查看器库（如需3D预览）

安装步骤:
请参考 OFFLINE_INSTALL_GUIDE.md
EOF

# 查看总大小
du -sh .
ls -lh

echo "✅ 离线安装包准备完成"
```

---

## 传输文件

### 传输方式选择

根据文件大小和可用方式选择：

| 方式 | 适用大小 | 优缺点 |
|------|---------|--------|
| U盘/移动硬盘 | 任意 | ✅ 最简单，❌ 物理传输 |
| SCP/SFTP | <10GB | ✅ 快速，❌ 需要临时网络 |
| 内部文件服务器 | 任意 | ✅ 便捷，❌ 需要配置 |
| 光盘刻录 | <50GB | ✅ 可归档，❌ 速度慢 |

### 使用U盘传输（推荐）

```bash
# 1. 插入U盘，查找挂载点
lsblk
# 假设U盘是 /dev/sdb1

# 2. 挂载U盘
sudo mount /dev/sdb1 /mnt/usb

# 3. 复制文件
cp -r offline_deploy_package /mnt/usb/

# 4. 安全卸载
sync
sudo umount /mnt/usb

# 5. 在目标机器上复制
sudo mount /dev/sdb1 /mnt/usb
cp -r /mnt/usb/offline_deploy_package /opt/
cd /opt/offline_deploy_package
```

---

## 离线安装步骤

### 在离线服务器上执行

#### 1️⃣ 准备Python环境

```bash
# 检查是否已安装Python
python3 --version
# 需要 Python 3.10 或 3.11

# 如果没有，需要从安装包安装
# 需要提前下载Python安装包：
# https://www.python.org/downloads/
# 选择对应平台的离线安装包
```

#### 2️⃣ 解压Conda环境

```bash
cd /opt/offline_deploy_package

# 创建目标目录
mkdir -p /opt/envs/deploy

# 解压环境
tar -xzf deploy_env.tar.gz -C /opt/envs/deploy

# 激活环境
source /opt/envs/deploy/bin/activate

# 修复路径（conda-pack要求）
conda-unpack

# 验证
python --version
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import dgl; print(f'DGL: {dgl.__version__}')"
python -c "from OCC.Core.STEPControl import STEPControl_Reader; print('pythonocc-core: OK')"
```

#### 3️⃣ 部署项目代码

```bash
# 解压项目代码
tar -xzf deploy_code.tar.gz -C /opt/

# 解压模型文件
cd /opt/deploy
tar -xzf ../offline_deploy_package/deploy_models.tar.gz
```

#### 4️⃣ 配置系统

```bash
cd /opt/deploy

# 编辑配置文件
vi config.yaml
```

**关键配置项**:

```yaml
model:
  checkpoint_path: "models/best_classifier.ckpt"  # 确认路径正确
  device: "cpu"  # 或 "cuda" 如果有GPU
  graph_emb_dim: 256

ui:
  title: "3D BREP 模型智能分类系统"
  server_port: 7860
  share: false
  enable_3d_viewer: false  # ⚠️ 离线环境建议设为false
```

#### 5️⃣ （可选）配置3D查看器

**仅在需要且已下载JS库时执行**

```bash
# 解压3D库
cd /opt/deploy
tar -xzf ../offline_deploy_package/3d_libs.tar.gz

# 验证文件
ls -lh static/libs/three/
ls -lh static/libs/opencascade/

# 修改配置
vi config.yaml
```

```yaml
ui:
  enable_3d_viewer: true  # 启用3D查看器
```

修改 `ui/viewer3d.py`:

```python
# 在 create_step_viewer_html 函数中
# 找到 CDN 导入部分，改为：
USE_LOCAL_LIBS = True  # 强制使用本地库
```

---

## 验证和启动

### 验证安装

```bash
# 1. 验证Python环境
python -c "
import sys
import torch
import dgl
import gradio as gr
from OCC.Core.STEPControl import STEPControl_Reader

print('='*50)
print('环境验证')
print('='*50)
print(f'Python: {sys.version}')
print(f'PyTorch: {torch.__version__}')
print(f'DGL: {dgl.__version__}')
print(f'Gradio: {gr.__version__}')
print(f'pythonocc-core: OK')
print('='*50)
print('✅ 所有依赖验证通过')
"

# 2. 验证模型文件
ls -lh models/best_classifier.ckpt

# 3. 验证配置
python -c "from config import AppConfig; cfg = AppConfig.load(); print('✅ 配置文件加载成功')"

# 4. 测试导入
python -c "from src.inference import ModelInference; print('✅ 核心模块导入成功')"
```

### 启动应用

```bash
cd /opt/deploy

# 确保在正确的环境中
source /opt/envs/deploy/bin/activate

# 启动应用
python app.py

# 或指定参数
python app.py --port 7860 --device cpu

# 查看帮助
python app.py --help
```

### 访问应用

```bash
# 在服务器本地
http://localhost:7860

# 从其他机器访问（需要配置防火墙）
http://<服务器IP>:7860
```

### 配置为系统服务（可选）

```bash
# 创建systemd服务文件
sudo vi /etc/systemd/system/brep-classifier.service
```

```ini
[Unit]
Description=3D BREP Model Classifier
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/deploy
Environment="PATH=/opt/envs/deploy/bin"
ExecStart=/opt/envs/deploy/bin/python app.py --port 7860
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable brep-classifier
sudo systemctl start brep-classifier

# 查看状态
sudo systemctl status brep-classifier

# 查看日志
sudo journalctl -u brep-classifier -f
```

---

## 故障排查

### 问题1: conda-unpack命令不存在

**原因**: 环境打包时未包含conda-pack

**解决**:
```bash
# 跳过conda-unpack，手动修复路径
cd /opt/envs/deploy
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
```

### 问题2: Import Error: No module named 'xxx'

**原因**: 某个依赖未安装或版本不匹配

**解决**:
```bash
# 检查已安装的包
pip list | grep xxx

# 查看requirements
cat requirements-full.txt

# 如果有pip包文件，离线安装
pip install --no-index --find-links=../python_packages xxx
```

### 问题3: pythonocc-core导入失败

**原因**: pythonocc-core未正确安装（conda-pack可能有问题）

**解决**:
```bash
# 检查conda环境
conda list | grep pythonocc

# 如果不存在，需要重新打包或使用其他方式安装
# 参考：https://github.com/tpaviot/pythonocc-core
```

### 问题4: 模型加载失败

**原因**: 模型文件路径错误或版本不匹配

**解决**:
```bash
# 检查模型文件
ls -lh models/

# 检查配置
cat config.yaml | grep checkpoint_path

# 测试加载
python -c "
from src.inference import ModelInference
from config import AppConfig
cfg = AppConfig.load()
model = ModelInference(cfg)
print('✅ 模型加载成功')
"
```

### 问题5: 端口已被占用

**解决**:
```bash
# 查找占用端口的进程
lsof -i :7860
# 或
netstat -tulpn | grep 7860

# 杀掉进程或更改端口
python app.py --port 8080
```

### 问题6: 3D查看器无法加载

**原因**: JS库路径不正确或未启用本地模式

**解决**:
1. 确认已解压3D库到 `static/libs/`
2. 确认修改了 `ui/viewer3d.py` 使用本地库
3. 或者禁用3D查看器：`config.yaml` 中设置 `enable_3d_viewer: false`

---

## 📊 依赖包大小参考

| 包/组件 | 大小 | 说明 |
|---------|------|------|
| Conda环境（CPU） | ~2.5GB | 包含所有Python依赖 |
| Conda环境（GPU） | ~4.5GB | 包含CUDA和cuDNN |
| 项目代码 | <10MB | Python源代码 |
| 模型文件 | 50-200MB | 取决于模型大小 |
| 3D查看器库 | ~32MB | 可选 |
| **总计** | **2.5-5GB** | 取决于配置 |

---

## 📞 技术支持

如遇到问题：

1. 查看日志文件
2. 检查环境变量和路径
3. 参考本文档的故障排查部分
4. 联系技术支持团队

---

## 📝 检查清单

部署前检查：

- [ ] Python 3.10/3.11 已安装
- [ ] 所有tar.gz文件已传输
- [ ] 有足够的磁盘空间（50GB+）
- [ ] 防火墙已配置（如需远程访问）

安装后验证：

- [ ] Python环境激活成功
- [ ] 所有依赖导入正常
- [ ] 模型文件存在且可加载
- [ ] 配置文件正确
- [ ] Web界面可访问
- [ ] 测试STEP文件分类正常

---

## 🎯 性能优化建议

### CPU优化
```bash
# 设置OpenMP线程数
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

# 启动应用
python app.py
```

### GPU优化
```bash
# 设置GPU设备
export CUDA_VISIBLE_DEVICES=0

# 启动应用
python app.py --device cuda
```

### 内存优化
```python
# 在config.yaml中
model:
  batch_size: 1  # 减小batch size
  num_workers: 2  # 减少worker数量
```

---

祝部署顺利！🚀

