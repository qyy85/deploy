#!/bin/bash
# 3D BREP 模型分类系统启动脚本
# ========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           3D BREP 模型智能分类系统                              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 检查Python环境
echo -e "${YELLOW}[1/4] 检查Python环境...${NC}"
if ! command -v python &> /dev/null; then
    echo -e "${RED}错误: 未找到Python，请先安装Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python版本: $PYTHON_VERSION${NC}"

# 检查依赖
echo -e "${YELLOW}[2/4] 检查依赖...${NC}"

check_package() {
    python -c "import $1" 2>/dev/null
    return $?
}

MISSING_DEPS=""

if ! check_package "gradio"; then
    MISSING_DEPS="$MISSING_DEPS gradio"
fi

if ! check_package "onnxruntime"; then
    MISSING_DEPS="$MISSING_DEPS onnxruntime"
fi

if ! check_package "torch"; then
    MISSING_DEPS="$MISSING_DEPS torch"
fi

if ! check_package "dgl"; then
    MISSING_DEPS="$MISSING_DEPS dgl"
fi

if [ -n "$MISSING_DEPS" ]; then
    echo -e "${YELLOW}警告: 缺少以下依赖:$MISSING_DEPS${NC}"
    echo -e "${YELLOW}尝试安装...${NC}"
    pip install -r deploy/requirements.txt
fi

echo -e "${GREEN}✓ 依赖检查完成${NC}"

# 检查模型文件
echo -e "${YELLOW}[3/4] 检查模型文件...${NC}"

if [ -f "deploy/models/classifier.onnx" ]; then
    echo -e "${GREEN}✓ 分类器ONNX模型已就绪${NC}"
else
    echo -e "${YELLOW}⚠ 未找到ONNX模型，将以演示模式运行${NC}"
    echo -e "${YELLOW}  如需完整功能，请先导出模型:${NC}"
    echo -e "${YELLOW}  python -m deploy.core.onnx_exporter --checkpoint <检查点路径> --output deploy/models/ --full-pipeline${NC}"
fi

# 解析参数
PORT=5000
SHARE=false
DEVICE="cpu"

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --share)
            SHARE=true
            shift
            ;;
        --gpu)
            DEVICE="cuda"
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --port <端口>    指定服务端口 (默认: 7860)"
            echo "  --share          生成公网共享链接"
            echo "  --gpu            使用GPU推理"
            echo "  --help, -h       显示帮助信息"
            exit 0
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            exit 1
            ;;
    esac
done

# 启动应用
echo -e "${YELLOW}[4/4] 启动Web应用...${NC}"
echo ""

SHARE_FLAG=""
if [ "$SHARE" = true ]; then
    SHARE_FLAG="--share"
fi

echo -e "${GREEN}启动参数:${NC}"
echo -e "  端口: $PORT"
echo -e "  设备: $DEVICE"
echo -e "  共享: $SHARE"
echo ""

python -m deploy.app --port $PORT --device $DEVICE $SHARE_FLAG

