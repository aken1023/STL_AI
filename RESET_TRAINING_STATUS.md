# 🔄 重置訓練狀態功能

## 📋 功能概述

**更新日期**: 2025-10-04

新增「重置訓練狀態」按鈕，可以清除卡住的訓練狀態而不實際停止正在運行的訓練進程。

---

## 🎯 使用場景

### 何時使用此功能？

1. **訓練狀態卡住**: 訓練已完成但介面仍顯示「訓練中」
2. **網頁異常中斷**: 刷新頁面後狀態不同步
3. **多用戶衝突**: 其他用戶的訓練狀態影響當前用戶
4. **調試目的**: 開發/測試時需要快速重置狀態
5. **誤觸訓練**: 意外啟動訓練但不想等待或停止進程

---

## 🔧 功能說明

### 與「停止訓練」的區別

| 功能 | 停止訓練 | 重置狀態 |
|-----|---------|---------|
| **停止訓練進程** | ✅ 是 | ❌ 否 |
| **清除訓練狀態** | ✅ 是 | ✅ 是 |
| **清除訓練會話** | ✅ 是 | ✅ 是 |
| **清空日誌** | ✅ 是 | ✅ 是 |
| **影響正在訓練** | 會終止 | 不影響 |
| **適用情境** | 主動停止訓練 | 狀態卡住/不同步 |

---

## 💻 實作細節

### 後端 API

**位置**: `web_interface.py` Lines 1436-1467

```python
@app.route('/api/reset_training_status', methods=['POST'])
def reset_training_status():
    """重置訓練狀態（不停止訓練進程）"""
    global training_sessions, training_status

    try:
        # 獲取客戶端 IP
        client_ip = request.remote_addr

        # 清除該客戶端的所有訓練會話
        sessions_to_remove = []
        for session_id, session_data in training_sessions.items():
            if session_data.get('client_ip') == client_ip:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del training_sessions[session_id]

        # 重置訓練狀態
        training_status['is_training'] = False
        training_status['current_epoch'] = 0
        training_status['total_epochs'] = 0
        training_status['log_lines'] = []

        return jsonify({
            'success': True,
            'message': '訓練狀態已重置',
            'cleared_sessions': len(sessions_to_remove)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

**重置內容**:
1. 清除該客戶端 IP 的所有訓練會話
2. 重置 `is_training` 為 `False`
3. 清空 epoch 計數器
4. 清空訓練日誌

**保留內容**:
- 實際的訓練進程（如果正在運行）
- 已生成的圖片和模型檔案
- 其他用戶的訓練會話

---

### 前端 UI

**位置**: `index_sidebar.html` Lines 1408-1410

```html
<button class="btn btn-outline-danger" onclick="resetTrainingStatus()">
    <i class="fas fa-sync-alt"></i> 重置狀態
</button>
```

**按鈕樣式**:
- `btn-outline-danger`: 紅色外框（警告但不顯眼）
- 位置：在「驗證模型」和「匯出模型」之後

---

### 前端函數

**位置**: `index_sidebar.html` Lines 5046-5095

```javascript
function resetTrainingStatus() {
    // 確認對話框
    const confirmMsg =
        '⚠️ 重置訓練狀態\n\n' +
        '此操作將會：\n' +
        '1. 清除當前的訓練狀態\n' +
        '2. 重置所有訓練進度\n' +
        '3. 清空訓練日誌\n\n' +
        '注意：這不會停止正在進行的訓練進程\n\n' +
        '確定要繼續嗎？';

    if (!confirm(confirmMsg)) {
        addTrainingLog('❌ 用戶取消重置狀態');
        return;
    }

    addTrainingLog('🔄 正在重置訓練狀態...');

    fetch('/api/reset_training_status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addTrainingLog('✅ 訓練狀態已重置');
            if (data.cleared_sessions > 0) {
                addTrainingLog(`   清除了 ${data.cleared_sessions} 個訓練會話`);
            }

            // 重置前端 UI
            resetTrainingUI();

            // 詢問是否重新載入頁面
            setTimeout(() => {
                if (confirm('狀態已重置。是否重新載入頁面以確保完全重置？')) {
                    location.reload();
                }
            }, 1000);
        } else {
            addTrainingLog('❌ 重置失敗: ' + (data.error || '未知錯誤'));
            alert('重置失敗: ' + (data.error || '未知錯誤'));
        }
    })
    .catch(error => {
        addTrainingLog('❌ 連接錯誤: ' + error.message);
        alert('重置失敗: ' + error.message);
    });
}
```

**執行流程**:
1. 顯示確認對話框（說明不會停止訓練進程）
2. 調用 `/api/reset_training_status`
3. 重置前端 UI (`resetTrainingUI()`)
4. 詢問是否重新載入頁面（可選）

---

## 🎬 使用流程

### 情境：訓練狀態卡住

```
1. 用戶發現訓練已完成但介面仍顯示「訓練中」
   └─> 按鈕被禁用，無法開始新訓練

2. 用戶點擊「重置狀態」按鈕
   └─> 彈出確認對話框

3. 用戶點擊「確定」
   ├─> 調用後端 API
   ├─> 清除訓練會話
   ├─> 重置訓練狀態
   └─> 清空日誌

4. 前端收到成功響應
   ├─> 日誌: ✅ 訓練狀態已重置
   ├─> 日誌:    清除了 1 個訓練會話
   ├─> 重置前端 UI
   └─> 詢問是否重新載入頁面

5. 用戶選擇重新載入
   └─> 頁面刷新，狀態完全重置

6. 用戶現在可以開始新訓練
   └─> 所有按鈕已啟用
```

---

## ⚠️ 注意事項

### 重要警告

1. **不會停止訓練進程**
   - 如果訓練正在後台運行，它會繼續執行
   - 僅清除前端和後端的狀態記錄
   - 如果需要停止訓練，請使用「停止訓練」按鈕

2. **多用戶環境**
   - 只清除當前用戶（IP）的訓練會話
   - 不影響其他用戶的訓練狀態

3. **資料保留**
   - 已生成的圖片不會被刪除
   - 已訓練的模型不會被刪除
   - 只清除記憶體中的狀態

4. **建議重新載入**
   - 重置後建議重新載入頁面
   - 確保前端狀態完全同步

---

## 🔍 問題排查

### 常見問題

**Q: 重置狀態後仍然無法訓練？**
```
A: 嘗試以下步驟：
1. 重新載入頁面（F5）
2. 清除瀏覽器快取
3. 檢查是否有其他用戶正在訓練
4. 使用「停止訓練」按鈕強制停止
```

**Q: 重置狀態會刪除訓練資料嗎？**
```
A: 不會。只清除狀態記錄，資料完全保留：
✅ dataset/ 圖片保留
✅ faiss_features.index 保留
✅ faiss_labels.pkl 保留
❌ 僅清除記憶體中的訓練狀態
```

**Q: 什麼時候應該用「重置狀態」而非「停止訓練」？**
```
A: 使用「重置狀態」當：
- 訓練已完成但介面卡住
- 頁面狀態不同步
- 不想影響正在運行的訓練

使用「停止訓練」當：
- 需要實際終止訓練進程
- 訓練出現錯誤需要中止
- 想要取消當前訓練
```

---

## 📝 總結

### 核心價值
**安全、快速、不破壞性**的狀態重置

### 主要功能

- 🔄 **清除狀態**: 重置所有訓練標記
- 🗑️ **清理會話**: 移除卡住的訓練會話
- 📋 **清空日誌**: 重置訓練日誌
- 🛡️ **保護資料**: 不刪除任何訓練成果
- 👥 **多用戶安全**: 只影響當前用戶

### 使用建議

- ✅ 適用於狀態不同步時
- ✅ 適用於調試和測試
- ✅ 適用於快速重置
- ❌ 不適用於停止訓練進程
- ❌ 不適用於清理訓練資料

---

**版本**: v3.6
**更新**: 重置訓練狀態功能
**狀態**: ✅ 已實作
**影響範圍**: 後端 API + 前端 UI
**功能影響**: 新增狀態重置功能，解決狀態卡住問題
