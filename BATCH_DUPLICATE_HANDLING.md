# 📋 批次重複檔案處理功能

**更新日期**: 2025-10-04

## 🎯 功能概述

改進多檔案上傳時的重複檔案處理方式，將所有重複檔案**一次性收集並詢問**，而不是每個檔案都彈出一次確認對話框。

---

## ❓ 為什麼需要批次處理？

### 原本的問題

**逐個詢問**（每遇到一個重複檔案就彈出對話框）：

❌ 用戶體驗差 - 上傳 8 個檔案，如果有 5 個重複，需要點擊 5 次
❌ 中斷上傳流程 - 每次都要等待用戶回應
❌ 不一致處理 - 可能前幾個選擇覆蓋，後面又選擇跳過

### 新的解決方案

**批次處理**（先檢查所有檔案，一次性詢問處理方式）：

✅ **一次決定** - 只彈出一次對話框
✅ **統一處理** - 所有重複檔案使用相同的處理方式
✅ **清晰列表** - 顯示所有重複檔案的名稱
✅ **不中斷** - 檢查完成後自動開始上傳

---

## 💻 實作邏輯

### 兩階段上傳流程

```
階段一：檢查重複（0-30% 進度）
├─> 逐個檢查所有檔案是否重複
├─> 收集所有重複檔案到 duplicateFiles 陣列
└─> 檢查完成後一次性詢問處理方式

階段二：實際上傳（30-100% 進度）
├─> 根據用戶選擇處理重複檔案
│   ├─> 覆蓋：帶 force=true 參數上傳
│   └─> 跳過：不上傳該檔案
└─> 逐個上傳所有檔案
```

---

## 🎬 使用流程

### 情境：上傳 8 個檔案，其中 3 個重複

```
1. 用戶選擇 8 個 STL 檔案
   └─> handleSTLFiles() 驗證格式

2. 階段一：檢查重複（0-30%）
   ├─> 顯示: "檢查重複: 1/8"
   ├─> 進度: 0% → 4%
   ├─> 發現: file1.stl 已存在 ✓
   ├─> 顯示: "檢查重複: 2/8"
   ├─> 進度: 4% → 8%
   ├─> 發現: file2.stl 不重複
   ├─> ...繼續檢查...
   ├─> 發現: file5.stl 已存在 ✓
   ├─> 發現: file7.stl 已存在 ✓
   └─> 檢查完成，進度 30%

3. 彈出一次性確認對話框
   ┌─────────────────────────────────────┐
   │ 發現 3 個重複檔案：                   │
   │                                     │
   │ • file1.stl                         │
   │ • file5.stl                         │
   │ • file7.stl                         │
   │                                     │
   │ 請選擇處理方式：                     │
   │                                     │
   │ 點擊「確定」覆蓋全部                 │
   │ 點擊「取消」跳過全部                 │
   └─────────────────────────────────────┘

4a. 用戶選擇「確定」（覆蓋全部）
    ├─> 日誌: "🔄 將覆蓋 3 個重複檔案"
    ├─> 設定: overwriteDuplicates = true
    └─> 開始階段二上傳

4b. 用戶選擇「取消」（跳過全部）
    ├─> 日誌: "⏭️ 將跳過 3 個重複檔案"
    ├─> 設定: skipDuplicates = true
    └─> 開始階段二上傳

5. 階段二：實際上傳（30-100%）

   如果選擇覆蓋：
   ├─> 上傳 file1.stl (帶 force=true)
   │   ├─> 日誌: "✅ [1/8] file1.stl"
   │   └─> 進度: 30% → 39%
   ├─> 上傳 file2.stl
   │   ├─> 日誌: "✅ [2/8] file2.stl"
   │   └─> 進度: 39% → 47%
   ├─> ...
   └─> 全部上傳完成，進度 100%

   如果選擇跳過：
   ├─> 跳過 file1.stl
   │   ├─> 日誌: "⏭️ [1/8] file1.stl (跳過)"
   │   └─> 進度: 30% → 39%
   ├─> 上傳 file2.stl
   │   ├─> 日誌: "✅ [2/8] file2.stl"
   │   └─> 進度: 39% → 47%
   ├─> ...
   └─> 完成，進度 100%

6. 最終報告
   ├─> 日誌: "✅ 成功上傳 5 個 STL 檔案"
   └─> 3 個跳過或覆蓋
```

---

## 📊 詳細實作

### 階段一：檢查重複

```javascript
function checkDuplicates() {
    let checkIndex = 0;

    function checkNext() {
        if (checkIndex >= fileArray.length) {
            // 檢查完成，詢問處理方式
            if (duplicateFiles.length > 0) {
                const duplicateNames = duplicateFiles.map(f => f.name).join('\n• ');
                const message = `發現 ${duplicateFiles.length} 個重複檔案：\n\n• ${duplicateNames}\n\n請選擇處理方式：`;

                if (confirm(message + '\n\n點擊「確定」覆蓋全部\n點擊「取消」跳過全部')) {
                    overwriteDuplicates = true;
                } else {
                    skipDuplicates = true;
                }
            }

            // 開始實際上傳
            uploadNextFile();
            return;
        }

        const file = fileArray[checkIndex];
        const formData = new FormData();
        formData.append('stl_files', file);

        const xhr = new XMLHttpRequest();
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);

                // 檢測重複檔案
                if (data.warning === 'duplicate_detected') {
                    duplicateFiles.push(file);
                }
            }

            checkIndex++;
            const progress = Math.round((checkIndex / fileArray.length) * 30);  // 前 30%
            progressBar.style.width = progress + '%';
            progressText.textContent = progress + '%';
            currentFile.textContent = `檢查重複: ${checkIndex}/${fileArray.length}`;

            checkNext();
        });

        xhr.open('POST', '/api/upload_stl');
        xhr.send(formData);
    }

    checkNext();
}
```

### 階段二：依據選擇上傳

```javascript
function uploadNextFile() {
    const file = fileArray[currentIndex];
    const fileNumber = currentIndex + 1;

    // 檢查是否為重複檔案且用戶選擇跳過
    const isDuplicate = duplicateFiles.some(f => f.name === file.name);
    if (isDuplicate && skipDuplicates) {
        addTrainingLog(`⏭️ [${fileNumber}/${fileArray.length}] ${file.name} (跳過)`);
        currentIndex++;
        uploadNextFile();
        return;
    }

    const formData = new FormData();
    formData.append('stl_files', file);

    // 如果是重複檔案且用戶選擇覆蓋，加上 force 參數
    if (isDuplicate && overwriteDuplicates) {
        formData.append('force', 'true');
    }

    // 上傳檔案...
    xhr.open('POST', '/api/upload_stl');
    xhr.send(formData);
}
```

---

## 📈 進度顯示

### 進度條分配

- **0-30%**: 檢查重複階段
  - 檢查每個檔案後更新進度
  - 公式: `(checkIndex / fileArray.length) × 30%`

- **30-100%**: 上傳階段
  - 基礎進度 30% + 上傳進度 70%
  - 公式: `30 + ((currentIndex + filePercent/100) / fileArray.length) × 70%`

### 狀態顯示

```
檢查階段: "檢查重複: 3/8"
上傳階段: "[5/8] filename.stl"
```

---

## 🔍 變數管理

```javascript
let duplicateFiles = [];         // 收集所有重複的檔案
let skipDuplicates = false;      // 是否跳過所有重複
let overwriteDuplicates = false; // 是否覆蓋所有重複
```

### 狀態流程

```
初始:
├─> duplicateFiles = []
├─> skipDuplicates = false
└─> overwriteDuplicates = false

檢查階段:
├─> 發現重複 → duplicateFiles.push(file)
└─> 繼續檢查...

詢問階段:
├─> 用戶點「確定」→ overwriteDuplicates = true
└─> 用戶點「取消」→ skipDuplicates = true

上傳階段:
├─> if (isDuplicate && skipDuplicates) → 跳過
├─> if (isDuplicate && overwriteDuplicates) → 加 force=true
└─> 否則 → 正常上傳
```

---

## ⚠️ 後端兼容性

**無需修改後端**！後端 API 已經支援：

1. **檢查重複**: 返回 `warning: 'duplicate_detected'`
2. **強制覆蓋**: 接受 `force=true` 參數

---

## 🎯 優勢對比

| 項目 | 舊版（逐個詢問） | 新版（批次處理） |
|------|----------------|-----------------|
| **彈窗次數** | 每個重複檔案 1 次 | 全部重複檔案 1 次 |
| **用戶點擊** | N 次（N = 重複數量） | 1 次 |
| **處理一致性** | 可能不一致 | 統一處理 |
| **中斷次數** | 多次中斷上傳 | 僅開始前詢問一次 |
| **可見性** | 逐個發現 | 一次性列出所有 |
| **用戶體驗** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 📝 技術細節

### 檢查重複的實作

**為什麼不直接檢查檔案系統？**

因為前端無法直接訪問伺服器檔案系統，所以：
1. 發送請求到後端
2. 後端檢查檔案是否存在
3. 返回 `warning: 'duplicate_detected'`
4. 前端收集重複檔案

**不會真的上傳兩次嗎？**

是的，檢查階段會發送請求，但：
- 如果後端返回重複警告，**檔案不會被保存**
- 第二階段上傳時，帶 `force=true` 才會真正保存
- 所以不會有重複保存的問題

---

## 📊 測試案例

### 案例 1: 沒有重複檔案

```
8 個檔案，全部都是新檔案
├─> 檢查階段: 0-30%，無重複發現
├─> 不彈出對話框
└─> 直接進入上傳階段: 30-100%
```

### 案例 2: 全部重複 + 選擇覆蓋

```
8 個檔案，全部重複
├─> 檢查階段: 發現 8 個重複
├─> 彈出對話框，用戶選「確定」
├─> 上傳階段: 8 個檔案全部帶 force=true 上傳
└─> 結果: 8 個檔案全部覆蓋成功
```

### 案例 3: 部分重複 + 選擇跳過

```
8 個檔案，3 個重複
├─> 檢查階段: 發現 3 個重複
├─> 彈出對話框，用戶選「取消」
├─> 上傳階段:
│   ├─> 3 個重複檔案跳過
│   └─> 5 個新檔案正常上傳
└─> 結果: 成功上傳 5 個檔案
```

---

## 🔄 完整流程圖

```
用戶選擇多個檔案
        ↓
handleSTLFiles() 驗證格式
        ↓
uploadSTLFiles() 開始
        ↓
checkDuplicates() 檢查階段
        ↓
    逐個檢查
    /        \
發現重複    沒重複
    ↓          ↓
收集到陣列  繼續
    ↓          ↓
檢查完成 ←────┘
    ↓
有重複？
  /    \
 是    否
  ↓      ↓
彈窗詢問  直接上傳
  ↓
用戶選擇
  /    \
覆蓋   跳過
  ↓      ↓
uploadNextFile() 上傳階段
        ↓
    逐個上傳
    /        \
是重複？    不重複
  /    \        ↓
覆蓋  跳過   正常上傳
  ↓    ↓        ↓
帶force  不上傳  上傳
  ↓    ↓        ↓
全部完成 ←───────┘
        ↓
顯示統計結果
```

---

## 📝 總結

### 核心改進

- 📋 **批次收集**: 一次性收集所有重複檔案
- 🎯 **統一處理**: 同一種方式處理所有重複
- 🚀 **一次詢問**: 只彈出一次確認對話框
- 📊 **清晰進度**: 分為檢查（0-30%）和上傳（30-100%）

### 用戶體驗提升

- ✅ 減少點擊次數（N 次 → 1 次）
- ✅ 提升處理一致性
- ✅ 減少中斷次數
- ✅ 提供清晰的重複檔案列表

---

**版本**: v3.8
**更新**: 批次重複檔案處理
**狀態**: ✅ 已實作
**影響範圍**: 前端 JavaScript
**功能影響**: 大幅提升多檔案上傳的用戶體驗
