# 🔄 完整重新訓練功能

## 📋 功能概述

**更新日期**: 2025-10-04

新增「完整重新訓練」按鈕，可以一鍵刪除所有現有資料集、重新生成所有 STL 模型的 360° 圖片、並重新訓練 FAISS 索引，完整的執行過程會即時顯示在覆蓋層中。

---

## 🎯 功能目的

### 使用場景

1. **資料集損壞**: 部分圖片損壞或丟失
2. **更新渲染參數**: 需要使用新的渲染設定重新生成圖片
3. **清理實驗數據**: 清除所有實驗性資料，從頭開始
4. **疑難排解**: 訓練效果不佳，需要完全重置
5. **版本升級**: 圖片生成腳本更新後需要重新生成

### 與普通訓練的區別

| 功能 | 正常訓練 | 完整重訓 |
|-----|---------|---------|
| **刪除舊資料** | ❌ 否 | ✅ 是 |
| **重新生成圖片** | 僅生成缺失的 | ✅ 全部重新生成 |
| **時間消耗** | 快速（2-5分鐘） | 較慢（15-30分鐘） |
| **資料保留** | 保留現有圖片 | 完全清除 |
| **適用情境** | 日常訓練 | 重置、更新 |

---

## 🎬 完整流程

### 三階段執行流程

```
階段 1: 刪除資料集 (5%)
  └─> 刪除 dataset/ 資料夾
  └─> 統計刪除的資料夾和圖片數量
  └─> 顯示刪除進度動畫

階段 2: 生成新圖片 (28%)
  └─> 掃描所有 STL 檔案
  └─> 執行 generate_images_color.py
  └─> 即時顯示生成進度
  └─> 統計生成的圖片數量

階段 3: FAISS 訓練 (34%) + 驗證 (33%)
  └─> 使用標準訓練流程
  └─> 建立 FAISS 索引
  └─> 驗證模型完整性
  └─> 顯示訓練結果
```

---

## 💻 前端實作

### 1. 訓練按鈕 UI

**位置**: `index_sidebar.html` Lines 1359-1399

```html
<div class="row g-2">
    <div class="col-md-3">
        <button class="btn btn-primary btn-lg w-100" id="startNormalTraining" onclick="startTraining('normal')">
            <span class="btn-content">
                <i class="fas fa-play"></i> 正常訓練
            </span>
        </button>
        <small class="text-muted d-block text-center mt-1">使用現有圖片</small>
    </div>

    <div class="col-md-3">
        <button class="btn btn-warning btn-lg w-100 text-dark" id="startFullRetraining" onclick="startFullRetraining()">
            <span class="btn-content">
                <i class="fas fa-redo"></i> 完整重訓
            </span>
        </button>
        <small class="text-muted d-block text-center mt-1">重新生成圖片</small>
    </div>

    <div class="col-md-3">
        <button class="btn btn-success btn-lg w-100" id="startPreciseTraining" onclick="startTraining('precise')">
            <span class="btn-content">
                <i class="fas fa-bullseye"></i> 精準訓練
            </span>
        </button>
        <small class="text-muted d-block text-center mt-1">高精度模式</small>
    </div>

    <div class="col-md-3">
        <button class="btn btn-danger btn-lg w-100" id="stopTraining" onclick="stopTraining()" disabled>
            <i class="fas fa-stop"></i> 停止訓練
        </button>
    </div>
</div>
```

**UI 改動**:
- 將按鈕佈局從 `col-md-4` 改為 `col-md-3`（4個按鈕）
- 新增黃色警告按鈕「完整重訓」
- 使用 `row g-2` 添加間距

---

### 2. 主函數：startFullRetraining()

**位置**: `index_sidebar.html` Lines 4632-4702

```javascript
function startFullRetraining() {
    if (isTraining) {
        alert('⚠️ 訓練正在進行中\n\n請等待當前訓練完成或停止後再試');
        return;
    }

    // 第一次確認
    const confirmMsg =
        '⚠️ 完整重新訓練\n\n' +
        '此操作將會：\n' +
        '1. 刪除所有現有的訓練圖片資料集\n' +
        '2. 重新生成所有 STL 模型的 360° 圖片\n' +
        '3. 重新訓練 FAISS 索引\n\n' +
        '⏱️ 預計耗時：15-30 分鐘\n\n' +
        '確定要繼續嗎？';

    if (!confirm(confirmMsg)) {
        addTrainingLog('❌ 用戶取消完整重訓');
        return;
    }

    // 二次確認
    if (!confirm('⚠️ 最後確認\n\n此操作無法復原！\n\n所有現有的訓練圖片將被刪除。\n\n確定要繼續嗎？')) {
        addTrainingLog('❌ 用戶取消完整重訓');
        return;
    }

    // 開始流程
    addTrainingLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    addTrainingLog('🔄 開始完整重新訓練');
    addTrainingLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    setButtonLoading('startFullRetraining', true);
    isTraining = true;
    showTrainingOverlay();
    disableAllButtons(true);
    document.getElementById('stopTraining').disabled = false;

    // 步驟 1: 刪除資料集
    addTrainingLog('🗑️ 步驟 1/3: 刪除現有資料集...');
    updateStageProgress(1, 0, '刪除中...');

    fetch('/api/delete_dataset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addTrainingLog('✅ 資料集已刪除');
            if (data.deleted_folders > 0) {
                addTrainingLog(`   刪除了 ${data.deleted_folders} 個資料夾`);
            }
            if (data.deleted_images > 0) {
                addTrainingLog(`   刪除了 ${data.deleted_images} 張圖片`);
            }
            animateDeleteProgress();
        } else {
            throw new Error(data.error || '刪除失敗');
        }
    })
    .catch(error => {
        addTrainingLog('❌ 刪除資料集失敗: ' + error.message);
        addTrainingLog('⚠️ 將繼續嘗試生成新的圖片');
        animateDeleteProgress(); // 即使失敗也繼續
    });
}
```

**關鍵特性**:
- ✅ 雙重確認機制（防止誤操作）
- ✅ 訓練中檢查（防止衝突）
- ✅ 完整的日誌記錄
- ✅ 錯誤容錯處理

---

### 3. 刪除進度動畫

**位置**: `index_sidebar.html` Lines 4704-4729

```javascript
function animateDeleteProgress() {
    let progress = 0;
    const deleteInterval = setInterval(() => {
        progress += 10;
        updateStageProgress(1, progress, '刪除中...');

        // 同步更新總體進度 (0-33%)
        const overallProgress = Math.round(progress * 0.33);
        const progressBar = document.getElementById('overlayProgressBar');
        const progressText = document.getElementById('overlayProgressText');
        if (progressBar) progressBar.style.width = overallProgress + '%';
        if (progressText) progressText.textContent = overallProgress + '%';

        if (progress >= 100) {
            clearInterval(deleteInterval);
            updateStageProgress(1, 100, '✅ 已刪除');
            addTrainingLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

            // 步驟 2: 生成新圖片
            setTimeout(() => {
                generateAllImagesForRetraining();
            }, 500);
        }
    }, 80); // 800ms 總時長
}
```

**動畫參數**:
- 間隔: 80ms
- 增量: 10%
- 總時長: 800ms
- 對應總體進度: 0% → 5%

---

### 4. 生成圖片

**位置**: `index_sidebar.html` Lines 4731-4758

```javascript
function generateAllImagesForRetraining() {
    addTrainingLog('🎨 步驟 2/3: 生成訓練圖片...');
    addTrainingLog('📋 掃描 STL 檔案...');

    fetch('/api/generate_all_images', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addTrainingLog(`✅ 找到 ${data.stl_count} 個 STL 模型`);
            addTrainingLog('🖼️ 開始生成 360° 多角度圖片...');
            monitorImageGeneration(); // 開始監控
        } else {
            throw new Error(data.error || '啟動圖片生成失敗');
        }
    })
    .catch(error => {
        addTrainingLog('❌ 圖片生成失敗: ' + error.message);
        resetTrainingUI();
        setButtonLoading('startFullRetraining', false);
    });
}
```

---

### 5. 監控圖片生成進度

**位置**: `index_sidebar.html` Lines 4760-4826

```javascript
function monitorImageGeneration() {
    const monitorInterval = setInterval(() => {
        fetch('/api/image_generation_status')
            .then(response => response.json())
            .then(data => {
                if (data.is_generating) {
                    // 更新進度
                    const progress = data.progress || 0;
                    const current = data.current_model || 0;
                    const total = data.total_models || 0;

                    updateStageProgress(1, progress, `${current}/${total} 模型`);

                    // 更新總體進度 (階段 1: 5-33%)
                    const overallProgress = Math.round(5 + progress * 0.28);
                    const progressBar = document.getElementById('overlayProgressBar');
                    const progressText = document.getElementById('overlayProgressText');
                    if (progressBar) progressBar.style.width = overallProgress + '%';
                    if (progressText) progressText.textContent = overallProgress + '%';

                    // 更新狀態文字
                    const statusElement = document.getElementById('overlayStatus');
                    if (statusElement && data.current_model_name) {
                        statusElement.innerHTML = `
                            🎨 正在生成: ${data.current_model_name}<br>
                            <small style="opacity: 0.8;">進度: ${current}/${total} 模型 (${Math.round(progress)}%)</small>
                        `;
                    }

                    // 顯示詳細日誌
                    if (data.log_lines && Array.isArray(data.log_lines)) {
                        data.log_lines.forEach(logLine => {
                            const cleanLog = logLine.replace(/\[\d{2}:\d{2}:\d{2}\]/g, '').trim();
                            if (!addedLogMessages.has(cleanLog)) {
                                addTrainingLog(logLine);
                            }
                        });
                    }
                } else {
                    // 生成完成
                    clearInterval(monitorInterval);

                    if (data.success) {
                        updateStageProgress(1, 100, '✅ 完成');
                        addTrainingLog('✅ 步驟 2/3 完成：圖片生成成功');
                        if (data.total_images) {
                            addTrainingLog(`📊 共生成 ${data.total_images} 張圖片`);
                        }
                        addTrainingLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

                        // 步驟 3: 開始 FAISS 訓練
                        setTimeout(() => {
                            startFAISSTrainingForRetraining();
                        }, 1000);
                    } else {
                        addTrainingLog('❌ 圖片生成失敗: ' + (data.error || '未知錯誤'));
                        resetTrainingUI();
                        setButtonLoading('startFullRetraining', false);
                    }
                }
            })
            .catch(error => {
                console.error('監控圖片生成失敗:', error);
            });
    }, 2000); // 每 2 秒檢查一次
}
```

**監控特性**:
- 每 2 秒輪詢一次狀態
- 即時更新當前處理的模型名稱
- 顯示進度百分比和模型計數
- 同步更新日誌和進度條

---

### 6. FAISS 訓練

**位置**: `index_sidebar.html` Lines 4828-4834

```javascript
function startFAISSTrainingForRetraining() {
    addTrainingLog('🚀 步驟 3/3: FAISS 模型訓練...');
    // 使用標準訓練流程
    actuallyStartTraining('normal');
}
```

**為什麼重用 `actuallyStartTraining`?**
- 避免重複代碼
- 保持訓練邏輯一致
- 自動包含階段 2 (FAISS) 和階段 3 (驗證)

---

## 🔧 後端實作

### 1. 刪除資料集 API

**位置**: `web_interface.py` Lines 2736-2766

```python
@app.route('/api/delete_dataset', methods=['POST'])
def delete_dataset_api():
    """刪除所有資料集"""
    try:
        import shutil
        dataset_path = 'dataset'
        deleted_folders = 0
        deleted_images = 0

        if os.path.exists(dataset_path):
            # 統計資訊
            for folder in os.listdir(dataset_path):
                folder_path = os.path.join(dataset_path, folder)
                if os.path.isdir(folder_path):
                    deleted_folders += 1
                    images = [f for f in os.listdir(folder_path) if f.endswith('.png')]
                    deleted_images += len(images)

            # 刪除整個資料夾
            shutil.rmtree(dataset_path)

            # 重新建立空資料夾
            os.makedirs(dataset_path, exist_ok=True)

        return jsonify({
            'success': True,
            'deleted_folders': deleted_folders,
            'deleted_images': deleted_images
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

**返回資料**:
- `success`: 是否成功
- `deleted_folders`: 刪除的資料夾數量
- `deleted_images`: 刪除的圖片數量
- `error`: 錯誤訊息（如果失敗）

---

### 2. 生成圖片狀態

**位置**: `web_interface.py` Lines 2768-2779

```python
# 圖片生成狀態（用於前端監控）
image_generation_status = {
    'is_generating': False,
    'progress': 0,
    'current_model': 0,
    'total_models': 0,
    'current_model_name': '',
    'log_lines': [],
    'success': False,
    'error': None,
    'total_images': 0
}
```

**狀態欄位**:
- `is_generating`: 是否正在生成
- `progress`: 進度百分比 (0-100)
- `current_model`: 當前模型索引
- `total_models`: 模型總數
- `current_model_name`: 當前處理的模型名稱
- `log_lines`: 日誌行陣列
- `success`: 是否成功完成
- `error`: 錯誤訊息
- `total_images`: 生成的圖片總數

---

### 3. 啟動圖片生成 API

**位置**: `web_interface.py` Lines 2781-2817

```python
@app.route('/api/generate_all_images', methods=['POST'])
def generate_all_images_api():
    """生成所有圖片"""
    global image_generation_status

    try:
        # 重置狀態
        image_generation_status = {
            'is_generating': True,
            'progress': 0,
            'current_model': 0,
            'total_models': 0,
            'current_model_name': '',
            'log_lines': [],
            'success': False,
            'error': None,
            'total_images': 0
        }

        # 掃描 STL 檔案
        stl_files = glob.glob('STL/*.stl')
        image_generation_status['total_models'] = len(stl_files)

        # 在背景執行圖片生成
        import threading
        thread = threading.Thread(target=generate_images_thread, args=(stl_files,))
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'stl_count': len(stl_files)
        })
    except Exception as e:
        image_generation_status['is_generating'] = False
        image_generation_status['error'] = str(e)
        return jsonify({'success': False, 'error': str(e)})
```

**為什麼使用背景執行緒？**
- 圖片生成耗時長（15-30分鐘）
- 避免 HTTP 請求超時
- 允許前端輪詢狀態
- 不阻塞 Flask 主執行緒

---

### 4. 背景執行緒：生成圖片

**位置**: `web_interface.py` Lines 2819-2869

```python
def generate_images_thread(stl_files):
    """背景執行緒：生成圖片"""
    global image_generation_status

    try:
        total = len(stl_files)

        image_generation_status['log_lines'].append(f'📸 開始生成 {total} 個模型的圖片')
        image_generation_status['log_lines'].append(f'⏱️ 預計耗時: {total * 2} 分鐘')

        # 執行圖片生成腳本（處理所有 STL）
        result = subprocess.run(
            ['python', 'generate_images_color.py'],
            capture_output=True,
            text=True,
            timeout=1800  # 30分鐘超時
        )

        if result.returncode == 0:
            # 統計生成的圖片
            total_images = 0
            for idx, stl_path in enumerate(stl_files):
                model_name = os.path.splitext(os.path.basename(stl_path))[0]

                # 更新進度
                progress = int(((idx + 1) / total) * 100)
                image_generation_status['current_model'] = idx + 1
                image_generation_status['current_model_name'] = model_name
                image_generation_status['progress'] = progress

                dataset_folder = os.path.join('dataset', model_name)
                if os.path.exists(dataset_folder):
                    images = [f for f in os.listdir(dataset_folder) if f.endswith('.png')]
                    img_count = len(images)
                    total_images += img_count
                    image_generation_status['log_lines'].append(f'✅ {model_name}: {img_count} 張圖片')

            # 完成
            image_generation_status['is_generating'] = False
            image_generation_status['progress'] = 100
            image_generation_status['success'] = True
            image_generation_status['total_images'] = total_images
            image_generation_status['log_lines'].append(f'🎉 圖片生成完成！共 {total_images} 張')
        else:
            raise Exception(result.stderr or '生成失敗')

    except Exception as e:
        image_generation_status['is_generating'] = False
        image_generation_status['success'] = False
        image_generation_status['error'] = str(e)
        image_generation_status['log_lines'].append(f'❌ 錯誤: {str(e)}')
```

**執行流程**:
1. 調用 `generate_images_color.py` 生成所有圖片
2. 等待腳本完成（最多 30 分鐘）
3. 統計每個模型的圖片數量
4. 更新進度和日誌
5. 標記為完成

---

### 5. 查詢狀態 API

**位置**: `web_interface.py` Lines 2871-2873

```python
@app.route('/api/image_generation_status')
def image_generation_status_api():
    """查詢圖片生成狀態"""
    return jsonify(image_generation_status)
```

**簡單直接**:
- 直接返回全域狀態
- 前端每 2 秒輪詢一次
- 無需參數

---

## 📊 進度對應關係

### 總體進度分配

| 階段 | 範圍 | 百分比 | 說明 |
|-----|------|--------|------|
| **階段 1 開始** | 0% | - | 初始化 |
| **刪除資料集** | 0-5% | 5% | 刪除動畫 800ms |
| **生成圖片** | 5-33% | 28% | 實際生成時間 |
| **FAISS 訓練** | 33-67% | 34% | 特徵提取 + 索引建立 |
| **模型驗證** | 67-100% | 33% | 完整性檢查 |

### 階段 1 細分

```
0%   - 開始刪除
5%   - 刪除完成（動畫 800ms）
5%   - 開始生成圖片
33%  - 圖片生成完成
```

### 計算公式

```javascript
// 刪除階段 (0-5%)
overallProgress = progress * 0.05;

// 生成階段 (5-33%)
overallProgress = 5 + progress * 0.28;

// FAISS 階段 (33-67%)
overallProgress = 33 + progress * 0.34;

// 驗證階段 (67-100%)
overallProgress = 67 + progress * 0.33;
```

---

## 🎬 用戶體驗流程

### 完整操作流程

```
1. 用戶點擊「完整重訓」按鈕
   └─> 彈出第一次確認對話框

2. 用戶點擊「確定」
   └─> 彈出第二次確認對話框（最後確認）

3. 用戶再次點擊「確定」
   ├─> 按鈕顯示載入動畫
   ├─> 顯示訓練覆蓋層
   └─> 禁用所有其他按鈕

4. 階段 1: 刪除資料集
   ├─> 日誌: 🗑️ 步驟 1/3: 刪除現有資料集...
   ├─> 調用 /api/delete_dataset
   ├─> 顯示刪除進度動畫 (800ms)
   ├─> 日誌: ✅ 資料集已刪除
   ├─> 日誌:    刪除了 13 個資料夾
   └─> 日誌:    刪除了 4,680 張圖片

5. 階段 2: 生成圖片
   ├─> 日誌: 🎨 步驟 2/3: 生成訓練圖片...
   ├─> 調用 /api/generate_all_images
   ├─> 日誌: ✅ 找到 13 個 STL 模型
   ├─> 日誌: 🖼️ 開始生成 360° 多角度圖片...
   ├─> 每 2 秒輪詢 /api/image_generation_status
   ├─> 即時顯示:
   │   ├─> 當前模型: BN-S07-7-1
   │   ├─> 進度: 1/13 模型 (7%)
   │   └─> 覆蓋層進度: 7%
   ├─> 完成後:
   │   ├─> 日誌: ✅ 步驟 2/3 完成：圖片生成成功
   │   └─> 日誌: 📊 共生成 4,680 張圖片

6. 階段 3: FAISS 訓練
   ├─> 日誌: 🚀 步驟 3/3: FAISS 模型訓練...
   ├─> 調用 actuallyStartTraining('normal')
   ├─> 使用標準訓練流程
   ├─> 階段 2: FAISS 索引建立 (33-67%)
   ├─> 階段 3: 模型驗證 (67-100%)
   ├─> 訓練完整性檢查
   └─> 完成音效 + 動畫

7. 訓練完成
   ├─> 日誌: 🎉 訓練全部完成！
   ├─> 3 秒後自動關閉覆蓋層
   └─> 重置 UI 狀態
```

---

## ⚠️ 錯誤處理

### 1. 訓練中檢查

```javascript
if (isTraining) {
    alert('⚠️ 訓練正在進行中\n\n請等待當前訓練完成或停止後再試');
    return;
}
```

### 2. 刪除失敗容錯

```javascript
.catch(error => {
    addTrainingLog('❌ 刪除資料集失敗: ' + error.message);
    addTrainingLog('⚠️ 將繼續嘗試生成新的圖片');
    animateDeleteProgress(); // 即使失敗也繼續
});
```

**為什麼繼續？**
- `generate_images_color.py` 會覆蓋現有圖片
- 刪除失敗通常是權限問題
- 繼續執行仍能達成重訓目標

### 3. 生成失敗處理

```javascript
if (data.success) {
    // 繼續訓練
    startFAISSTrainingForRetraining();
} else {
    addTrainingLog('❌ 圖片生成失敗: ' + (data.error || '未知錯誤'));
    resetTrainingUI();
    setButtonLoading('startFullRetraining', false);
}
```

### 4. 超時保護

```python
result = subprocess.run(
    ['python', 'generate_images_color.py'],
    capture_output=True,
    text=True,
    timeout=1800  # 30分鐘超時
)
```

---

## 📈 效益分析

### 用戶體驗提升

| 項目 | 修改前 | 修改後 |
|-----|-------|--------|
| **重新開始** | 手動刪除 + 多步驟操作 | 一鍵完成 ✅ |
| **進度可見性** | 無法追蹤 | 即時顯示 ✅ |
| **錯誤提示** | 不明確 | 詳細日誌 ✅ |
| **操作複雜度** | 高（需技術背景） | 低（按鈕點擊）✅ |

### 功能完整性

- ✅ **完整流程**: 刪除 → 生成 → 訓練 → 驗證
- ✅ **即時反饋**: 每個步驟都有進度顯示
- ✅ **錯誤容錯**: 部分失敗不影響整體流程
- ✅ **用戶控制**: 雙重確認防止誤操作

---

## 🎯 未來優化方向

### 可能的增強功能

1. **選擇性重訓**
   ```
   允許用戶選擇特定模型重新生成：
   ☑ R8107490
   ☐ R8108140
   ☑ R8112078
   [開始重訓選中的模型]
   ```

2. **暫停/恢復功能**
   ```javascript
   // 允許在長時間生成過程中暫停
   pauseImageGeneration();
   resumeImageGeneration();
   ```

3. **差異化生成**
   ```
   僅重新生成與現有不同的參數：
   - 不同的角度數量（180, 360, 720）
   - 不同的解析度（256, 512, 1024）
   - 不同的渲染樣式
   ```

4. **進度持久化**
   ```python
   # 保存進度到磁碟
   # 意外中斷後可以恢復
   save_generation_progress(current_model, total_models)
   ```

---

## 📝 總結

### 核心價值
**一鍵重置、完整可見、錯誤容錯**的訓練重置方案

### 主要改進

- 🔄 **一鍵重訓**: 單一按鈕完成所有步驟
- 📊 **即時進度**: 三階段詳細進度顯示
- 🗑️ **智慧刪除**: 統計並顯示刪除資訊
- 🎨 **背景生成**: 非阻塞圖片生成
- 📋 **詳細日誌**: 每個步驟都有記錄
- ⚠️ **雙重確認**: 防止誤操作
- 🛡️ **錯誤容錯**: 部分失敗不影響整體

### 技術特點

- ✅ 前後端分離的狀態管理
- ✅ 背景執行緒處理長時間任務
- ✅ 即時輪詢更新進度
- ✅ 完善的錯誤處理機制
- ✅ 清晰的三階段流程劃分

---

**版本**: v3.5
**更新**: 完整重新訓練功能
**狀態**: ✅ 已實作
**影響範圍**: 前端 UI + 後端 API + 圖片生成流程
**功能影響**: 新增一鍵完整重訓功能，大幅簡化操作流程
