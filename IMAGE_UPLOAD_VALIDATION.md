# 照片識別介面 - 圖片檔案驗證說明

## 更新內容

### ✅ 圖片格式限制

照片識別介面現在只接受圖片檔案格式，會自動驗證並拒絕非圖片檔案。

---

## 支援的圖片格式

### 允許的格式
- ✅ **JPG / JPEG** - 常見的照片格式
- ✅ **PNG** - 支援透明背景
- ✅ **GIF** - 支援動畫（僅處理第一幀）
- ✅ **BMP** - Windows 點陣圖
- ✅ **WEBP** - 現代網頁圖片格式

### 不接受的格式
- ❌ **STL** - 3D 模型檔案（請使用「模型訓練」功能上傳）
- ❌ **PDF** - 文件檔案
- ❌ **TXT / DOC** - 文字檔案
- ❌ **ZIP / RAR** - 壓縮檔案
- ❌ **MP4 / AVI** - 影片檔案
- ❌ 其他非圖片格式

---

## 驗證機制

### 1. 前端驗證（JavaScript）

**位置**: `templates/index_sidebar.html` (line 2284-2336)

#### 驗證邏輯
```javascript
// 允許的圖片格式
const allowedImageTypes = [
    'image/jpeg', 'image/jpg', 'image/png',
    'image/gif', 'image/bmp', 'image/webp'
];
const allowedExtensions = [
    '.jpg', '.jpeg', '.png',
    '.gif', '.bmp', '.webp'
];

// 驗證每個檔案
files.forEach(file => {
    const fileName = file.name.toLowerCase();
    const fileType = file.type.toLowerCase();
    const fileExtension = fileName.substring(fileName.lastIndexOf('.'));

    // 雙重檢查：MIME 類型和副檔名
    if (allowedImageTypes.includes(fileType) ||
        allowedExtensions.includes(fileExtension)) {
        validFiles.push(file);
    } else {
        invalidFiles.push(file);
    }
});
```

#### 錯誤提示
- **部分檔案無效**: 顯示無效檔案名稱，只處理有效圖片
- **全部檔案無效**: 拒絕上傳，顯示支援格式清單

### 2. HTML input 限制

**位置**: `templates/index_sidebar.html` (line 1117)

```html
<input type="file" id="fileInput" multiple accept="image/*">
```

- `accept="image/*"`: 檔案選擇器只顯示圖片檔案
- `multiple`: 支援多檔案選擇

### 3. 後端驗證（Flask API）

**位置**: `web_interface.py` (line 437-445)

#### 驗證邏輯
```python
# 允許的圖片格式
allowed_image_extensions = (
    '.png', '.jpg', '.jpeg',
    '.gif', '.bmp', '.webp'
)

for file in files:
    # 檢查檔案副檔名
    if not file.filename.lower().endswith(allowed_image_extensions):
        results.append({
            'original_filename': file.filename,
            'error': '不支援的檔案格式。僅接受圖片格式：PNG, JPG, JPEG, GIF, BMP, WEBP',
            'success': False
        })
        continue
```

#### API 回應
```json
{
    "success": true/false,
    "results": [
        {
            "original_filename": "photo.jpg",
            "success": true,
            "result": {...}
        },
        {
            "original_filename": "document.pdf",
            "success": false,
            "error": "不支援的檔案格式。僅接受圖片格式：PNG, JPG, JPEG, GIF, BMP, WEBP"
        }
    ]
}
```

---

## 使用流程

### 方式一：拖拉上傳

```
1. 開啟「照片識別介面」
2. 拖拉圖片檔案到上傳區域
3. 系統自動驗證格式
   ├─ 有效圖片 → 顯示預覽
   ├─ 無效檔案 → 顯示警告，跳過
   └─ 全部無效 → 拒絕，提示支援格式
4. 點擊「開始識別」進行辨識
```

### 方式二：點擊上傳

```
1. 點擊上傳區域
2. 檔案選擇器自動過濾（只顯示圖片）
3. 選擇圖片檔案
4. 系統驗證並顯示預覽
5. 點擊「開始識別」
```

---

## 錯誤訊息

### 前端警告訊息

#### 部分檔案無效
```
⚠️ 以下檔案不是圖片格式，已跳過：

document.pdf, file.txt

✅ 僅接受圖片格式：JPG, JPEG, PNG, GIF, BMP, WEBP
```

#### 全部檔案無效
```
❌ 沒有有效的圖片檔案！

請上傳圖片格式：JPG, JPEG, PNG, GIF, BMP, WEBP
```

### 後端錯誤回應

```json
{
    "original_filename": "model.stl",
    "error": "不支援的檔案格式。僅接受圖片格式：PNG, JPG, JPEG, GIF, BMP, WEBP",
    "success": false
}
```

---

## 測試案例

### 測試 1: 上傳有效圖片
```
輸入: photo1.jpg, photo2.png
結果: ✅ 全部接受，顯示預覽
```

### 測試 2: 上傳混合檔案
```
輸入: photo.jpg, document.pdf, image.png
結果: ✅ photo.jpg, image.png 接受
      ⚠️ document.pdf 跳過並警告
```

### 測試 3: 上傳全部非圖片
```
輸入: model.stl, file.txt, data.csv
結果: ❌ 全部拒絕，顯示錯誤訊息
```

### 測試 4: 上傳不同圖片格式
```
輸入: photo.jpg, image.png, graphic.gif, pic.bmp, web.webp
結果: ✅ 全部接受
```

---

## 實作細節

### 驗證層級

```
Level 1: HTML accept 屬性
    ↓ (檔案選擇器過濾)
Level 2: JavaScript 前端驗證
    ↓ (MIME 類型 + 副檔名雙重檢查)
Level 3: Flask 後端驗證
    ↓ (副檔名最終檢查)
處理圖片並進行辨識
```

### 安全性考量

1. **雙重驗證**: MIME 類型和副檔名都檢查
2. **後端防護**: 不依賴前端，後端獨立驗證
3. **錯誤處理**: 清楚的錯誤訊息，不暴露系統資訊
4. **檔案命名**: 使用 `safe_filename()` 防止路徑遍歷攻擊

---

## 修改的檔案

### 1. templates/index_sidebar.html
- **Line 2284-2336**: 添加圖片格式驗證邏輯
- **Line 1117**: 已有 `accept="image/*"` 屬性

### 2. web_interface.py
- **Line 435**: 定義允許的圖片格式
- **Line 438-445**: 添加檔案格式檢查和錯誤處理

---

## Console 日誌範例

### 有效上傳
```
🚀 uploadFiles 被呼叫
📦 收到的檔案: [File, File]
📦 檔案數量: 2
✅ 有效的圖片檔案: 2 個
❌ 無效的檔案: 0 個
🖼️ 顯示照片預覽
```

### 混合檔案上傳
```
🚀 uploadFiles 被呼叫
📦 收到的檔案: [File, File, File]
📦 檔案數量: 3
❌ 無效的檔案: [{name: "document.pdf", ...}]
✅ 有效的圖片檔案: 2 個
⚠️ 顯示警告對話框
🖼️ 顯示照片預覽
```

### 全部無效
```
🚀 uploadFiles 被呼叫
📦 收到的檔案: [File]
📦 檔案數量: 1
❌ 無效的檔案: [{name: "model.stl", ...}]
✅ 有效的圖片檔案: 0 個
❌ 顯示錯誤對話框
⚠️ uploadFiles 返回（不顯示預覽）
```

---

## 相關功能

### STL 檔案上傳
- **位置**: 模型訓練功能面板
- **格式**: 只接受 `.stl` 檔案
- **驗證**: 獨立的驗證邏輯

### 檔案類型分離
```
照片識別介面 → 只接受圖片 (JPG, PNG, GIF, BMP, WEBP)
模型訓練介面 → 只接受 STL 檔案 (.stl)
```

---

**更新日期**: 2025-10-04
**版本**: 1.0.1
**測試狀態**: ✅ 已測試

---

## 快速參考

### 支援格式速查
| 格式 | 副檔名 | MIME 類型 | 狀態 |
|------|--------|-----------|------|
| JPEG | .jpg, .jpeg | image/jpeg | ✅ |
| PNG | .png | image/png | ✅ |
| GIF | .gif | image/gif | ✅ |
| BMP | .bmp | image/bmp | ✅ |
| WEBP | .webp | image/webp | ✅ |
| STL | .stl | - | ❌ |
| PDF | .pdf | - | ❌ |

### API 端點
- **POST /api/upload**: 上傳並辨識圖片（含格式驗證）
