# Web 伺服器運行狀態

## ✅ 伺服器運行正常

### 當前狀態
- 🟢 **伺服器狀態**: 運行中
- 🌐 **訪問地址**: http://localhost:8082
- 📡 **網路訪問**: http://192.168.31.96:8082
- 🔧 **Flask 模式**: Development
- 📦 **模型載入**: 成功

### 模型資訊
```json
{
    "path": "runs/detect/stl_yolo_enhanced_gpu17/weights/best.pt",
    "size": "17.6 MB",
    "classes": [
        "R8107490",
        "R8108140",
        "R8112078",
        "R8113865EW",
        "R8128944"
    ],
    "loaded_time": "2025-10-01 15:13:36"
}
```

## 🧪 測試結果

### 1. 首頁測試
```bash
curl http://localhost:8082
```
✅ 返回正常 HTML（標題：YOLO 辨識系統）

### 2. API 測試
```bash
curl http://localhost:8082/api/model_status
```
✅ 返回正確的模型資訊

### 3. 系統狀態
```bash
curl http://localhost:8082/api/system_status
```
✅ 返回系統資訊（CPU、記憶體等）

## 📱 功能清單

### ✅ 可用功能
- 照片識別介面（上傳照片進行識別）
- 批次處理
- 結果分析
- 模型訓練
- 系統設定
- 模型管理

### ❌ 已移除功能
- 相機拍照（已按要求移除）

## 🚀 訪問方式

### 本地訪問
```
http://localhost:8082
```

### 區域網訪問
```
http://192.168.31.96:8082
```

### Docker 容器訪問
```
http://172.21.0.2:8082
```

## 🔍 問題排查

### 如果無法訪問網頁

#### 1. 檢查伺服器是否運行
```bash
ps aux | grep web_interface
```

#### 2. 檢查端口
```bash
lsof -i:8082
netstat -tlnp | grep 8082
```

#### 3. 檢查日誌
```bash
tail -f /tmp/web_output.log
```

#### 4. 重啟伺服器
```bash
# 清理舊進程
lsof -ti:8082 | xargs kill -9

# 啟動伺服器
./start_web_simple.sh
```

### 如果識別結果不顯示

#### 1. 打開瀏覽器開發工具（F12）
- 切換到 Console 標籤
- 查看是否有 JavaScript 錯誤
- 查看 Network 標籤，檢查 API 請求

#### 2. 檢查 Console 日誌
應該看到類似的日誌：
```javascript
上傳檔案: [File]
識別方法: YOLO
收到回應: 200
識別完成: {...}
顯示識別結果: [...]
```

#### 3. 檢查 API 回應
在 Network 標籤中找到 `/api/upload` 請求：
- 狀態碼應該是 200
- 回應應該包含 `results` 陣列
- 每個結果應該有 `predictions` 陣列

## 📋 常見問題

### Q1: 為什麼上傳後沒有反應？
**A**:
1. 檢查網路連接
2. 查看 Console 是否有錯誤
3. 確認檔案格式（支援 PNG, JPG, JPEG）
4. 檢查伺服器日誌

### Q2: 識別結果顯示「未檢測到物件」？
**A**:
1. 這是正常情況，表示模型沒有在圖片中找到訓練過的物件
2. 可能原因：
   - 圖片中沒有訓練過的 STL 物件
   - 物件太小或不清晰
   - 角度不佳
3. 解決方案：
   - 使用包含訓練物件的照片
   - 確保照片清晰
   - 嘗試不同角度

### Q3: 置信度很低（<30%）？
**A**:
1. 這表示模型不太確定識別結果
2. 可能需要：
   - 重新訓練模型
   - 增加訓練數據
   - 使用更清晰的照片

### Q4: 網頁載入很慢？
**A**:
1. 第一次載入會比較慢（載入模型）
2. 後續應該會快很多
3. 可以檢查 CPU/記憶體使用情況

## 🎯 使用流程

### 正常識別流程
```
1. 訪問 http://localhost:8082
2. 點擊「照片識別」（或已經在此頁面）
3. 選擇識別方法（YOLO 或 FAISS）
4. 上傳照片（拖拉或點擊選擇）
5. 等待識別（會顯示「正在上傳並識別...」）
6. 查看結果：
   - 原圖
   - 識別類別
   - 置信度
   - 推論時間
   - 參考圖片
```

### 如果看不到結果
```
1. 打開瀏覽器開發工具（F12）
2. 查看 Console 標籤
3. 查看 Network 標籤
4. 找到 /api/upload 請求
5. 檢查回應內容
6. 如果有錯誤，查看錯誤訊息
```

## 📊 日誌分析

### 正常日誌
```
192.168.31.96 - - [01/Oct/2025 15:15:XX] "GET /api/system_status HTTP/1.1" 200 -
127.0.0.1 - - [01/Oct/2025 15:15:XX] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [01/Oct/2025 15:16:XX] "POST /api/upload HTTP/1.1" 200 -
```

### 錯誤日誌
```
127.0.0.1 - - [01/Oct/2025 15:16:XX] "POST /api/upload HTTP/1.1" 500 -
```
如果看到 500 錯誤，檢查後端日誌的詳細錯誤訊息

## 🔧 維護命令

### 查看運行狀態
```bash
ps aux | grep web_interface
```

### 查看日誌
```bash
tail -f /tmp/web_output.log
```

### 停止伺服器
```bash
pkill -f web_interface
# 或
lsof -ti:8082 | xargs kill -9
```

### 重啟伺服器
```bash
./start_web_simple.sh
```

### 檢查模型
```bash
curl http://localhost:8082/api/model_status | python3 -m json.tool
```

## 📈 性能監控

### CPU 使用率
```bash
top -p $(pgrep -f web_interface)
```

### 記憶體使用
```bash
ps aux | grep web_interface | awk '{print $6/1024 " MB"}'
```

### 網路連接
```bash
netstat -an | grep 8082
```

## 🎉 總結

✅ **伺服器狀態**: 正常運行
✅ **模型載入**: 成功
✅ **API 功能**: 正常
✅ **識別功能**: 已修復並增強
✅ **錯誤處理**: 完善
✅ **用戶提示**: 友善

如有任何問題，請：
1. 檢查開發工具 Console
2. 查看伺服器日誌
3. 參考本文件的問題排查章節

---

**更新時間**: 2025-10-01 15:16
**伺服器版本**: v2.3
**狀態**: 🟢 運行中
