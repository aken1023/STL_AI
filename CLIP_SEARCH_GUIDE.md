# 🔍 CLIP + FAISS 智能搜尋系統使用指南

## 📋 系統概述

本系統整合了 OpenAI 的 CLIP 模型與 Facebook 的 FAISS 索引技術，提供強大的多模態圖像相似性搜尋功能。

### 核心技術

- **CLIP (Contrastive Language-Image Pre-training)**: OpenAI 的多模態模型，可同時理解圖像和文字
- **FAISS (Facebook AI Similarity Search)**: 高效的向量相似度搜索引擎
- **特徵維度**: 512 維 (ViT-B/32 模型)
- **搜尋速度**: 毫秒級響應
- **資料集**: 4,749 張圖片，18 個類別

---

## 🚀 快速開始

### 1. 建立 CLIP 索引（首次使用）

```bash
# 方法 A: 使用 Python 腳本（推薦）
python clip_feature_extractor.py

# 方法 B: 透過 Web 介面
# 訪問 http://localhost:8082/search/
# 點擊「建立 CLIP 索引」按鈕
```

**處理時間**: 約 5-10 分鐘（取決於資料集大小和硬體）

**生成檔案**:
- `clip_features.npy` - CLIP 特徵向量 (約 10 MB)
- `clip_labels.pkl` - 類別標籤
- `clip_paths.pkl` - 圖片路徑
- `clip_faiss.index` - FAISS 索引檔案

### 2. 訪問搜尋介面

```
http://localhost:8082/search/
```

---

## 🎯 三種搜尋模式

### 模式 1: 圖像搜尋 (Image-to-Image)

**使用情境**:
- 找到與查詢圖片相似的 STL 模型
- 根據實體拍照尋找對應的 3D 模型

**操作步驟**:
1. 點擊「圖像搜尋」標籤
2. 拖拉或選擇圖片
3. 調整返回結果數量 (3-20)
4. 點擊「開始搜尋」

**API 端點**:
```bash
POST /search/api/search/image
Form Data:
  - image: [圖片檔案]
  - k: 5 (返回結果數量)
```

**範例程式碼**:
```python
import requests

url = 'http://localhost:8082/search/api/search/image'
files = {'image': open('test.jpg', 'rb')}
data = {'k': 5}

response = requests.post(url, files=files, data=data)
results = response.json()

for result in results['results']:
    print(f"{result['rank']}. {result['class_name']} - {result['confidence']:.2f}%")
```

---

### 模式 2: 文字搜尋 (Text-to-Image)

**使用情境**:
- 用文字描述搜尋符合特徵的圖片
- 語意化搜尋 (例如: "a metallic ring")

**操作步驟**:
1. 點擊「文字搜尋」標籤
2. 輸入英文描述
3. 調整返回結果數量
4. 點擊「開始搜尋」

**最佳實踐**:
- ✅ 使用英文描述（CLIP 對英文支援最佳）
- ✅ 描述物體特徵（顏色、材質、形狀）
- ✅ 簡潔明確的描述

**範例描述**:
```
✅ 良好: "a metallic ring"
✅ 良好: "a silver jewelry with diamonds"
✅ 良好: "a golden bracelet"

⚠️ 避免: "很漂亮的戒指" (中文)
⚠️ 避免: 過於複雜或抽象的描述
```

**API 端點**:
```bash
POST /search/api/search/text
JSON:
  {
    "text": "a metallic ring",
    "k": 5
  }
```

**範例程式碼**:
```python
import requests

url = 'http://localhost:8082/search/api/search/text'
data = {
    'text': 'a metallic ring',
    'k': 5
}

response = requests.post(url, json=data)
results = response.json()
```

---

### 模式 3: 混合搜尋 (Hybrid Search)

**使用情境**:
- 結合圖像和文字進行更精確的搜尋
- 同時考慮視覺特徵和語意描述

**操作步驟**:
1. 點擊「混合搜尋」標籤
2. 上傳圖片（可選）
3. 輸入文字描述（可選）
4. 調整圖像/文字權重比例
5. 點擊「開始搜尋」

**權重調整**:
- **圖像權重 0.7 / 文字權重 0.3**: 以圖像為主，文字輔助
- **圖像權重 0.5 / 文字權重 0.5**: 平衡模式
- **圖像權重 0.3 / 文字權重 0.7**: 以文字為主，圖像輔助

**API 端點**:
```bash
POST /search/api/search/hybrid
Form Data:
  - image: [圖片檔案] (可選)
  - text: "a metallic ring" (可選)
  - k: 5
  - image_weight: 0.7
```

**範例程式碼**:
```python
import requests

url = 'http://localhost:8082/search/api/search/hybrid'
files = {'image': open('test.jpg', 'rb')} if use_image else {}
data = {
    'text': 'a metallic ring',
    'k': 5,
    'image_weight': 0.7
}

response = requests.post(url, files=files, data=data)
results = response.json()
```

---

## 📊 搜尋結果解讀

### 結果格式

```json
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "class_name": "R8113865EW",
      "image_path": "dataset/R8113865EW/img_001.png",
      "image_url": "/dataset/R8113865EW/img_001.png",
      "similarity": 0.9821,
      "confidence": 98.21
    }
  ],
  "total": 5
}
```

### 相似度指標

- **Similarity (0-1)**: 餘弦相似度，越接近 1 越相似
- **Confidence (0-100%)**: 相似度百分比
- **Rank**: 排名（1 = 最相似）

### 參考標準

| 相似度 | 判斷 | 說明 |
|--------|------|------|
| > 0.95 | 極高相似 | 幾乎相同的物件 |
| 0.85-0.95 | 高度相似 | 同一類型或相近特徵 |
| 0.70-0.85 | 中等相似 | 有部分共同特徵 |
| < 0.70 | 低相似度 | 可能不相關 |

---

## 🔧 進階功能

### 重建索引

**使用情境**:
- 資料集有更新（新增/刪除 STL 檔案）
- 切換不同的 CLIP 模型
- 索引檔案損壞

**方法 1: Web 介面**
```
訪問 /search/
點擊「建立 CLIP 索引」按鈕
```

**方法 2: API**
```bash
curl -X POST http://localhost:8082/search/api/search/rebuild_index
```

**方法 3: 命令列**
```bash
python clip_feature_extractor.py
python clip_faiss_search.py  # 測試索引
```

---

### 查詢索引統計

**API 端點**:
```bash
GET /search/api/search/stats
```

**回應範例**:
```json
{
  "success": true,
  "stats": {
    "total_images": 4749,
    "total_classes": 18,
    "feature_dim": 512,
    "index_type": "IndexFlatIP",
    "class_distribution": {
      "R8113865EW": 360,
      "R8113743": 360,
      ...
    }
  }
}
```

---

## 🎨 CLIP 模型變體

### 可選模型

| 模型 | 特徵維度 | 速度 | 準確度 | 記憶體 |
|------|---------|------|--------|--------|
| ViT-B/32 | 512 | ⚡⚡⚡ | ⭐⭐⭐ | 350 MB |
| ViT-B/16 | 512 | ⚡⚡ | ⭐⭐⭐⭐ | 350 MB |
| ViT-L/14 | 768 | ⚡ | ⭐⭐⭐⭐⭐ | 900 MB |

### 切換模型

修改 `clip_feature_extractor.py`:
```python
extractor = CLIPFeatureExtractor(model_name="ViT-L/14")  # 使用大型模型
```

然後重建索引：
```bash
python clip_feature_extractor.py
```

---

## 🚨 常見問題

### Q1: 索引不存在錯誤

**錯誤訊息**: "CLIP 特徵索引不存在"

**解決方法**:
```bash
python clip_feature_extractor.py
```

---

### Q2: GPU 記憶體不足

**症狀**: CUDA out of memory

**解決方法**:
1. 降低 batch_size:
```python
extractor.build_dataset_index(batch_size=16)  # 預設 32
```

2. 使用 CPU 版本:
```python
extractor = CLIPFeatureExtractor(device="cpu")
```

---

### Q3: 文字搜尋效果不佳

**可能原因**:
- 使用中文描述（CLIP 對英文支援較佳）
- 描述過於抽象

**改善建議**:
- ✅ 使用具體的英文描述
- ✅ 描述視覺特徵（顏色、形狀、材質）
- ✅ 參考範例描述格式

---

### Q4: 搜尋速度慢

**優化建議**:

1. **使用 GPU 加速**:
```python
# 自動檢測並使用 GPU
extractor = CLIPFeatureExtractor()  # 預設會用 GPU
```

2. **使用 FAISS GPU 版本**:
```bash
pip uninstall faiss-cpu
pip install faiss-gpu
```

3. **使用更快的索引類型**:
```python
# 對於大型資料集，使用 IVF 索引
import faiss
index = faiss.IndexIVFFlat(quantizer, d, nlist)
```

---

## 📈 效能基準測試

### 索引建立時間

| 資料集大小 | GPU (CUDA) | CPU |
|-----------|-----------|-----|
| 1,000 張 | ~1 分鐘 | ~3 分鐘 |
| 5,000 張 | ~5 分鐘 | ~15 分鐘 |
| 10,000 張 | ~10 分鐘 | ~30 分鐘 |

### 搜尋速度

| 索引大小 | 單次搜尋時間 |
|---------|-------------|
| 1,000 張 | < 10 ms |
| 5,000 張 | < 20 ms |
| 10,000 張 | < 50 ms |

---

## 🔬 技術原理

### CLIP 工作原理

1. **圖像編碼**: Vision Transformer 提取視覺特徵
2. **文字編碼**: Text Transformer 提取語意特徵
3. **特徵對齊**: 對比學習將圖像和文字映射到同一空間
4. **相似度計算**: 使用餘弦相似度衡量距離

### FAISS 索引策略

本系統使用 **IndexFlatIP** (Inner Product):
- 適合中小型資料集 (< 100K)
- 精確搜索，無損準確率
- 在正規化向量上等同於餘弦相似度

對於大型資料集，可考慮：
- **IndexIVFFlat**: 近似搜索，速度更快
- **IndexHNSW**: 圖索引，平衡速度和準確率

---

## 📚 相關資源

### 官方文件
- [CLIP GitHub](https://github.com/openai/CLIP)
- [CLIP 論文](https://arxiv.org/abs/2103.00020)
- [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)

### 教學資源
- [CLIP Tutorial](https://huggingface.co/docs/transformers/model_doc/clip)
- [FAISS Tutorial](https://www.pinecone.io/learn/faiss-tutorial/)

---

## ✅ 總結

### 系統優勢

✅ **多模態搜尋**: 支援圖像、文字、混合三種模式
✅ **高效索引**: FAISS 提供毫秒級搜尋速度
✅ **語意理解**: CLIP 模型理解視覺和語意關聯
✅ **易於使用**: Web 介面友善，API 完整
✅ **可擴展**: 支援不同 CLIP 模型和 FAISS 索引

### 使用建議

1. **首次使用**: 建立索引 → 測試圖像搜尋 → 嘗試文字搜尋
2. **日常使用**: 圖像搜尋為主，文字搜尋輔助
3. **精確搜尋**: 使用混合模式，調整權重
4. **大型資料集**: 考慮使用 IVF 索引加速

---

**版本**: v1.0
**最後更新**: 2025-10-04
**維護狀態**: ✅ 活躍開發中
