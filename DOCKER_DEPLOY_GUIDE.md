# STL 物件識別系統 - Docker 部署指南

## 📋 目錄

- [快速開始](#快速開始)
- [詳細步驟](#詳細步驟)
- [容器管理](#容器管理)
- [常見問題](#常見問題)
- [進階配置](#進階配置)

---

## 🚀 快速開始

### 一鍵部署（推薦）

```bash
# 1. 賦予執行權限
chmod +x docker-deploy.sh

# 2. 執行部署（自動構建 + 啟動）
./docker-deploy.sh
```

### 或使用 docker-compose

```bash
# 構建並啟動
docker-compose up -d --build

# 查看日誌
docker-compose logs -f
```

### 訪問系統

- **本地訪問**：http://localhost:5000
- **區域網訪問**：http://你的IP:5000

---

## 📖 詳細步驟

### 1️⃣ 環境準備

#### 安裝 Docker（如尚未安裝）

**Ubuntu/Debian:**
```bash
# 更新套件列表
sudo apt update

# 安裝 Docker
sudo apt install -y docker.io docker-compose

# 啟動 Docker 服務
sudo systemctl start docker
sudo systemctl enable docker

# 將當前用戶加入 docker 群組（避免需要 sudo）
sudo usermod -aG docker $USER
newgrp docker
```

**其他系統:**
- [Docker 官方安裝文檔](https://docs.docker.com/get-docker/)

#### 驗證安裝

```bash
docker --version
docker-compose --version
```

### 2️⃣ 準備專案

```bash
# 進入專案目錄
cd /home/aken/code/STL

# 確保 STL 檔案存在
ls -l STL/*.stl
```

### 3️⃣ 構建 Docker 映像

#### 方法一：使用部署腳本（推薦）

```bash
./docker-deploy.sh build
```

#### 方法二：使用 docker-compose

```bash
docker-compose build --no-cache
```

#### 方法三：直接使用 Docker

```bash
docker build -t stl-detection:latest .
```

**預計時間**：5-10 分鐘（取決於網速）

### 4️⃣ 啟動容器

#### 方法一：使用部署腳本

```bash
./docker-deploy.sh start
```

#### 方法二：使用 docker-compose

```bash
docker-compose up -d
```

#### 方法三：直接使用 Docker

```bash
docker run -d \
  --name stl-object-detection \
  -p 5000:5000 \
  -v $(pwd)/STL:/app/STL:ro \
  -v $(pwd)/dataset:/app/dataset \
  -v $(pwd)/runs:/app/runs \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  stl-detection:latest
```

### 5️⃣ 驗證部署

```bash
# 查看容器狀態
docker ps | grep stl-object-detection

# 查看容器日誌
docker logs -f stl-object-detection

# 測試 Web 服務
curl http://localhost:5000
```

---

## 🛠️ 容器管理

### 使用部署腳本（推薦）

```bash
# 查看完整幫助
./docker-deploy.sh --help

# 啟動容器
./docker-deploy.sh start

# 停止容器
./docker-deploy.sh stop

# 重啟容器
./docker-deploy.sh restart

# 查看日誌
./docker-deploy.sh logs

# 查看狀態
./docker-deploy.sh status

# 清理容器和映像
./docker-deploy.sh clean
```

### 使用 Docker Compose

```bash
# 啟動（後台運行）
docker-compose up -d

# 停止
docker-compose down

# 重啟
docker-compose restart

# 查看日誌
docker-compose logs -f

# 查看狀態
docker-compose ps
```

### 使用 Docker 原生指令

```bash
# 啟動容器
docker start stl-object-detection

# 停止容器
docker stop stl-object-detection

# 重啟容器
docker restart stl-object-detection

# 刪除容器
docker rm stl-object-detection

# 查看日誌（即時）
docker logs -f stl-object-detection

# 查看日誌（最後 100 行）
docker logs --tail 100 stl-object-detection

# 進入容器內部
docker exec -it stl-object-detection bash

# 查看容器資源使用
docker stats stl-object-detection
```

---

## 🔧 常見問題

### ❓ 容器無法啟動

**解決方法：**

1. 查看日誌找出錯誤原因
   ```bash
   docker logs stl-object-detection
   ```

2. 檢查端口是否被佔用
   ```bash
   sudo netstat -tulpn | grep 5000
   ```

3. 如果端口被佔用，修改 `docker-compose.yml` 中的端口映射
   ```yaml
   ports:
     - "8080:5000"  # 改用 8080 端口
   ```

### ❓ 找不到 STL 檔案

**原因**：STL 目錄未正確映射

**解決方法：**

```bash
# 確保 STL 目錄存在
mkdir -p STL

# 將 STL 檔案放入目錄
cp /path/to/your/*.stl STL/

# 重啟容器
docker-compose restart
```

### ❓ 記憶體不足

**症狀**：容器頻繁重啟或訓練失敗

**解決方法：**

修改 `docker-compose.yml` 降低資源限制：

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
```

### ❓ 需要使用 GPU

**解決方法：**

1. 安裝 NVIDIA Docker 支援
   ```bash
   # Ubuntu/Debian
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

   sudo apt-get update
   sudo apt-get install -y nvidia-docker2
   sudo systemctl restart docker
   ```

2. 修改 `docker-compose.yml` 啟用 GPU
   ```yaml
   runtime: nvidia
   environment:
     - NVIDIA_VISIBLE_DEVICES=all
   ```

### ❓ Web 介面無法訪問

**檢查清單：**

1. 容器是否正常運行
   ```bash
   docker ps | grep stl-object-detection
   ```

2. 健康檢查是否通過
   ```bash
   docker inspect stl-object-detection | grep -A 5 Health
   ```

3. 防火牆是否允許 5000 端口
   ```bash
   sudo ufw allow 5000
   ```

4. 瀏覽器控制台是否有錯誤訊息

---

## 🔬 進階配置

### 自定義端口

編輯 `docker-compose.yml`：

```yaml
ports:
  - "8080:5000"  # 將主機 8080 映射到容器 5000
```

### 啟用開發模式

```yaml
environment:
  - FLASK_ENV=development  # 啟用自動重載
```

### 持久化更多資料

```yaml
volumes:
  - ./custom_models:/app/custom_models
  - ./exports:/app/exports
```

### 使用外部資料庫

如需將訓練任務存儲到資料庫：

```yaml
environment:
  - DATABASE_URL=postgresql://user:pass@db:5432/stl
```

### 多容器部署

如需增加 Nginx 反向代理：

```yaml
services:
  stl-detection:
    # ... 原有配置 ...
    expose:
      - "5000"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - stl-detection
```

---

## 📊 監控和日誌

### 查看容器資源使用

```bash
# 即時監控
docker stats stl-object-detection

# 單次查詢
docker stats --no-stream stl-object-detection
```

### 日誌管理

```bash
# 查看所有日誌
docker logs stl-object-detection

# 即時跟蹤
docker logs -f stl-object-detection

# 最後 N 行
docker logs --tail 100 stl-object-detection

# 帶時間戳
docker logs -t stl-object-detection

# 特定時間範圍
docker logs --since 2024-01-01 stl-object-detection
```

### 日誌檔案位置

- **容器內部**：`/app/logs/`
- **主機映射**：`./logs/`
- **Docker 日誌**：`/var/lib/docker/containers/.../*.log`

---

## 🔐 安全性建議

### 1. 限制容器權限

```yaml
security_opt:
  - no-new-privileges:true
user: "1000:1000"  # 使用非 root 用戶
```

### 2. 使用 secrets 管理敏感資訊

```yaml
secrets:
  - db_password

services:
  stl-detection:
    secrets:
      - db_password
```

### 3. 網絡隔離

```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
```

---

## 📦 資料備份

### 備份重要資料

```bash
# 備份訓練結果
tar -czf stl-backup-$(date +%Y%m%d).tar.gz \
  STL/ dataset/ runs/ models/

# 備份到遠端
rsync -avz STL/ dataset/ runs/ user@remote:/backup/
```

### 恢復資料

```bash
# 解壓備份
tar -xzf stl-backup-20240930.tar.gz

# 重啟容器以載入資料
docker-compose restart
```

---

## 🚀 生產環境部署

### 使用 Gunicorn（已內建）

容器預設使用 Gunicorn 作為 WSGI 伺服器，配置如下：

- **Workers**: 2
- **Threads**: 4
- **Timeout**: 300 秒

### 反向代理（Nginx）

**nginx.conf 範例：**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支援（如需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超時設定
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # 靜態檔案
    location /static {
        alias /app/static;
        expires 30d;
    }
}
```

### SSL/TLS（HTTPS）

使用 Certbot 自動獲取 Let's Encrypt 證書：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🤝 貢獻與支援

如遇到問題或有建議，請聯繫專案維護者。

---

**版本**: 2.0
**最後更新**: 2025-09-30
**維護狀態**: ✅ 活躍開發中