# 静态资源目录

此目录用于存放3D查看器所需的JavaScript库（离线部署时使用）。

## 📁 目录结构

```
static/
├── README.md           # 本文件
└── libs/               # JavaScript库（需要手动下载）
    ├── three/          # Three.js (约1.5MB)
    └── opencascade/    # opencascade.js (约31MB)
```

## 🌐 在线模式（默认）

默认情况下，应用从CDN加载JavaScript库，**不需要**此目录中的文件。

## 🔌 离线模式

如果需要在**无网络环境**中部署，需要预先下载JS库到此目录。

### 下载步骤

详见：[离线部署指南](../docs/3D_VIEWER_OFFLINE_SETUP.md)

### 快速下载（在有网络的环境中执行）

```bash
cd libs/
./download_libs.sh
```

下载后的文件约 **32 MB**。

## ⚠️ 注意事项

1. **此目录中的文件不会被Git追踪**（已添加到.gitignore）
2. 如果只需要分类功能，可以完全删除此目录
3. 离线部署还需要修改代码中的导入路径

## 📚 相关文档

- [3D查看器集成文档](../docs/3D_VIEWER_INTEGRATION.md)
- [离线部署指南](../docs/3D_VIEWER_OFFLINE_SETUP.md)

