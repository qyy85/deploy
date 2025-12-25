#!/bin/bash
# 使用现有镜像创建容器，自动执行 run.sh
# ========================================

# 配置
CONTAINER_NAME="brep-classifier"
IMAGE_NAME="python:3.10-slim"  # 可以改为任何现有镜像
PROJECT_ROOT="/root/workspace"
PORT=5001

# 删除已存在的容器（如果有）
docker rm -f ${CONTAINER_NAME} 2>/dev/null || true

# 创建容器，设置启动命令为 run.sh
docker run -d \
  --name ${CONTAINER_NAME} \
  --restart always \
  -p ${PORT}:${PORT} \
  -v ${PROJECT_ROOT}:/app \
  -w /app \
  -e DOCKER_CONTAINER=1 \
  ${IMAGE_NAME} \
  bash -c "
    # 确保脚本可执行
    chmod +x /app/deploy/run.sh
    # 执行启动脚本
    exec /app/deploy/run.sh
  "

echo "容器已创建并启动"
echo "查看日志: docker logs -f ${CONTAINER_NAME}"

