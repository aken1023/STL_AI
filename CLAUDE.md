# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains STL (STereoLithography) 3D model files used for 3D printing and CAD applications. The repository structure is:

```
STL/
├── H09-EC11X8.stl
├── N9000151.stl
├── R8107490.stl
├── R8108140.stl
├── R8112078.stl
├── R8113139-TW.stl
├── R8113597-10.5-.stl
├── R8113743.stl
├── R8113865EW.stl
├── R8113930-.stl
├── R8113978.stl
├── R8126257-A--ok.stl
├── R8128944.stl
└── R8128946-A--OK.stl
```

## File Types

- **STL Files**: Binary STereoLithography files containing 3D mesh data for manufacturing/printing
- These are part numbers (R8xxxxxx format) representing specific 3D models or components

## Working with STL Files

STL files are binary formats that contain:
- Triangular mesh data defining 3D surfaces
- Normal vectors for each triangle
- Vertex coordinates in 3D space

Common operations:
- View/analyze: Use 3D modeling software (Blender, MeshLab, etc.)
- Convert: Tools like OpenSCAD, FreeCAD for format conversion
- Validate: Check mesh integrity and printability
- Repair: Fix mesh issues before printing

## Development Notes

This repository serves as part of a machine learning pipeline for 3D object recognition and dataset generation.

## 🎯 專案目標

本專案旨在將 .\STL 資料夾內的所有 3D STL 檔案，自動轉換成多角度的照片，用於建立 機器學習資料集。同時，透過 Python 程式，將實體拍照的影像與 STL 生成的影像進行比對，用於 物件辨識訓練。

包含兩個面向：

- STL 檔案管理與批量擷取照片
- Python 程式自動化 STL → 照片轉換
- 實體拍照比對 → 機器學習資料集建立

## 📂 專案結構

**核心資料夾**：
- 📁 `STL/` - 14 個 STL 模型檔案
- 📁 `dataset/` - 5,040 張訓練圖片 (14×360)
- 📁 `web_interface.py` - Web 介面主程式（含自動驗證功能）

<details>
<summary><b>🗂️ 完整專案結構樹狀圖</b>（點擊展開）</summary>

```
project-root/
│── CLAUDE.md                    # 專案說明文件
│── MULTI_USER_TRAINING.md       # 多用戶訓練系統說明
│── requirements.txt             # 依賴套件
│
├── 圖片生成
│   ├── generate_images.py       # 基本 STL → 圖片轉換
│   ├── generate_images_color.py # 彩色渲染版本
│   └── generate_cropped_images.py  # 裁切版本
│
├── 模型訓練
│   ├── train_model.py          # CNN ResNet50 訓練
│   └── faiss_recognition.py    # FAISS 特徵向量訓練
│
├── 模型預測
│   ├── predict_model.py        # CNN 預測
│   └── camera_test.py          # 相機測試
│
├── Web 介面
│   ├── web_interface.py        # 主 Web 介面（FAISS 訓練）
│   └── training_monitor_web.py # 訓練監控介面
│
├── 啟動腳本
│   ├── start_web.sh            # 啟動 Web 伺服器
│   └── setup_public_access.sh  # 公網訪問設定
│
├── STL/                        # 存放 STL 檔案（14個模型）
│    ├── H09-EC11X8.stl
│    ├── N9000151.stl
│    ├── R8107490.stl
│    ├── R8108140.stl
│    ├── R8112078.stl
│    ├── R8113139-TW.stl
│    ├── R8113597-10.5-.stl
│    ├── R8113743.stl
│    ├── R8113865EW.stl
│    ├── R8113930-.stl
│    ├── R8113978.stl
│    ├── R8126257-A--ok.stl
│    ├── R8128944.stl
│    └── R8128946-A--OK.stl
│
├── dataset/                    # 自動生成的資料集（14個模型 × 360張 = 5,040張）
│    ├── H09-EC11X8/  (360張)
│    ├── N9000151/  (360張)
│    ├── R8107490/  (360張)
│    ├── R8108140/  (360張)
│    ├── R8112078/  (360張)
│    ├── R8113139-TW/  (360張)
│    ├── R8113597-10.5-/  (360張)
│    ├── R8113743/  (360張)
│    ├── R8113865EW/  (360張)
│    ├── R8113930-/  (360張)
│    ├── R8113978/  (360張)
│    ├── R8126257-A--ok/  (360張)
│    ├── R8128944/  (360張)
│    └── R8128946-A--OK/  (360張)
│
├── static/                    # Web 靜態資源（參考圖片）
├── templates/                 # Web HTML 模板
├── training_logs/            # 訓練日誌
└── web_uploads/              # Web 上傳檔案
```

</details>

## 🛠️ 安裝需求

```bash
pip install -r requirements.txt
```

requirements.txt：
```
numpy
opencv-python
matplotlib
trimesh
pyvista
Pillow
tensorflow
scikit-learn
pyglet<2
Flask
faiss-cpu  # 或 faiss-gpu（如果有 GPU）
```

## 📸 STL → 多角度照片生成

**資料集狀態**：✅ 已完成（最後更新：2025-10-02）
- 📦 **14 個 STL 模型** × 360 張圖片 = **5,040 張圖片**
- 🎯 **真正的 360° 多角度視角**生成
- 📐 **解析度**：512×512 像素
- 🎨 **彩色渲染**：6 種顏色層，多重光源效果
- 📂 **位置**：`dataset/` 資料夾

### 執行指令
```bash
# 生成彩色版本（推薦）
python generate_images_color.py

# 或生成基本版本
python generate_images.py
```

<details>
<summary><b>📐 角度分佈策略與技術細節</b>（點擊展開）</summary>

### 角度分佈策略
- **總圖片數量**：每個 STL 檔案產生 360 張圖片
- **垂直角度層**：6 層，從 -75° 到 +75°
- **水平角度**：每層 60 個角度，完整 360° 覆蓋
- **圖片解析度**：統一 512×512 像素
- **檔案命名**：img_001.png 到 img_360.png

### 球面座標系統
使用球面座標轉換確保視角均勻分佈：
- **Elevation (垂直角度)**：-75°, -45°, -15°, +15°, +45°, +75°
- **Azimuth (水平角度)**：每層 0° 到 354° (每 6° 一張)

</details>

## 📷 實體拍照比對 (Camera → Dataset)

**功能**：使用相機拍攝實體物件，與資料集進行比對識別

**執行**：`python capture_and_match.py`

## 🚀 使用流程

### 完整工作流程

1. **準備 STL 檔案**
   ```bash
   # 放置 STL 檔案到 ./STL/ 資料夾
   ```

2. **安裝依賴套件**
   ```bash
   pip install -r requirements.txt
   pip install "pyglet<2"  # 確保 trimesh 相容性
   ```

3. **生成多角度圖片資料集**
   ```bash
   python generate_images_color.py
   ```
   - 自動處理所有 STL 檔案
   - 每個檔案產生 360 張不同角度圖片
   - 圖片儲存至 `./dataset/模型名稱/` 資料夾

4. **實體拍照比對**
   ```bash
   python capture_and_match.py
   ```
   - 自動啟動相機拍照
   - 與資料集中的圖片進行比對
   - 找出最相似的 STL 模型

5. **機器學習應用**
   - 使用生成的資料集訓練物件辨識模型
   - 進行實時物件辨識和分類

### 重要注意事項

- **角度覆蓋**：確保每個 STL 都有完整的 360° × 垂直 6 層視角
- **圖片品質**：所有圖片統一 512×512 解析度，適合 ML 訓練
- **檔案命名**：使用 img_001.png 到 img_360.png 的統一命名規則
- **比對精度**：使用 ORB 特徵點匹配算法進行圖片相似度計算

## 🎨 彩色渲染版本

### generate_images_color.py
提供豐富的視覺效果：
- **多重光源設定**：主光源、補助光源、背景光源
- **材質效果**：環境光、漫射光、鏡面反射
- **顏色方案**：每個垂直角度層使用不同顏色
- **背景漸層**：白色、淺藍、淺灰漸層背景

```bash
python generate_images_color.py
```

## 🤖 機器學習訓練

**推薦方案**：FAISS 特徵索引 ⭐
- **執行訓練**：透過 Web 介面訓練
- **訓練方法**：ResNet50 特徵提取 + FAISS 索引

<details>
<summary><b>🔬 訓練方案詳細說明</b>（點擊展開）</summary>

### FAISS 特徵向量檢索

**faiss_recognition.py** - 使用 FAISS 進行快速相似度搜尋：

```bash
# 主要特色
- 基於特徵向量的檢索
- 超快速搜尋（毫秒級）
- 不需要重新訓練
- 適合大規模資料集
- 支援 GPU 加速

# 建立 FAISS 索引
python faiss_recognition.py

# 特徵檔案
- faiss_features.index (11.8MB)
- faiss_labels.pkl (79KB)
```

</details>

## 🎯 預測和推論

**快速預測**：透過 Web 介面上傳圖片進行預測
- 選項 1：上傳單張圖片識別
- 選項 2：批次上傳識別

## 🌐 Web 介面系統

**快速啟動**：
```bash
./start_web.sh  # 或 python web_interface.py
# 訪問：http://localhost:5000
```

**核心功能**：圖片上傳預測 | 訓練監控 | FAISS 訓練 | 三階段訓練流程

<details>
<summary><b>🖥️ Web 介面詳細說明</b>（點擊展開）</summary>

### 主要功能
- **Web 上傳與預測**：透過瀏覽器上傳圖片進行物件辨識
- **訓練監控**：即時查看訓練進度和日誌
- **FAISS 訓練**：支援 FAISS 特徵索引訓練
- **獨占訓練模式**：確保訓練品質，一次只允許一個用戶訓練
- **參考圖片展示**：展示所有 STL 模型的參考圖片
- **三階段訓練流程**：
  - 階段 1: STL → 圖片（0-33%）
  - 階段 2: FAISS 訓練（34-67%）
  - 階段 3: 模型驗證（68-100%）

### 啟動 Web 介面

#### Linux / macOS
```bash
# 啟動 Web 伺服器（預設 port 5000）
./start_web.sh

# 或手動啟動
python web_interface.py
```

#### 公網訪問設定
```bash
# 設定公網訪問（使用 ngrok 或 localtunnel）
./setup_public_access.sh
```

### Web 介面功能說明

#### 1. 首頁 - 圖片上傳與預測
- 上傳圖片進行物件辨識
- 顯示辨識結果和置信度
- 展示 Top-K 相似結果
- **實時上傳進度條**：顯示上傳百分比和檔案大小

#### 2. 訓練頁面
- 設定 FAISS 訓練配置
- 即時顯示訓練日誌
- 訓練進度條和狀態顯示
- 三階段訓練流程可視化

#### 3. STL 上傳頁面
- 拖拉上傳 STL 檔案
- **實時上傳進度追蹤**：
  - 顯示上傳百分比（0-100%）
  - 顯示已上傳/總大小（例如：2.5 MB / 5.0 MB）
  - 自動檢測卡住情況（10秒無進度自動中斷）
  - 60秒超時保護
- 檔案列表預覽和管理

#### 4. 參考圖片頁面
- 展示所有 STL 模型的參考圖片
- 快速預覽資料集內容

### FAISS 訓練配置

#### 特徵提取模型
- **ResNet50**（推薦）：平衡準確率和速度
- **ResNet101**：更深層網路，準確率更高
- **VGG16**：經典模型
- **EfficientNet**：高效模型

#### 搜索相似度 K 值
- 範圍：3-20
- 預設：5
- 返回最相似的前 K 個結果

#### 索引類型
- **IndexFlatIP**（內積索引）：精確搜索
- **IndexFlatL2**（L2 距離索引）：精確搜索
- **IndexIVFFlat**（IVF 索引）：快速搜索

### API 端點

#### POST /api/upload
上傳圖片進行預測
- 支援格式：JPG, PNG, JPEG
- 返回：預測結果、置信度、Top-K 結果
- **支援上傳進度追蹤**：使用 XMLHttpRequest 監聽 upload.progress 事件

#### POST /api/upload_stl
上傳 STL 檔案
- 支援格式：.stl
- 支援多檔案上傳
- **實時進度追蹤**：百分比、檔案大小、傳輸狀態
- **智能錯誤處理**：超時檢測、卡住檢測、網路錯誤處理
- 返回：上傳結果、檔案列表

#### POST /api/start_training
啟動訓練任務
- 參數：training_methods, faiss_config
- 返回：session_id, 訓練狀態

#### GET /api/training_status
查詢訓練狀態
- 返回：is_training, current_epoch, log_lines

#### POST /api/stop_training
停止訓練任務
- 返回：操作結果

#### POST /api/validate_model
驗證模型準確率
- 返回：overall_accuracy, 各類別準確率

### 訪問方式
```
本地訪問：http://localhost:5000
區域網訪問：http://[你的IP]:5000
公網訪問：使用 setup_public_access.sh 設定
```

</details>

## 🎓 快速開始指南

### 新手入門（5 分鐘上手）

#### 步驟 1：安裝依賴
```bash
pip install -r requirements.txt
```

#### 步驟 2：生成資料集（如果尚未生成）
```bash
# 生成彩色版本（推薦）
python generate_images_color.py
```

#### 步驟 3：啟動 Web 介面（推薦）
```bash
# Linux / macOS
./start_web.sh

# 或直接執行
python web_interface.py

# 然後在瀏覽器開啟 http://localhost:5000
```

#### 步驟 4：開始訓練
1. 前往 Web 介面的「模型訓練」頁面
2. 設定 FAISS 配置
3. 點擊「開始訓練」
4. 觀察三階段訓練流程

## 📈 專案統計

### 核心數據
- 📦 **14 個 STL 模型** → 5,040 張訓練圖片
- 🎯 **FAISS 索引**：快速相似度搜索
- ⚡ **搜索速度**：毫秒級響應
- 💾 **索引大小**：約 12 MB

<details>
<summary><b>📊 詳細統計資訊</b>（點擊展開）</summary>

### 資料集規模
- **STL 模型數量**：14 個
- **生成圖片總數**：5,040 張（14 × 360）
- **每模型角度數**：360 個唯一視角
- **圖片解析度**：512×512 像素
- **資料集大小**：約 200-300 MB

### FAISS 訓練成果
- **特徵提取模型**：ResNet50
- **特徵向量維度**：2048
- **索引類型**：IndexFlatIP（內積索引）
- **搜索 K 值**：5
- **索引大小**：約 12 MB

### 可用工具
- **圖片生成工具**：3 個（基本、彩色、裁切）
- **訓練腳本**：2 個（FAISS、CNN）
- **預測工具**：2 個
- **Web 介面**：2 個（主介面、訓練監控）
- **輔助工具**：資料增強、監控、測試等

</details>

## 🔧 技術棧

### 核心技術
- **3D 渲染**：PyVista, Trimesh
- **深度學習**：TensorFlow, ResNet50
- **特徵檢索**：FAISS (Facebook AI Similarity Search)
- **圖像處理**：OpenCV, Pillow, NumPy
- **Web 框架**：Flask
- **視覺化**：Matplotlib

### 支援環境
- **作業系統**：Linux, Windows, macOS
- **Python 版本**：3.8+
- **硬體需求**：
  - CPU：任意現代處理器
  - RAM：最低 4GB，建議 8GB+
  - GPU：可選（AMD/NVIDIA），大幅加速訓練
  - 硬碟空間：最低 2GB

## 📚 相關文件

- **CLAUDE.md**：本文件，專案完整說明
- **MULTI_USER_TRAINING.md**：多用戶訓練系統說明
- **REAL_VALIDATION_UPDATE.md**：真實模型驗證實作說明
- **FAISS_ONLY_UPDATE.md**：FAISS 訓練系統簡化說明

## 🤝 貢獻與支援

### 專案特色
- ✅ 完整的 STL → 圖片 → 訓練 → 預測工作流
- ✅ FAISS 高速相似度搜索
- ✅ 友善的 Web 介面
- ✅ **實時上傳進度追蹤**（百分比、檔案大小、錯誤處理）
- ✅ 三階段訓練流程可視化
- ✅ 獨占訓練模式確保品質
- ✅ 豐富的輔助工具和腳本
- ✅ GPU/CPU 雙支援

### 常見問題

#### Q: 如何新增 STL 模型？
1. 將 STL 檔案上傳至 Web 介面
2. 系統自動生成 360 張圖片
3. 重新訓練 FAISS 索引

#### Q: 訓練需要多久？
- FAISS 索引建立：約 5-10 分鐘（取決於模型數量）
- 圖片生成：每個模型約 2-5 分鐘

#### Q: 如何提高識別準確率？
1. 增加訓練數據（更多角度、光照）
2. 使用更深的特徵提取模型（ResNet101）
3. 調整 K 值以獲得更多候選結果

#### Q: Web 介面無法訪問？
1. 檢查防火牆設定
2. 確認 port 5000 未被佔用
3. 使用 `./start_web.sh` 啟動
4. 查看 `web.log` 日誌

#### Q: 上傳檔案時卡住怎麼辦？
系統已內建智能檢測機制：
- **自動超時**：60 秒後自動中斷
- **卡住檢測**：10 秒無進度自動重試
- **詳細錯誤訊息**：顯示具體失敗原因
- **進度追蹤**：實時顯示上傳百分比和速度

## 🎓 學習資源

### FAISS 相關
- [FAISS Documentation](https://faiss.ai/)
- [FAISS GitHub](https://github.com/facebookresearch/faiss)

### STL 與 3D 渲染
- [PyVista Documentation](https://docs.pyvista.org/)
- [Trimesh Documentation](https://trimsh.org/)

### 深度學習
- [TensorFlow Tutorials](https://www.tensorflow.org/tutorials)
- [ResNet Paper](https://arxiv.org/abs/1512.03385)

---

## 📝 更新日誌

### v3.1 (2025-10-06)
- ✨ **新增實時上傳進度條功能**
  - STL 檔案上傳：顯示百分比、檔案大小、傳輸狀態
  - 圖片識別上傳：批次上傳進度追蹤
  - 智能錯誤處理：60秒超時、10秒卡住檢測
  - 使用 XMLHttpRequest 替代 fetch 以支援進度監聽
- 🐛 修復上傳時可能出現的假死問題
- 📚 更新 CLAUDE.md 文件說明

### v3.0 (2025-10-04)
- 完整的 FAISS 訓練系統
- 移除 YOLO 支援，專注於 FAISS
- 三階段訓練流程可視化

---

**專案版本**：v3.1
**最後更新**：2025-10-06
**維護狀態**：✅ 活躍開發中
**訓練方法**：FAISS 特徵索引（已移除 YOLO 支援）
**GitHub Repository**：https://github.com/aken1023/STL_AI
