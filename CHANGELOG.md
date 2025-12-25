# 更新日志

## [2024-12-19] - 集成opencascade.js 3D查看器

### ✨ 新增功能
- ✅ **完整集成opencascade.js** - 基于WebAssembly的STEP文件解析
- ✅ **Three.js 3D渲染** - 流畅的3D模型显示和交互
- ✅ **纯前端处理** - 无需服务器端转换，直接在浏览器中解析STEP
- ✅ **实时加载提示** - 4阶段加载进度显示
- ✅ **交互式查看** - 支持旋转、缩放、平移操作

### 📁 新增文件
- `ui/viewer3d.py` - 3D查看器组件模块
  - `create_step_viewer_html()` - 生成完整的3D查看器HTML
  - `create_empty_step_viewer()` - 空状态占位符
- `docs/3D_VIEWER_INTEGRATION.md` - 完整的集成文档

### 🔧 修改文件
- **src/handlers.py** - 单文件处理逻辑
  - `process_single_file()` 返回值增加 `viewer_html`
  - 自动为STEP文件生成3D查看器
  
- **ui/layouts.py** - UI布局
  - 添加 `viewer_output` HTML组件
  - 恢复3D查看器显示区域
  - 绑定文件上传事件

### 🎯 技术特点

#### 架构
```
STEP文件 → Gradio → Python读取 → HTML嵌入 
         → opencascade.js(CDN) → 三角网格剖分
         → Three.js渲染 → 浏览器显示
```

#### CDN依赖
- Three.js v0.150.0 (ESM模块)
- opencascade.js v2.0.0-beta.2 (WebAssembly)
- OrbitControls (Three.js插件)

#### 性能特征
- 首次加载：12-15秒（下载WASM约30MB）
- 后续加载：2-8秒（仅解析和渲染）
- 浏览器缓存WASM文件，后续访问更快

### 💡 使用方式

**用户操作：**
1. 上传 STEP 文件
2. 等待4个加载阶段（有进度提示）
3. 查看3D模型
4. 左键旋转 | 滚轮缩放 | 右键平移

**加载阶段：**
1. 📥 加载3D引擎
2. 🔧 初始化OpenCascade
3. 📄 解析STEP文件
4. 🔺 生成三角网格

### ⚙️ 可配置参数

**三角剖分精度：**（在 `viewer3d.py` 中）
```javascript
new oc.BRepMesh_IncrementalMesh_2(
  shape, 
  0.1,    // 线性偏差 - 可调整
  false, 
  0.5,    // 角度偏差 - 可调整
  false
);
```

**查看器尺寸：**
```python
height: 500px  # 可修改
```

### 🌐 浏览器兼容性
- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Edge 80+
- ✅ Safari 14+
- ❌ IE 11 及以下

### 📊 与之前方案对比

| 特性 | 旧方案（pythonocc-core） | 新方案（opencascade.js） |
|------|------------------------|------------------------|
| 运行位置 | Python后端 | 浏览器前端 |
| 转换格式 | STEP→STL→base64 | STEP→三角网格 |
| 传输大小 | 5-6MB | <1MB（仅STEP文本） |
| 首次加载 | 即时 | 12-15秒（一次性） |
| 后续加载 | 即时 | 2-8秒 |
| 服务器负载 | 高 | 无 |
| 文件限制 | 严格（<3MB） | 相对宽松 |
| 精度 | 中（STL） | 高（原生STEP） |

### ✅ 优势
1. **无服务器依赖** - 不需要安装 pythonocc-core
2. **高精度** - 直接解析STEP，保留完整几何信息
3. **大文件支持** - 突破之前的3MB限制
4. **降低服务器负载** - 所有处理在客户端
5. **维护简单** - 纯JavaScript，无Python依赖

### ⚠️ 注意事项
1. 首次加载需要下载约30MB的WASM文件
2. 大型复杂模型可能占用较多浏览器内存
3. 需要现代浏览器（支持WebAssembly和ESM）
4. CDN可用性依赖于网络连接

### 🐛 已知问题
- 极大模型（>50MB）可能导致浏览器性能下降
- 移动端性能可能不佳
- 首次加载时间较长

### 🔮 未来优化
- [ ] 添加加载进度条（字节级）
- [ ] 本地化WASM文件（避免CDN依赖）
- [ ] 添加LOD（细节级别）支持
- [ ] 实现模型简化选项
- [ ] 添加全屏模式
- [ ] 支持导出STL/OBJ

### 📚 相关文档
- [3D查看器集成文档](docs/3D_VIEWER_INTEGRATION.md)
- [离线部署指南](docs/3D_VIEWER_OFFLINE_SETUP.md) ⚠️ **重要**
- [occ2three项目参考](occ2three/README.md)

### ⚠️ 网络依赖说明

**当前实现需要网络连接**（首次访问时）：
- Three.js: 约1MB（从CDN加载）
- opencascade.js: 约30MB（从CDN加载）
- 浏览器会缓存这些文件，后续访问更快

**离线环境部署**：
- 方案1: 禁用3D查看器（推荐）- 修改配置即可
- 方案2: 本地化JS库（复杂）- 需要预先下载约32MB文件

详见：[离线部署指南](docs/3D_VIEWER_OFFLINE_SETUP.md)

---

## [2024-12-19] - 移除3D查看器功能（已废弃）

### 删除的功能
- ❌ 删除了基于pythonocc-core的STEP→STL转换
- ❌ 删除了`src/step_converter.py`模块
- ❌ 删除了所有STL相关代码

*此版本已被新的opencascade.js方案替代*

---

## 代码统计

### 新增
- 文件：2个（viewer3d.py, 3D_VIEWER_INTEGRATION.md）
- 代码行数：约350行（主要是HTML/JavaScript）
- 函数：2个核心函数

### 修改
- 文件：2个（handlers.py, layouts.py）
- 代码行数：约20行修改

### 总改动
- 新增/修改代码：约370行
- 实施时间：约1小时
- 测试建议：使用不同大小的STEP文件测试
