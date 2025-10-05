# STL 識別系統完整使用指南

## 📋 系統概述

本系統提供完整的 STL 3D 模型識別解決方案，包含：
- STL 檔案管理與圖片生成
- FAISS 特徵向量訓練
- 圖片上傳識別
- Web 管理介面

## 🚀 快速開始

### 訪問系統
```
http://localhost:8082
```

### 主要功能頁面

| 頁面 | 路徑 | 功能 |
|------|------|------|
| 首頁 | `/` | 系統儀表板 |
| 圖片識別 | `/recognition` | 上傳圖片進行識別 |
| 訓練控制 | `/training` | FAISS 模型訓練 |
| STL 管理 | `/stl` | STL 檔案列表 |
| STL 上傳 | `/stl/upload` | 上傳新的 STL 檔案 |
| 圖片生成 | `/stl/generate` | 從 STL 生成訓練圖片 |

## 📊 目前系統狀態

### 已訓練模型
- **識別引擎**: FAISS (IndexFlatIP)
- **特徵模型**: ResNet50 (ImageNet 預訓練)
- **類別數量**: 18 個
- **訓練圖片**: 996 張
- **特徵維度**: 2048 維
- **訓練時間**: 2025-10-05 15:42

### 訓練類別列表
```
[ 0] 600980-65-版-BN-OK-GT (60 張)
[ 1] 601400-92-75-貨-BN-倒14K黃-GT (15 張)
[ 2] 604650-65-貨-BN-倒PT950補口含釕 (60 張)
[ 3] BN-H06-MQ160X80-磁鐵款-貨-GT (60 張)
[ 4] BN-S07-7-1-磁铁款-版-GT白銅104 (60 張)
[ 5] BN-S07-7-2-磁铁款-版-GT-白銅104 (60 張)
[ 6] BN-S07-7-3-磁铁款-版-GT-白銅104 (60 張)
[ 7] R8113139-TW (60 張)
[ 8] R8113597-105胶膜版-倒银 (60 張)
[ 9] R8113743 (60 張)
[10] R8113865EW (60 張)
[11] R8113930-版 (60 張)
[12] R8113978 (60 張)
[13] R8116440 (21 張)
[14] R8126257-A-铝模版-ok (60 張)
[15] R8128945-A-铝模版-OK (60 張)
[16] R8128946-A-铝模版-OK (60 張)
[17] SO1249-RD80-17471-7-貨-JA-倒14K黃 (60 張)
```

## 🔧 完整工作流程

### 1. 添加新的 STL 模型

#### 步驟 1：上傳 STL 檔案
1. 訪問 `/stl/upload`
2. 選擇 STL 檔案上傳
3. 系統會自動保存到 `STL/` 目錄

#### 步驟 2：生成訓練圖片

**方案 A：基本彩色渲染**（當前使用）
```bash
python3 generate_images_color.py
```
- 每個 STL 生成 360 張圖片
- 6 種顏色層
- 多角度覆蓋

**方案 B：真實感渲染**（改進版）
```bash
python3 generate_realistic_images.py
```
- 每個 STL 生成 100 張圖片
- 5 種材質（金、銀、銅、白色塑料、灰色塑料）
- 多光源設置
- 數據增強（亮度、對比度、銳度、模糊、噪點）

生成的圖片會保存到：
- 方案 A: `dataset/[模型名稱]/`
- 方案 B: `dataset_realistic/[模型名稱]/`

### 2. 訓練 FAISS 模型

#### 透過 Web 介面訓練（推薦）
1. 訪問 `/training`
2. 點擊「開始訓練」
3. 系統會自動：
   - 掃描 `dataset/` 目錄
   - 提取 ResNet50 特徵
   - 建立 FAISS 索引
   - 保存模型檔案

#### 透過命令行訓練
```bash
python3 faiss_recognition.py
```

訓練完成後會生成：
- `faiss_features.index` - FAISS 索引文件
- `faiss_labels.pkl` - 標籤文件

### 3. 進行圖片識別

#### 方法 A：Web 介面（推薦）
1. 訪問 `/recognition`
2. 拖拉或選擇圖片
3. 點擊「開始批次識別」
4. 查看識別結果

#### 方法 B：命令行測試
```bash
python3 -c "
from faiss_recognition import predict_with_faiss

result = predict_with_faiss('path/to/image.jpg')
if result:
    for pred in result['predictions'][:3]:
        print(f\"{pred['class_name']}: {pred['confidence']*100:.2f}%\")
"
```

## 📈 識別結果說明

識別結果包含以下資訊：

| 欄位 | 說明 |
|------|------|
| class_id | 分類編號（0-17） |
| class_name | 分類名稱 |
| confidence | 信心度（0-1） |
| inference_time | 推論時間（毫秒） |
| top_k | Top 5 相似結果 |
| vote_count | 投票數量 |

### FAISS 投票機制
- 系統尋找 K=5 個最相似的特徵向量
- 統計每個類別的投票數
- 計算平均信心度
- 返回最高分數的類別

## ⚠️ 重要限制

### 當前訓練數據
✅ **可以識別**：STL 3D 渲染圖
❌ **無法準確識別**：實物照片

### 原因
- 訓練數據：STL 3D 模型的彩色渲染圖
- 特徵差異：實物照片的材質、光照、背景與渲染圖不同
- ResNet50 提取的特徵向量差異過大

### 解決方案

**選項 1：收集實物照片（最有效）**
1. 為每個 STL 模型拍攝 20-50 張實物照片
2. 將照片放到對應的 `dataset/[模型名稱]/` 目錄
3. 重新訓練 FAISS 模型

**選項 2：使用改進的渲染**
1. 運行 `generate_realistic_images.py`
2. 生成多材質、多光照的渲染圖
3. 使用 `dataset_realistic/` 重新訓練
4. 效果會改善但仍有限

**選項 3：混合訓練（推薦）**
1. 保留 STL 渲染圖
2. 添加實物照片到同一目錄
3. 重新訓練，讓模型同時學習兩種特徵

## 🔄 重新訓練流程

### 1. 準備數據
```bash
# 檢查數據集
ls dataset/*/  # 查看每個類別的圖片數量

# 或使用改進的數據集
ls dataset_realistic/*/
```

### 2. 刪除舊模型
```bash
rm -f faiss_features.index faiss_labels.pkl
```

### 3. 開始訓練

**Web 介面**：
1. 訪問 `/training`
2. 點擊「開始訓練」
3. 等待訓練完成（約 5-10 分鐘）

**命令行**：
```bash
python3 faiss_recognition.py
```

### 4. 驗證模型
```bash
python3 -c "
import faiss
import pickle

# 檢查索引
index = faiss.read_index('faiss_features.index')
print(f'特徵向量總數: {index.ntotal}')

# 檢查標籤
with open('faiss_labels.pkl', 'rb') as f:
    data = pickle.load(f)
    print(f'類別總數: {len(data[\"classes\"])}')
    print(f'類別列表: {data[\"classes\"]}')
"
```

## 🛠️ 故障排除

### 問題 1：訓練失敗
**症狀**：訓練時出現錯誤或中斷

**解決**：
```bash
# 檢查數據集完整性
ls -R dataset/ | grep -c "\.png\|\.jpg"

# 重新生成圖片
python3 generate_images_color.py

# 清理舊模型後重試
rm -f faiss_features.index faiss_labels.pkl
```

### 問題 2：識別準確率低
**症狀**：上傳圖片後識別結果不正確

**可能原因**：
1. 上傳的是實物照片（訓練數據是渲染圖）
2. 圖片角度差異太大
3. 圖片模糊或質量差

**解決**：
1. 使用 STL 渲染圖測試（從 `dataset/` 中選擇）
2. 收集實物照片重新訓練
3. 確保圖片清晰、光照良好

### 問題 3：Web 介面無法訪問
**症狀**：無法打開 http://localhost:8082

**解決**：
```bash
# 檢查服務是否運行
ps aux | grep web_interface

# 重啟服務
pkill -f web_interface
python3 web_interface.py
```

## 📦 系統檔案結構

```
STL/
├── STL/                          # STL 模型檔案
│   ├── *.stl                     # 18 個 STL 檔案
├── dataset/                      # 訓練數據集（當前）
│   ├── [模型名稱]/
│   │   ├── img_001.png
│   │   ├── img_002.png
│   │   └── ...                   # 每個模型 60-360 張
├── dataset_realistic/            # 真實感渲染數據集（可選）
│   ├── [模型名稱]/
│   │   └── img_*.png             # 每個模型 100 張
├── web_uploads/                  # Web 上傳的圖片
├── faiss_features.index          # FAISS 索引（7.8 MB）
├── faiss_labels.pkl              # 標籤文件（63 KB）
├── templates/                    # Web 介面模板
│   ├── recognition/
│   ├── training/
│   └── stl/
├── generate_images_color.py      # 基本彩色渲染
├── generate_realistic_images.py  # 真實感渲染
├── faiss_recognition.py          # FAISS 訓練與預測
└── web_interface.py              # Web 主程式
```

## 🎯 最佳實踐

### 數據收集
1. **多角度拍攝**：至少 20 個不同角度
2. **統一光照**：使用一致的光照條件
3. **清晰對焦**：確保物體清晰
4. **簡潔背景**：使用純色或簡單背景

### 訓練建議
1. **數據平衡**：每個類別圖片數量盡量相近
2. **定期重訓**：添加新數據後重新訓練
3. **備份模型**：定期備份 `.index` 和 `.pkl` 檔案

### 識別建議
1. **相似條件**：識別時的拍攝條件接近訓練數據
2. **批次識別**：一次識別多張提高效率
3. **查看 Top K**：參考前 5 個結果，不只看第一名

## 📞 技術支援

### 系統資訊
- **Python 版本**：3.8+
- **主要依賴**：FAISS, PyTorch, PyVista, Flask
- **GPU 支援**：✅ CUDA 可用時自動啟用

### 日誌文件
```bash
# Web 服務日誌
tail -f web.log

# 訓練日誌
ls -lt training_logs/
```

---

**版本**：v1.0
**更新日期**：2025-10-05
**維護狀態**：✅ 完整功能
