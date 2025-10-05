# 📤 STL 檔案逐個依序上傳功能

**更新日期**: 2025-10-04

## 🎯 功能概述

將多檔案上傳改為**逐個依序上傳**，解決大量檔案同時上傳導致的超時和連接問題。

---

## ❓ 為什麼需要改為依序上傳？

### 原本的問題

**多檔案同時上傳**（一次將 8 個檔案 126MB 全部包在一個請求中）會導致：

1. **連接超時** - 大型請求容易被 nginx/proxy 中斷
2. **記憶體壓力** - 前端和後端都需要同時處理所有檔案
3. **進度卡住** - 上傳進度停在 1% 無法繼續
4. **失敗全部重來** - 一個檔案失敗會導致所有檔案需重新上傳

### 新的解決方案

**逐個依序上傳**（一次上傳一個檔案，完成後自動上傳下一個）：

✅ **穩定可靠** - 單個檔案上傳成功率高
✅ **進度清晰** - 顯示當前上傳的檔案名稱和整體進度
✅ **失敗重試** - 單個檔案失敗不影響其他檔案
✅ **減少壓力** - 降低伺服器和網路負載

---

## 💻 實作細節

### 前端邏輯 (index_sidebar.html Lines 5946-6104)

```javascript
function uploadSTLFiles(files) {
    const fileArray = Array.from(files);
    let currentIndex = 0;
    let successCount = 0;
    let failedFiles = [];

    // 逐個上傳檔案
    function uploadNextFile() {
        if (currentIndex >= fileArray.length) {
            // 全部上傳完成
            addTrainingLog(`✅ 成功上傳 ${successCount} 個 STL 檔案`);
            if (failedFiles.length > 0) {
                addTrainingLog(`❌ 失敗 ${failedFiles.length} 個: ${failedFiles.join(', ')}`);
            }
            return;
        }

        const file = fileArray[currentIndex];
        const fileNumber = currentIndex + 1;

        // 創建 FormData，每次只包含一個檔案
        const formData = new FormData();
        formData.append('stl_files', file);

        const xhr = new XMLHttpRequest();

        // 監聽單個檔案的上傳進度
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const filePercent = (e.loaded / e.total) * 100;
                // 整體進度 = 已完成檔案數量 + 當前檔案進度
                const overallProgress = Math.round(((currentIndex + (filePercent / 100)) / fileArray.length) * 100);
                progressBar.style.width = overallProgress + '%';
                progressText.textContent = overallProgress + '%';
            }
        });

        // 單個檔案上傳完成
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);

                if (data.success) {
                    successCount++;
                    addTrainingLog(`✅ [${fileNumber}/${fileArray.length}] ${file.name}`);

                    // 繼續下一個檔案
                    currentIndex++;
                    uploadNextFile();
                } else {
                    failedFiles.push(file.name);
                    currentIndex++;
                    uploadNextFile();
                }
            }
        });

        xhr.open('POST', '/api/upload_stl');
        xhr.send(formData);
    }

    // 開始上傳第一個檔案
    uploadNextFile();
}
```

---

## 🎬 使用流程

### 情境：上傳 8 個 STL 檔案

```
1. 用戶選擇 8 個 STL 檔案（總共 126.76 MB）
   └─> handleSTLFiles() 驗證檔案格式

2. uploadSTLFiles() 開始執行
   ├─> 顯示: "準備上傳 8 個檔案..."
   └─> 調用 uploadNextFile() 上傳第一個檔案

3. 上傳第 1 個檔案 (#600980-6.5#-版-(BN)-OK-GT.stl, 17.34 MB)
   ├─> 顯示: "[1/8] #600980-6.5#-版-(BN)-OK-GT.stl"
   ├─> 進度條: 0% → 12% (約 1/8 的整體進度)
   ├─> 日誌: "✅ [1/8] #600980-6.5#-版-(BN)-OK-GT.stl"
   └─> currentIndex++ → 繼續下一個

4. 上傳第 2 個檔案 (#601400-92-7.5#-貨-(BN)-倒14K黃-GT.stl, 14.24 MB)
   ├─> 顯示: "[2/8] #601400-92-7.5#-貨-(BN)-倒14K黃-GT.stl"
   ├─> 進度條: 12% → 25%
   ├─> 日誌: "✅ [2/8] #601400-92-7.5#-貨-(BN)-倒14K黃-GT.stl"
   └─> 繼續...

5. 依序上傳第 3-7 個檔案...

6. 上傳第 8 個檔案 (BN-S03-7#-3-磁铁款-版-GT.stl, 6.66 MB)
   ├─> 顯示: "[8/8] BN-S03-7#-3-磁铁款-版-GT.stl"
   ├─> 進度條: 87% → 100%
   └─> 日誌: "✅ [8/8] BN-S03-7#-3-磁铁款-版-GT.stl"

7. 全部上傳完成
   ├─> 進度條: 綠色 "上傳完成"
   ├─> 日誌: "✅ 成功上傳 8 個 STL 檔案"
   └─> 3 秒後自動隱藏進度條
```

---

## 🔍 進度顯示詳細說明

### 整體進度計算公式

```javascript
整體進度 = ((已完成檔案數 + 當前檔案進度) / 總檔案數) × 100%
```

**範例**：上傳 8 個檔案

- 第 1 個檔案上傳到 50%: `(0 + 0.5) / 8 = 6.25%`
- 第 1 個檔案完成: `(1 + 0) / 8 = 12.5%`
- 第 2 個檔案上傳到 50%: `(1 + 0.5) / 8 = 18.75%`
- 第 2 個檔案完成: `(2 + 0) / 8 = 25%`
- ...
- 第 8 個檔案完成: `(8 + 0) / 8 = 100%`

### 顯示元素

1. **當前檔案名稱**: `[1/8] filename.stl`
2. **進度條**: 視覺化整體進度
3. **百分比**: 數字顯示整體進度
4. **檔案大小**: 當前檔案已上傳/總大小
5. **訓練日誌**: 每個檔案的上傳狀態

---

## ⚠️ 錯誤處理

### 單個檔案失敗

如果某個檔案上傳失敗：

```
❌ [3/8] filename.stl: HTTP 500
```

- **不會中斷**: 繼續上傳下一個檔案
- **記錄失敗**: 添加到 `failedFiles` 陣列
- **最終報告**: 顯示成功和失敗的數量

### 重複檔案處理

如果檔案已存在：

```
⚠️ 檔案 "filename.stl" 已存在，是否覆蓋？

[確定] → 強制覆蓋
[取消] → 跳過此檔案
```

- 用戶選擇「確定」: 重新上傳並帶 `force=true` 參數
- 用戶選擇「取消」: 跳過，繼續下一個檔案

### 網路錯誤

```
❌ [5/8] filename.stl: 網路連線失敗
```

- 記錄失敗
- 繼續下一個檔案

---

## 🎯 效能優化

### 與舊版比較

| 項目 | 舊版（同時上傳） | 新版（依序上傳） |
|------|-----------------|-----------------|
| **單次請求大小** | 126 MB (8 個檔案) | 6-48 MB (單個檔案) |
| **成功率** | 低（容易超時） | 高（穩定） |
| **失敗影響** | 全部重來 | 單個檔案重試 |
| **進度顯示** | 不清楚 | 清晰明確 |
| **伺服器負載** | 峰值高 | 平均分散 |
| **記憶體使用** | 同時佔用大量 | 逐步釋放 |

### 上傳時間估算

假設網速 10 Mbps：

- **舊版**: 126 MB ÷ 1.25 MB/s = 約 100 秒（但可能超時失敗）
- **新版**:
  - 檔案 1 (17 MB): ~14 秒
  - 檔案 2 (14 MB): ~11 秒
  - ...
  - **總計**: ~100 秒（但穩定成功）

**實際效能**：雖然總時間相近，但新版的成功率大幅提升！

---

## 📝 技術細節

### 遞迴調用

使用 **遞迴** 而非迴圈來實現依序上傳：

```javascript
function uploadNextFile() {
    if (currentIndex >= fileArray.length) {
        // 完成
        return;
    }

    // 上傳當前檔案
    xhr.addEventListener('load', () => {
        currentIndex++;
        uploadNextFile();  // 遞迴調用自己
    });

    xhr.send(formData);
}
```

**優點**：
- 自動等待每個請求完成
- 避免並發請求
- 錯誤處理簡單

### 變數管理

```javascript
let currentIndex = 0;       // 當前正在上傳的檔案索引
let successCount = 0;       // 成功上傳的數量
let failedFiles = [];       // 失敗的檔案名稱列表
const fileArray = Array.from(files);  // 檔案陣列
```

---

## 🔄 後端兼容性

後端 API (`/api/upload_stl`) **無需修改**：

- 仍然支援單個或多個檔案上傳
- 新版前端每次只發送一個檔案
- 後端處理邏輯完全相同

---

## 📊 總結

### 核心改進

- 🔄 **依序上傳**: 一次一個檔案，穩定可靠
- 📊 **進度清晰**: 顯示當前檔案和整體進度
- 🛡️ **錯誤處理**: 單個失敗不影響其他檔案
- ⚡ **效能優化**: 降低伺服器和網路負載

### 使用建議

- ✅ 適用於大量檔案上傳
- ✅ 適用於大型檔案上傳
- ✅ 適用於不穩定的網路環境
- ✅ 提供清晰的上傳反饋

---

**版本**: v3.7
**更新**: 改為逐個依序上傳 STL 檔案
**狀態**: ✅ 已實作
**影響範圍**: 前端 JavaScript
**功能影響**: 大幅提升多檔案上傳成功率和用戶體驗
