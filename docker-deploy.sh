#!/bin/bash
# STL 物件識別系統 - Docker 快速部署腳本
# 版本: 2.0
# 作者: Claude Code

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函數：顯示彩色訊息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 函數：顯示橫幅
show_banner() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  STL 物件識別系統 - Docker 部署工具"
    echo "  版本: 2.0"
    echo "=============================================="
    echo -e "${NC}"
}

# 函數：檢查 Docker 環境
check_docker() {
    print_info "檢查 Docker 環境..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安裝，請先安裝 Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安裝，請先安裝 Docker Compose"
        exit 1
    fi

    print_success "Docker 環境檢查通過"
    docker --version
    docker compose version 2>/dev/null || docker-compose --version
}

# 函數：創建必要目錄
create_directories() {
    print_info "創建必要的目錄結構..."

    mkdir -p STL dataset yolo_dataset runs models logs training_logs web_uploads static
    mkdir -p yolo_dataset/train/{images,labels}
    mkdir -p yolo_dataset/val/{images,labels}

    print_success "目錄結構已創建"
}

# 函數：構建 Docker 映像
build_image() {
    print_info "開始構建 Docker 映像（這可能需要 5-10 分鐘）..."

    # 使用 docker-compose 構建
    if docker compose version &> /dev/null; then
        docker compose build --no-cache
    else
        docker-compose build --no-cache
    fi

    print_success "Docker 映像構建完成"
}

# 函數：啟動容器
start_container() {
    print_info "啟動 STL 物件識別系統容器..."

    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi

    print_success "容器已啟動"
}

# 函數：顯示容器狀態
show_status() {
    print_info "容器狀態："
    echo ""
    docker ps -a --filter "name=stl-object-detection" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
}

# 函數：顯示日誌
show_logs() {
    print_info "容器啟動日誌（按 Ctrl+C 退出）："
    echo ""

    if docker compose version &> /dev/null; then
        docker compose logs -f --tail=50
    else
        docker-compose logs -f --tail=50
    fi
}

# 函數：等待容器健康
wait_for_health() {
    print_info "等待容器完全啟動（最多 120 秒）..."

    local max_wait=120
    local elapsed=0

    while [ $elapsed -lt $max_wait ]; do
        health=$(docker inspect --format='{{.State.Health.Status}}' stl-object-detection 2>/dev/null || echo "starting")

        if [ "$health" = "healthy" ]; then
            print_success "容器已完全啟動並運行正常！"
            return 0
        fi

        echo -ne "⏳ 等待中... ${elapsed}s / ${max_wait}s\r"
        sleep 5
        elapsed=$((elapsed + 5))
    done

    print_warning "容器啟動超時，但可能仍在正常運行"
    return 1
}

# 函數：顯示訪問資訊
show_access_info() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  🎉 STL 物件識別系統部署成功！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}📡 訪問方式：${NC}"
    echo "   🌐 本地訪問：http://localhost:5000"
    echo "   🌐 區域網訪問：http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    echo -e "${BLUE}🛠️  常用指令：${NC}"
    echo "   查看日誌：docker logs -f stl-object-detection"
    echo "   停止容器：docker-compose down"
    echo "   重啟容器：docker-compose restart"
    echo "   進入容器：docker exec -it stl-object-detection bash"
    echo ""
    echo -e "${BLUE}📂 資料目錄：${NC}"
    echo "   STL 檔案：./STL/"
    echo "   資料集：./dataset/"
    echo "   訓練結果：./runs/"
    echo "   日誌：./logs/"
    echo ""
    echo -e "${YELLOW}⚠️  注意事項：${NC}"
    echo "   - 首次啟動可能需要 1-2 分鐘"
    echo "   - 訓練模型需要較多資源，建議至少 4GB RAM"
    echo "   - STL 檔案請放置在 ./STL/ 目錄下"
    echo ""
}

# 主函數
main() {
    show_banner

    # 解析命令行參數
    case "${1:-}" in
        build)
            check_docker
            create_directories
            build_image
            ;;
        start)
            check_docker
            start_container
            show_status
            wait_for_health
            show_access_info
            ;;
        restart)
            print_info "重啟容器..."
            if docker compose version &> /dev/null; then
                docker compose restart
            else
                docker-compose restart
            fi
            show_status
            ;;
        stop)
            print_info "停止容器..."
            if docker compose version &> /dev/null; then
                docker compose down
            else
                docker-compose down
            fi
            print_success "容器已停止"
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        clean)
            print_warning "清理所有容器和映像（資料不會被刪除）..."
            read -p "確定要繼續嗎？(y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                if docker compose version &> /dev/null; then
                    docker compose down -v --rmi all
                else
                    docker-compose down -v --rmi all
                fi
                print_success "清理完成"
            else
                print_info "已取消"
            fi
            ;;
        *)
            # 預設：完整部署流程
            check_docker
            create_directories
            build_image
            start_container
            show_status
            wait_for_health
            show_access_info

            # 詢問是否查看日誌
            echo ""
            read -p "是否查看即時日誌？(y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                show_logs
            fi
            ;;
    esac
}

# 腳本使用說明
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "STL 物件識別系統 - Docker 部署腳本"
    echo ""
    echo "使用方式："
    echo "  ./docker-deploy.sh           # 完整部署（構建 + 啟動）"
    echo "  ./docker-deploy.sh build     # 只構建映像"
    echo "  ./docker-deploy.sh start     # 只啟動容器"
    echo "  ./docker-deploy.sh restart   # 重啟容器"
    echo "  ./docker-deploy.sh stop      # 停止容器"
    echo "  ./docker-deploy.sh logs      # 查看日誌"
    echo "  ./docker-deploy.sh status    # 查看狀態"
    echo "  ./docker-deploy.sh clean     # 清理容器和映像"
    echo ""
    exit 0
fi

# 執行主函數
main "$@"