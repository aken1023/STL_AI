# STL 檔案上傳政策

## 防重複上傳機制

### 規則
✅ **所有上傳的 STL 檔案都不可以重複**

### 實作方式

#### 1. 檔案上傳檢查 (web_interface.py)
```python
# 在 /api/upload_stl 端點中
- 檢查檔案名稱是否已存在於 STL/ 目錄
- 如果檔案已存在，跳過上傳並返回警告訊息
- 記錄跳過的檔案清單
```

#### 2. 上傳回應格式
```json
{
  "success": true,
  "files": [...],           // 成功上傳的檔案
  "count": 5,               // 成功上傳數量
  "skipped": [...],         // 跳過的重複檔案
  "skipped_count": 2,       // 跳過的數量
  "message": "成功上傳 5 個檔案，跳過 2 個重複檔案"
}
```

#### 3. 檔案檢查邏輯
```python
filepath = os.path.join('STL', filename)

if os.path.exists(filepath):
    # 檔案已存在，跳過
    skipped_files.append({
        'name': filename,
        'reason': '檔案已存在，不允許重複上傳'
    })
    continue
```

### 目前狀態

#### STL 檔案清單（17 個）
1. H09-EC11X8.stl (5.18 MB)
2. N9000151.stl (3.23 MB)
3. R8107490.stl (0.52 MB)
4. R8108140.stl (0.63 MB)
5. R8112078.stl (0.38 MB)
6. R8113139-TW.stl (0.90 MB)
7. R8113597-10.5-.stl (1.14 MB)
8. R8113743.stl (1.46 MB)
9. R8113865EW.stl (1.47 MB)
10. R8113930-.stl (1.27 MB)
11. R8113978.stl (1.27 MB)
12. R8116440.stl (1.73 MB)
13. R8126257-A--ok.stl (1.90 MB)
14. R8128944.stl (0.36 MB)
15. R8128945-A--OK.stl (2.01 MB)
16. R8128946-A--OK.stl (2.13 MB)
17. S03-1.stl (2.44 MB)

✅ **所有檔案名稱唯一，無重複**
✅ **所有 STL 都有對應的 dataset 訓練資料**
✅ **FAISS 索引包含所有 17 個模型（6,120 個特徵向量）**

### 測試工具

運行測試腳本檢查重複：
```bash
python3 test_duplicate_prevention.py
```

### 使用注意事項

1. **上傳前檢查**：確認檔案名稱不與現有檔案重複
2. **相同檔案不同版本**：如需更新，請先刪除舊檔案
3. **檔案命名規範**：使用唯一的型號或編號命名
4. **中文檔名支援**：系統支援中文檔名，但會自動清理特殊字符

### 檔案生命週期

```
上傳 STL → 檢查重複 → 儲存到 STL/ → 生成 360 張圖片 → 訓練 FAISS 索引
    ↓           ↓           ↓               ↓                    ↓
  Web API   重複跳過    STL/檔名.stl   dataset/檔名/  faiss_features.index
```

### 相關檔案

- **Web 介面**: `web_interface.py` (line 1594-1649)
- **圖片生成**: `generate_images_color.py`
- **FAISS 訓練**: `faiss_recognition.py`
- **測試腳本**: `test_duplicate_prevention.py`

### API 端點

- **POST /api/upload_stl**: 上傳 STL 檔案（含重複檢查）
- **POST /api/generate_from_stl**: 從 STL 生成訓練圖片
- **GET /api/list_stl_files**: 列出所有 STL 檔案

---

**最後更新**: 2025-10-04
**版本**: 1.0
