# STL 物件識別系統 - Docker 部署指南

## 📦 快速開始

### 1. 構建 Docker 映像

```bash
# 方法一：使用 Docker Compose（推薦）
docker-compose build

# 方法二：直接使用 Docker
docker build -t stl-detection:latest .
```

### 2. 啟動容器

```bash
# 方法一：使用 Docker Compose（推薦）
docker-compose up -d

# 方法二：直接使用 Docker
docker run -d \
  --name stl-object-detection \
  -p 8082:8082 \
  -v $(pwd)/STL:/app/STL \
  -v $(pwd)/dataset:/app/dataset \
  -v $(pwd)/yolo_dataset:/app/yolo_dataset \
  -v $(pwd)/runs:/app/runs \
  -v $(pwd)/static/uploads:/app/static/uploads \
  stl-detection:latest
```

### 3. 訪問系統

瀏覽器打開：http://localhost:8082

## 🛠️ 常用命令

### 查看容器狀態
```bash
docker-compose ps
# 或
docker ps | grep stl
```

### 查看日誌
```bash
docker-compose logs -f
# 或
docker logs -f stl-object-detection
```

### 停止容器
```bash
docker-compose down
# 或
docker stop stl-object-detection
```

### 重啟容器
```bash
docker-compose restart
# 或
docker restart stl-object-detection
```

### 進入容器
```bash
docker-compose exec stl-detection bash
# 或
docker exec -it stl-object-detection bash
```

### 清理容器和映像
```bash
# 停止並移除容器
docker-compose down

# 移除映像
docker rmi stl-detection:latest

# 清理所有未使用的資源
docker system prune -a
```

## 📂 資料持久化

以下目錄會掛載到主機，確保資料持久化：

- `./STL` - STL 3D 模型檔案
- `./dataset` - 生成的訓練資料集
- `./yolo_dataset` - YOLO 格式資料集
- `./runs` - 訓練結果和模型
- `./static/uploads` - 使用者上傳的檔案
- `./logs` - 應用程式日誌

## 🔧 配置選項

### 修改端口

在 `docker-compose.yml` 中修改：
```yaml
ports:
  - "8082:8082"  # 改為 "你的端口:8082"
```

### 資源限制

在 `docker-compose.yml` 中調整：
```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # CPU 核心數
      memory: 8G       # 記憶體上限
```

### 環境變數

在 `docker-compose.yml` 中添加：
```yaml
environment:
  - PYTHONUNBUFFERED=1
  - TZ=Asia/Taipei
  - YOUR_CUSTOM_VAR=value
```

## 🐛 故障排除

### 1. 容器無法啟動

```bash
# 查看詳細日誌
docker-compose logs

# 檢查端口是否被佔用
netstat -tuln | grep 8082
```

### 2. 權限問題

```bash
# 修正目錄權限
chmod -R 755 STL dataset runs static

# 或進入容器修正
docker-compose exec stl-detection bash
chown -R $(id -u):$(id -g) /app
```

### 3. 模型載入失敗

確保 `runs/detect/` 目錄中有訓練好的模型：
```bash
ls -la runs/detect/*/weights/best.pt
```

### 4. 記憶體不足

調整 docker-compose.yml 中的記憶體限制：
```yaml
deploy:
  resources:
    limits:
      memory: 16G  # 增加記憶體
```

## 🚀 生產環境部署

### 使用 Gunicorn（推薦）

修改 Dockerfile 中的啟動命令：
```dockerfile
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8082", "--timeout", "300", "web_interface:app"]
```

需要先安裝 gunicorn：
```bash
pip install gunicorn
```

### 使用 Nginx 反向代理

創建 `nginx.conf`：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 效能優化

### 1. 使用 GPU 加速

修改 `docker-compose.yml`：
```yaml
services:
  stl-detection:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
```

需要安裝 NVIDIA Container Toolkit。

### 2. 減小映像大小

- 使用多階段構建
- 清理不必要的檔案
- 使用 `.dockerignore`

### 3. 快取優化

構建時使用快取：
```bash
docker-compose build --no-cache  # 不使用快取（重新構建）
docker-compose build             # 使用快取（更快）
```

## 🔐 安全建議

1. **不要在映像中包含敏感資訊**
2. **使用環境變數管理配置**
3. **定期更新基礎映像**
4. **限制容器資源使用**
5. **使用非 root 用戶運行**（可選）

## 📝 版本資訊

- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **Python**: 3.12
- **系統**: Linux/macOS/Windows (with WSL2)

## 📞 支援

遇到問題？請查看：
- 容器日誌：`docker-compose logs`
- 系統狀態：http://localhost:8082/api/system_status
- 健康檢查：`docker inspect --format='{{json .State.Health}}' stl-object-detection`

## 🎉 完整部署流程範例

```bash
# 1. 克隆或進入專案目錄
cd /path/to/STL

# 2. 構建映像
docker-compose build

# 3. 啟動服務
docker-compose up -d

# 4. 查看啟動日誌
docker-compose logs -f

# 5. 訪問系統
# 瀏覽器打開 http://localhost:8082

# 6. 停止服務（需要時）
docker-compose down
```

祝您使用愉快！🎊