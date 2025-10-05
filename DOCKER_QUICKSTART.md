# 🚀 Docker 快速啟動

## 最快速的方式

```bash
# 1. 使用互動式腳本（推薦）
./docker-start.sh

# 2. 或直接使用命令
docker-compose up -d
```

然後訪問：http://localhost:8082

---

## 📋 常用命令速查表

| 操作 | 命令 |
|------|------|
| **構建映像** | `docker-compose build` |
| **啟動容器** | `docker-compose up -d` |
| **停止容器** | `docker-compose down` |
| **查看日誌** | `docker-compose logs -f` |
| **查看狀態** | `docker-compose ps` |
| **重啟容器** | `docker-compose restart` |
| **進入容器** | `docker-compose exec stl-detection bash` |

---

## 🎯 一鍵部署

```bash
# 完整流程（首次使用）
docker-compose build && docker-compose up -d && docker-compose logs -f
```

---

## 🛑 停止和清理

```bash
# 停止容器
docker-compose down

# 完全清理（包含映像）
docker-compose down
docker rmi stl-detection:latest
docker system prune -f
```

---

## 🔧 問題排查

### 容器無法啟動？
```bash
# 查看詳細日誌
docker-compose logs

# 檢查端口
netstat -tuln | grep 8082
```

### 權限問題？
```bash
# 修正權限
chmod -R 755 STL dataset runs static
```

### 重建容器？
```bash
# 完全重建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 📊 效能監控

```bash
# 查看資源使用
docker stats stl-object-detection

# 查看健康狀態
docker inspect --format='{{.State.Health.Status}}' stl-object-detection
```

---

## 💡 提示

- 首次啟動需要下載依賴，約需 3-5 分鐘
- 建議分配至少 4GB RAM
- 資料會持久化保存在主機目錄
- 詳細文檔請參考 `DOCKER_README.md`