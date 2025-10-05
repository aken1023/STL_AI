# 系統設定功能說明

## 功能概述

本系統新增了完整的系統設定和資料管理功能，包括：

### 📊 核心功能

1. **上傳歷史追蹤**
   - 記錄所有上傳的檔案
   - 儲存上傳時間、檔案大小、IP 位址等資訊
   - 支援分頁查詢和篩選

2. **辨識紀錄管理**
   - 記錄每次辨識的結果
   - 包含預測類別、置信度、推論時間
   - 區分成功和失敗的辨識
   - 支援 YOLO 和 FAISS 兩種方法

3. **訓練歷史記錄**
   - 記錄所有訓練任務
   - 儲存訓練參數、最終準確率、mAP 等指標
   - 追蹤訓練時間和狀態

4. **完整的模型管理**
   - 掃描和列出所有訓練好的模型
   - 顯示詳細的模型資訊（大小、訓練輪數、準確率等）
   - 支援模型切換、刪除、匯出、備份
   - 可視化訓練結果（混淆矩陣、訓練曲線等）

5. **系統統計儀表板**
   - 顯示總上傳次數、總辨識次數
   - 計算辨識成功率和平均置信度
   - 統計各方法使用次數
   - 分析類別辨識分佈

6. **資料匯出與清理**
   - 匯出所有系統資料到 JSON 格式
   - 支援分類匯出（上傳、辨識、訓練記錄）
   - 自動清理舊資料（可設定天數）

## 技術架構

### 後端模組

1. **data_manager.py** - 資料管理模組
   - 使用 SQLite 資料庫儲存所有記錄
   - 提供完整的 CRUD 操作
   - 線程安全的資料存取
   - 支援資料統計和匯出

2. **model_manager.py** - 模型管理模組
   - 自動掃描訓練模型
   - 解析訓練配置和結果
   - 支援模型載入、備份、還原
   - 提供模型比較功能

3. **web_interface.py** - Web API 整合
   - 新增 12+ 個 API 端點
   - 整合資料記錄功能到上傳流程
   - 提供系統設定頁面路由

### 前端界面

- **templates/settings.html** - 系統設定頁面
  - 響應式設計
  - 6 個主要分頁
  - 即時資料載入
  - 豐富的視覺化效果

## 資料庫結構

### upload_history（上傳歷史）
- id, timestamp, filename, file_size, file_path
- client_ip, user_agent, status

### recognition_history（辨識紀錄）
- id, timestamp, upload_id（外鍵）
- method, predicted_class, confidence
- inference_time, result_image_path
- success, error_message

### training_history（訓練歷史）
- id, timestamp, model_name, model_type
- epochs, batch_size, final_accuracy, final_map
- training_time, model_path, client_ip, status

### model_registry（模型註冊表）
- id, model_name, model_type, model_path
- created_time, file_size, epochs
- accuracy, map_score, is_active, description

### system_settings（系統設定）
- key, value, updated_at

## API 端點

### 資料查詢
- `GET /api/statistics` - 獲取系統統計
- `GET /api/upload_history?page=1&limit=20` - 上傳歷史
- `GET /api/recognition_history?page=1&limit=20` - 辨識紀錄
- `GET /api/training_history?page=1&limit=50` - 訓練歷史

### 模型管理
- `GET /api/models_detailed` - 詳細模型列表
- `POST /api/activate_model` - 啟用模型
- `POST /api/delete_model` - 刪除模型
- `GET /api/export_model?path=...` - 匯出模型
- `POST /api/backup_model` - 備份模型

### 資料管理
- `GET /api/export_data?type=all` - 匯出資料
- `POST /api/clear_old_data` - 清理舊資料

## 使用方法

### 1. 啟動系統

```bash
# 啟動 Web 伺服器
python3 web_interface.py

# 或使用啟動腳本
./start_web.sh
```

### 2. 訪問系統設定

訪問 `http://localhost:8082/settings` 查看系統設定頁面

### 3. 查看統計資訊

系統概覽分頁顯示：
- 總上傳次數
- 總辨識次數
- 辨識成功率
- 平均置信度
- 平均推論時間
- 訓練次數

### 4. 管理模型

在模型管理分頁可以：
- 查看所有訓練好的模型
- 切換使用的模型
- 刪除不需要的模型
- 匯出模型供其他用途
- 備份重要模型

### 5. 查看記錄

- **上傳歷史**：查看所有上傳的檔案和時間
- **辨識紀錄**：查看所有辨識結果和準確率
- **訓練歷史**：查看所有訓練任務和結果

### 6. 匯出資料

在資料匯出分頁可以：
- 匯出所有資料（JSON 格式）
- 匯出特定類型的資料
- 清理 30 天前的舊資料

## 自動資料記錄

系統會自動記錄：

1. **每次上傳**
   - 檔案名稱、大小
   - 上傳時間
   - 客戶端 IP 和 User-Agent

2. **每次辨識**
   - 使用的方法（YOLO/FAISS）
   - 預測結果和置信度
   - 推論時間
   - 成功或失敗狀態

3. **每次訓練**（需要在訓練完成時手動添加）
   - 模型名稱和類型
   - 訓練參數
   - 最終準確率和 mAP
   - 訓練總時間

## 資料持久化

- 所有資料儲存在 `system_data.db` SQLite 資料庫中
- 資料庫檔案自動創建，無需手動設定
- 支援並發存取，線程安全
- 資料不會因為系統重啟而丟失

## 效能優化

1. **資料庫索引**
   - 時間戳記索引加速查詢
   - 外鍵索引提升關聯查詢速度

2. **分頁載入**
   - 預設每頁 20 條記錄
   - 支援自定義分頁大小

3. **異步操作**
   - 資料記錄不阻塞主流程
   - 使用線程鎖確保資料一致性

## 安全性

1. **SQL 注入防護**
   - 使用參數化查詢
   - 避免字串拼接 SQL

2. **資料驗證**
   - 檢查輸入參數類型
   - 限制查詢範圍

3. **存取控制**
   - IP 記錄追蹤使用者
   - User-Agent 記錄客戶端資訊

## 未來擴展

可以進一步添加：

1. **使用者認證系統**
   - 多使用者管理
   - 角色權限控制

2. **更多統計圖表**
   - 時間序列分析
   - 準確率趨勢圖

3. **自動備份**
   - 定期自動備份資料庫
   - 模型自動歸檔

4. **通知系統**
   - 訓練完成通知
   - 異常警報

5. **資料分析**
   - 辨識熱點分析
   - 使用模式分析

## 故障排除

### 問題：無法訪問系統設定頁面

```bash
# 檢查伺服器是否運行
netstat -tulnp | grep 8082

# 檢查日誌
tail -f web.log
```

### 問題：資料庫鎖定

```bash
# 檢查是否有多個程序訪問資料庫
lsof system_data.db

# 重啟伺服器
pkill -f web_interface.py
python3 web_interface.py
```

### 問題：模型列表為空

```bash
# 檢查模型目錄
ls -la runs/detect/*/weights/

# 確認有 best.pt 或 last.pt 檔案
find runs/detect -name "*.pt"
```

## 總結

系統設定功能提供了完整的資料管理和模型管理能力，讓您可以：

- ✅ 追蹤所有系統活動
- ✅ 管理訓練模型
- ✅ 分析使用統計
- ✅ 匯出和備份資料
- ✅ 優化系統效能

所有資料都會自動記錄和保存，無需額外操作！

---

**版本**: v1.0
**更新日期**: 2025-10-02
