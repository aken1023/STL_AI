# 🐳 Portainer 管理指南

## 📍 如何在 Portainer 找到 STL 物件識別系統容器

### 方法一：透過容器列表（推薦）

1. **登入 Portainer**
   ```
   預設位址：http://localhost:9000
   或您的伺服器：http://your-server:9000
   ```

2. **導航到容器頁面**
   ```
   左側選單 → Environments → local → Containers
   ```

3. **找到容器**
   - 容器名稱：`stl-object-detection`
   - 映像名稱：`stl-detection:latest`
   - 狀態：應顯示綠色的 "running"
   - 端口：`0.0.0.0:8082 → 8082/tcp`

### 方法二：透過搜尋功能

1. 在容器列表頁面右上角找到搜尋框
2. 輸入：`stl` 或 `object-detection`
3. 系統會即時過濾並顯示匹配的容器

### 方法三：透過 Stack 管理

如果使用 docker-compose 部署：
```
左側選單 → Stacks → stl (stack 名稱)
```
會看到該 Stack 下的所有容器。

---

## 🎛️ Portainer 容器管理操作

### 基本操作

#### 1. 查看容器詳細資訊
```
點擊容器名稱 → 進入容器詳情頁面
```
顯示內容：
- 容器狀態
- 網路設定
- 卷掛載
- 環境變數
- 資源使用情況

#### 2. 查看實時日誌
```
容器頁面 → Logs 標籤
```
功能：
- 實時日誌串流
- 日誌搜尋
- 自動滾動
- 複製日誌內容

快捷鍵：
- `Ctrl + F`：搜尋日誌
- 勾選 "Auto-refresh"：自動刷新

#### 3. 查看容器統計資訊
```
容器頁面 → Stats 標籤
```
監控項目：
- CPU 使用率
- 記憶體使用量
- 網路流量（上傳/下載）
- I/O 操作

#### 4. 進入容器終端
```
容器頁面 → Console 標籤
```
選項：
- Command：選擇 `/bin/bash` 或 `/bin/sh`
- User：選擇 `root`
- 點擊 "Connect" 進入互動式終端

常用命令：
```bash
# 查看 Python 進程
ps aux | grep python

# 查看訓練日誌
tail -f web.log

# 檢查磁碟使用
df -h

# 查看 GPU 狀態（如有）
nvidia-smi

# 測試 API
curl http://localhost:8082/api/model_status
```

#### 5. 重啟容器
```
容器列表 → 選中容器 → Restart 按鈕
或
容器詳情頁面 → 頂部 "Restart container" 按鈕
```

#### 6. 停止容器
```
容器列表 → 選中容器 → Stop 按鈕
```

#### 7. 啟動已停止的容器
```
容器列表 → 選中容器 → Start 按鈕
```

---

## 🔍 進階功能

### 1. 編輯容器配置

```
容器詳情頁面 → Duplicate/Edit 按鈕
```

可修改：
- 環境變數
- 卷掛載
- 端口映射
- 資源限制
- 網路設定

⚠️ **注意**：需要停止並重新創建容器才能應用更改。

### 2. 備份容器數據

```bash
# 在 Console 中執行
tar -czf /tmp/backup.tar.gz /app/runs /app/dataset

# 然後在主機下載
docker cp stl-object-detection:/tmp/backup.tar.gz ./
```

### 3. 監控容器健康狀態

```
容器詳情頁面 → Health status
```
顯示：
- 健康檢查狀態（healthy/unhealthy）
- 最後檢查時間
- 檢查失敗次數

STL 系統的健康檢查：
```bash
curl -f http://localhost:8082/api/model_status
```

### 4. 查看容器資源限制

```
容器詳情頁面 → Resources 區塊
```
當前配置：
- CPU：4 核心上限
- 記憶體：8GB 上限

### 5. 管理容器卷（Volumes）

```
左側選單 → Volumes
```
STL 系統的資料卷：
- `./STL` → STL 模型檔案
- `./dataset` → 訓練圖片
- `./yolo_dataset` → YOLO 格式資料集
- `./runs` → 訓練結果
- `./static/uploads` → 上傳的圖片

操作：
- 瀏覽卷內容
- 下載檔案
- 刪除卷

---

## 🚨 故障排查

### 容器無法啟動

1. **查看日誌**
   ```
   Containers → stl-object-detection → Logs
   ```
   尋找錯誤訊息（紅色文字）

2. **檢查端口衝突**
   ```
   Containers → 檢查是否有其他容器使用 8082 端口
   ```

3. **檢查卷掛載**
   ```
   容器詳情 → Volumes 標籤
   確認所有目錄存在且有正確權限
   ```

### 容器運行但無法訪問

1. **檢查端口映射**
   ```
   容器詳情 → Network → Published ports
   應該看到：0.0.0.0:8082 → 8082/tcp
   ```

2. **檢查防火牆**
   ```bash
   # 在主機執行
   sudo ufw status
   sudo ufw allow 8082
   ```

3. **測試連接**
   ```
   容器 Console → 執行：
   curl http://localhost:8082
   ```

### 容器健康檢查失敗

1. **查看健康檢查日誌**
   ```
   容器詳情 → Inspect → Health status
   ```

2. **手動測試健康檢查**
   ```bash
   # 在容器 Console 執行
   curl -f http://localhost:8082/api/model_status
   ```

3. **重啟服務**
   ```
   容器 Console → 執行：
   pkill -f python3
   python3 /app/web_interface.py
   ```

---

## 📊 監控儀表板

### 設置自訂儀表板

1. **安裝監控工具**
   ```
   左側選單 → App Templates → Prometheus + Grafana
   ```

2. **配置數據源**
   - 添加 Docker 作為數據源
   - 配置容器指標收集

3. **常用監控指標**
   - CPU 使用率趨勢
   - 記憶體使用趨勢
   - 網路流量
   - 容器重啟次數
   - 健康檢查狀態

---

## 🔐 安全設定

### 1. 限制容器權限

```yaml
# docker-compose.yml 添加
security_opt:
  - no-new-privileges:true
read_only: false  # STL 系統需要寫入權限
```

### 2. 設定資源配額

已配置：
```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 8G
```

### 3. 網路隔離

```
左側選單 → Networks → 創建新網路
將容器加入專用網路
```

---

## 📱 Portainer 行動版操作

### 透過手機/平板訪問

1. **安裝 Portainer App**（iOS/Android）
2. **添加環境**
   - 輸入 Portainer URL
   - 登入帳號
3. **管理容器**
   - 查看狀態
   - 重啟容器
   - 查看日誌

---

## 🔗 快速連結

### 常用 URL

| 功能 | URL |
|------|-----|
| **Portainer** | http://localhost:9000 |
| **STL 系統** | http://localhost:8082 |
| **容器日誌** | Portainer → Containers → stl-object-detection → Logs |
| **健康檢查** | http://localhost:8082/api/model_status |

---

## 💡 最佳實踐

### 1. 定期備份

```bash
# 每週備份訓練結果
docker exec stl-object-detection tar -czf /app/backup_$(date +%Y%m%d).tar.gz /app/runs
docker cp stl-object-detection:/app/backup_*.tar.gz ./backups/
```

### 2. 監控資源使用

- 定期查看 Stats 標籤
- 設定記憶體/CPU 使用警報
- 監控磁碟空間（/app/runs 資料夾）

### 3. 日誌管理

```bash
# 清理舊日誌
docker exec stl-object-detection find /app -name "*.log" -mtime +30 -delete
```

### 4. 定期更新

```bash
# 更新容器
cd /home/aken/code/STL
docker-compose down
docker-compose pull  # 如果使用遠端映像
docker-compose build  # 重新構建
docker-compose up -d
```

---

## 📞 支援資訊

### 查看容器版本

```bash
docker exec stl-object-detection python3 -c "import ultralytics; print(ultralytics.__version__)"
```

### 查看系統資訊

```bash
docker exec stl-object-detection python3 -c "import sys; print(sys.version)"
```

### 檢查依賴套件

```bash
docker exec stl-object-detection pip list
```

---

## ✅ 檢查清單

部署後確認：

- [ ] 容器狀態為 "running"（綠色）
- [ ] 健康檢查為 "healthy"
- [ ] 可以訪問 http://localhost:8082
- [ ] API 端點正常：http://localhost:8082/api/model_status
- [ ] 日誌沒有嚴重錯誤
- [ ] 卷掛載正確
- [ ] 資源使用正常（CPU < 80%, Memory < 6GB）

---

**📚 更多文檔**：
- [DOCKER_README.md](DOCKER_README.md) - Docker 完整文檔
- [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) - 快速啟動指南
- [README_DOCKER.md](README_DOCKER.md) - 專案總覽