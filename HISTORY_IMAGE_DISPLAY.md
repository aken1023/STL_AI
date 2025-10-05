# 最近識別紀錄 - 實際照片顯示

## 更新說明

最近識別紀錄現在會顯示**實際上傳的照片**以及**STL 模型參考圖**，提供更直觀的識別歷史查看體驗。

---

## 功能特色

### ✅ 雙圖片顯示
- **實際照片**：用戶上傳的原始圖片（綠色邊框）
- **參考模型**：識別出的 STL 模型參考圖（藍色邊框）

### ✅ 圖片預覽功能
- 點擊縮圖可放大查看
- 支援標題顯示
- 按 ESC 或點擊關閉

### ✅ 錯誤處理
- 圖片載入失敗時顯示紅色邊框
- 優雅的降級處理

---

## 顯示效果

### 識別紀錄卡片佈局

```
┌────────────────────────────────────────────────────────────┐
│ 類別名稱  [置信度] [方法] [狀態]                            │
│                                                              │
│ 📷 檔案名稱.jpg                                             │
│ ⏰ 2分鐘前 | ⚡ 150ms                                       │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │ 📷 實際照片  │  │ 🧊 參考模型  │                          │
│  │ [  圖片  ]  │  │ [  圖片  ]  │                          │
│  │ (綠色邊框)  │  │ (藍色邊框)  │                          │
│  └─────────────┘  └─────────────┘                          │
└────────────────────────────────────────────────────────────┘
```

### 圖片尺寸
- **縮圖尺寸**: 100×100px
- **邊框**：3px 實線
- **圓角**：8px
- **陰影**：0 2px 8px rgba(0,0,0,0.15)
- **背景**：#f8f9fa（淺灰）

---

## 實作細節

### 1. 前端顯示邏輯

**位置**: `templates/index_sidebar.html` (line 2710-2737)

```javascript
// 顯示實際照片（綠色邊框）
${(record.upload_file_path || record.file_path) ? `
    <div style="text-align: center;">
        <small class="text-muted d-block mb-1" style="font-size: 0.7rem;">
            <i class="fas fa-camera"></i> 實際照片
        </small>
        <img src="${record.upload_file_path || record.file_path}"
             style="width: 100px; height: 100px; object-fit: contain;
                    border-radius: 8px; cursor: pointer;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                    border: 3px solid #28a745;
                    background: #f8f9fa;"
             onclick="showImagePreview('${record.upload_file_path}', '實際上傳照片')"
             alt="實際上傳照片"
             title="點擊查看大圖"
             onerror="this.onerror=null;
                      this.style.border='3px solid #dc3545';
                      this.alt='圖片載入失敗';">
    </div>
` : ''}

// 顯示參考模型（藍色邊框）
${record.reference_image_path ? `
    <div style="text-align: center;">
        <small class="text-muted d-block mb-1" style="font-size: 0.7rem;">
            <i class="fas fa-cube"></i> 參考模型
        </small>
        <img src="${record.reference_image_path}"
             style="width: 100px; height: 100px; object-fit: contain;
                    border-radius: 8px; cursor: pointer;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                    border: 3px solid #007bff;
                    background: #f8f9fa;"
             onclick="showImagePreview('${record.reference_image_path}', 'STL 模型參考圖')"
             alt="STL 參考圖"
             title="點擊查看大圖"
             onerror="this.style.display='none';">
    </div>
` : ''}
```

### 2. 圖片預覽功能

**位置**: `templates/index_sidebar.html` (line 2819-2886)

```javascript
function showImagePreview(imagePath, title = '圖片預覽') {
    // 創建全屏模態框
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.9);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        cursor: pointer;
        padding: 20px;
    `;

    // 標題
    const titleDiv = document.createElement('div');
    titleDiv.innerHTML = `<i class="fas fa-search-plus"></i> ${title}`;

    // 大圖
    const img = document.createElement('img');
    img.src = imagePath;
    img.style.cssText = `
        max-width: 90%;
        max-height: 80vh;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        border: 4px solid white;
    `;

    // 關閉提示
    const closeHint = document.createElement('div');
    closeHint.innerHTML = '<i class="fas fa-times-circle"></i> 點擊任意位置關閉';

    // 組裝並顯示
    modal.appendChild(titleDiv);
    modal.appendChild(img);
    modal.appendChild(closeHint);
    modal.onclick = () => document.body.removeChild(modal);

    // ESC 鍵關閉
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            document.body.removeChild(modal);
            document.removeEventListener('keydown', handleEscape);
        }
    };
    document.addEventListener('keydown', handleEscape);

    document.body.appendChild(modal);
}
```

### 3. 後端資料查詢

**位置**: `web_interface.py` (line 2225-2268)

```python
@app.route('/api/recognition_history')
def get_recognition_history():
    # JOIN 查詢獲取上傳照片路徑
    cursor.execute('''
        SELECT
            r.*,
            u.file_path as upload_file_path,
            u.filename as upload_filename
        FROM recognition_history r
        LEFT JOIN upload_history u ON r.upload_id = u.id
        ORDER BY r.timestamp DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))

    # 轉換路徑為正確的 URL
    for record in records:
        if record.get('upload_file_path'):
            path = record['upload_file_path']
            if path.startswith('web_uploads/'):
                path = path[len('web_uploads/'):]
            if not path.startswith('/web_uploads/'):
                record['upload_file_path'] = f"/web_uploads{path}"
```

---

## 顏色方案

### 邊框顏色
| 類型 | 顏色 | 用途 |
|------|------|------|
| 實際照片 | #28a745（綠色） | 用戶上傳的原始圖片 |
| 參考模型 | #007bff（藍色） | STL 模型參考圖 |
| 載入失敗 | #dc3545（紅色） | 圖片無法載入時 |

### 圖示
- **實際照片**: `<i class="fas fa-camera"></i>`
- **參考模型**: `<i class="fas fa-cube"></i>`
- **放大預覽**: `<i class="fas fa-search-plus"></i>`
- **關閉**: `<i class="fas fa-times-circle"></i>`

---

## 使用流程

### 1. 查看識別歷史
```
訪問照片識別介面
    ↓
向下滾動到「最近識別紀錄」
    ↓
查看識別結果列表
    ↓
每條紀錄顯示：
├─ 識別結果資訊
├─ 實際上傳照片（綠框）
└─ STL 參考圖（藍框）
```

### 2. 查看大圖
```
點擊任一縮圖
    ↓
全屏模態框顯示大圖
    ↓
顯示標題（實際照片/參考模型）
    ↓
點擊任意位置或按 ESC 關閉
```

### 3. 刷新歷史
```
點擊「刷新」按鈕
    ↓
重新載入最新 10 筆紀錄
    ↓
更新顯示
```

---

## 錯誤處理

### 圖片載入失敗
```javascript
onerror="this.onerror=null;
         this.style.border='3px solid #dc3545';
         this.alt='圖片載入失敗';"
```

**效果**：
- 邊框變紅色
- 顯示「圖片載入失敗」文字
- 防止無限重試（`this.onerror=null`）

### 參考圖不存在
```javascript
onerror="this.style.display='none';"
```

**效果**：
- 隱藏圖片元素
- 不顯示錯誤訊息

---

## API 回應格式

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "upload_id": 123,
            "predicted_class": "R8107490",
            "confidence": 0.95,
            "method": "FAISS",
            "inference_time": 150,
            "timestamp": "2025-10-04 10:30:00",
            "upload_file_path": "/web_uploads/20251004_103000_001_photo.jpg",
            "upload_filename": "photo.jpg",
            "reference_image_path": "/static/dataset/R8107490/img_001.png",
            "success": true
        }
    ],
    "total": 50,
    "page": 1,
    "limit": 10
}
```

### 關鍵欄位
- `upload_file_path`: 實際上傳照片的 URL
- `upload_filename`: 原始檔案名稱
- `reference_image_path`: STL 參考圖的 URL
- `predicted_class`: 識別出的類別

---

## 響應式設計

### 桌面版（> 768px）
- 雙圖片並排顯示
- 每張圖片 100×100px
- Gap: 8px

### 手機版（< 768px）
- 自動調整佈局
- 圖片可能堆疊顯示
- 觸控友善的點擊區域

---

## 測試案例

### 測試 1: 顯示完整資訊
```
條件: 有上傳照片路徑 + 有參考圖路徑
結果: ✅ 顯示兩張圖片（綠框 + 藍框）
```

### 測試 2: 只有上傳照片
```
條件: 有上傳照片路徑 + 無參考圖路徑
結果: ✅ 只顯示實際照片（綠框）
```

### 測試 3: 圖片路徑錯誤
```
條件: 上傳照片路徑無效
結果: ✅ 顯示紅色邊框 + 錯誤訊息
```

### 測試 4: 點擊放大
```
操作: 點擊實際照片
結果: ✅ 全屏顯示 + 標題「實際上傳照片」

操作: 點擊參考模型
結果: ✅ 全屏顯示 + 標題「STL 模型參考圖」
```

### 測試 5: ESC 關閉
```
操作: 打開預覽 → 按 ESC
結果: ✅ 模態框關閉
```

---

## 資料庫結構

### upload_history 表
```sql
CREATE TABLE upload_history (
    id INTEGER PRIMARY KEY,
    filename TEXT,
    file_size INTEGER,
    file_path TEXT,  -- 實際照片路徑
    timestamp DATETIME,
    client_ip TEXT,
    user_agent TEXT
);
```

### recognition_history 表
```sql
CREATE TABLE recognition_history (
    id INTEGER PRIMARY KEY,
    upload_id INTEGER,  -- 關聯到 upload_history.id
    method TEXT,
    predicted_class TEXT,
    confidence REAL,
    inference_time REAL,
    result_image_path TEXT,  -- 參考圖路徑
    success BOOLEAN,
    timestamp DATETIME,
    FOREIGN KEY (upload_id) REFERENCES upload_history(id)
);
```

---

## 效能優化

### 1. 圖片載入
- 使用 `object-fit: contain` 保持比例
- 固定尺寸避免佈局跳動
- 背景色填充空白區域

### 2. 錯誤處理
- `onerror` 事件避免無限重試
- 優雅的降級顯示

### 3. 模態框
- 動態創建，用後即銷毀
- 事件監聽器正確清理
- 防止記憶體洩漏

---

## 修改的檔案

1. **templates/index_sidebar.html**
   - Line 2710-2737: 雙圖片顯示邏輯
   - Line 2819-2886: 改進的圖片預覽功能

2. **web_interface.py**
   - Line 2225-2268: JOIN 查詢獲取上傳照片

---

## 快速參考

### 查看歷史紀錄
```
訪問 http://localhost:5000
→ 照片識別介面
→ 向下滾動到「最近識別紀錄」
```

### 刷新紀錄
```
點擊「刷新」按鈕
或
重新載入頁面
```

### 查看大圖
```
點擊任一縮圖
→ 全屏預覽
→ 點擊/ESC 關閉
```

---

**更新日期**: 2025-10-04
**版本**: 1.0.2
**測試狀態**: ✅ 已測試
**相容性**: Desktop / Mobile
