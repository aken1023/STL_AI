# STL 物件識別系統 🎯

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.12-green.svg)](https://www.python.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-latest-red.svg)](https://github.com/ultralytics/ultralytics)

基於 YOLOv8 和 FAISS 的 3D STL 模型物件識別與訓練系統，支援 Web 界面操作。

---

## 🎉 主要功能

- ✅ **STL 檔案處理** - 自動生成多角度訓練圖片
- ✅ **YOLOv8 訓練** - 支援正常/精準訓練模式
- ✅ **即時預測** - 相機拍照或檔案上傳識別
- ✅ **模型管理** - 查看、切換、匯出訓練模型
- ✅ **訓練監控** - 實時日誌、進度追蹤
- ✅ **多用戶支援** - 訓練會話管理
- ✅ **Docker 部署** - 一鍵容器化部署

---

## 🚀 快速開始

### 方式一：Docker 部署（推薦）

```bash
# 1. 克隆專案
git clone <repository-url>
cd STL

# 2. 啟動 Docker
./docker-start.sh
# 或
docker-compose up -d

# 3. 訪問系統
瀏覽器打開：http://localhost:8082
```

### 方式二：本地部署

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 啟動服務
python3 web_interface.py

# 3. 訪問系統
瀏覽器打開：http://localhost:8082
```

---

## 📦 Docker 相關文件

- **[DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)** - 快速啟動指南
- **[DOCKER_README.md](DOCKER_README.md)** - 完整 Docker 文檔
- **[docker-start.sh](docker-start.sh)** - 互動式啟動腳本

---

## 📊 系統架構

```
STL 物件識別系統
├── Web 界面 (Flask)
│   ├── 檔案上傳識別
│   ├── 相機即時識別
│   ├── 模型訓練管理
│   └── 系統監控
│
├── STL 處理 (PyVista)
│   ├── 3D 模型渲染
│   └── 多角度圖片生成
│
├── 物件檢測 (YOLOv8)
│   ├── 模型訓練
│   ├── 即時預測
│   └── 結果可視化
│
└── 特徵索引 (FAISS)
    ├── 特徵提取
    └── 相似度搜索
```

---

## 🎯 使用流程

### 1. 上傳 STL 檔案
將 3D 模型檔案（.stl）上傳到系統

### 2. 生成訓練資料集
系統自動生成 360 度多角度圖片

### 3. 開始訓練
選擇訓練模式（正常/精準），啟動訓練

### 4. 監控進度
實時查看訓練日誌、Loss、準確率

### 5. 使用模型
上傳圖片或使用相機進行物件識別

---

## 🔧 系統需求

### Docker 部署
- Docker >= 20.10
- Docker Compose >= 2.0
- 4GB+ RAM
- 10GB+ 磁碟空間

### 本地部署
- Python 3.12
- CUDA（可選，用於 GPU 加速）
- 4GB+ RAM

---

## 📁 專案結構

```
STL/
├── web_interface.py          # Web 服務主程式
├── multi_user_training.py    # 多用戶訓練管理
├── generate_images_color.py  # STL 圖片生成
├── train_yolo.py             # YOLO 訓練腳本
├── predict_yolo.py           # YOLO 預測腳本
│
├── templates/                # HTML 模板
├── static/                   # 靜態資源
├── STL/                      # STL 模型檔案
├── dataset/                  # 訓練資料集
├── yolo_dataset/            # YOLO 格式資料集
└── runs/                    # 訓練結果
```

---

## 🎨 功能截圖

### Web 界面
- 檔案上傳與識別
- 相機即時拍照
- 訓練配置與啟動
- 系統監控儀表板

### 訓練監控
- 實時日誌輸出
- 進度條與時間預估
- Loss/準確率圖表
- 模型效能指標

### 模型管理
- 已訓練模型列表
- 模型切換與載入
- 模型資訊查看
- 模型匯出與刪除

---

## 🔐 安全說明

- ✅ 檔名衝突檢查
- ✅ 訓練獨占模式
- ✅ 資料持久化
- ✅ 健康檢查機制

---

## 📝 更新日誌

### v2.0.0 (2025-09-30)
- ✨ 新增 Docker 支援
- ✨ 新增模型管理功能
- ✨ 新增訓練衝突檢查
- 🐛 修復多用戶訓練問題
- 📊 優化訓練日誌輸出

### v1.0.0 (2025-09-28)
- 🎉 初始版本發布
- ✅ YOLOv8 訓練支援
- ✅ Web 界面實現

---

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

---

## 📄 授權

MIT License

---

## 📞 支援

- 文檔：查看 `CLAUDE.md`、`MULTI_USER_TRAINING.md`
- Docker：查看 `DOCKER_README.md`
- 問題回報：提交 GitHub Issue

---

## 🌟 特別感謝

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [PyVista](https://github.com/pyvista/pyvista)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Flask](https://github.com/pallets/flask)