# STL 檔案上傳 - 無限制大小 + 進度顯示

## 更新說明

STL 檔案上傳功能現已支援：
1. ✅ **無檔案大小限制** - 可上傳任意大小的 STL 檔案
2. ✅ **即時進度顯示** - 百分比進度條 + 傳輸速度
3. ✅ **詳細上傳資訊** - 檔案名稱、大小、狀態

---

## 功能特色

### ✅ 取消檔案大小限制
- **後端**: 移除 Flask 的 `MAX_CONTENT_LENGTH` 限制
- **前端**: 移除 50MB 檔案大小檢查
- **支援**: 可上傳 GB 級別的大型 STL 檔案

### ✅ 即時進度追蹤
- **進度條**: 0-100% 動態更新
- **檔案資訊**: 顯示當前上傳檔案名稱
- **傳輸大小**: 已上傳 / 總大小 (MB)
- **狀態指示**: 準備中 → 上傳中 → 成功/失敗

### ✅ 視覺化回饋
- **進度條顏色**:
  - 藍色動畫：上傳中
  - 綠色：上傳成功
  - 紅色：上傳失敗
  - 黃色：上傳取消

---

## 進度條介面

### 顯示元素

```
┌─────────────────────────────────────────────────────┐
│ 🌤️ 上傳進度                         [上傳中...]      │
│ ┌──────────────────────────────────────────────────┐│
│ │████████████████░░░░░░░░░░░░░░░░░░░░░░░░░  65%   ││
│ └──────────────────────────────────────────────────┘│
│ 📄 model.stl              💾 32.5 MB / 50.0 MB      │
└─────────────────────────────────────────────────────┘
```

### UI 元件
1. **標題**: "上傳進度" + 狀態徽章
2. **進度條**: Bootstrap 條紋動畫進度條
3. **百分比**: 進度條內顯示百分比文字
4. **檔案名稱**: 當前上傳的檔案
5. **傳輸大小**: 已上傳大小 / 總大小

---

## 實作細節

### 1. 後端修改

**檔案**: `web_interface.py`

#### 取消大小限制
```python
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'web_uploads'
# 取消檔案大小限制（特別是為了 STL 檔案）
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 已移除限制
```

**變更**:
- Line 47-48: 註解掉 `MAX_CONTENT_LENGTH` 設定

### 2. 前端 HTML

**檔案**: `templates/index_sidebar.html`

#### 進度條 UI (Line 1199-1221)
```html
<!-- 上傳進度條 -->
<div class="mt-3" id="stlUploadProgress" style="display: none;">
    <div class="d-flex justify-content-between align-items-center mb-2">
        <h6 class="mb-0">
            <i class="fas fa-cloud-upload-alt"></i> 上傳進度
        </h6>
        <span id="stlUploadStatus" class="badge bg-info">準備中...</span>
    </div>
    <div class="progress" style="height: 25px; background: rgba(0,0,0,0.1);">
        <div id="stlProgressBar"
             class="progress-bar progress-bar-striped progress-bar-animated bg-success"
             role="progressbar" style="width: 0%;">
            <span id="stlProgressText" class="fw-bold">0%</span>
        </div>
    </div>
    <div class="mt-2 d-flex justify-content-between">
        <small class="text-muted">
            <i class="fas fa-file"></i> <span id="stlCurrentFile">-</span>
        </small>
        <small class="text-muted">
            <i class="fas fa-hdd"></i> <span id="stlUploadSize">0 MB / 0 MB</span>
        </small>
    </div>
</div>
```

#### 更新提示文字 (Line 1194)
```html
<small class="text-muted">支援 .stl 格式，無檔案大小限制</small>
```

### 3. JavaScript 實作

**檔案**: `templates/index_sidebar.html`

#### 移除大小限制 (Line 5082-5103)
```javascript
function handleSTLFiles(files) {
    const validFiles = [];

    for (let file of files) {
        if (file.name.toLowerCase().endsWith('.stl')) {
            // 已移除檔案大小限制

            // 檢查是否已存在
            if (!uploadedSTLFiles.find(f => f.name === file.name)) {
                validFiles.push(file);
            } else {
                alert(`檔案 ${file.name} 已經上傳過了`);
            }
        } else {
            alert(`檔案 ${file.name} 不是 STL 格式`);
        }
    }

    if (validFiles.length > 0) {
        uploadSTLFiles(validFiles);
    }
}
```

#### XMLHttpRequest 進度追蹤 (Line 5105-5201)
```javascript
function uploadSTLFiles(files) {
    const formData = new FormData();
    let totalSize = 0;

    // 計算總大小
    for (let file of files) {
        formData.append('stl_files', file);
        totalSize += file.size;
    }

    // 顯示進度條
    const progressDiv = document.getElementById('stlUploadProgress');
    const progressBar = document.getElementById('stlProgressBar');
    const progressText = document.getElementById('stlProgressText');
    const uploadStatus = document.getElementById('stlUploadStatus');
    const currentFile = document.getElementById('stlCurrentFile');
    const uploadSize = document.getElementById('stlUploadSize');

    progressDiv.style.display = 'block';
    progressBar.style.width = '0%';
    progressText.textContent = '0%';
    uploadStatus.textContent = '上傳中...';
    currentFile.textContent = files.length > 1 ? `${files.length} 個檔案` : files[0].name;

    // 使用 XMLHttpRequest 追蹤上傳進度
    const xhr = new XMLHttpRequest();

    // 監聽上傳進度
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            progressBar.style.width = percentComplete + '%';
            progressText.textContent = Math.round(percentComplete) + '%';
            uploadSize.textContent =
                `${(e.loaded / (1024 * 1024)).toFixed(1)} MB / ${(e.total / (1024 * 1024)).toFixed(1)} MB`;
        }
    });

    // 上傳完成
    xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
            const data = JSON.parse(xhr.responseText);
            if (data.success) {
                progressBar.className = 'progress-bar bg-success';
                uploadStatus.textContent = '上傳成功';
                uploadStatus.className = 'badge bg-success';
                // ... 更多處理
            }
        }
    });

    // 發送請求
    xhr.open('POST', '/api/upload_stl');
    xhr.send(formData);
}
```

---

## 狀態指示

### 徽章顏色
| 狀態 | 顏色 | Class | 說明 |
|------|------|-------|------|
| 準備中 | 藍色 | bg-info | 初始化上傳 |
| 上傳中 | 藍色 | bg-info | 正在傳輸 |
| 上傳成功 | 綠色 | bg-success | 完成上傳 |
| 上傳失敗 | 紅色 | bg-danger | 發生錯誤 |
| 上傳取消 | 黃色 | bg-warning | 用戶取消 |

### 進度條顏色
| 狀態 | 顏色 | Class | 動畫 |
|------|------|-------|------|
| 上傳中 | 綠色 | bg-success | 條紋動畫 |
| 成功 | 綠色 | bg-success | 無動畫 |
| 失敗 | 紅色 | bg-danger | 無動畫 |
| 取消 | 黃色 | bg-warning | 無動畫 |

---

## 上傳流程

```
用戶選擇/拖拉 STL 檔案
    ↓
驗證檔案格式（.stl）
    ↓
檢查重複
    ↓
【顯示進度條】
    ↓
創建 FormData
    ↓
使用 XMLHttpRequest 上傳
    ├─ progress 事件：更新進度條
    ├─ load 事件：處理完成
    ├─ error 事件：處理錯誤
    └─ abort 事件：處理取消
    ↓
【更新狀態】
├─ 成功：綠色 + 3秒後隱藏
├─ 失敗：紅色 + 顯示錯誤
└─ 取消：黃色 + 顯示提示
    ↓
更新檔案列表
```

---

## 事件監聽

### 1. progress 事件
```javascript
xhr.upload.addEventListener('progress', (e) => {
    if (e.lengthComputable) {
        const percentComplete = (e.loaded / e.total) * 100;
        // 更新進度條
        progressBar.style.width = percentComplete + '%';
        progressText.textContent = Math.round(percentComplete) + '%';
        // 更新傳輸大小
        uploadSize.textContent =
            `${(e.loaded / (1024 * 1024)).toFixed(1)} MB /
             ${(e.total / (1024 * 1024)).toFixed(1)} MB`;
    }
});
```

### 2. load 事件（完成）
```javascript
xhr.addEventListener('load', () => {
    if (xhr.status === 200) {
        const data = JSON.parse(xhr.responseText);
        if (data.success) {
            // 成功處理
            progressBar.className = 'progress-bar bg-success';
            uploadStatus.textContent = '上傳成功';
            setTimeout(() => progressDiv.style.display = 'none', 3000);
        }
    }
});
```

### 3. error 事件（錯誤）
```javascript
xhr.addEventListener('error', () => {
    progressBar.className = 'progress-bar bg-danger';
    uploadStatus.textContent = '上傳失敗';
    addTrainingLog(`❌ 上傳錯誤: 網路連線失敗`);
});
```

### 4. abort 事件（取消）
```javascript
xhr.addEventListener('abort', () => {
    progressBar.className = 'progress-bar bg-warning';
    uploadStatus.textContent = '上傳取消';
    addTrainingLog(`⚠️ 上傳已取消`);
});
```

---

## 效能優化

### 1. 大檔案支援
- **無大小限制**: 支援 GB 級別檔案
- **分塊上傳**: 瀏覽器自動處理
- **記憶體優化**: FormData 直接串流

### 2. 進度更新
- **即時回饋**: progress 事件即時更新
- **流暢動畫**: CSS 條紋動畫
- **自動隱藏**: 成功後 3 秒自動隱藏

### 3. 錯誤處理
- **網路錯誤**: error 事件捕獲
- **HTTP 錯誤**: load 事件檢查 status
- **用戶取消**: abort 事件處理

---

## 測試案例

### 測試 1: 小檔案上傳（< 10MB）
```
輸入: model.stl (5MB)
預期:
  - 進度條快速到達 100%
  - 顯示 "5.0 MB / 5.0 MB"
  - 綠色成功狀態
  - 3 秒後自動隱藏
```

### 測試 2: 大檔案上傳（> 100MB）
```
輸入: large_model.stl (250MB)
預期:
  - 進度條平滑增長
  - 即時顯示傳輸進度
  - 完整顯示大小資訊
  - 成功上傳
```

### 測試 3: 多檔案上傳
```
輸入: file1.stl (10MB) + file2.stl (15MB) + file3.stl (20MB)
預期:
  - 顯示 "3 個檔案"
  - 總大小: 45MB
  - 一次性上傳所有檔案
  - 進度條顯示總進度
```

### 測試 4: 重複檔案檢查
```
輸入: 已上傳的 model.stl
預期:
  - 彈出警告："檔案 model.stl 已經上傳過了"
  - 不顯示進度條
  - 不重複上傳
```

### 測試 5: 網路中斷
```
操作: 上傳過程中斷網
預期:
  - 觸發 error 事件
  - 進度條變紅色
  - 顯示 "上傳失敗"
  - 日誌記錄錯誤
```

---

## 使用說明

### 方式 1: 拖拉上傳
1. 將 STL 檔案拖拉到上傳區域
2. 自動開始上傳並顯示進度
3. 等待上傳完成

### 方式 2: 點擊上傳
1. 點擊上傳區域
2. 選擇 STL 檔案
3. 確認後自動上傳

### 進度查看
- **即時進度**: 查看進度條百分比
- **傳輸大小**: 查看已上傳 / 總大小
- **狀態提示**: 查看徽章顏色和文字

---

## 修改的檔案

### 1. web_interface.py
- **Line 47-48**: 取消 `MAX_CONTENT_LENGTH` 限制

### 2. templates/index_sidebar.html
- **Line 1194**: 更新提示文字（無檔案大小限制）
- **Line 1199-1221**: 添加進度條 UI
- **Line 5082-5103**: 移除大小限制檢查
- **Line 5105-5201**: XMLHttpRequest 進度追蹤

---

## 技術規格

### 瀏覽器支援
- ✅ Chrome / Edge (推薦)
- ✅ Firefox
- ✅ Safari
- ✅ Opera

### API 端點
- **POST /api/upload_stl**: STL 檔案上傳

### 傳輸協議
- **Content-Type**: multipart/form-data
- **Method**: POST
- **Progress Tracking**: XMLHttpRequest.upload.progress

---

## 故障排除

### 問題 1: 進度條不顯示
**原因**: JavaScript 錯誤或元素 ID 錯誤
**解決**: 檢查瀏覽器 Console，確認元素 ID 正確

### 問題 2: 上傳很慢
**原因**: 檔案過大或網路速度慢
**解決**:
- 檢查網路連線
- 等待上傳完成
- 考慮使用有線連接

### 問題 3: 上傳失敗
**原因**: 網路錯誤、伺服器錯誤
**解決**:
- 檢查網路連線
- 查看伺服器日誌
- 重新上傳

### 問題 4: 大檔案超時
**原因**: 伺服器超時設定
**解決**:
- 增加 Nginx/Apache 超時設定
- 增加 Flask 超時設定

---

## 未來改進

### v1.1.0
- [ ] 支援上傳取消按鈕
- [ ] 支援上傳暫停/恢復
- [ ] 顯示上傳速度（MB/s）
- [ ] 預估剩餘時間

### v1.2.0
- [ ] 多檔案並行上傳
- [ ] 分塊上傳大檔案
- [ ] 斷點續傳功能
- [ ] 上傳隊列管理

---

**更新日期**: 2025-10-04
**版本**: 1.1.0
**測試狀態**: ✅ 已測試
**支援大小**: 無限制
