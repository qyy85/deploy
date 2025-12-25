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

# 项目根目录 (deploy目录)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           3D BREP 模型智能分类系统                              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 切换到deploy目录
cd "$SCRIPT_DIR"

# 激活虚拟环境dgl
echo -e "${YELLOW}[1/5] 激活虚拟环境dgl...${NC}"
if [ -n "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" = "dgl" ]; then
    echo -e "${GREEN}✓ 已在dgl环境中${NC}"
elif command -v conda &> /dev/null; then
    # 尝试使用conda激活
    if conda env list | grep -q "^dgl "; then
        echo -e "${GREEN}激活conda环境: dgl${NC}"
        eval "$(conda shell.bash hook)"
        conda activate dgl
        echo -e "${GREEN}✓ conda环境dgl已激活${NC}"
    else
        echo -e "${YELLOW}⚠ 未找到conda环境dgl，尝试其他方式...${NC}"
        # 尝试查找并激活虚拟环境
        if [ -f "$HOME/anaconda3/envs/dgl/bin/activate" ] || [ -f "$HOME/miniconda3/envs/dgl/bin/activate" ]; then
            ENV_PATH=$(find "$HOME" -name "activate" -path "*/envs/dgl/bin/activate" 2>/dev/null | head -1)
            if [ -n "$ENV_PATH" ]; then
                source "$ENV_PATH"
                echo -e "${GREEN}✓ 虚拟环境dgl已激活${NC}"
            else
                echo -e "${YELLOW}⚠ 无法自动激活dgl环境，请手动激活后运行此脚本${NC}"
            fi
        else
            echo -e "${YELLOW}⚠ 无法找到dgl环境，请确保已创建并激活dgl虚拟环境${NC}"
        fi
    fi
else
    # 尝试使用venv/virtualenv
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✓ 本地虚拟环境已激活${NC}"
    else
        echo -e "${YELLOW}⚠ 未找到conda，尝试查找其他虚拟环境...${NC}"
        # 尝试查找常见的虚拟环境路径
        for env_path in "$HOME/anaconda3/envs/dgl" "$HOME/miniconda3/envs/dgl" "/opt/conda/envs/dgl"; do
            if [ -d "$env_path" ] && [ -f "$env_path/bin/activate" ]; then
                source "$env_path/bin/activate"
                echo -e "${GREEN}✓ 虚拟环境dgl已激活 (路径: $env_path)${NC}"
                break
            fi
        done
    fi
fi

# 检查Python环境
echo -e "${YELLOW}[2/5] 检查Python环境...${NC}"
if ! command -v python &> /dev/null; then
    echo -e "${RED}错误: 未找到Python，请先安装Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python版本: $PYTHON_VERSION${NC}"

# 读取配置文件并检查端口
echo -e "${YELLOW}[3/5] 检查配置文件端口...${NC}"
CONFIG_FILE="config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠ 配置文件不存在: $CONFIG_FILE，使用默认端口${NC}"
    DEFAULT_PORT=5000
else
    # 使用python读取yaml文件中的端口
    DEFAULT_PORT=$(python -c "
import sys
try:
    import yaml
    with open('$CONFIG_FILE', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        port = config.get('ui', {}).get('server_port', 5000)
        print(port)
except ImportError:
    # 如果没有yaml模块，尝试使用正则表达式简单解析
    try:
        import re
        with open('$CONFIG_FILE', 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'server_port:\s*(\d+)', content)
            if match:
                print(match.group(1))
            else:
                print('5000')
    except:
        print('5000')
except Exception:
    print('5000')
" 2>/dev/null || echo "5000")
    
    if [ -z "$DEFAULT_PORT" ]; then
        DEFAULT_PORT=5000
    fi
    echo -e "${GREEN}✓ 配置文件端口: $DEFAULT_PORT${NC}"
fi

# 检查端口是否可用
check_port() {
    local port=$1
    if command -v netstat &> /dev/null; then
        netstat -tuln 2>/dev/null | grep -q ":$port " && return 1
    elif command -v ss &> /dev/null; then
        ss -tuln 2>/dev/null | grep -q ":$port " && return 1
    elif command -v lsof &> /dev/null; then
        lsof -i :$port &> /dev/null && return 1
    else
        # 尝试使用python检查端口
        python -c "
import socket
import sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(('', $port))
    s.close()
    sys.exit(0)
except OSError:
    sys.exit(1)
" 2>/dev/null && return 0 || return 1
    fi
    return 0
}

if ! check_port "$DEFAULT_PORT"; then
    echo -e "${RED}错误: 端口 $DEFAULT_PORT 已被占用，请修改配置文件 $CONFIG_FILE 中的 ui.server_port 或释放该端口${NC}"
    echo -e "${YELLOW}提示: 可以使用以下命令查看端口占用情况:${NC}"
    echo -e "${YELLOW}  - netstat -tuln | grep $DEFAULT_PORT${NC}"
    echo -e "${YELLOW}  - ss -tuln | grep $DEFAULT_PORT${NC}"
    echo -e "${YELLOW}  - lsof -i :$DEFAULT_PORT${NC}"
    exit 1
else
    echo -e "${GREEN}✓ 端口 $DEFAULT_PORT 可用${NC}"
fi

# 检查模型文件
echo -e "${YELLOW}[4/5] 检查模型文件...${NC}"

if [ -f "models/classifier.onnx" ]; then
    echo -e "${GREEN}✓ 分类器ONNX模型已就绪${NC}"
else
    echo -e "${YELLOW}⚠ 未找到ONNX模型，将以演示模式运行${NC}"
    echo -e "${YELLOW}  如需完整功能，请先导出模型:${NC}"
    echo -e "${YELLOW}  python -m deploy.core.onnx_exporter --checkpoint <检查点路径> --output models/ --full-pipeline${NC}"
fi

# 解析参数
PORT=$DEFAULT_PORT
SHARE=false
DEVICE="cpu"

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            # 检查用户指定的端口是否可用
            if ! check_port "$PORT"; then
                echo -e "${RED}错误: 端口 $PORT 已被占用，请选择其他端口${NC}"
                exit 1
            else
                echo -e "${GREEN}✓ 用户指定端口 $PORT 可用${NC}"
            fi
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
            echo "  --port <端口>    指定服务端口 (默认: 从config.yaml读取)"
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
echo -e "${YELLOW}[5/5] 启动Web应用...${NC}"
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

python app.py --port $PORT --device $DEVICE $SHARE_FLAG

