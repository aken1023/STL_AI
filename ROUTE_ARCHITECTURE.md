# 🗺️ STL 專案路由架構規劃

**建立日期**: 2025-10-04
**目的**: 重構專案路由結構，實現頁面分離與模組化管理

---

## 📋 目錄

- [現有路由分析](#現有路由分析)
- [新路由架構設計](#新路由架構設計)
- [頁面路由](#頁面路由)
- [API 路由](#api-路由)
- [實作計劃](#實作計劃)

---

## 🔍 現有路由分析

### 目前路由總數：**54 個**

#### 頁面路由 (Page Routes)
```python
@app.route('/')                    # 主頁 - index_sidebar.html
@app.route('/simple')              # 簡易介面
@app.route('/advanced')            # 進階介面
@app.route('/single')              # 單一上傳
@app.route('/settings')            # 設定頁面
```

#### 靜態資源路由 (Static Routes)
```python
@app.route('/static/uploads/<filename>')
@app.route('/favicon.ico')
@app.route('/web_uploads/<path:filename>')
@app.route('/dataset/<path:filename>')
```

#### API 路由 (50+ 個)
- 模型相關：`/api/model_status`, `/api/load_model`, ...
- 上傳相關：`/api/upload`, `/api/upload_stl`, ...
- 訓練相關：`/api/start_training`, `/api/training_status`, ...
- STL 處理：`/api/generate_from_stl`, `/api/list_stl_files`, ...
- 系統管理：`/api/system_info`, `/api/statistics`, ...

---

## 🏗️ 新路由架構設計

### 設計原則

1. **頁面路由分離** - 每個功能頁面獨立路由
2. **API 路由分組** - 按功能模組組織 API
3. **RESTful 設計** - 遵循 REST API 最佳實踐
4. **版本控制** - 為 API 添加版本號
5. **模組化** - 使用 Blueprint 分離路由邏輯

---

## 📄 頁面路由 (Page Routes)

### 主要頁面

```python
# 首頁與儀表板
@app.route('/')                          # 主儀表板 (Dashboard)
@app.route('/dashboard')                 # 儀表板別名

# 模型識別
@app.route('/recognition')               # 模型識別頁面
@app.route('/recognition/upload')        # 上傳識別
@app.route('/recognition/camera')        # 相機識別
@app.route('/recognition/batch')         # 批次識別

# STL 管理
@app.route('/stl')                       # STL 檔案管理
@app.route('/stl/upload')                # STL 上傳
@app.route('/stl/list')                  # STL 列表
@app.route('/stl/generate')              # 圖片生成

# 訓練管理
@app.route('/training')                  # 訓練控制台
@app.route('/training/new')              # 新訓練任務
@app.route('/training/monitor')          # 訓練監控
@app.route('/training/history')          # 訓練歷史

# 資料集管理
@app.route('/dataset')                   # 資料集管理
@app.route('/dataset/browse')            # 瀏覽資料集
@app.route('/dataset/validate')          # 驗證資料集
@app.route('/dataset/augment')           # 資料增強

# 系統設定
@app.route('/settings')                  # 系統設定
@app.route('/settings/models')           # 模型設定
@app.route('/settings/system')           # 系統設定
@app.route('/settings/advanced')         # 進階設定

# 統計與報表
@app.route('/statistics')                # 統計報表
@app.route('/analytics')                 # 分析頁面
@app.route('/history')                   # 操作歷史
```

---

## 🔌 API 路由 (API Routes)

### API v1 路由結構

使用 Blueprint 組織 API：

```python
# API 版本前綴
API_V1_PREFIX = '/api/v1'

# 模型識別 API
/api/v1/recognition/upload              POST   # 上傳圖片識別
/api/v1/recognition/camera              POST   # 相機拍照識別
/api/v1/recognition/batch               POST   # 批次識別
/api/v1/recognition/history             GET    # 識別歷史

# STL 管理 API
/api/v1/stl/list                        GET    # 列出 STL 檔案
/api/v1/stl/upload                      POST   # 上傳 STL
/api/v1/stl/delete/<id>                 DELETE # 刪除 STL
/api/v1/stl/info/<id>                   GET    # STL 資訊
/api/v1/stl/generate                    POST   # 生成圖片

# 訓練管理 API
/api/v1/training/start                  POST   # 開始訓練
/api/v1/training/stop                   POST   # 停止訓練
/api/v1/training/status                 GET    # 訓練狀態
/api/v1/training/reset                  POST   # 重置訓練
/api/v1/training/history                GET    # 訓練歷史
/api/v1/training/validate               POST   # 驗證模型

# 資料集 API
/api/v1/dataset/list                    GET    # 列出資料集
/api/v1/dataset/samples                 GET    # 取得樣本
/api/v1/dataset/validate                POST   # 驗證資料集
/api/v1/dataset/delete                  DELETE # 刪除資料集
/api/v1/dataset/statistics              GET    # 資料集統計

# 模型管理 API
/api/v1/models/list                     GET    # 列出模型
/api/v1/models/load                     POST   # 載入模型
/api/v1/models/info/<id>                GET    # 模型資訊
/api/v1/models/export/<id>              GET    # 匯出模型
/api/v1/models/delete/<id>              DELETE # 刪除模型
/api/v1/models/activate/<id>            POST   # 啟用模型

# 系統 API
/api/v1/system/status                   GET    # 系統狀態
/api/v1/system/info                     GET    # 系統資訊
/api/v1/system/statistics               GET    # 系統統計
/api/v1/system/settings                 GET    # 取得設定
/api/v1/system/settings                 POST   # 儲存設定
/api/v1/system/version                  GET    # 版本資訊
```

### RESTful API 設計規範

| HTTP 方法 | 用途 | 範例 |
|----------|------|------|
| GET | 取得資源 | `/api/v1/stl/list` |
| POST | 建立資源 | `/api/v1/stl/upload` |
| PUT | 完整更新 | `/api/v1/models/update/<id>` |
| PATCH | 部分更新 | `/api/v1/settings/update` |
| DELETE | 刪除資源 | `/api/v1/stl/delete/<id>` |

---

## 📁 Blueprint 模組化架構

### 檔案結構

```
STL/
├── web_interface.py              # 主應用程式
├── blueprints/                   # Blueprint 模組
│   ├── __init__.py
│   ├── recognition.py            # 識別相關路由
│   ├── stl_management.py         # STL 管理路由
│   ├── training.py               # 訓練相關路由
│   ├── dataset.py                # 資料集路由
│   ├── models.py                 # 模型管理路由
│   └── system.py                 # 系統相關路由
├── templates/
│   ├── base.html                 # 基礎模板
│   ├── dashboard.html            # 儀表板
│   ├── recognition/              # 識別頁面
│   │   ├── upload.html
│   │   ├── camera.html
│   │   └── batch.html
│   ├── stl/                      # STL 頁面
│   │   ├── list.html
│   │   ├── upload.html
│   │   └── generate.html
│   ├── training/                 # 訓練頁面
│   │   ├── control.html
│   │   ├── monitor.html
│   │   └── history.html
│   └── settings/                 # 設定頁面
│       ├── general.html
│       ├── models.html
│       └── advanced.html
└── static/
    ├── css/
    ├── js/
    └── img/
```

### Blueprint 範例

```python
# blueprints/stl_management.py
from flask import Blueprint, request, jsonify, render_template

stl_bp = Blueprint('stl', __name__, url_prefix='/stl')

@stl_bp.route('/')
def index():
    """STL 管理主頁"""
    return render_template('stl/list.html')

@stl_bp.route('/upload')
def upload_page():
    """STL 上傳頁面"""
    return render_template('stl/upload.html')

# blueprints/api/stl.py
from flask import Blueprint

stl_api = Blueprint('stl_api', __name__, url_prefix='/api/v1/stl')

@stl_api.route('/list', methods=['GET'])
def list_stl():
    """列出所有 STL 檔案"""
    # ... 實作邏輯
    return jsonify({'success': True, 'files': files})

@stl_api.route('/upload', methods=['POST'])
def upload_stl():
    """上傳 STL 檔案"""
    # ... 實作邏輯
    return jsonify({'success': True, 'message': '上傳成功'})
```

### 主應用程式整合

```python
# web_interface.py
from flask import Flask
from blueprints.stl_management import stl_bp
from blueprints.api.stl import stl_api
from blueprints.training import training_bp
from blueprints.api.training import training_api
# ... 其他 blueprints

app = Flask(__name__)

# 註冊頁面 Blueprints
app.register_blueprint(stl_bp)
app.register_blueprint(training_bp)
# ...

# 註冊 API Blueprints
app.register_blueprint(stl_api)
app.register_blueprint(training_api)
# ...

@app.route('/')
def index():
    return render_template('dashboard.html')
```

---

## 🎯 路由命名規範

### 頁面路由命名
- 使用 **名詞** 描述資源：`/stl`, `/training`, `/dataset`
- 使用 **動詞** 描述動作子頁面：`/upload`, `/list`, `/generate`
- 保持 **簡潔** 和 **語義化**

### API 路由命名
- 使用 **版本前綴**：`/api/v1/...`
- 使用 **資源名詞**：`/stl/`, `/models/`
- 使用 **HTTP 方法** 表達動作（GET, POST, DELETE）
- 避免在 URL 中使用動詞（除了特殊操作如 `/start`, `/stop`）

---

## 🔄 向後兼容策略

### 保留舊路由（漸進式遷移）

```python
# 舊路由重定向到新路由
@app.route('/api/upload', methods=['POST'])
def old_upload_api():
    """舊版上傳 API - 重定向到新版"""
    return redirect(url_for('recognition_api.upload'), code=308)

@app.route('/api/upload_stl', methods=['POST'])
def old_upload_stl_api():
    """舊版 STL 上傳 - 重定向到新版"""
    return redirect(url_for('stl_api.upload'), code=308)
```

### 或保留舊路由並標記為廢棄

```python
@app.route('/api/upload', methods=['POST'])
@deprecated(version='v1', alternative='/api/v1/recognition/upload')
def old_upload_api():
    """
    DEPRECATED: 請使用 /api/v1/recognition/upload
    此 API 將在下一版本移除
    """
    # ... 舊的實作邏輯
```

---

## 🚀 實作計劃

### 階段 1: 規劃與設計（已完成）
- [x] 分析現有路由結構
- [x] 設計新路由架構
- [x] 建立路由命名規範
- [x] 規劃 Blueprint 模組結構

### 階段 2: 建立基礎架構
- [ ] 建立 `blueprints/` 目錄結構
- [ ] 創建基礎 Blueprint 模組
- [ ] 設置 API 版本控制
- [ ] 建立基礎模板結構

### 階段 3: 遷移路由
- [ ] 遷移 STL 相關路由到 Blueprint
- [ ] 遷移訓練相關路由到 Blueprint
- [ ] 遷移識別相關路由到 Blueprint
- [ ] 遷移系統管理路由到 Blueprint

### 階段 4: 頁面重構
- [ ] 創建獨立頁面模板
- [ ] 重構前端 JavaScript
- [ ] 更新導航選單
- [ ] 實作頁面間跳轉

### 階段 5: 測試與部署
- [ ] 功能測試
- [ ] API 測試
- [ ] 向後兼容測試
- [ ] 文件更新

---

## 📊 路由對照表

### 舊路由 → 新路由對照

| 舊路由 | 新路由 | 說明 |
|--------|--------|------|
| `/api/upload` | `/api/v1/recognition/upload` | 圖片上傳識別 |
| `/api/upload_stl` | `/api/v1/stl/upload` | STL 上傳 |
| `/api/start_training` | `/api/v1/training/start` | 開始訓練 |
| `/api/training_status` | `/api/v1/training/status` | 訓練狀態 |
| `/api/list_stl_files` | `/api/v1/stl/list` | STL 列表 |
| `/api/model_status` | `/api/v1/models/status` | 模型狀態 |
| `/api/system_info` | `/api/v1/system/info` | 系統資訊 |

---

## 💡 最佳實踐建議

### 1. 使用 Blueprint 分組

```python
# ✅ 好的做法
stl_bp = Blueprint('stl', __name__, url_prefix='/stl')
stl_api = Blueprint('stl_api', __name__, url_prefix='/api/v1/stl')

# ❌ 避免的做法
# 所有路由都寫在 web_interface.py
```

### 2. 遵循 RESTful 原則

```python
# ✅ RESTful 設計
GET    /api/v1/stl/123        # 取得 STL
POST   /api/v1/stl/           # 建立 STL
PUT    /api/v1/stl/123        # 更新 STL
DELETE /api/v1/stl/123        # 刪除 STL

# ❌ 非 RESTful 設計
POST /api/get_stl
POST /api/delete_stl
POST /api/update_stl
```

### 3. API 版本控制

```python
# ✅ 使用版本前綴
/api/v1/stl/upload
/api/v2/stl/upload  # 新版本

# ❌ 無版本控制
/api/stl/upload  # 無法平滑升級
```

### 4. 錯誤處理

```python
@stl_api.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@stl_api.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
```

---

## 📝 注意事項

### 遷移注意事項

1. **漸進式遷移** - 不要一次性更改所有路由
2. **保持向後兼容** - 舊路由保留或重定向至少一個版本
3. **更新文件** - 同步更新 API 文件和使用說明
4. **測試覆蓋** - 確保所有路由都有測試覆蓋
5. **前端更新** - 記得更新前端 API 調用路徑

### 效能考量

1. **Blueprint 開銷** - Blueprint 有輕微效能開銷，但可忽略
2. **URL 匹配** - 避免過於複雜的 URL 模式
3. **靜態資源** - 使用 CDN 或專用靜態伺服器
4. **快取策略** - 為 API 響應添加適當的快取

---

## 🎉 預期效益

### 開發效益
- ✅ 代碼組織更清晰
- ✅ 功能模組化，易於維護
- ✅ 團隊協作更便利
- ✅ 新功能開發更快速

### 使用者體驗
- ✅ 頁面載入更快速
- ✅ URL 語義化，易於理解
- ✅ 功能導航更直觀
- ✅ API 使用更簡單

### 系統架構
- ✅ 職責分離更明確
- ✅ 擴展性更好
- ✅ 版本升級更平滑
- ✅ 測試更容易編寫

---

**版本**: v1.0
**狀態**: ✅ 規劃完成
**下一步**: 開始實作 Blueprint 基礎架構

