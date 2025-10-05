# 🚀 CLIP + FAISS 圖像相似性搜尋引擎架構

**建立日期**: 2025-10-04
**目標**: 整合 CLIP 和 FAISS 打造超強圖像相似性搜尋系統

---

## 📋 目錄

- [系統概述](#系統概述)
- [技術架構](#技術架構)
- [CLIP vs ResNet50 對比](#clip-vs-resnet50-對比)
- [實作計劃](#實作計劃)
- [API 設計](#api-設計)
- [使用場景](#使用場景)

---

## 🎯 系統概述

### 當前架構
```
STL 圖片 → ResNet50 特徵提取 → FAISS 索引 → 相似度搜尋
```

### 升級架構
```
STL 圖片 → CLIP 多模態特徵提取 → FAISS 索引 → 智能相似度搜尋
              ↓
         文字描述 → CLIP 文字編碼 → 跨模態搜尋
```

### 核心優勢

#### CLIP 的優勢
1. **多模態理解**: 同時理解圖像和文字
2. **語義豐富**: 比 ResNet50 更深層的語義理解
3. **零樣本學習**: 無需大量訓練即可識別新類別
4. **文字搜圖**: 支援用自然語言描述搜尋圖片
5. **圖搜圖增強**: 更精準的視覺相似性

#### FAISS 的優勢
1. **超快速搜尋**: 毫秒級響應
2. **大規模支援**: 支援百萬級特徵向量
3. **GPU 加速**: 充分利用硬體資源
4. **多種索引**: 精確搜尋 / 近似搜尋

---

## 🏗️ 技術架構

### 1. 特徵提取層

#### CLIP 模型選擇
```python
# 推薦使用的 CLIP 模型
- ViT-B/32: 快速，適合即時應用
- ViT-L/14: 高精度，適合離線建索引
- RN50x64: 超高精度，需要更多資源
```

#### 特徵維度
```python
# CLIP 特徵維度
ViT-B/32:  512 維
ViT-L/14:  768 維
RN50x64:   1024 維

# ResNet50 (現有)
ResNet50:  2048 維
```

### 2. FAISS 索引結構

```
faiss_indices/
├── clip_vit_b32.index       # CLIP ViT-B/32 索引
├── clip_vit_l14.index        # CLIP ViT-L/14 索引 (可選)
├── resnet50.index            # ResNet50 索引 (保留向後兼容)
├── clip_labels.pkl           # 標籤映射
└── metadata.json             # 索引元數據
```

### 3. 混合搜尋策略

```python
# 策略 1: 純圖像搜尋 (CLIP)
Query Image → CLIP Encoder → FAISS Search → Top-K Results

# 策略 2: 文字搜圖 (跨模態)
Query Text → CLIP Text Encoder → FAISS Search → Top-K Results

# 策略 3: 混合搜尋 (圖 + 文)
Query Image + Text → CLIP Fusion → FAISS Search → Top-K Results

# 策略 4: 多模型融合 (最強)
Query → [CLIP + ResNet50] → Score Fusion → Top-K Results
```

---

## 📊 CLIP vs ResNet50 對比

| 特性 | ResNet50 (現有) | CLIP | 優勢 |
|------|----------------|------|------|
| **特徵維度** | 2048 | 512-1024 | CLIP 更緊湊 |
| **語義理解** | 視覺特徵 | 多模態語義 | ✅ CLIP |
| **文字搜圖** | ❌ 不支援 | ✅ 支援 | ✅ CLIP |
| **零樣本學習** | ❌ 需訓練 | ✅ 原生支援 | ✅ CLIP |
| **搜尋精度** | 高 | 極高 | ✅ CLIP |
| **推理速度** | 快 | 中等 | ✅ ResNet50 |
| **記憶體需求** | 中 | 中-高 | - 相當 |
| **訓練需求** | 需要 | 預訓練即用 | ✅ CLIP |

### 建議策略

**雙引擎模式**：
- 保留 ResNet50 用於快速檢索
- CLIP 用於精確語義搜尋
- 提供選項讓用戶選擇引擎

---

## 🚀 實作計劃

### Phase 1: CLIP 整合 (基礎)

#### 1.1 安裝依賴
```bash
pip install openai-clip torch torchvision
# 或使用 transformers
pip install transformers
```

#### 1.2 創建 CLIP 特徵提取器
```python
# clip_feature_extractor.py
import torch
import clip
from PIL import Image

class CLIPFeatureExtractor:
    def __init__(self, model_name="ViT-B/32", device="cuda"):
        self.device = device
        self.model, self.preprocess = clip.load(model_name, device=device)

    def extract_image_features(self, image_path):
        """提取圖像特徵"""
        image = Image.open(image_path)
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            features = self.model.encode_image(image_input)
            features = features / features.norm(dim=-1, keepdim=True)

        return features.cpu().numpy()[0]

    def extract_text_features(self, text):
        """提取文字特徵"""
        text_input = clip.tokenize([text]).to(self.device)

        with torch.no_grad():
            features = self.model.encode_text(text_input)
            features = features / features.norm(dim=-1, keepdim=True)

        return features.cpu().numpy()[0]
```

#### 1.3 建立 CLIP-FAISS 索引
```python
# clip_faiss_builder.py
import faiss
import numpy as np

class CLIPFAISSIndexBuilder:
    def __init__(self, dimension=512):
        self.dimension = dimension
        # 使用內積索引 (cosine similarity)
        self.index = faiss.IndexFlatIP(dimension)

    def build_from_dataset(self, dataset_dir):
        """從資料集建立索引"""
        extractor = CLIPFeatureExtractor()

        features_list = []
        labels_list = []

        for class_name in os.listdir(dataset_dir):
            class_dir = os.path.join(dataset_dir, class_name)
            for img_file in os.listdir(class_dir):
                img_path = os.path.join(class_dir, img_file)

                # 提取特徵
                features = extractor.extract_image_features(img_path)
                features_list.append(features)
                labels_list.append(class_name)

        # 建立索引
        features_array = np.array(features_list).astype('float32')
        self.index.add(features_array)

        # 保存
        faiss.write_index(self.index, "clip_faiss.index")
        with open("clip_labels.pkl", "wb") as f:
            pickle.dump(labels_list, f)
```

### Phase 2: 智能搜尋 API

#### 2.1 圖像相似性搜尋
```python
@app.route('/api/search/image', methods=['POST'])
def search_by_image():
    """以圖搜圖 API"""
    file = request.files['image']
    k = int(request.form.get('k', 5))

    # 提取特徵
    features = clip_extractor.extract_image_features(file)

    # FAISS 搜尋
    distances, indices = clip_index.search(features.reshape(1, -1), k)

    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            'class_name': labels[idx],
            'similarity': float(distances[0][i]),
            'rank': i + 1
        })

    return jsonify({'success': True, 'results': results})
```

#### 2.2 文字搜圖 API
```python
@app.route('/api/search/text', methods=['POST'])
def search_by_text():
    """文字搜圖 API"""
    query_text = request.json.get('query')
    k = int(request.json.get('k', 5))

    # 提取文字特徵
    features = clip_extractor.extract_text_features(query_text)

    # FAISS 搜尋
    distances, indices = clip_index.search(features.reshape(1, -1), k)

    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            'class_name': labels[idx],
            'similarity': float(distances[0][i]),
            'description': query_text,
            'rank': i + 1
        })

    return jsonify({'success': True, 'results': results})
```

#### 2.3 混合搜尋 API
```python
@app.route('/api/search/hybrid', methods=['POST'])
def hybrid_search():
    """混合搜尋：圖像 + 文字"""
    file = request.files.get('image')
    text = request.form.get('text', '')
    k = int(request.form.get('k', 5))

    # 提取並融合特徵
    img_features = clip_extractor.extract_image_features(file)
    text_features = clip_extractor.extract_text_features(text)

    # 加權融合 (可調整權重)
    alpha = 0.6  # 圖像權重
    beta = 0.4   # 文字權重
    combined_features = alpha * img_features + beta * text_features
    combined_features = combined_features / np.linalg.norm(combined_features)

    # FAISS 搜尋
    distances, indices = clip_index.search(combined_features.reshape(1, -1), k)

    return jsonify({'success': True, 'results': build_results(distances, indices)})
```

### Phase 3: 前端搜尋介面

#### 3.1 搜尋頁面結構
```html
<!-- templates/search/index.html -->
<div class="search-container">
    <!-- 搜尋模式選擇 -->
    <ul class="nav nav-tabs">
        <li><a data-tab="image">以圖搜圖</a></li>
        <li><a data-tab="text">文字搜圖</a></li>
        <li><a data-tab="hybrid">混合搜尋</a></li>
    </ul>

    <!-- 以圖搜圖 -->
    <div id="image-search">
        <div class="upload-area">拖拉圖片或點擊上傳</div>
        <button>搜尋相似圖片</button>
    </div>

    <!-- 文字搜圖 -->
    <div id="text-search">
        <input type="text" placeholder="描述你要找的 STL 模型...">
        <button>搜尋</button>
    </div>

    <!-- 混合搜尋 -->
    <div id="hybrid-search">
        <div class="upload-area">上傳參考圖片</div>
        <input type="text" placeholder="補充文字描述...">
        <button>智能搜尋</button>
    </div>

    <!-- 搜尋結果 -->
    <div class="search-results">
        <!-- 動態載入結果 -->
    </div>
</div>
```

#### 3.2 結果展示
```html
<!-- 搜尋結果卡片 -->
<div class="result-card">
    <img src="/dataset/model_name/img_001.png">
    <div class="result-info">
        <h5>模型名稱</h5>
        <div class="similarity-bar">
            <div class="progress" style="width: 95%">95% 相似</div>
        </div>
        <span class="badge">Rank #1</span>
    </div>
</div>
```

---

## 🎨 進階功能

### 1. 多引擎融合搜尋
```python
def multi_engine_search(query_image, k=10):
    """融合 CLIP 和 ResNet50 的搜尋結果"""

    # CLIP 搜尋
    clip_results = clip_engine.search(query_image, k=k)

    # ResNet50 搜尋
    resnet_results = resnet_engine.search(query_image, k=k)

    # 分數融合 (Reciprocal Rank Fusion)
    fused_scores = {}
    for i, result in enumerate(clip_results):
        fused_scores[result['class']] = 1.0 / (i + 1)

    for i, result in enumerate(resnet_results):
        if result['class'] in fused_scores:
            fused_scores[result['class']] += 0.5 / (i + 1)
        else:
            fused_scores[result['class']] = 0.5 / (i + 1)

    # 排序並返回
    sorted_results = sorted(fused_scores.items(),
                          key=lambda x: x[1], reverse=True)

    return sorted_results[:k]
```

### 2. 智能查詢擴展
```python
# 自動擴展搜尋查詢
query_templates = [
    "a 3D model of {object}",
    "{object} from front view",
    "{object} rendered in high quality",
    "CAD model of {object}"
]

def expand_text_query(base_query):
    """擴展文字查詢以提高召回率"""
    expanded_queries = [template.format(object=base_query)
                       for template in query_templates]

    # 對每個擴展查詢進行搜尋並融合結果
    all_results = []
    for query in expanded_queries:
        results = clip_engine.search_by_text(query)
        all_results.extend(results)

    # 去重並排序
    return deduplicate_and_rank(all_results)
```

### 3. 視覺解釋
```python
# 使用 Grad-CAM 解釋為什麼兩個圖片相似
def explain_similarity(query_img, result_img):
    """生成視覺解釋熱力圖"""
    # 使用 Grad-CAM 顯示關注區域
    attention_map = generate_gradcam(query_img, result_img)

    return {
        'attention_map': attention_map,
        'key_features': extract_key_features(attention_map),
        'explanation': generate_text_explanation(attention_map)
    }
```

---

## 📈 效能優化

### 1. 索引優化
```python
# 使用 IVF 索引加速大規模搜尋
nlist = 100  # 聚類數量
quantizer = faiss.IndexFlatIP(dimension)
index = faiss.IndexIVFFlat(quantizer, dimension, nlist)

# 訓練索引
index.train(training_vectors)
index.add(vectors)

# 搜尋時設定探測範圍
index.nprobe = 10  # 探測 10 個聚類
```

### 2. GPU 加速
```python
# 將索引移至 GPU
res = faiss.StandardGpuResources()
gpu_index = faiss.index_cpu_to_gpu(res, 0, cpu_index)

# 批次搜尋
batch_results = gpu_index.search(batch_queries, k)
```

### 3. 快取策略
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_feature_extraction(image_hash):
    """快取特徵提取結果"""
    return clip_extractor.extract_features(image_hash)
```

---

## 🔧 配置檔案

```yaml
# config/search_config.yaml
clip:
  model_name: "ViT-B/32"  # 或 "ViT-L/14"
  device: "cuda"
  batch_size: 32

faiss:
  index_type: "IVFFlat"  # 或 "Flat", "HNSW"
  nlist: 100
  nprobe: 10
  dimension: 512

search:
  default_k: 5
  max_k: 20
  fusion_weights:
    clip: 0.7
    resnet: 0.3

similarity_threshold: 0.5
```

---

## 📊 評估指標

### 搜尋品質指標
```python
# 評估搜尋引擎效能
metrics = {
    'precision@k': calculate_precision_at_k(results, ground_truth, k=5),
    'recall@k': calculate_recall_at_k(results, ground_truth, k=5),
    'mrr': calculate_mean_reciprocal_rank(results, ground_truth),
    'ndcg': calculate_ndcg(results, ground_truth)
}
```

### 效能指標
```python
performance = {
    'index_build_time': measure_build_time(),
    'search_latency_p50': measure_search_latency(percentile=50),
    'search_latency_p95': measure_search_latency(percentile=95),
    'throughput': measure_throughput()
}
```

---

## 🎯 使用場景

### 場景 1: 找相似 STL 模型
```python
# 用戶上傳一張圖片，找最相似的 STL 模型
query_img = "user_upload.jpg"
results = clip_search_engine.search_by_image(query_img, k=10)

# 結果：Top 10 最相似的 STL 模型
```

### 場景 2: 自然語言搜尋
```python
# 用戶輸入文字描述
query = "銀色戒指，有鑽石，圓形"
results = clip_search_engine.search_by_text(query, k=5)

# 結果：符合描述的 STL 模型
```

### 場景 3: 品質檢測
```python
# 比對生產品與原始 STL 的相似度
production_img = "production_sample.jpg"
original_stl = "original_model.stl"

similarity = clip_search_engine.compare_similarity(
    production_img,
    original_stl
)

if similarity < 0.9:
    alert("品質異常！相似度僅 {similarity*100}%")
```

### 場景 4: 自動分類
```python
# 自動將新 STL 分類到現有類別
new_stl = "new_model.stl"
top_class = clip_search_engine.classify(new_stl)

print(f"建議分類: {top_class['name']} (信心度: {top_class['confidence']})")
```

---

## 🚀 部署建議

### 開發環境
```bash
# 本地測試
python clip_faiss_engine.py --mode dev --device cpu
```

### 生產環境
```bash
# GPU 伺服器
python clip_faiss_engine.py --mode prod --device cuda --workers 4

# 使用 Docker
docker run -it --gpus all \
  -v ./data:/data \
  -p 8082:8082 \
  stl-clip-search:latest
```

### 微服務架構
```
├── Feature Extraction Service (CLIP)
├── FAISS Search Service
├── API Gateway
└── Web Frontend
```

---

## 📝 下一步行動

### 立即實作 (Priority 1)
- [ ] 安裝 CLIP 依賴
- [ ] 創建 CLIP 特徵提取器
- [ ] 建立 CLIP-FAISS 索引
- [ ] 實作基本搜尋 API

### 短期目標 (Priority 2)
- [ ] 開發搜尋介面
- [ ] 實作文字搜圖
- [ ] 添加混合搜尋
- [ ] 效能測試與優化

### 長期目標 (Priority 3)
- [ ] 多引擎融合
- [ ] 視覺解釋功能
- [ ] 自動查詢擴展
- [ ] 生產環境部署

---

## 📚 參考資源

### CLIP 資源
- [OpenAI CLIP](https://github.com/openai/CLIP)
- [Hugging Face CLIP](https://huggingface.co/openai/clip-vit-base-patch32)
- [CLIP 論文](https://arxiv.org/abs/2103.00020)

### FAISS 資源
- [FAISS GitHub](https://github.com/facebookresearch/faiss)
- [FAISS 文檔](https://faiss.ai/)
- [FAISS 教學](https://github.com/facebookresearch/faiss/wiki)

---

**版本**: v1.0
**狀態**: 📋 規劃完成，準備實作
**預期效果**: 🚀 超強圖像相似性搜尋引擎
