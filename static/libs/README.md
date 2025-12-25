# JavaScript库目录

## ✅ 安装状态

**已安装**: 2024-12-19

| 库名 | 版本 | 大小 | 状态 |
|------|------|------|------|
| Three.js | 0.150.0 | 17MB | ✅ 已安装 |
| opencascade.js | 1.1.1 | 64MB | ✅ 已安装 |

**总大小**: 81MB

## 📁 目录结构

```
libs/
├── three/
│   ├── three.module.js          - Three.js核心模块 (1.2MB)
│   └── jsm/                     - 扩展模块 (16MB)
│       └── controls/
│           └── OrbitControls.js - 相机控制
└── opencascade/
    ├── opencascade.wasm.js      - JS胶水代码 (324KB)
    ├── opencascade.wasm.wasm    - WASM主模块 (63MB)
    └── Supported APIs.md        - API文档 (342KB)
```

## 🔄 更新库

如需更新到最新版本：

```bash
cd /root/workspace/deploy/static/libs

# 更新Three.js
rm -rf three
npm pack three@latest
tar -xzf three-*.tgz
mkdir -p three
cp package/build/three.module.js three/
cp -r package/examples/jsm three/
rm -rf package three-*.tgz

# 更新opencascade.js
rm -rf opencascade
npm pack opencascade.js@latest
tar -xzf opencascade.js-*.tgz
mkdir -p opencascade
cp -r package/dist/* opencascade/
rm -rf package opencascade.js-*.tgz

echo "✅ 更新完成"
```

## 📝 使用说明

这些库已被 `ui/viewer3d.py` 使用，通过Gradio的 `/file=` 路径访问。

**代码中的导入路径**:
```javascript
import * as THREE from '/file=/root/workspace/deploy/static/libs/three/three.module.js';
import { OrbitControls } from '/file=/root/workspace/deploy/static/libs/three/jsm/controls/OrbitControls.js';
const { default: initOpenCascade } = await import('/file=/root/workspace/deploy/static/libs/opencascade/opencascade.wasm.js');
```

## ⚠️ 注意事项

1. **不要删除此目录**: 3D查看器功能依赖这些文件
2. **Git忽略**: 这些文件已添加到 `.gitignore`，不会被提交
3. **离线可用**: 无需网络连接即可使用3D预览功能

## 📚 相关文档

- [INSTALLATION_STATUS.md](../../INSTALLATION_STATUS.md) - 安装状态
- [3D_VIEWER_OFFLINE_SETUP.md](../../docs/3D_VIEWER_OFFLINE_SETUP.md) - 配置指南
