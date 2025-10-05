#!/bin/bash

# STL 物件識別系統 - Docker 快速啟動腳本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 顯示 Logo
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║     STL 物件識別系統 - Docker 部署工具               ║
║                                                       ║
║     STL Object Detection System                      ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# 檢查 Docker 是否安裝
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 錯誤: Docker 未安裝${NC}"
    echo "請先安裝 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 檢查 Docker Compose 是否安裝
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ 錯誤: Docker Compose 未安裝${NC}"
    echo "請先安裝 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# 使用 docker-compose 或 docker compose
DOCKER_COMPOSE="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
fi

# 選單函數
show_menu() {
    echo -e "${BLUE}請選擇操作：${NC}"
    echo "1) 🚀 構建並啟動容器"
    echo "2) ▶️  啟動已存在的容器"
    echo "3) ⏹️  停止容器"
    echo "4) 🔄 重啟容器"
    echo "5) 📋 查看日誌"
    echo "6) 🔍 查看容器狀態"
    echo "7) 💻 進入容器終端"
    echo "8) 🗑️  停止並刪除容器"
    echo "9) 🧹 完整清理（包含映像）"
    echo "0) 🚪 退出"
    echo ""
    read -p "請輸入選項 [0-9]: " choice
}

# 構建並啟動
build_and_start() {
    echo -e "${YELLOW}📦 開始構建 Docker 映像...${NC}"
    $DOCKER_COMPOSE build

    echo -e "${YELLOW}🚀 啟動容器...${NC}"
    $DOCKER_COMPOSE up -d

    echo -e "${GREEN}✅ 容器已啟動！${NC}"
    echo -e "${BLUE}🌐 訪問地址: http://localhost:8082${NC}"

    echo -e "${YELLOW}⏳ 等待服務啟動（約30秒）...${NC}"
    sleep 5

    echo -e "${BLUE}📊 查看實時日誌...${NC}"
    $DOCKER_COMPOSE logs -f
}

# 啟動容器
start_container() {
    echo -e "${YELLOW}▶️  啟動容器...${NC}"
    $DOCKER_COMPOSE up -d

    echo -e "${GREEN}✅ 容器已啟動！${NC}"
    echo -e "${BLUE}🌐 訪問地址: http://localhost:8082${NC}"
}

# 停止容器
stop_container() {
    echo -e "${YELLOW}⏹️  停止容器...${NC}"
    $DOCKER_COMPOSE stop

    echo -e "${GREEN}✅ 容器已停止${NC}"
}

# 重啟容器
restart_container() {
    echo -e "${YELLOW}🔄 重啟容器...${NC}"
    $DOCKER_COMPOSE restart

    echo -e "${GREEN}✅ 容器已重啟${NC}"
}

# 查看日誌
view_logs() {
    echo -e "${BLUE}📋 實時日誌（按 Ctrl+C 退出）：${NC}"
    $DOCKER_COMPOSE logs -f
}

# 查看狀態
view_status() {
    echo -e "${BLUE}🔍 容器狀態：${NC}"
    $DOCKER_COMPOSE ps

    echo ""
    echo -e "${BLUE}💾 磁碟使用：${NC}"
    docker system df

    echo ""
    echo -e "${BLUE}🏥 健康檢查：${NC}"
    docker inspect --format='{{.State.Health.Status}}' stl-object-detection 2>/dev/null || echo "容器未運行"
}

# 進入終端
enter_terminal() {
    echo -e "${BLUE}💻 進入容器終端（輸入 exit 退出）：${NC}"
    $DOCKER_COMPOSE exec stl-detection bash || echo -e "${RED}容器未運行或無法連接${NC}"
}

# 停止並刪除
stop_and_remove() {
    echo -e "${YELLOW}🗑️  停止並刪除容器...${NC}"
    $DOCKER_COMPOSE down

    echo -e "${GREEN}✅ 容器已刪除${NC}"
}

# 完整清理
full_cleanup() {
    echo -e "${RED}⚠️  警告：這將刪除容器、映像和未使用的資源！${NC}"
    read -p "確定要繼續嗎？ (y/N): " confirm

    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        echo -e "${YELLOW}🧹 停止並刪除容器...${NC}"
        $DOCKER_COMPOSE down

        echo -e "${YELLOW}🗑️  刪除映像...${NC}"
        docker rmi stl-detection:latest 2>/dev/null || echo "映像不存在"

        echo -e "${YELLOW}🧹 清理未使用的資源...${NC}"
        docker system prune -f

        echo -e "${GREEN}✅ 清理完成${NC}"
    else
        echo -e "${BLUE}已取消${NC}"
    fi
}

# 主循環
while true; do
    show_menu

    case $choice in
        1)
            build_and_start
            ;;
        2)
            start_container
            ;;
        3)
            stop_container
            ;;
        4)
            restart_container
            ;;
        5)
            view_logs
            ;;
        6)
            view_status
            ;;
        7)
            enter_terminal
            ;;
        8)
            stop_and_remove
            ;;
        9)
            full_cleanup
            ;;
        0)
            echo -e "${GREEN}👋 再見！${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ 無效的選項，請重試${NC}"
            ;;
    esac

    echo ""
    read -p "按 Enter 繼續..."
    clear
done