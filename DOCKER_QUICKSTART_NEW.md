# STL 物件識別系統 - Docker 快速開始 🚀

## 快速部署（推薦）

```bash
# 一鍵部署
./docker-deploy.sh

# 或分步執行
./docker-deploy.sh build   # 構建映像
./docker-deploy.sh start   # 啟動容器
```

## 訪問系統

- **本地**: http://localhost:5000
- **區域網**: http://你的IP:5000

## 常用指令

```bash
# 查看狀態
docker ps | grep stl-object-detection

# 查看日誌
docker logs -f stl-object-detection

# 停止容器
docker-compose down

# 重啟容器
docker-compose restart

# 進入容器
docker exec -it stl-object-detection bash
```

## 目錄結構

- `STL/` - STL 模型檔案（唯讀）
- `dataset/` - 生成的訓練資料集
- `runs/` - 訓練結果和模型
- `logs/` - 系統日誌

## 故障排除

### 端口被佔用
修改 `docker-compose.yml` 中的端口：
```yaml
ports:
  - "8080:5000"  # 改用 8080
```

### 記憶體不足
修改資源限制：
```yaml
deploy:
  resources:
    limits:
      memory: 4G  # 降低限制
```

### 構建失敗
清理並重新構建：
```bash
docker system prune -a
./docker-deploy.sh build
```

## 更多信息

詳細文檔請參考 `DOCKER_DEPLOY_GUIDE.md`
