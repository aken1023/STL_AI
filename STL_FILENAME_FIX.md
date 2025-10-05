# STL 檔案名稱清理與路徑解析修復

## 問題描述

訓練過程中出現錯誤訊息：
```
圖片生成失敗：以下 STL 檔案不存在於 STL 目錄:
#600980-6.5#-版-(BN)-OK-GT.stl,
#601400-92-7.5#-貨-(BN)-倒14K黃-GT.stl,
#604650-6.5#-貨-(BN)-倒TP950(補口含釘).stl,
SO1249-RD8.0-17471-7#-貨-(JA)-倒14K黃.stl
```

## 根本原因

1. **檔名清理機制**：`safe_filename()` 函數會移除特殊字元：
   - 移除 `#` 字元
   - 移除括號 `()`
   - 轉換數字模式：`6.5#` → `65`、`8.0` → `80`

2. **檔名不一致**：
   - **前端**：儲存原始檔名（含特殊字元），例如 `#600980-6.5#-版-(BN)-OK-GT.stl`
   - **後端**：儲存清理後檔名到磁碟，例如 `600980-65-版-BN-OK-GT.stl`
   - **訓練時**：前端發送原始檔名，後端找不到對應檔案

## 修復方案

### 1. 後端路徑解析增強 (web_interface.py)

**檔案**: `web_interface.py` (Line 1678-1707)

```python
# 檢查 STL 檔案是否都在 STL 目錄中
# 注意：檔案名稱可能已被 safe_filename 清理過
missing_files = []
valid_files = []

for stl_file in stl_files:
    # 首先嘗試原始檔名
    stl_path = os.path.join('STL', stl_file)
    if os.path.exists(stl_path):
        valid_files.append(stl_file)
        continue

    # 如果原始檔名不存在，嘗試清理後的檔名
    safe_name = safe_filename(stl_file)
    safe_path = os.path.join('STL', safe_name)
    if os.path.exists(safe_path):
        valid_files.append(safe_name)  # ✅ 使用實際存在的檔名
        continue

    # 兩者都不存在，標記為缺失
    missing_files.append(stl_file)

if missing_files:
    return jsonify({
        'success': False,
        'error': f'以下 STL 檔案不存在於 STL 目錄: {", ".join(missing_files)}。請檢查檔案名稱是否正確。'
    })

# 使用找到的有效檔案名稱
stl_files = valid_files
```

**修復邏輯**：
1. 首先嘗試原始檔名
2. 若不存在，嘗試 `safe_filename()` 清理後的檔名
3. 兩者都存在時，使用**實際存在磁碟上的檔名**
4. 兩者都不存在時，回報錯誤

### 2. 前端使用伺服器返回的清理檔名 (templates/index_sidebar.html)

**檔案**: `templates/index_sidebar.html` (Line 5152-5179)

```javascript
// 上傳完成後，使用伺服器返回的清理後檔名
xhr.addEventListener('load', () => {
    if (xhr.status === 200) {
        const data = JSON.parse(xhr.responseText);
        if (data.success) {
            // 添加到已上傳列表 - 使用伺服器返回的清理後檔名
            if (data.files && data.files.length > 0) {
                for (let uploadedFile of data.files) {
                    uploadedSTLFiles.push({
                        name: uploadedFile.name,  // ✅ 清理後的檔名（實際存在磁碟上的）
                        displayName: uploadedFile.original_name || uploadedFile.name,  // 顯示用的原始檔名
                        size: uploadedFile.size
                    });
                }
            }

            // 顯示跳過的重複檔案
            if (data.skipped && data.skipped.length > 0) {
                addTrainingLog(`⚠️ 跳過 ${data.skipped.length} 個重複檔案`);
            }
        }
    }
});
```

**修復邏輯**：
- `name`：儲存清理後的檔名（用於 API 請求）
- `displayName`：儲存原始檔名（用於介面顯示）
- 訓練時發送 `name`（清理後的檔名），確保能找到檔案

### 3. 伺服器上傳回應格式 (web_interface.py)

**檔案**: `web_interface.py` (Line 1643-1648)

```python
file.save(filepath)
uploaded_files.append({
    'name': filename,  # 清理後的檔名
    'original_name': file.filename,  # 原始檔名
    'size': os.path.getsize(filepath),
    'path': filepath
})
```

**回應格式**：
```json
{
    "success": true,
    "files": [
        {
            "name": "600980-65-版-BN-OK-GT.stl",  // 清理後（磁碟上的檔名）
            "original_name": "#600980-6.5#-版-(BN)-OK-GT.stl",  // 原始檔名
            "size": 123456,
            "path": "STL/600980-65-版-BN-OK-GT.stl"
        }
    ],
    "count": 1
}
```

## 檔名清理規則

### safe_filename() 函數行為

| 原始檔名 | 清理後檔名 | 說明 |
|---------|----------|------|
| `#600980-6.5#-版-(BN)-OK-GT.stl` | `600980-65-版-BN-OK-GT.stl` | 移除 `#`、括號、轉換 `6.5#` → `65` |
| `#601400-92-7.5#-貨-(BN)-倒14K黃-GT.stl` | `601400-92-75-貨-BN-倒14K黃-GT.stl` | 移除 `#`、括號、轉換 `7.5#` → `75` |
| `SO1249-RD8.0-17471-7#-貨-(JA)-倒14K黃.stl` | `SO1249-RD80-17471-7-貨-JA-倒14K黃.stl` | 移除 `#`、括號、轉換 `8.0` → `80` |

### 特殊字元處理
- **移除字元**：`#`、`(`、`)`、`[`、`]`、`{`、`}`
- **數字模式轉換**：
  - `6.5#` → `65`
  - `8.0` → `80`
  - `10.5` → `105`

## 測試結果

### 測試案例 1：正常檔名
```
原始檔名: H09-EC11X8.stl
磁碟檔名: H09-EC11X8.stl
結果: ✅ 直接找到
```

### 測試案例 2：含特殊字元檔名
```
原始檔名: #600980-6.5#-版-(BN)-OK-GT.stl
磁碟檔名: 600980-65-版-BN-OK-GT.stl
流程:
1. 嘗試原始檔名 → ❌ 找不到
2. 嘗試清理檔名 → ✅ 找到
3. 使用: 600980-65-版-BN-OK-GT.stl
```

### 測試案例 3：帶括號和數字
```
原始檔名: SO1249-RD8.0-17471-7#-貨-(JA)-倒14K黃.stl
磁碟檔名: SO1249-RD80-17471-7-貨-JA-倒14K黃.stl
流程:
1. 嘗試原始檔名 → ❌ 找不到
2. 嘗試清理檔名 → ✅ 找到
3. 使用: SO1249-RD80-17471-7-貨-JA-倒14K黃.stl
```

## 邊緣案例處理

### 案例 1：檔案已手動改名
```
上傳檔名: #604650-6.5#-貨-(BN)-倒TP950(補口含釘).stl
磁碟檔名: 604650-65-貨-BN-倒PT950補口含釕.stl
問題: TP950 → PT950（手動改名）
結果: ❌ 兩種路徑都找不到，回報錯誤
建議: 避免上傳後手動改名檔案
```

### 案例 2：重複上傳
```
已存在: 600980-65-版-BN-OK-GT.stl
上傳: #600980-6.5#-版-(BN)-OK-GT.stl
流程:
1. safe_filename() 清理 → 600980-65-版-BN-OK-GT.stl
2. 檢查檔案存在 → ✅ 已存在
3. 回應: 跳過重複檔案
```

## 修復效果

### 修復前
```
❌ 訓練失敗：找不到檔案
- 前端發送: #600980-6.5#-版-(BN)-OK-GT.stl
- 後端查找: STL/#600980-6.5#-版-(BN)-OK-GT.stl
- 結果: 檔案不存在
```

### 修復後
```
✅ 訓練成功
- 前端發送: 600980-65-版-BN-OK-GT.stl（清理後的檔名）
- 後端查找:
  1. STL/600980-65-版-BN-OK-GT.stl → ✅ 找到
- 結果: 成功開始圖片生成
```

## 相關檔案

### 後端
- `web_interface.py`
  - Line 1614-1666: `/api/upload_stl` - STL 上傳 API
  - Line 1668-1760: `/api/generate_from_stl` - 圖片生成 API（含路徑解析修復）

### 前端
- `templates/index_sidebar.html`
  - Line 5105-5201: `uploadSTLFiles()` - STL 上傳函數
  - Line 5152-5179: 使用伺服器返回的清理檔名

## 使用建議

### ✅ 推薦做法
1. **上傳後不要手動改名**：避免檔名不一致
2. **使用系統介面上傳**：確保檔名正確清理
3. **檢查上傳日誌**：確認檔名清理結果

### ❌ 避免做法
1. **上傳後手動改名 STL 檔案**
2. **直接複製檔案到 STL 目錄**（繞過清理機制）
3. **使用過於複雜的檔名**（過多特殊字元）

## 故障排除

### 問題：訓練時找不到 STL 檔案
**檢查步驟**：
1. 確認檔案存在於 `STL/` 目錄
2. 檢查檔名是否包含特殊字元
3. 查看伺服器日誌中的清理後檔名
4. 確認前端是否使用伺服器返回的檔名

### 問題：重複檔案無法上傳
**原因**：系統設計為不允許重複上傳
**解決**：
- 如需重新上傳，先刪除舊檔案
- 檢查是否已存在同名（清理後）檔案

## 更新日期

- **版本**: 1.0.1
- **日期**: 2025-10-04
- **狀態**: ✅ 已修復並測試
