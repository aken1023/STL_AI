# 🖼️ 識別結果參考圖片縮圖功能

## 📋 更新日期
**2025-10-04**

## ✨ 功能概述

識別結果現在會顯示**最接近的參考圖片縮圖**，讓您清楚看到系統是根據哪些訓練圖片做出識別判斷。

---

## 🎯 功能特點

### ✅ 智能匹配
- 顯示 FAISS 找到的**最相似的前5張**參考圖片
- 按相似度從高到低排序
- 自動標示最相似的圖片

### ✅ 視覺化呈現
- 網格式縮圖顯示
- 每張圖片顯示相似度百分比
- 懸停效果（陰影、放大、高亮邊框）
- 響應式設計（手機、平板、桌面自適應）

### ✅ 互動功能
- 點擊縮圖查看大圖
- 懸停顯示詳細資訊
- 最相似的圖片有紅色「最相似」標籤

---

## 🖥️ 顯示效果

### 識別結果佈局

```
┌─────────────────────────────────────────────────────────┐
│  📁 上傳原圖          │  🎯 識別結果                     │
│  ┌──────────┐         │  識別結果: R8107490              │
│  │          │         │  置信度: 95.3%                   │
│  │  原圖    │         │  推論時間: 15ms                  │
│  │          │         │  檢測方式: FAISS 物件檢測        │
│  └──────────┘         │                                  │
├─────────────────────────────────────────────────────────┤
│  🖼️ 最接近的參考圖片 (共 5 張)                          │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐          │
│  │[最  │  │     │  │     │  │     │  │     │          │
│  │相似]│  │     │  │     │  │     │  │     │          │
│  │ img │  │ img │  │ img │  │ img │  │ img │          │
│  │ 001 │  │ 045 │  │ 089 │  │ 123 │  │ 156 │          │
│  │⭐98%│  │⭐96%│  │⭐94%│  │⭐92%│  │⭐90%│          │
│  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘          │
└─────────────────────────────────────────────────────────┘
```

### 實際 HTML 結構

```html
<div class="mt-3">
    <h6 class="text-muted mb-2">
        <i class="fas fa-images"></i> 最接近的參考圖片
        <small class="text-muted">(共 5 張)</small>
    </h6>
    <div class="reference-gallery row g-2">
        <!-- 參考圖片 1 - 最相似 -->
        <div class="col-4 col-md-3 col-lg-2">
            <div class="reference-item position-relative">
                <img src="/static/ref_R8107490_img_001.png"
                     class="img-fluid rounded border reference-thumbnail"
                     onclick="showImage(...)"
                     title="相似度: 98.5%">
                <div class="position-absolute bottom-0 bg-dark bg-opacity-75 text-white">
                    <i class="fas fa-star text-warning"></i> 98.5%
                </div>
                <div class="position-absolute top-0 end-0 badge bg-danger m-1">
                    最相似
                </div>
            </div>
        </div>

        <!-- 參考圖片 2-5 類似結構... -->
    </div>
</div>
```

---

## 🔧 技術實作

### **後端處理** (`web_interface.py`)

#### 1. **FAISS 預測包裝函數** (Lines 221-294)

```python
def predict_with_faiss_wrapper(image_path):
    """FAISS 預測包裝函數，統一輸出格式"""
    result = predict_with_faiss(image_path)

    # 獲取詳細匹配結果
    detailed_results = result.get('detailed_results', [])

    for pred in result['predictions']:
        reference_images = []
        class_name = pred['class_name']

        # 找出該類別最相似的前5個結果
        class_matches = [d for d in detailed_results
                        if d['class_name'] == class_name]
        class_matches = sorted(class_matches,
                              key=lambda x: x['confidence'],
                              reverse=True)[:5]

        for match in class_matches:
            ref_image_path = match.get('reference_image')
            if ref_image_path and os.path.exists(ref_image_path):
                # 複製到 static 資料夾
                img_name = os.path.basename(ref_image_path)
                static_filename = f"ref_{class_name}_{img_name}"
                static_path = os.path.join('static', static_filename)

                shutil.copy2(ref_image_path, static_path)

                reference_images.append({
                    'filename': img_name,
                    'url': f"/static/{static_filename}",
                    'confidence': match['confidence']  # 包含相似度
                })

        formatted_predictions.append({
            'class_name': pred['class_name'],
            'confidence': pred['confidence'],
            'reference_images': reference_images  # 最相似的5張圖片
        })
```

**關鍵特點**：
- ✅ 從 `detailed_results` 提取最相似的匹配
- ✅ 每個匹配包含 `reference_image` 路徑和 `confidence`
- ✅ 只選擇同類別中相似度最高的前5張
- ✅ 自動複製圖片到 static 目錄供網頁訪問

---

### **前端顯示** (`index_sidebar.html`)

#### 1. **參考圖片渲染** (Lines 2518-2549)

```javascript
if (prediction.reference_images && prediction.reference_images.length > 0) {
    itemHTML += `
        <div class="mt-3">
            <h6 class="text-muted mb-2">
                <i class="fas fa-images"></i> 最接近的參考圖片
                <small class="text-muted">(共 ${prediction.reference_images.length} 張)</small>
            </h6>
            <div class="reference-gallery row g-2">
    `;

    prediction.reference_images.forEach((refImg, idx) => {
        const confidencePercent = ((refImg.confidence || 0) * 100).toFixed(1);
        itemHTML += `
            <div class="col-4 col-md-3 col-lg-2">
                <div class="reference-item position-relative">
                    <!-- 縮圖 -->
                    <img src="${refImg.url}"
                         class="img-fluid rounded border reference-thumbnail"
                         style="cursor: pointer; aspect-ratio: 1/1;"
                         onclick="showImage('${refImg.url}', '${refImg.filename}')"
                         title="相似度: ${confidencePercent}%">

                    <!-- 相似度標籤 -->
                    <div class="position-absolute bottom-0 bg-dark bg-opacity-75 text-white">
                        <i class="fas fa-star text-warning"></i> ${confidencePercent}%
                    </div>

                    <!-- 最相似標記 -->
                    ${idx === 0 ? '<div class="badge bg-danger m-1">最相似</div>' : ''}
                </div>
            </div>
        `;
    });

    itemHTML += `</div></div>`;
}
```

#### 2. **CSS 樣式** (Lines 826-846)

```css
/* 參考圖片縮圖容器 */
.reference-item {
    transition: all 0.3s ease;
    border-radius: 8px;
    overflow: hidden;
}

.reference-item:hover {
    transform: translateY(-5px);        /* 懸停上浮 */
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);  /* 陰影效果 */
}

.reference-thumbnail {
    transition: all 0.3s ease;
    border: 2px solid rgba(255,255,255,0.2);
}

.reference-thumbnail:hover {
    border-color: #ffc107;              /* 金色邊框 */
    box-shadow: 0 0 15px rgba(255,193,7,0.5);  /* 發光效果 */
}
```

---

## 📊 數據流程

### **完整識別流程**

```
1. 用戶上傳圖片
    ↓
2. 前端發送 POST /api/upload
    ↓
3. 後端呼叫 predict_with_faiss_wrapper()
    ↓
4. FAISS 返回 detailed_results（包含所有匹配）
    [
        {
            'class_name': 'R8107490',
            'confidence': 0.985,
            'reference_image': 'dataset/R8107490/img_001.png'
        },
        {
            'class_name': 'R8107490',
            'confidence': 0.962,
            'reference_image': 'dataset/R8107490/img_045.png'
        },
        ...
    ]
    ↓
5. 後端過濾並排序
    - 只保留同類別的匹配
    - 按 confidence 降序排列
    - 取前5個
    ↓
6. 複製圖片到 static/
    dataset/R8107490/img_001.png
        → static/ref_R8107490_img_001.png
    ↓
7. 返回給前端
    {
        'predictions': [{
            'class_name': 'R8107490',
            'confidence': 0.985,
            'reference_images': [
                {
                    'url': '/static/ref_R8107490_img_001.png',
                    'filename': 'img_001.png',
                    'confidence': 0.985
                },
                ...
            ]
        }]
    }
    ↓
8. 前端顯示
    - 渲染縮圖網格
    - 顯示相似度百分比
    - 添加互動效果
```

---

## 🎨 視覺化特效

### **縮圖效果**

| 狀態 | 效果 |
|------|------|
| **正常** | 半透明白色邊框 |
| **懸停** | 金色邊框 + 發光效果 + 上浮 5px |
| **點擊** | 顯示大圖（全螢幕檢視） |

### **相似度標籤**

```
┌─────────────┐
│  [最相似]   │ ← 紅色標籤（僅第一張）
│             │
│   縮圖      │
│             │
│ ⭐ 98.5%   │ ← 黑底半透明，金色星星
└─────────────┘
```

### **響應式佈局**

| 螢幕寬度 | 每行顯示 | 列數 |
|---------|---------|------|
| < 768px (手機) | 3 張 | `col-4` |
| 768px - 992px (平板) | 4 張 | `col-md-3` |
| > 992px (桌面) | 6 張 | `col-lg-2` |

---

## 💡 使用範例

### **範例 1: 單一識別結果**

**上傳圖片**: `my_ring.jpg`

**識別結果**:
```
🎯 識別結果: R8107490
置信度: 95.3%
推論時間: 15ms

🖼️ 最接近的參考圖片 (共 5 張):
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│[最相似]│ │        │ │        │ │        │ │        │
│img_001 │ │img_045 │ │img_089 │ │img_123 │ │img_156 │
│⭐98.5% │ │⭐96.2% │ │⭐94.1% │ │⭐92.8% │ │⭐90.5% │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

**說明**:
- 系統找到 5 張最相似的訓練圖片
- 第一張 `img_001.png` 相似度最高 (98.5%)
- 所有圖片都來自 `R8107490` 類別
- 點擊任一縮圖可查看大圖

---

### **範例 2: 多物件識別**

**上傳圖片**: `jewelry_collection.jpg`

**識別結果**:
```
物件 1:
🎯 R8107490 (95.3%)
🖼️ 參考圖片: 5 張 (98.5%, 96.2%, 94.1%, 92.8%, 90.5%)

物件 2:
🎯 R8108140 (89.7%)
🖼️ 參考圖片: 5 張 (92.1%, 88.5%, 85.3%, 82.7%, 80.2%)
```

---

## 🔍 功能優勢

### 🎯 透明度提升

- ✅ 清楚看到系統的判斷依據
- ✅ 了解哪些訓練圖片影響識別結果
- ✅ 驗證識別結果的合理性

### ⚡ 用戶體驗

- ✅ 視覺化的信心指標
- ✅ 快速對比原圖與參考圖
- ✅ 互動式大圖檢視
- ✅ 響應式設計，任何裝置都能使用

### 🔒 可靠性

- ✅ 基於實際特徵匹配結果
- ✅ 按相似度排序，不是隨機選擇
- ✅ 顯示具體相似度數值
- ✅ 可追溯到訓練資料集

---

## ⚠️ 注意事項

### 1. **圖片快取**

參考圖片會被複製到 `static/` 目錄：
- 原始位置: `dataset/R8107490/img_001.png`
- 複製位置: `static/ref_R8107490_img_001.png`

建議定期清理 `static/ref_*` 檔案以節省空間。

### 2. **磁碟空間**

每次識別會複製 5 張參考圖片：
- 每張約 30-50 KB
- 每次識別約 150-250 KB
- 100 次識別約 15-25 MB

### 3. **顯示數量**

目前固定顯示前 5 張最相似圖片。可在後端修改：

```python
# web_interface.py:246
class_matches = sorted(class_matches,
                      key=lambda x: x['confidence'],
                      reverse=True)[:5]  # 修改這裡的數字
```

---

## 🛠️ 自訂設定

### **調整縮圖大小**

修改 `index_sidebar.html:2534`:

```html
<!-- 小縮圖 (60x60) -->
<img style="width: 60px; height: 60px;">

<!-- 中縮圖 (100x100) -->
<img style="width: 100px; height: 100px;">

<!-- 大縮圖 (150x150) -->
<img style="width: 150px; height: 150px;">

<!-- 響應式 (寬度100%, 1:1比例) -->
<img style="width: 100%; aspect-ratio: 1/1;">
```

### **調整每行顯示數量**

修改 Bootstrap 列類別:

```html
<!-- 每行 3 張 -->
<div class="col-4">

<!-- 每行 4 張 -->
<div class="col-3">

<!-- 每行 6 張 -->
<div class="col-2">
```

### **隱藏相似度標籤**

移除或註解掉 `index_sidebar.html:2537-2539`:

```html
<!-- 註解掉這段即可隱藏相似度 -->
<!--
<div class="position-absolute bottom-0 bg-dark bg-opacity-75">
    <i class="fas fa-star text-warning"></i> ${confidencePercent}%
</div>
-->
```

---

## 🎉 總結

### 核心價值

**透明、直觀、可信賴**的識別結果展示

### 主要功能

- 🎯 **智能匹配**: 顯示最相似的前5張參考圖片
- 📊 **相似度顯示**: 每張圖片顯示具體相似度百分比
- 🖼️ **視覺化呈現**: 網格式縮圖，美觀易讀
- 🔍 **大圖檢視**: 點擊縮圖查看完整圖片
- 📱 **響應式設計**: 適配所有裝置

### 適用場景

- ✅ 驗證識別結果
- ✅ 理解系統判斷依據
- ✅ 對比訓練資料
- ✅ 除錯和優化

---

**版本**: v3.0
**更新**: 參考圖片縮圖顯示功能
**狀態**: ✅ 已上線
**相關檔案**:
- `web_interface.py` (後端)
- `templates/index_sidebar.html` (前端)
- `faiss_recognition.py` (FAISS 引擎)
