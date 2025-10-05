#!/usr/bin/env python3
"""
STL 物件識別 - 完整網頁介面
包含檔案上傳、相機拍照、模型測試等完整功能
"""

# 版本資訊
APP_VERSION = "1.0.0"
APP_BUILD_DATE = "2025-10-04"

from flask import Flask, render_template, request, jsonify, send_file, url_for, send_from_directory, session
from werkzeug.utils import secure_filename
import os
import re
import unicodedata
import cv2
import numpy as np
import base64
import io
from PIL import Image
from datetime import datetime, timedelta
from pathlib import Path
import json
import time
import random
import psutil

# 導入 FAISS 識別引擎
try:
    from faiss_recognition import predict_with_faiss, initialize_faiss
    FAISS_AVAILABLE = True
    print("✅ FAISS 識別引擎可用")
except ImportError as e:
    print(f"⚠️ FAISS 識別引擎不可用: {e}")
    FAISS_AVAILABLE = False
import subprocess
import threading
import shutil
import glob

# 多用戶訓練模組已移除，改用 FAISS
# 資料管理和模型管理模組已移除

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'web_uploads'
# 設置最大上傳大小為 500MB（支援大型 STL 檔案和多檔案上傳）
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB

# 確保上傳資料夾存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 註冊 Blueprints
from blueprints import stl_bp, recognition_bp, training_bp, search_bp
app.register_blueprint(stl_bp)
app.register_blueprint(recognition_bp)
app.register_blueprint(training_bp)
app.register_blueprint(search_bp)

# 支援中文的安全檔名函數
def safe_filename(filename):
    """
    支援中文字符的安全檔名函數
    保留中文、英文、數字、點、底線、連字號
    """
    # 分離檔名和副檔名
    name, ext = os.path.splitext(filename)

    # 移除或替換危險字符，但保留中文、英文、數字、底線、連字號
    # 允許的字符：中文、英文字母、數字、底線、連字號、空格
    safe_name = re.sub(r'[^\w\s\-\u4e00-\u9fff]', '', name)

    # 移除開頭和結尾的空白
    safe_name = safe_name.strip()

    # 如果檔名為空（可能全是特殊字符），使用時間戳
    if not safe_name:
        from datetime import datetime
        safe_name = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 重新組合檔名和副檔名
    return safe_name + ext
os.makedirs('static', exist_ok=True)
os.makedirs('static/results', exist_ok=True)
os.makedirs('training_stl', exist_ok=True)  # STL 檔案上傳資料夾

# 全域變數
model = None
model_loaded = False
model_info = {}
training_state_file = 'training_state.json'
class_names_file = 'class_names.json'

# 多用戶訓練管理
training_sessions = {}  # 存儲多個訓練會話 {session_id: {process, status, ...}}
training_lock = threading.Lock()

# 資料管理器 - 實作資料庫寫入功能
class DataManager:
    def __init__(self, db_path='system_data.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化資料庫表格"""
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 上傳歷史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS upload_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_size INTEGER,
                    file_path TEXT,
                    client_ip TEXT,
                    user_agent TEXT,
                    status TEXT DEFAULT 'success'
                )
            ''')

            # 識別歷史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recognition_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    upload_id INTEGER,
                    timestamp TEXT NOT NULL,
                    method TEXT,
                    predicted_class TEXT,
                    confidence REAL,
                    inference_time REAL,
                    result_image_path TEXT,
                    success INTEGER,
                    error_message TEXT,
                    FOREIGN KEY (upload_id) REFERENCES upload_history (id)
                )
            ''')

            conn.commit()

    def add_upload_record(self, filename, file_size, file_path, client_ip=None, user_agent=None):
        """添加上傳記錄"""
        import sqlite3
        from datetime import datetime

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO upload_history (timestamp, filename, file_size, file_path, client_ip, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), filename, file_size, file_path, client_ip, user_agent))
            conn.commit()
            return cursor.lastrowid

    def add_recognition_record(self, upload_id, method, predicted_class=None, confidence=None,
                              inference_time=None, result_image_path=None, success=True, error_message=None):
        """添加識別記錄"""
        import sqlite3
        from datetime import datetime

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO recognition_history
                (upload_id, timestamp, method, predicted_class, confidence, inference_time,
                 result_image_path, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (upload_id, datetime.now().isoformat(), method, predicted_class, confidence,
                  inference_time, result_image_path, 1 if success else 0, error_message))
            conn.commit()
            return cursor.lastrowid

    def get_statistics(self):
        """獲取系統統計資料"""
        import os
        import glob

        # 統計 STL 檔案數量
        stl_files = glob.glob('STL/*.stl')
        stl_count = len(stl_files)

        # 統計訓練圖片數量
        image_count = 0
        if os.path.exists('dataset'):
            for model_dir in os.listdir('dataset'):
                model_path = os.path.join('dataset', model_dir)
                if os.path.isdir(model_path):
                    images = glob.glob(os.path.join(model_path, '*.png'))
                    image_count += len(images)

        # 統計今日識別次數（從數據庫）
        recognition_count = 0
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM recognition_history
                WHERE date(timestamp) = date('now')
            ''')
            result = cursor.fetchone()
            recognition_count = result[0] if result else 0
            conn.close()
        except:
            recognition_count = 0

        return {
            'stl_count': stl_count,
            'image_count': image_count,
            'recognition_count': recognition_count,
            'class_count': stl_count  # 類別數量等於 STL 模型數量
        }

    def get_upload_history(self, **kwargs):
        return []

    def get_recognition_history(self, **kwargs):
        return []

    def get_training_history(self, **kwargs):
        return []

    def set_active_model(self, path):
        pass

    def scan_models(self):
        return []

    def get_model_summary(self):
        return {}

    def load_model(self, path):
        return False

    def get_current_model(self):
        return None

data_manager = DataManager()
model_manager = DataManager()  # 保持相容性，雖然不使用

def load_model():
    """載入模型 - 使用 FAISS 識別引擎"""
    global model, model_loaded, model_info

    print("ℹ️ 系統使用 FAISS 識別引擎")

    if FAISS_AVAILABLE:
        # 初始化 FAISS
        try:
            initialize_faiss()
            model_loaded = True
            model_info = {
                'method': 'FAISS',
                'loaded_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            print("✅ FAISS 識別引擎已初始化")
            return True
        except Exception as e:
            print(f"❌ FAISS 初始化失敗: {e}")
            return False
    else:
        print("❌ FAISS 識別引擎不可用")
        return False

def predict_with_faiss_wrapper(image_path):
    """FAISS 預測包裝函數，統一輸出格式"""
    try:
        result = predict_with_faiss(image_path)
        if not result:
            return {
                'predictions': [],
                'inference_time': 0,
                'result_image': None,
                'success': False,
                'error': 'FAISS 預測失敗',
                'method': 'FAISS'
            }

        # 轉換格式使其與 FAISS 結果一致
        formatted_predictions = []
        detailed_results = result.get('detailed_results', [])

        for pred in result['predictions']:
            # 從 detailed_results 獲取該類別最相似的參考圖片
            reference_images = []
            class_name = pred['class_name']

            # 找出該類別最相似的前8個結果
            class_matches = [d for d in detailed_results if d['class_name'] == class_name]
            class_matches = sorted(class_matches, key=lambda x: x['confidence'], reverse=True)[:8]

            for match in class_matches:
                ref_image_path = match.get('reference_image')
                if ref_image_path and os.path.exists(ref_image_path):
                    # 複製到 static 資料夾以便網頁存取
                    img_name = os.path.basename(ref_image_path)
                    static_filename = f"ref_{class_name}_{img_name}"
                    static_path = os.path.join('static', static_filename)

                    if not os.path.exists(static_path):
                        import shutil
                        try:
                            shutil.copy2(ref_image_path, static_path)
                        except Exception as e:
                            print(f"複製參考圖片失敗: {e}")
                            continue

                    reference_images.append({
                        'filename': img_name,
                        'url': f"/static/{static_filename}",
                        'confidence': match['confidence']
                    })

            # 查找對應的 STL 檔案
            stl_file = None
            stl_preview = None
            stl_path = os.path.join('STL', f"{class_name}.stl")
            if os.path.exists(stl_path):
                stl_file = f"/STL/{class_name}.stl"
                # 使用資料集的第一張圖作為 STL 預覽
                dataset_dir = os.path.join('dataset', class_name)
                if os.path.exists(dataset_dir):
                    images = sorted([f for f in os.listdir(dataset_dir) if f.endswith(('.jpg', '.png'))])
                    if images:
                        preview_img = images[0]
                        static_preview = f"stl_preview_{class_name}_{preview_img}"
                        static_preview_path = os.path.join('static', static_preview)

                        if not os.path.exists(static_preview_path):
                            import shutil
                            try:
                                shutil.copy2(os.path.join(dataset_dir, preview_img), static_preview_path)
                            except Exception as e:
                                print(f"複製 STL 預覽圖失敗: {e}")

                        stl_preview = f"/static/{static_preview}"

            formatted_predictions.append({
                'class_id': pred['class_id'],
                'class_name': pred['class_name'],
                'confidence': pred['confidence'],
                'method': 'FAISS',
                'reference_images': reference_images,
                'stl_file': stl_file,
                'stl_preview': stl_preview
            })

        return {
            'predictions': formatted_predictions,
            'inference_time': result['inference_time'],
            'result_image': None,  # FAISS 不產生標註圖片
            'success': True,
            'method': 'FAISS'
        }

    except Exception as e:
        return {
            'predictions': [],
            'inference_time': 0,
            'result_image': None,
            'success': False,
            'error': f'FAISS 預測錯誤: {str(e)}',
            'method': 'FAISS'
        }

def predict_image(image_path, method='FAISS'):
    """預測圖片 - 只使用 FAISS 方法"""
    global model, model_loaded

    # 強制使用 FAISS
    if not FAISS_AVAILABLE:
        return {
            'predictions': [],
            'inference_time': 0,
            'result_image': None,
            'success': False,
            'error': 'FAISS 識別引擎不可用'
        }

    return predict_with_faiss_wrapper(image_path)

def get_dataset_samples():
    """取得數據集樣本"""
    samples = []

    # 使用標準資料集目錄
    dataset_dir = "dataset"

    if not os.path.exists(dataset_dir):
        return samples

    if os.path.exists(dataset_dir):
        classes = [d for d in os.listdir(dataset_dir)
                   if os.path.isdir(os.path.join(dataset_dir, d))]

        for class_name in classes:
            class_dir = os.path.join(dataset_dir, class_name)
            images = [f for f in os.listdir(class_dir) if f.endswith(('.jpg', '.png'))]

            if images:
                # 隨機選擇3張圖片
                selected_images = random.sample(images, min(3, len(images)))

                for img_name in selected_images:
                    img_path = os.path.join(class_dir, img_name)

                    # 複製到 static 資料夾以便網頁存取
                    static_filename = f"sample_{class_name}_{img_name}"
                    static_path = os.path.join('static', static_filename)

                    if not os.path.exists(static_path):
                        import shutil
                        shutil.copy2(img_path, static_path)

                    samples.append({
                        'class_name': class_name,
                        'filename': img_name,
                        'url': f"/static/{static_filename}",
                        'path': img_path
                    })

    return samples

def get_reference_images(class_name, count=3):
    """獲取指定類別的參考圖片"""
    reference_images = []

    # 使用標準資料集目錄
    dataset_dir = "dataset"

    if os.path.exists(dataset_dir):
        class_dir = os.path.join(dataset_dir, class_name)
        if os.path.exists(class_dir):
            images = [f for f in os.listdir(class_dir) if f.endswith(('.jpg', '.png'))]
            if images:
                # 隨機選擇指定數量的圖片
                selected_images = random.sample(images, min(count, len(images)))

                for img_name in selected_images:
                    img_path = os.path.join(class_dir, img_name)

                    # 複製到 static 資料夾以便網頁存取
                    static_filename = f"ref_{class_name}_{img_name}"
                    static_path = os.path.join('static', static_filename)

                    if not os.path.exists(static_path):
                        import shutil
                        shutil.copy2(img_path, static_path)

                    reference_images.append({
                        'class_name': class_name,
                        'filename': img_name,
                        'url': f"/static/{static_filename}",
                        'path': img_path
                    })

    return reference_images

# STL 檔案服務路由
@app.route('/STL/<path:filename>')
def serve_stl_file(filename):
    """提供 STL 檔案服務（支援中文檔名）"""
    try:
        stl_dir = os.path.abspath('STL')
        return send_from_directory(stl_dir, filename, as_attachment=False)
    except Exception as e:
        print(f"STL 檔案服務錯誤: {e}")
        return jsonify({'error': f'檔案不存在: {filename}'}), 404

@app.route('/test_3d')
def test_3d():
    """3D 預覽測試頁面"""
    return render_template('test_3d.html')

@app.route('/')
def index():
    """主頁面 - 儀表板"""
    return render_template('dashboard/index.html',
                         version=APP_VERSION,
                         build_date=APP_BUILD_DATE)

@app.route('/legacy')
def legacy_index():
    """舊版主頁面 - 保留向後兼容"""
    return render_template('index_sidebar.html',
                         version=APP_VERSION,
                         build_date=APP_BUILD_DATE)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    """服務上傳的檔案"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/favicon.ico')
def favicon():
    """網站圖標"""
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/web_uploads/<path:filename>', endpoint='web_uploads_file')
def serve_uploaded_file(filename):
    """提供上傳檔案訪問"""
    return send_from_directory('web_uploads', filename)

@app.route('/dataset/<path:filename>')
def serve_dataset_file(filename):
    """提供 dataset 資料夾中的圖片訪問"""
    return send_from_directory('dataset', filename)

@app.route('/simple')
def simple():
    """簡化界面"""
    return render_template('index_simple.html')

@app.route('/advanced')
def advanced():
    """進階功能頁面"""
    return render_template('index_multi_upload.html')

@app.route('/single')
def single_upload():
    """單檔案上傳頁面"""
    return render_template('index.html')

@app.route('/recognition')
def recognition():
    """圖片識別頁面"""
    return render_template('recognition/index.html')

@app.route('/search')
def search():
    """智能搜尋頁面"""
    return render_template('search/index.html')

@app.route('/training')
def training():
    """訓練控制頁面"""
    return render_template('training/index.html')

@app.route('/stl')
def stl_list():
    """STL 檔案列表頁面"""
    return render_template('stl/list.html')

@app.route('/stl/upload')
def stl_upload_page():
    """STL 上傳頁面"""
    return render_template('stl/upload.html')

@app.route('/stl/generate')
def stl_generate_page():
    """STL 生成圖片頁面"""
    return render_template('stl/generate.html')

@app.route('/api/model_status')
def model_status():
    """獲取模型狀態"""
    return jsonify({
        'loaded': model_loaded,
        'info': model_info if model_loaded else {}
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """檔案上傳處理 - 支援多檔案和模型選擇"""
    files = request.files.getlist('files') or [request.files.get('file')]
    files = [f for f in files if f and f.filename != '']
    recognition_method = 'FAISS'  # 只使用 FAISS

    if not files:
        return jsonify({'success': False, 'error': '沒有選擇檔案'})

    results = []
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')

    # 允許的圖片格式
    allowed_image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')

    for i, file in enumerate(files):
        # 檢查是否為圖片檔案
        if not file.filename.lower().endswith(allowed_image_extensions):
            results.append({
                'original_filename': file.filename,
                'error': f'不支援的檔案格式。僅接受圖片格式：PNG, JPG, JPEG, GIF, BMP, WEBP',
                'success': False
            })
            continue

        if file and file.filename.lower().endswith(allowed_image_extensions):
            filename = safe_filename(file.filename)
            unique_filename = f"{timestamp}_{i:03d}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            file_size = os.path.getsize(filepath)

            # 記錄上傳
            upload_id = data_manager.add_upload_record(
                filename=file.filename,
                file_size=file_size,
                file_path=filepath,
                client_ip=client_ip,
                user_agent=user_agent
            )

            # 進行預測（使用選定的方法）
            result = predict_image(filepath, method=recognition_method)

            if result and result.get('success'):
                # 記錄辨識結果
                predictions = result.get('predictions', [])
                if predictions:
                    pred = predictions[0]  # 取第一個預測結果
                    data_manager.add_recognition_record(
                        upload_id=upload_id,
                        method=recognition_method,
                        predicted_class=pred.get('class_name'),
                        confidence=pred.get('confidence'),
                        inference_time=result.get('inference_time'),
                        result_image_path=result.get('result_image'),
                        success=True
                    )
                else:
                    data_manager.add_recognition_record(
                        upload_id=upload_id,
                        method=recognition_method,
                        success=False,
                        error_message='未偵測到物件'
                    )

                # 扁平化結果以匹配前端格式
                predictions = result.get('predictions', [])
                top_prediction = predictions[0] if predictions else None

                result_data = {
                    'original_filename': file.filename,
                    'saved_filename': unique_filename,
                    'original_image_url': f"/static/uploads/{unique_filename}",
                    'success': True,
                    'method': result.get('method', 'FAISS'),
                    'inference_time': result.get('inference_time', 0)
                }

                # 添加預測結果
                if top_prediction:
                    result_data['class_id'] = top_prediction.get('class_id', -1)
                    result_data['class_name'] = top_prediction.get('class_name', 'Unknown')
                    result_data['confidence'] = top_prediction.get('confidence', 0)
                    result_data['top_k'] = predictions[:5]  # Top 5 結果
                    result_data['reference_images'] = top_prediction.get('reference_images', [])
                    result_data['stl_file'] = top_prediction.get('stl_file')
                    result_data['stl_preview'] = top_prediction.get('stl_preview')

                results.append(result_data)
            else:
                # 記錄失敗的辨識
                error_msg = result.get('error', '預測失敗') if result else '預測失敗'
                data_manager.add_recognition_record(
                    upload_id=upload_id,
                    method=recognition_method,
                    success=False,
                    error_message=error_msg
                )

                results.append({
                    'original_filename': file.filename,
                    'saved_filename': unique_filename,
                    'error': error_msg,
                    'success': False
                })
        else:
            results.append({
                'original_filename': file.filename if file else 'unknown',
                'error': '不支援的檔案格式',
                'success': False
            })

    # 計算成功率
    successful = len([r for r in results if r['success']])
    total = len(results)

    return jsonify({
        'success': successful > 0,
        'total_files': total,
        'successful_files': successful,
        'failed_files': total - successful,
        'results': results
    })

@app.route('/api/camera_capture', methods=['POST'])
def camera_capture():
    """相機拍照處理"""
    try:
        # 獲取資料
        data = request.get_json()
        image_data = data['image'].split(',')[1]  # 移除 data:image/jpeg;base64, 前綴
        recognition_method = 'FAISS'  # 只使用 FAISS

        # 解碼並儲存
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"camera_{timestamp}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        # 進行預測（使用選定的方法）
        result = predict_image(filepath, method=recognition_method)

        if result:
            return jsonify({
                'success': True,
                'filename': filename,
                'result': result
            })
        else:
            return jsonify({'success': False, 'error': '預測失敗'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test_sample/<class_name>/<filename>')
def test_sample(class_name, filename):
    """測試數據集樣本"""
    # 使用標準資料集目錄
    img_path = os.path.join("dataset", class_name, filename)

    if os.path.exists(img_path):
        result = predict_image(img_path)

        if result:
            return jsonify({
                'success': True,
                'true_class': class_name,
                'result': result
            })
        else:
            return jsonify({'success': False, 'error': '預測失敗'})
    else:
        return jsonify({'success': False, 'error': '找不到圖片'})

@app.route('/api/dataset_samples')
def dataset_samples():
    """獲取數據集樣本"""
    samples = get_dataset_samples()
    return jsonify({'samples': samples})

@app.route('/api/performance_test')
def performance_test():
    """效能測試"""
    if not model_loaded:
        return jsonify({'success': False, 'error': '模型未載入'})

    try:
        # 找一張測試圖片
        dataset_dir = "dataset"
        test_image = None

        for class_dir in os.listdir(dataset_dir):
            class_path = os.path.join(dataset_dir, class_dir)
            if os.path.isdir(class_path):
                images = [f for f in os.listdir(class_path) if f.endswith(('.jpg', '.png'))]
                if images:
                    test_image = os.path.join(class_path, images[0])
                    break

        if not test_image:
            return jsonify({'success': False, 'error': '找不到測試圖片'})

        # 執行多次測試
        times = []
        for i in range(10):
            start_time = time.time()
            results = model(test_image, verbose=False)
            end_time = time.time()
            times.append((end_time - start_time) * 1000)  # ms

        avg_time = np.mean(times)
        min_time = np.min(times)
        max_time = np.max(times)
        fps = 1000.0 / avg_time

        return jsonify({
            'success': True,
            'avg_time': round(avg_time, 1),
            'min_time': round(min_time, 1),
            'max_time': round(max_time, 1),
            'fps': round(fps, 1),
            'test_count': len(times)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/batch_test')
def batch_test():
    """批次測試"""
    # FAISS 系統不需要檢查 model_loaded，因為它始終可用
    if not FAISS_AVAILABLE:
        return jsonify({'success': False, 'error': 'FAISS 引擎不可用'})

    try:
        # 使用 dataset 資料夾（原始數據集）
        dataset_dir = "dataset"
        if not os.path.exists(dataset_dir):
            return jsonify({'success': False, 'error': f'資料集目錄 {dataset_dir} 不存在'})

        classes = [d for d in os.listdir(dataset_dir)
                   if os.path.isdir(os.path.join(dataset_dir, d))]

        if not classes:
            return jsonify({'success': False, 'error': '資料集中沒有找到任何類別'})

        results = {}
        total_correct = 0
        total_tested = 0

        for class_name in classes:
            class_dir = os.path.join(dataset_dir, class_name)
            # 支援 .jpg 和 .png 格式
            images = [f for f in os.listdir(class_dir) if f.lower().endswith(('.jpg', '.png'))]

            if not images:
                continue

            # 隨機選擇10張圖片測試
            test_images = random.sample(images, min(10, len(images)))

            correct = 0
            for img_name in test_images:
                img_path = os.path.join(class_dir, img_name)

                # 使用 FAISS 進行預測
                try:
                    result = predict_with_faiss(img_path)
                    if result and 'predictions' in result and result['predictions']:
                        predicted_class = result['predictions'][0]['class_name']
                        if predicted_class == class_name:
                            correct += 1
                except Exception as pred_error:
                    print(f"預測失敗: {img_path}, 錯誤: {pred_error}")
                    continue

                total_tested += 1

            accuracy = correct / len(test_images) if test_images else 0
            total_correct += correct

            results[class_name] = {
                'correct': correct,
                'total': len(test_images),
                'accuracy': round(accuracy * 100, 1)
            }

        overall_accuracy = total_correct / total_tested if total_tested > 0 else 0

        return jsonify({
            'success': True,
            'results': results,
            'overall_accuracy': round(overall_accuracy * 100, 1),
            'accuracy': round(overall_accuracy * 100, 1),
            'map50': round(overall_accuracy * 100, 1),  # 簡化處理，實際使用時應計算真正的 mAP50
            'total_correct': total_correct,
            'total_tested': total_tested
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

# 訓練狀態全域變數
training_process = None
training_status = {
    'is_training': False,
    'current_epoch': 0,
    'total_epochs': 0,
    'accuracy': 0,
    'log_lines': [],
    'start_time': None,
    'model_name': None,
    'pid': None
}

# 載入持久化的訓練狀態
def load_training_state():
    """載入訓練狀態"""
    global training_status, training_process
    try:
        if os.path.exists(training_state_file):
            with open(training_state_file, 'r', encoding='utf-8') as f:
                saved_state = json.load(f)
                training_status.update(saved_state)

            # 檢查是否有正在進行的訓練程序
            if training_status.get('pid') and training_status.get('is_training'):
                try:
                    # 檢查程序是否還在運行
                    import psutil
                    if psutil.pid_exists(training_status['pid']):
                        proc = psutil.Process(training_status['pid'])
                        if 'python' in proc.name().lower() and 'FAISS_training' in ' '.join(proc.cmdline()):
                            print(f"發現正在運行的訓練程序 (PID: {training_status['pid']})")
                            # 重新連接到現有程序 (這裡簡化處理，實際使用中可能需要更複雜的邏輯)
                        else:
                            training_status['is_training'] = False
                    else:
                        training_status['is_training'] = False
                except:
                    training_status['is_training'] = False

    except Exception as e:
        print(f"載入訓練狀態失敗: {e}")
        training_status['is_training'] = False

# 保存訓練狀態
def save_training_state():
    """保存訓練狀態"""
    try:
        with open(training_state_file, 'w', encoding='utf-8') as f:
            json.dump(training_status, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存訓練狀態失敗: {e}")

# 載入和保存分類名稱
def load_class_names():
    """載入自訂分類名稱"""
    try:
        if os.path.exists(class_names_file):
            with open(class_names_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"載入分類名稱失敗: {e}")
    return {}

def save_class_names(class_names):
    """保存自訂分類名稱"""
    try:
        with open(class_names_file, 'w', encoding='utf-8') as f:
            json.dump(class_names, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存分類名稱失敗: {e}")
        return False

# 獲取 STL 檔案的預設分類名稱
def get_default_class_names():
    """獲取 STL 檔案的預設分類名稱"""
    class_names = {}

    # 掃描 STL 資料夾
    stl_files = glob.glob('STL/*.stl') + glob.glob('training_stl/*.stl')
    for stl_path in stl_files:
        filename = os.path.basename(stl_path)
        name_without_ext = os.path.splitext(filename)[0]
        class_names[filename] = name_without_ext

    # 掃描 dataset 資料夾中的類別
    if os.path.exists('dataset'):
        for class_dir in os.listdir('dataset'):
            class_path = os.path.join('dataset', class_dir)
            if os.path.isdir(class_path):
                # 檢查是否有對應的 STL 檔案
                stl_file = f"{class_dir}.stl"
                if stl_file not in class_names:
                    class_names[stl_file] = class_dir

    return class_names

def get_system_info():
    """獲取系統資訊"""
    try:
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 記憶體資訊
        memory = psutil.virtual_memory()
        memory_used = f"{memory.used // (1024**3):.1f}GB"
        memory_total = f"{memory.total // (1024**3):.1f}GB"

        # 磁碟資訊
        disk = psutil.disk_usage('/')
        disk_used = f"{disk.used // (1024**3):.1f}GB"
        disk_total = f"{disk.total // (1024**3):.1f}GB"

        # 網路資訊
        network = psutil.net_io_counters()
        network_sent = f"{network.bytes_sent // (1024**2):.0f}MB"
        network_recv = f"{network.bytes_recv // (1024**2):.0f}MB"

        # GPU 資訊 (嘗試使用 nvidia-smi)
        gpu_info = None
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
                                   '--format=csv,noheader,nounits'], capture_output=True, text=True)
            if result.returncode == 0:
                gpu_data = result.stdout.strip().split(', ')
                if len(gpu_data) >= 4:
                    gpu_info = {
                        'utilization': gpu_data[0],
                        'memory_used': gpu_data[1],
                        'memory_total': gpu_data[2],
                        'memory_percent': f"{float(gpu_data[1]) / float(gpu_data[2]) * 100:.1f}",
                        'temperature': gpu_data[3]
                    }
        except:
            pass

        # 系統溫度 (優先獲取 CPU 核心溫度)
        temperature = None
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    # 優先選擇 coretemp (CPU 核心溫度)
                    if 'coretemp' in temps and temps['coretemp']:
                        temperature = temps['coretemp'][0].current
                    elif 'acpitz' in temps and temps['acpitz']:
                        temperature = temps['acpitz'][0].current
                    else:
                        # 如果沒有找到特定溫度感測器，使用第一個可用的
                        for name, entries in temps.items():
                            if entries:
                                temperature = entries[0].current
                                break
        except:
            pass

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used': memory_used,
            'memory_total': memory_total,
            'disk_percent': disk.percent,
            'disk_used': disk_used,
            'disk_total': disk_total,
            'network_sent': network_sent,
            'network_recv': network_recv,
            'gpu_info': gpu_info,
            'temperature': temperature
        }
    except Exception as e:
        return {'error': str(e)}

@app.route('/api/system_status')
def system_status():
    """系統狀態API"""
    status = get_system_info()

    # 計算已訓練的 STL 檔案數量（dataset 資料夾中的子資料夾數量）
    try:
        from pathlib import Path
        dataset_path = Path('dataset')
        if dataset_path.exists():
            # 計算有圖片的子資料夾數量
            trained_stl_count = sum(1 for item in dataset_path.iterdir()
                                   if item.is_dir() and any(item.glob('*.png')))
            status['trained_stl_count'] = trained_stl_count
        else:
            status['trained_stl_count'] = 0
    except Exception as e:
        print(f"計算訓練 STL 數量錯誤: {e}")
        status['trained_stl_count'] = 0

    return jsonify({'success': True, 'status': status})

@app.route('/api/start_training', methods=['POST'])
def start_training():
    """開始多模型訓練API - 支持多用戶並發訓練"""
    global training_sessions

    try:
        config = request.get_json()
        client_ip = request.remote_addr

        # 生成唯一會話ID
        session_id = f"{client_ip}_{int(time.time() * 1000)}"

        print(f"📥 收到訓練請求 - IP: {client_ip}, Session: {session_id}")

        # 檢查當前活躍訓練數量 - 只允許一個人訓練
        with training_lock:
            active_sessions = [s for s in training_sessions.values() if s['status']['is_training']]

            # 如果有其他用戶正在訓練，拒絕新的訓練請求
            if len(active_sessions) > 0:
                # 檢查是否是同一個用戶
                current_training = active_sessions[0]
                if current_training['client_ip'] != client_ip:
                    # 其他用戶正在訓練，拒絕
                    other_user_ip = current_training['client_ip']
                    error_msg = f"⚠️ 系統正忙：用戶 {other_user_ip} 正在訓練中"
                    print(error_msg)
                    return jsonify({
                        'success': False,
                        'error': '訓練系統正在使用中',
                        'message': f'另一個用戶（{other_user_ip}）正在進行訓練，請稍後再試',
                        'other_user': other_user_ip,
                        'retry_after': '請等待當前訓練完成'
                    })
                else:
                    # 同一個用戶，允許重新訓練（先清理舊會話）
                    print(f"用戶 {client_ip} 重新開始訓練，清理舊會話")
                    # 不阻止，讓其繼續創建新會話

        # 檢查訓練方法選擇 - 只支援 FAISS
        training_methods_list = config.get('training_methods', ['faiss'])
        # 強制只使用 FAISS
        faiss_enabled = True

        # 訓練方法字典（用於狀態追踪）
        training_methods = {
            'faiss': True
        }

        # 創建新的訓練會話
        training_status = {
            'is_training': True,
            'current_epoch': 0,
            'total_epochs': config.get('faiss_config', {}).get('epochs', 50) if faiss_enabled else 1,
            'accuracy': 0,
            'log_lines': [],
            'training_methods': training_methods,
            'faiss_enabled': faiss_enabled,
            'faiss_enabled': faiss_enabled,
            'start_time': time.time(),
            'client_ip': client_ip
        }

        # 添加多用戶警告到日誌
        training_status['log_lines'].append('🚀 開始多模型訓練系統初始化...')
        with training_lock:
            active_count = len([s for s in training_sessions.values() if s['status']['is_training']])
            if active_count > 0:
                training_status['log_lines'].append(f'⚠️ 系統當前有 {active_count} 個訓練任務正在運行')
                training_status['log_lines'].append('💡 提示：多個訓練任務會共享GPU資源，可能影響訓練速度')

        # 顯示訓練方法 - 只使用 FAISS
        training_status['log_lines'].append('🎯 使用訓練方法: FAISS 特徵索引')

        # 存儲會話
        with training_lock:
            training_sessions[session_id] = {
                'client_ip': client_ip,
                'status': training_status,
                'process': None,
                'created_at': time.time()
            }

        # 啟動訓練任務 - 自動生成圖片 + FAISS 訓練
        training_status['log_lines'].append('🚀 開始完整訓練流程...')

        # 完整訓練流程：1. 檢查/生成圖片 → 2. FAISS 訓練
        def run_faiss_training():
            # 輔助函數：添加日誌並打印到控制台（帶時間戳記）
            def add_log(message):
                import datetime
                timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                timestamped_message = f"[{timestamp}] {message}"
                with training_lock:
                    if session_id in training_sessions:
                        training_sessions[session_id]['status']['log_lines'].append(timestamped_message)
                print(f"[訓練日誌] {timestamped_message}")

            try:
                import subprocess
                import os

                with training_lock:
                    if session_id in training_sessions:
                        status = training_sessions[session_id]['status']

                # 階段 1: 檢查訓練圖片
                add_log('📋 階段 1/2: 檢查訓練圖片...')

                # 掃描 STL 檔案
                stl_files = glob.glob('STL/*.stl')
                need_generate = False
                total_images = 0

                for stl_path in stl_files:
                    stl_name = os.path.splitext(os.path.basename(stl_path))[0]
                    image_dir = os.path.join('dataset', stl_name)

                    if not os.path.exists(image_dir):
                        need_generate = True
                        add_log(f'   ⚠️ {stl_name}: 圖片資料夾不存在')
                    else:
                        images = [f for f in os.listdir(image_dir) if f.endswith('.png')]
                        total_images += len(images)
                        if len(images) == 0:
                            need_generate = True
                            add_log(f'   ⚠️ {stl_name}: 無圖片')
                        else:
                            add_log(f'   ✅ {stl_name}: {len(images)} 張圖片')

                # 如果需要生成圖片（只在完全沒有圖片時才生成）
                if need_generate:
                    add_log('📸 偵測到部分模型無圖片，開始自動生成...')
                    add_log(f'   找到 {len(stl_files)} 個 STL 模型')

                    # 使用 Popen 實時讀取圖片生成輸出
                    process = subprocess.Popen(
                        ['python', '-u', 'generate_images_color.py'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )

                    # 實時讀取並顯示輸出
                    for line in iter(process.stdout.readline, ''):
                        if not line:
                            break
                        line = line.strip()
                        if line:
                            add_log(f'   {line}')

                    process.wait()

                    if process.returncode == 0:
                        add_log('✅ 圖片生成完成')
                    else:
                        add_log(f'❌ 圖片生成失敗，返回碼: {process.returncode}')
                        with training_lock:
                            if session_id in training_sessions:
                                training_sessions[session_id]['status']['is_training'] = False
                        return
                else:
                    add_log(f'✅ 所有模型已有圖片，總計 {total_images} 張，直接開始訓練')

                # 階段 2: FAISS 訓練
                add_log('📋 階段 2/2: FAISS 索引建立...')

                # 使用 Popen 實時讀取輸出
                import re
                process = subprocess.Popen(
                    ['python', '-u', 'faiss_recognition.py'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                # 實時讀取輸出並解析進度
                total_images = 0
                processed_images = 0

                for line in iter(process.stdout.readline, ''):
                    if not line:
                        break

                    line = line.strip()
                    if line:
                        add_log(line)

                        # 解析總圖片數
                        total_match = re.search(r'總共需要處理\s+(\d+)\s+張圖片', line)
                        if total_match:
                            total_images = int(total_match.group(1))

                        # 解析當前進度
                        progress_match = re.search(r'進度:\s+(\d+)/(\d+)\s+張圖片\s+\((\d+\.?\d*)%\)', line)
                        if progress_match and total_images > 0:
                            processed_images = int(progress_match.group(1))
                            progress_percent = float(progress_match.group(3))

                            # 更新訓練狀態的進度
                            with training_lock:
                                if session_id in training_sessions:
                                    training_sessions[session_id]['status']['current_epoch'] = processed_images
                                    training_sessions[session_id]['status']['total_epochs'] = total_images
                                    training_sessions[session_id]['status']['progress_percent'] = progress_percent

                process.wait()

                if process.returncode == 0:
                    add_log('✅ FAISS 訓練完成')

                    # 訓練完成報告
                    add_log('')
                    add_log('╔═══════════════════════════════════════════════╗')
                    add_log('║          📊 訓練完成報告                      ║')
                    add_log('╚═══════════════════════════════════════════════╝')
                    add_log('')

                    # 檢查 STL 檔案數量 vs 訓練的模型數量
                    stl_files = glob.glob('STL/*.stl')
                    stl_count = len(stl_files)

                    # 統計資料集圖片數量
                    total_dataset_images = 0
                    for stl_path in stl_files:
                        stl_name = os.path.splitext(os.path.basename(stl_path))[0]
                        image_dir = os.path.join('dataset', stl_name)
                        if os.path.exists(image_dir):
                            images = [f for f in os.listdir(image_dir) if f.endswith('.png')]
                            total_dataset_images += len(images)

                    # 檢查 FAISS 訓練的模型數量
                    try:
                        import pickle
                        import datetime

                        if os.path.exists('faiss_labels.pkl'):
                            with open('faiss_labels.pkl', 'rb') as f:
                                faiss_data = pickle.load(f)
                                trained_classes = len(faiss_data.get('classes', []))
                                total_features = len(faiss_data.get('labels', []))

                            # 獲取索引文件大小
                            index_size = 0
                            if os.path.exists('faiss_features.index'):
                                index_size = os.path.getsize('faiss_features.index') / (1024 * 1024)  # MB

                            add_log('📦 資料集統計：')
                            add_log(f'   └─ STL 模型數量: {stl_count} 個')
                            add_log(f'   └─ 訓練圖片總數: {total_dataset_images} 張')
                            add_log(f'   └─ 平均每模型: {total_dataset_images // stl_count if stl_count > 0 else 0} 張圖片')
                            add_log('')

                            add_log('🎯 FAISS 索引資訊：')
                            add_log(f'   └─ 訓練類別數: {trained_classes} 個')
                            add_log(f'   └─ 特徵向量數: {total_features} 個')
                            add_log(f'   └─ 索引檔案大小: {index_size:.2f} MB')
                            add_log(f'   └─ 索引類型: IndexFlatIP (內積相似度)')
                            add_log('')

                            # 檢查完整性
                            if trained_classes < stl_count:
                                missing_count = stl_count - trained_classes
                                add_log('⚠️  訓練完整性檢查：')
                                add_log(f'   ├─ STL 檔案總數: {stl_count} 個')
                                add_log(f'   ├─ 已訓練模型數: {trained_classes} 個')
                                add_log(f'   └─ 未訓練模型數: {missing_count} 個')
                                add_log('')

                                # 找出未訓練的模型
                                trained_names = set(faiss_data.get('classes', []))
                                stl_names = set(os.path.splitext(os.path.basename(f))[0] for f in stl_files)
                                missing_models = stl_names - trained_names

                                if missing_models:
                                    add_log('❌ 未訓練的模型：')
                                    for model in sorted(missing_models):
                                        add_log(f'   • {model}')
                                    add_log('')
                                    add_log('💡 建議：請重新訓練以包含所有模型')

                                with training_lock:
                                    if session_id in training_sessions:
                                        training_sessions[session_id]['status']['training_incomplete'] = True
                            else:
                                add_log('✅ 訓練完整性檢查：')
                                add_log(f'   └─ 所有 {trained_classes} 個模型已成功訓練')
                                add_log('')

                                with training_lock:
                                    if session_id in training_sessions:
                                        training_sessions[session_id]['status']['training_incomplete'] = False

                            # 訓練總結
                            add_log('📈 訓練總結：')
                            add_log(f'   └─ 訓練狀態: {"⚠️ 不完整" if trained_classes < stl_count else "✅ 完整"}')
                            add_log(f'   └─ 訓練方法: FAISS 特徵索引')
                            add_log(f'   └─ 特徵提取: ResNet50 (ImageNet 預訓練)')
                            add_log(f'   └─ 搜索方式: K-近鄰投票機制')
                            add_log('')

                            # 使用說明
                            add_log('🎓 使用說明：')
                            add_log('   ├─ 1. 前往首頁上傳圖片進行識別')
                            add_log('   ├─ 2. 系統會返回最相似的模型和置信度')
                            add_log('   ├─ 3. "投票數" 表示 K 個最相似圖片中有幾個屬於該類別')
                            add_log('   └─ 4. 投票數越高，識別結果越可靠')
                            add_log('')

                            add_log('╔═══════════════════════════════════════════════╗')
                            add_log('║          🎉 訓練完成！系統已就緒              ║')
                            add_log('╚═══════════════════════════════════════════════╝')

                            # 生成訓練報告文件
                            try:
                                report_filename = f'training_report_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
                                with open(report_filename, 'w', encoding='utf-8') as rf:
                                    rf.write('═' * 60 + '\n')
                                    rf.write('          📊 FAISS 訓練完成報告\n')
                                    rf.write('═' * 60 + '\n\n')
                                    rf.write(f'報告生成時間: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')

                                    rf.write('━' * 60 + '\n')
                                    rf.write('📦 資料集統計\n')
                                    rf.write('━' * 60 + '\n')
                                    rf.write(f'STL 模型數量: {stl_count} 個\n')
                                    rf.write(f'訓練圖片總數: {total_dataset_images} 張\n')
                                    rf.write(f'平均每模型: {total_dataset_images // stl_count if stl_count > 0 else 0} 張圖片\n\n')

                                    rf.write('━' * 60 + '\n')
                                    rf.write('🎯 FAISS 索引資訊\n')
                                    rf.write('━' * 60 + '\n')
                                    rf.write(f'訓練類別數: {trained_classes} 個\n')
                                    rf.write(f'特徵向量數: {total_features} 個\n')
                                    rf.write(f'索引檔案大小: {index_size:.2f} MB\n')
                                    rf.write(f'索引類型: IndexFlatIP (內積相似度)\n\n')

                                    rf.write('━' * 60 + '\n')
                                    rf.write('✅ 訓練完整性檢查\n')
                                    rf.write('━' * 60 + '\n')
                                    if trained_classes < stl_count:
                                        rf.write(f'狀態: ⚠️ 訓練不完整\n')
                                        rf.write(f'STL 檔案總數: {stl_count} 個\n')
                                        rf.write(f'已訓練模型數: {trained_classes} 個\n')
                                        rf.write(f'未訓練模型數: {stl_count - trained_classes} 個\n\n')
                                        if missing_models:
                                            rf.write('未訓練的模型列表:\n')
                                            for model in sorted(missing_models):
                                                rf.write(f'  ❌ {model}\n')
                                    else:
                                        rf.write(f'狀態: ✅ 訓練完整\n')
                                        rf.write(f'所有 {trained_classes} 個模型已成功訓練\n')
                                    rf.write('\n')

                                    rf.write('━' * 60 + '\n')
                                    rf.write('📈 訓練總結\n')
                                    rf.write('━' * 60 + '\n')
                                    rf.write(f'訓練狀態: {"⚠️ 不完整" if trained_classes < stl_count else "✅ 完整"}\n')
                                    rf.write(f'訓練方法: FAISS 特徵索引\n')
                                    rf.write(f'特徵提取: ResNet50 (ImageNet 預訓練)\n')
                                    rf.write(f'搜索方式: K-近鄰投票機制\n\n')

                                    rf.write('━' * 60 + '\n')
                                    rf.write('🎓 使用說明\n')
                                    rf.write('━' * 60 + '\n')
                                    rf.write('1. 前往首頁上傳圖片進行識別\n')
                                    rf.write('2. 系統會返回最相似的模型和置信度\n')
                                    rf.write('3. "投票數" 表示 K 個最相似圖片中有幾個屬於該類別\n')
                                    rf.write('4. 投票數越高，識別結果越可靠\n\n')

                                    rf.write('═' * 60 + '\n')
                                    rf.write('          🎉 訓練完成！系統已就緒\n')
                                    rf.write('═' * 60 + '\n')

                                add_log(f'📄 訓練報告已儲存至: {report_filename}')
                            except Exception as e:
                                add_log(f'⚠️ 生成報告文件失敗: {str(e)}')

                        else:
                            add_log('⚠️ 找不到 FAISS 標籤檔案')
                    except Exception as e:
                        add_log(f'⚠️ 完整性檢查錯誤: {str(e)}')

                    with training_lock:
                        if session_id in training_sessions:
                            training_sessions[session_id]['status']['is_training'] = False
                else:
                    add_log(f'❌ FAISS 訓練失敗: {result.stderr}')
                    with training_lock:
                        if session_id in training_sessions:
                            training_sessions[session_id]['status']['is_training'] = False

            except Exception as e:
                add_log(f'❌ 錯誤: {str(e)}')
                with training_lock:
                    if session_id in training_sessions:
                        training_sessions[session_id]['status']['is_training'] = False

        training_thread = threading.Thread(target=run_faiss_training)
        training_thread.daemon = True
        training_thread.start()

        return jsonify({
            'success': True,
            'message': '多模型訓練已啟動',
            'session_id': session_id,
            'active_sessions': len([s for s in training_sessions.values() if s['status']['is_training']])
        })

    except Exception as e:
        import traceback
        print(f"❌ 訓練啟動失敗: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

def monitor_training_process():
    """監控訓練過程"""
    global training_process, training_status

    if not training_process:
        return

    import re
    last_heartbeat = time.time()
    heartbeat_interval = 10  # 每10秒發送一次心跳訊息

    try:
        while True:
            # 非阻塞讀取
            line = training_process.stdout.readline()

            if not line:
                # 檢查進程是否結束
                if training_process.poll() is not None:
                    break

                # 如果長時間沒有輸出，發送心跳訊息
                current_time = time.time()
                if current_time - last_heartbeat > heartbeat_interval:
                    current_epoch = training_status.get('current_epoch', 0)
                    total_epochs = training_status.get('total_epochs', 0)
                    if current_epoch > 0:
                        progress = (current_epoch / total_epochs * 100) if total_epochs > 0 else 0
                        training_status['log_lines'].append(f'💓 訓練運行中... Epoch {current_epoch}/{total_epochs} ({progress:.1f}%)')
                    else:
                        training_status['log_lines'].append('💓 訓練初始化中，請稍候...')
                    last_heartbeat = current_time

                time.sleep(0.1)
                continue

            line = line.strip()
            if line:
                # 重置心跳計時器
                last_heartbeat = time.time()

                # 添加所有非空日誌行
                training_status['log_lines'].append(line)
                print(f"[訓練日誌] {line}")  # 同時輸出到控制台

                # 解析訓練進度（更強健的正則表達式匹配）
                epoch_pattern = r'(\d+)/(\d+)'
                if 'epoch' in line.lower():
                    try:
                        match = re.search(epoch_pattern, line)
                        if match:
                            current = int(match.group(1))
                            total = int(match.group(2))
                            training_status['current_epoch'] = current
                            training_status['total_epochs'] = total
                    except Exception as e:
                        print(f"解析 epoch 失敗: {e}")

                # 解析損失值
                if 'loss' in line.lower():
                    try:
                        loss_match = re.search(r'loss[:\s]+(\d+\.\d+)', line.lower())
                        if loss_match:
                            training_status['loss'] = float(loss_match.group(1))
                    except:
                        pass

                # 解析準確率
                if 'acc' in line.lower() or 'accuracy' in line.lower():
                    try:
                        acc_match = re.search(r'acc(?:uracy)?[:\s]+(\d+\.?\d*)', line.lower())
                        if acc_match:
                            training_status['accuracy'] = float(acc_match.group(1))
                    except:
                        pass

                # 解析 mAP 並添加重點標註
                if 'map' in line.lower():
                    try:
                        map_match = re.search(r'map(?:@?[\d.]*)?[:\s]+(\d+\.\d+)', line.lower())
                        if map_match:
                            training_status['mAP'] = float(map_match.group(1))
                            training_status['log_lines'].append(f"📊 檢測到 mAP 指標: {training_status['mAP']:.4f}")
                    except:
                        pass

                # 保持最新的300行日誌（增加容量以顯示更多內容）
                if len(training_status['log_lines']) > 300:
                    training_status['log_lines'] = training_status['log_lines'][-300:]

        # 訓練完成
        training_status['is_training'] = False
        training_status['log_lines'].append('━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        training_status['log_lines'].append('🏁 訓練已完成')
        training_status['log_lines'].append('━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        print("訓練進程已結束")

    except Exception as e:
        training_status['is_training'] = False
        training_status['log_lines'].append(f"❌ 監控錯誤: {str(e)}")
        print(f"監控錯誤: {e}")

@app.route('/api/training_status')
def get_training_status():
    """獲取訓練狀態 - 多用戶版本"""
    global training_sessions, training_status

    client_ip = request.remote_addr

    # 查找該用戶的最新會話
    with training_lock:
        user_sessions = [(sid, s) for sid, s in training_sessions.items() if s['client_ip'] == client_ip]

        if user_sessions:
            # 按創建時間排序，取最新的
            user_sessions.sort(key=lambda x: x[1]['created_at'], reverse=True)
            session_id, session_data = user_sessions[0]
            status = session_data['status'].copy()

            # 添加多用戶信息
            active_sessions = [s for s in training_sessions.values() if s['status']['is_training']]
            status['active_sessions_count'] = len(active_sessions)
            status['session_id'] = session_id

            return jsonify(status)
        else:
            # 沒有會話，返回默認狀態
            return jsonify(training_status)

@app.route('/api/stop_training', methods=['POST'])
def stop_training():
    """停止訓練"""
    global training_process, training_status

    try:
        if training_process:
            training_process.terminate()
            training_process = None

        training_status['is_training'] = False
        training_status['log_lines'].append("訓練已手動停止")

        return jsonify({'success': True, 'message': '訓練已停止'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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

# ==================== 模型管理 API ====================

@app.route('/api/list_models')
def list_models():
    """列出所有已訓練的模型（FAISS）"""
    try:
        models = []

        # 檢查 FAISS 模型檔案
        faiss_index_path = Path('faiss_features.index')
        faiss_labels_path = Path('faiss_labels.pkl')

        if faiss_index_path.exists() and faiss_labels_path.exists():
            import pickle

            # 獲取檔案信息
            index_stat = faiss_index_path.stat()
            labels_stat = faiss_labels_path.stat()
            total_size = index_stat.st_size + labels_stat.st_size

            # 讀取標籤獲取類別信息
            try:
                with open(faiss_labels_path, 'rb') as f:
                    labels_data = pickle.load(f)
                    # labels_data 是字典，包含 'labels' 和 'classes' 鍵
                    if isinstance(labels_data, dict):
                        class_names = labels_data.get('classes', [])
                        label_array = labels_data.get('labels', [])
                        num_classes = len(class_names)
                        num_features = len(label_array)
                    else:
                        # 如果是舊格式（list）
                        num_classes = len(set(labels_data))
                        num_features = len(labels_data)
                        class_names = sorted(set(labels_data))
            except:
                num_classes = 0
                num_features = 0
                class_names = []

            # FAISS 模型始終處於活動狀態（只要檔案存在）
            is_active = FAISS_AVAILABLE

            model_info = {
                'name': 'FAISS 識別模型',
                'path': str(faiss_index_path),
                'type': 'FAISS',
                'size': total_size,
                'created_time': datetime.fromtimestamp(index_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'num_classes': num_classes,
                'num_features': num_features,
                'class_names': class_names,
                'is_active': is_active,
                'files': {
                    'index': str(faiss_index_path),
                    'labels': str(faiss_labels_path),
                    'index_size': index_stat.st_size,
                    'labels_size': labels_stat.st_size
                }
            }
            models.append(model_info)

        return jsonify({'success': True, 'models': models})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/load_model', methods=['POST'])
def switch_model():
    """切換到指定的模型"""
    global faiss_engine

    try:
        data = request.json
        model_path = data.get('model_path')

        if not model_path or not Path(model_path).exists():
            return jsonify({'success': False, 'error': '模型檔案不存在'})

        # FAISS 已移除，只使用 FAISS
        return jsonify({'success': False, 'error': '系統已改用 FAISS，不支援 FAISS 模型載入'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/model_info')
def model_info():
    """獲取模型詳細資訊"""
    try:
        model_path = request.args.get('path')

        if not model_path or not Path(model_path).exists():
            return jsonify({'success': False, 'error': '模型檔案不存在'})

        model_path = Path(model_path)
        stat = model_path.stat()
        run_dir = model_path.parent.parent

        info = {
            'name': f"{run_dir.name}/{model_path.name}",
            'path': str(model_path),
            'size': stat.st_size,
            'created_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        }

        # 讀取訓練配置
        args_file = run_dir / 'args.yaml'
        if args_file.exists():
            try:
                import yaml
                with open(args_file, 'r') as f:
                    args = yaml.safe_load(f)
                    info['epochs'] = args.get('epochs')
                    info['batch_size'] = args.get('batch')
                    info['image_size'] = args.get('imgsz')
            except:
                pass

        # 讀取訓練結果
        results_file = run_dir / 'results.csv'
        if results_file.exists():
            try:
                import pandas as pd
                df = pd.read_csv(results_file)
                if not df.empty:
                    last_row = df.iloc[-1]
                    # 嘗試讀取各種可能的列名
                    for col in df.columns:
                        col_lower = col.strip().lower()
                        if 'map' in col_lower or 'map50' in col_lower:
                            info['map'] = f"{float(last_row[col]):.4f}"
                        elif 'precision' in col_lower:
                            info['precision'] = f"{float(last_row[col]):.4f}"
                        elif 'recall' in col_lower:
                            info['recall'] = f"{float(last_row[col]):.4f}"
            except:
                pass

        return jsonify({'success': True, 'info': info})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/export_model', methods=['GET', 'POST'])
def export_model():
    """匯出模型檔案"""
    try:
        # 支援 GET 和 POST 兩種方式，同時支援 path 和 model_path 參數名
        if request.method == 'POST':
            data = request.json
            model_path = data.get('model_path') or data.get('path') if data else None
        else:
            model_path = request.args.get('path') or request.args.get('model_path')

        if not model_path:
            return jsonify({'success': False, 'error': '未指定模型路徑'})

        model_path = Path(model_path)

        if not model_path.exists():
            return jsonify({'success': False, 'error': f'模型檔案不存在: {model_path}'})

        return send_file(str(model_path), as_attachment=True)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete_model', methods=['POST'])
def delete_model():
    """刪除模型檔案"""
    try:
        data = request.json
        model_path = data.get('model_path')

        if not model_path:
            return jsonify({'success': False, 'error': '未指定模型路徑'})

        model_path = Path(model_path)

        # 檢查是否是當前使用的模型
        current_model_path = None
        try:
            if hasattr(app, 'faiss_engine') and app.faiss_engine:
                current_model_path = str(getattr(app.faiss_engine, 'ckpt_path', None))
        except:
            pass

        if str(model_path) == current_model_path:
            return jsonify({'success': False, 'error': '無法刪除正在使用的模型'})

        if model_path.exists():
            model_path.unlink()
            return jsonify({'success': True, 'message': '模型已刪除'})
        else:
            return jsonify({'success': False, 'error': '模型檔案不存在'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/check_training_conflict', methods=['POST'])
def check_training_conflict():
    """檢查訓練輸出目錄是否已存在"""
    try:
        data = request.json
        project_name = data.get('project_name', 'faiss_model')

        # 檢查是否有同名的訓練目錄
        base_path = Path('./runs/detect')
        conflicts = []

        if not base_path.exists():
            return jsonify({'success': True, 'has_conflict': False})

        # 檢查精確匹配和帶數字後綴的匹配
        for item in base_path.iterdir():
            if item.is_dir():
                # 檢查是否是同名或同名加數字
                if item.name == project_name or item.name.startswith(project_name):
                    # 檢查是否有權重檔案
                    weights_dir = item / 'weights'
                    if weights_dir.exists():
                        best_pt = weights_dir / 'best.pt'
                        last_pt = weights_dir / 'last.pt'

                        if best_pt.exists() or last_pt.exists():
                            stat = best_pt.stat() if best_pt.exists() else last_pt.stat()
                            conflicts.append({
                                'name': item.name,
                                'path': str(item),
                                'size': stat.st_size,
                                'created_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                                'has_best': best_pt.exists(),
                                'has_last': last_pt.exists()
                            })

        if conflicts:
            return jsonify({
                'success': True,
                'has_conflict': True,
                'conflicts': conflicts
            })
        else:
            return jsonify({
                'success': True,
                'has_conflict': False
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate_dataset', methods=['POST'])
def generate_dataset():
    """重新生成資料集"""
    try:
        # 執行圖片生成腳本
        result = subprocess.run(['python', 'generate_images.py'],
                              capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            # 計算生成的圖片數量
            image_count = 0
            dataset_dir = "dataset"

            if os.path.exists(dataset_dir):
                for class_dir in os.listdir(dataset_dir):
                    class_path = os.path.join(dataset_dir, class_dir)
                    if os.path.isdir(class_path):
                        images = [f for f in os.listdir(class_path) if f.endswith(('.jpg', '.png'))]
                        image_count += len(images)

            return jsonify({'success': True, 'image_count': image_count})
        else:
            return jsonify({'success': False, 'error': result.stderr})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/validate_model', methods=['POST'])
def validate_model():
    """驗證模型"""
    try:
        # 使用現有的批次測試功能
        return batch_test()

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/validate_models', methods=['POST'])
def validate_models():
    """驗證所有模型（FAISS 系統只有一個模型，所以等同於 validate_model）"""
    try:
        return batch_test()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/upload_stl', methods=['POST'])
def upload_stl():
    """STL檔案上傳API - 檢測重複並提供選項"""
    import time
    start_time = time.time()

    try:
        files = request.files.getlist('stl_files')
        force_upload = request.form.get('force_upload', 'false').lower() == 'true'

        if not files:
            return jsonify({'success': False, 'error': '沒有選擇檔案'})

        print(f"📤 收到 {len(files)} 個 STL 檔案上傳請求")

        # 確保 STL 目錄存在
        stl_dir = 'STL'
        os.makedirs(stl_dir, exist_ok=True)

        # 先將所有檔案保存到臨時位置以避免記憶體問題
        import tempfile
        temp_files = []

        for file in files:
            if file and file.filename.lower().endswith('.stl'):
                # 保存到臨時檔案
                temp_fd, temp_path = tempfile.mkstemp(suffix='.stl')
                os.close(temp_fd)
                file.save(temp_path)

                temp_files.append({
                    'original_name': file.filename,
                    'safe_name': safe_filename(file.filename),
                    'temp_path': temp_path,
                    'size': os.path.getsize(temp_path)
                })
            else:
                # 清理已保存的臨時檔案
                for tf in temp_files:
                    try:
                        os.remove(tf['temp_path'])
                    except:
                        pass
                return jsonify({'success': False, 'error': f'檔案 {file.filename} 不是STL格式'})

        # 檢查重複檔案
        duplicate_files = []
        new_files = []

        for temp_file in temp_files:
            filename = temp_file['safe_name']
            filepath = os.path.join(stl_dir, filename)

            if os.path.exists(filepath):
                # 獲取現有檔案資訊
                existing_size = os.path.getsize(filepath)
                existing_time = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')

                duplicate_files.append({
                    'name': filename,
                    'original_name': temp_file['original_name'],
                    'existing_size': existing_size,
                    'existing_time': existing_time,
                    'temp_path': temp_file['temp_path'],
                    'new_size': temp_file['size']
                })
            else:
                new_files.append({
                    'name': filename,
                    'original_name': temp_file['original_name'],
                    'temp_path': temp_file['temp_path'],
                    'size': temp_file['size']
                })

        # 如果有重複檔案且未強制上傳，清理臨時檔案並返回警告
        if duplicate_files and not force_upload:
            # 清理所有臨時檔案
            for tf in temp_files:
                try:
                    os.remove(tf['temp_path'])
                except:
                    pass

            return jsonify({
                'success': False,
                'warning': 'duplicate_detected',
                'duplicate_files': [{
                    'name': f['name'],
                    'original_name': f['original_name'],
                    'existing_size': f['existing_size'],
                    'existing_time': f['existing_time']
                } for f in duplicate_files],
                'new_files_count': len(new_files),
                'duplicate_count': len(duplicate_files),
                'message': f'發現 {len(duplicate_files)} 個重複檔案'
            })

        # 執行上傳（從臨時檔案移動到目標位置）
        uploaded_files = []

        # 上傳新檔案
        for file_info in new_files:
            filename = file_info['name']
            filepath = os.path.join(stl_dir, filename)

            # 從臨時位置移動到目標位置
            import shutil
            shutil.move(file_info['temp_path'], filepath)

            uploaded_files.append({
                'name': filename,
                'original_name': file_info['original_name'],
                'size': os.path.getsize(filepath),
                'path': filepath,
                'status': 'new'
            })

        # 如果強制上傳，覆蓋重複檔案
        if force_upload and duplicate_files:
            for file_info in duplicate_files:
                filename = file_info['name']
                filepath = os.path.join(stl_dir, filename)

                # 刪除舊的圖片資料夾
                model_name = os.path.splitext(filename)[0]
                dataset_dir = os.path.join('dataset', model_name)
                if os.path.exists(dataset_dir):
                    import shutil
                    shutil.rmtree(dataset_dir)

                # 從臨時位置移動到目標位置（覆蓋）
                shutil.move(file_info['temp_path'], filepath)

                uploaded_files.append({
                    'name': filename,
                    'original_name': file_info['original_name'],
                    'size': os.path.getsize(filepath),
                    'path': filepath,
                    'status': 'replaced'
                })

        response = {
            'success': True,
            'files': uploaded_files,
            'count': len(uploaded_files),
            'new_count': len([f for f in uploaded_files if f['status'] == 'new']),
            'replaced_count': len([f for f in uploaded_files if f['status'] == 'replaced'])
        }

        if force_upload and duplicate_files:
            response['message'] = f'成功上傳 {len(new_files)} 個新檔案，覆蓋 {len(duplicate_files)} 個重複檔案'
        else:
            response['message'] = f'成功上傳 {len(uploaded_files)} 個檔案'

        return jsonify(response)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate_from_stl', methods=['POST'])
def generate_from_stl():
    """從STL檔案生成訓練資料集 - 使用背景任務避免超時"""
    try:
        data = request.get_json()
        stl_files = data.get('stl_files', [])

        if not stl_files:
            return jsonify({'success': False, 'error': '沒有STL檔案'})

        # 檢查 STL 檔案是否都在 STL 目錄中
        # 注意：檔案名稱可能已被 safe_filename 清理過
        missing_files = []
        valid_files = []

        for stl_file in stl_files:
            # 首先嘗試原始檔名
            stl_path = os.path.join('STL', stl_file)
            if os.path.exists(stl_path):
                valid_files.append(stl_file)
                continue

            # 如果原始檔名不存在，嘗試清理後的檔名
            safe_name = safe_filename(stl_file)
            safe_path = os.path.join('STL', safe_name)
            if os.path.exists(safe_path):
                valid_files.append(safe_name)
                continue

            # 兩者都不存在，標記為缺失
            missing_files.append(stl_file)

        if missing_files:
            return jsonify({
                'success': False,
                'error': f'以下 STL 檔案不存在於 STL 目錄: {", ".join(missing_files)}。請檢查檔案名稱是否正確。'
            })

        # 使用找到的有效檔案名稱
        stl_files = valid_files

        # 計算圖片數量
        images_per_stl = 360  # 每個STL生成360張圖片
        total_images = len(stl_files) * images_per_stl

        # 使用背景進程執行圖片生成，避免超時
        import subprocess
        import threading

        # 創建日誌文件
        log_file = 'training_logs/image_generation.log'
        os.makedirs('training_logs', exist_ok=True)

        def run_generation():
            global training_status
            try:
                # 更新訓練狀態
                training_status['is_training'] = True
                training_status['current_epoch'] = 0
                training_status['total_epochs'] = len(stl_files)
                training_status['log_lines'] = []
                training_status['log_lines'].append(f'📦 開始生成 {len(stl_files)} 個模型的圖片資料集')
                training_status['log_lines'].append(f'📊 預計生成 {total_images} 張訓練圖片')

                # 使用 Popen 實時讀取輸出
                process = subprocess.Popen(
                    ['python', 'generate_images_color.py'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                # 實時讀取並記錄輸出
                with open(log_file, 'w', encoding='utf-8') as f:
                    for line in process.stdout:
                        line = line.strip()
                        if line:
                            # 寫入日誌文件
                            f.write(line + '\n')
                            f.flush()

                            # 更新訓練狀態
                            training_status['log_lines'].append(line)

                            # 限制日誌行數
                            if len(training_status['log_lines']) > 200:
                                training_status['log_lines'] = training_status['log_lines'][-200:]

                            # 解析進度信息
                            if 'Processing' in line or '處理' in line:
                                # 嘗試解析模型序號
                                import re
                                match = re.search(r'(\d+)/(\d+)', line)
                                if match:
                                    current = int(match.group(1))
                                    training_status['current_epoch'] = current

                process.wait()

                # 完成後更新狀態
                if process.returncode == 0:
                    training_status['log_lines'].append('✅ 圖片生成完成！')
                    training_status['is_training'] = False
                else:
                    training_status['log_lines'].append(f'❌ 圖片生成失敗，返回碼: {process.returncode}')
                    training_status['is_training'] = False

            except Exception as e:
                training_status['log_lines'].append(f'❌ 生成異常: {str(e)}')
                training_status['is_training'] = False

        # 啟動背景線程
        thread = threading.Thread(target=run_generation, daemon=True)
        thread.start()

        # 立即返回成功，不等待完成
        return jsonify({
            'success': True,
            'image_count': total_images,
            'message': f'已啟動圖片生成任務，預計生成 {total_images} 張訓練圖片',
            'status': 'generating',
            'estimated_time': len(stl_files) * 2,  # 每個STL約2分鐘
            'log_file': log_file
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/validate_dataset', methods=['POST'])
def validate_dataset():
    """驗證資料集是否完整"""
    try:
        data = request.get_json()
        stl_files = data.get('stl_files', [])

        missing_images = []
        incomplete = []
        complete = []

        for stl_file in stl_files:
            # 移除 .stl 副檔名
            model_name = os.path.splitext(stl_file)[0] if stl_file.endswith('.stl') else stl_file
            image_dir = os.path.join('dataset', model_name)

            if not os.path.exists(image_dir):
                missing_images.append({
                    'name': model_name,
                    'status': 'missing',
                    'count': 0
                })
            else:
                # 檢查圖片數量
                image_files = [f for f in os.listdir(image_dir) if f.endswith('.png')]
                image_count = len(image_files)

                if image_count < 360:
                    incomplete.append({
                        'name': model_name,
                        'status': 'incomplete',
                        'count': image_count,
                        'expected': 360
                    })
                else:
                    complete.append({
                        'name': model_name,
                        'status': 'complete',
                        'count': image_count
                    })

        is_valid = len(missing_images) == 0 and len(incomplete) == 0

        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'complete': complete,
            'incomplete': incomplete,
            'missing': missing_images,
            'summary': {
                'total': len(stl_files),
                'complete': len(complete),
                'incomplete': len(incomplete),
                'missing': len(missing_images)
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_class_names')
def get_class_names():
    """獲取分類名稱對應表"""
    try:
        # 合併預設和自訂分類名稱
        default_names = get_default_class_names()
        custom_names = load_class_names()

        # 自訂名稱優先
        for file_key, custom_name in custom_names.items():
            if file_key in default_names:
                default_names[file_key] = custom_name

        return jsonify({
            'success': True,
            'class_names': default_names
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update_class_names', methods=['POST'])
def update_class_names():
    """更新分類名稱"""
    try:
        data = request.get_json()
        class_names = data.get('class_names', {})

        if save_class_names(class_names):
            return jsonify({'success': True, 'message': '分類名稱已更新'})
        else:
            return jsonify({'success': False, 'error': '保存失敗'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reset_class_names', methods=['POST'])
def reset_class_names():
    """重置為預設分類名稱"""
    try:
        # 刪除自訂分類檔案
        if os.path.exists(class_names_file):
            os.remove(class_names_file)

        return jsonify({'success': True, 'message': '已重置為預設分類名稱'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/version', methods=['GET'])
def get_version():
    """獲取系統版本資訊"""
    return jsonify({
        'version': APP_VERSION,
        'build_date': APP_BUILD_DATE,
        'faiss_available': FAISS_AVAILABLE
    })

# 模型初始化標記
_model_init_attempted = False

# 用於 Flask 的 before_first_request（確保至少執行一次）
@app.before_request
def initialize():
    """確保模型已載入"""
    global model_loaded, _model_init_attempted
    if not _model_init_attempted:
        _model_init_attempted = True
        print("🔄 首次請求，初始化系統...")
        load_model()
        load_training_state()
        print("✅ 系統初始化完成")

if __name__ == '__main__':
    # 直接執行時的初始化
    print("🔄 初始化系統...")
    load_model()
    load_training_state()
    print("✅ 系統初始化完成")

    # 啟動網頁伺服器
    print("🚀 啟動 FAISS 辨識系統")
    print("=" * 50)
    print("📱 功能包含:")
    print("  • 檔案上傳識別")
    print("  • 相機即時拍照識別")
    print("  • 數據集樣本測試")
    print("  • 模型訓練和管理")
    print("  • STL 檔案處理")
    print("  • 分類名稱自訂")
    print("  • 訓練狀態持久化")
    print()
    print("🌐 請開啟瀏覽器訪問: http://localhost:8082")
    print("⚠️  按 Ctrl+C 停止伺服器")
    print()

def start_faiss_training(config):
    """啟動FAISS單獨訓練"""
    global training_process, training_status

    try:
        faiss_config = config.get('faiss_config', {})

        # 構建FAISS訓練命令 - 使用 faiss_recognition.py
        # 使用 -u 參數讓 Python 使用無緩衝輸出
        cmd = ['python3', '-u', 'faiss_recognition.py']

        training_status['log_lines'].append(f'📝 FAISS 命令: {" ".join(cmd)}')
        training_status['log_lines'].append(f'⚙️ 訓練配置: Epochs={faiss_config.get("epochs", 100)}, Batch={faiss_config.get("batch_size", 16)}')
        training_status['log_lines'].append('━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        training_status['log_lines'].append('📊 訓練日誌開始...')

        # 啟動FAISS訓練進程 - 使用 unbuffered 輸出
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'  # 確保 Python 輸出不被緩衝

        training_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env
        )

        # 啟動監控線程
        monitor_thread = threading.Thread(target=monitor_training_process)
        monitor_thread.daemon = True
        monitor_thread.start()

        training_status['log_lines'].append('✅ FAISS 訓練進程已啟動')
        training_status['log_lines'].append('⏳ 正在等待訓練輸出...')

    except Exception as e:
        training_status['log_lines'].append(f'❌ FAISS 訓練啟動失敗: {e}')
        training_status['is_training'] = False
        print(f"訓練啟動錯誤: {e}")

def start_faiss_training(config):
    """啟動FAISS索引建立"""
    global training_status

    try:
        if not FAISS_AVAILABLE:
            training_status['log_lines'].append('❌ FAISS 不可用，請檢查安裝')
            training_status['is_training'] = False
            return

        training_status['log_lines'].append('🔍 開始建立 FAISS 特徵索引...')

        # 在單獨線程中建立FAISS索引
        faiss_thread = threading.Thread(target=build_faiss_index_async, args=(config,))
        faiss_thread.daemon = True
        faiss_thread.start()

    except Exception as e:
        training_status['log_lines'].append(f'❌ FAISS 索引建立失敗: {e}')
        training_status['is_training'] = False

def start_dual_training(config):
    """啟動雙模型並行訓練"""
    global training_status

    try:
        training_status['log_lines'].append('🔄 初始化並行訓練系統...')

        # 先啟動FAISS索引建立（通常較快）
        training_status['log_lines'].append('🔍 步驟 1/2: 開始建立 FAISS 特徵索引...')
        if FAISS_AVAILABLE:
            faiss_thread = threading.Thread(target=build_faiss_index_async, args=(config,))
            faiss_thread.daemon = True
            faiss_thread.start()
        else:
            training_status['log_lines'].append('⚠️ FAISS 不可用，跳過特徵索引建立')

        # 然後啟動FAISS訓練
        training_status['log_lines'].append('🎯 步驟 2/2: 開始 FAISS 模型訓練...')
        start_faiss_training(config)

        training_status['log_lines'].append('⚡ 並行訓練系統已啟動')

    except Exception as e:
        training_status['log_lines'].append(f'❌ 並行訓練啟動失敗: {e}')
        training_status['is_training'] = False

def build_faiss_index_async(config):
    """異步建立FAISS索引"""
    global training_status

    try:
        from faiss_recognition import initialize_faiss

        training_status['log_lines'].append('📦 載入 FAISS 識別引擎...')

        # 初始化FAISS引擎
        if initialize_faiss():
            training_status['log_lines'].append('✅ FAISS 特徵索引建立完成')
        else:
            training_status['log_lines'].append('❌ FAISS 特徵索引建立失敗')

        # 如果只進行FAISS訓練，則完成後結束
        if training_status.get('faiss_enabled') and not training_status.get('faiss_enabled'):
            training_status['is_training'] = False
            training_status['log_lines'].append('🎉 FAISS 訓練完成')

    except Exception as e:
        training_status['log_lines'].append(f'❌ FAISS 異步建立失敗: {e}')

# ==================== 系統設定相關 API ====================

@app.route('/settings')
def settings_page():
    """系統設定頁面"""
    return render_template('settings.html')

@app.route('/api/get_models')
def get_models():
    """獲取模型列表（兼容舊版 API）- FAISS 版本"""
    try:
        import pickle

        # 檢查 FAISS 模型檔案
        faiss_index_path = Path('faiss_features.index')
        faiss_labels_path = Path('faiss_labels.pkl')

        current_model = None
        available_models = []

        if faiss_index_path.exists() and faiss_labels_path.exists():
            # 獲取檔案信息
            index_stat = faiss_index_path.stat()
            labels_stat = faiss_labels_path.stat()
            total_size = index_stat.st_size + labels_stat.st_size
            size_mb = total_size / (1024 * 1024)

            # 讀取標籤獲取類別信息
            try:
                with open(faiss_labels_path, 'rb') as f:
                    labels_data = pickle.load(f)
                    if isinstance(labels_data, dict):
                        class_names = labels_data.get('classes', [])
                        label_array = labels_data.get('labels', [])
                        num_classes = len(class_names)
                        num_features = len(label_array)
                    else:
                        num_classes = len(set(labels_data))
                        num_features = len(labels_data)
                        class_names = sorted(set(labels_data))
            except:
                num_classes = 0
                num_features = 0
                class_names = []

            # 構建當前使用的模型信息
            current_model = {
                'name': 'FAISS 識別模型',
                'path': str(faiss_index_path),
                'size': f'{size_mb:.2f} MB',
                'classes': f'{num_classes} 個類別',
                'created_date': datetime.fromtimestamp(index_stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                'status': '使用中' if FAISS_AVAILABLE else '未載入',
                'accuracy': None,  # 可以從驗證結果獲取
                'num_features': num_features,
                'class_names': class_names
            }

        return jsonify({
            'success': True,
            'current_model': current_model,
            'available_models': available_models,
            'models': available_models
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save_settings', methods=['POST'])
def save_settings():
    """儲存系統設定"""
    try:
        settings = request.json
        import sqlite3

        db_path = 'system_data.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 建立或更新設定表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 儲存每個設定
            for key, value in settings.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO system_settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, str(value)))

            conn.commit()

        return jsonify({'success': True, 'message': '設定已儲存'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_settings')
def get_settings():
    """獲取系統設定"""
    try:
        import sqlite3

        db_path = 'system_data.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 確保表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 獲取所有設定
            cursor.execute('SELECT key, value FROM system_settings')
            rows = cursor.fetchall()

            settings = {}
            for key, value in rows:
                # 嘗試轉換為數值
                try:
                    if '.' in value:
                        settings[key] = float(value)
                    else:
                        settings[key] = int(value)
                except:
                    settings[key] = value

            # 提供預設值
            default_settings = {
                'confidence_threshold': 0.25,
                'nms_threshold': 0.45,
                'max_detections': 10,
                'input_size': 640
            }

            for key, default_value in default_settings.items():
                if key not in settings:
                    settings[key] = default_value

        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/system_info')
def system_info():
    """獲取系統資訊"""
    try:
        import platform
        import subprocess

        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # 記憶體資訊
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # GPU 資訊
        gpu_memory = 'N/A'
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                gpu_data = result.stdout.strip().split(', ')
                if len(gpu_data) >= 2:
                    used = float(gpu_data[0])
                    total = float(gpu_data[1])
                    gpu_memory = f"{used:.0f}/{total:.0f} MB"
        except:
            pass

        info = {
            'success': True,
            'python_version': platform.python_version(),
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_total': f"{memory.total / (1024**3):.2f} GB",
            'disk_total': f"{psutil.disk_usage('/').total / (1024**3):.2f} GB",
            'gpu_memory': gpu_memory
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/list_stl_files')
def list_stl_files():
    """列出 STL 資料夾中的所有 STL 檔案"""
    try:
        import os
        from pathlib import Path

        stl_dir = Path('STL')
        if not stl_dir.exists():
            return jsonify({'success': True, 'files': [], 'total': 0})

        stl_files = []
        for file_path in stl_dir.glob('*.stl'):
            stat = file_path.stat()

            # 檢查對應的資料集圖片數量
            model_name = file_path.stem  # 不含副檔名的檔案名
            dataset_dir = Path('dataset') / model_name
            image_count = 0
            if dataset_dir.exists():
                image_count = len(list(dataset_dir.glob('*.png')))

            stl_files.append({
                'name': file_path.name,
                'path': str(file_path),
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'created_time': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'image_count': image_count
            })

        # 按名稱排序
        stl_files.sort(key=lambda x: x['name'])

        return jsonify({
            'success': True,
            'files': stl_files,
            'total': len(stl_files)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/statistics')
def get_statistics():
    """獲取系統統計資料"""
    try:
        stats = data_manager.get_statistics()
        # 直接返回統計數據在頂層，而不是嵌套在 statistics 下
        return jsonify({
            'success': True,
            'stl_count': stats.get('stl_count', 0),
            'image_count': stats.get('image_count', 0),
            'recognition_count': stats.get('recognition_count', 0),
            'class_count': stats.get('class_count', 0)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/upload_history')
def get_upload_history():
    """獲取上傳歷史"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit

        records = data_manager.get_upload_history(limit=limit, offset=offset)
        return jsonify({'success': True, 'records': records, 'page': page})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/recognition_history')
def get_recognition_history():
    """獲取辨識歷史"""
    try:
        import sqlite3
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit

        # 直接查詢資料庫
        db_path = 'system_data.db'
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 獲取記錄，JOIN upload_history 來獲取原始上傳照片
            cursor.execute('''
                SELECT
                    r.*,
                    u.file_path as upload_file_path,
                    u.filename as upload_filename
                FROM recognition_history r
                LEFT JOIN upload_history u ON r.upload_id = u.id
                ORDER BY r.timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            rows = cursor.fetchall()
            records = [dict(row) for row in rows]

            # 轉換圖片路徑為正確的 URL，並添加 STL 參考圖片
            for record in records:
                # 處理上傳照片路徑
                if record.get('upload_file_path'):
                    # 移除 'web_uploads/' 前綴，然後加上 '/web_uploads/'
                    path = record['upload_file_path']
                    if path.startswith('web_uploads/'):
                        path = path[len('web_uploads/'):]
                    if not path.startswith('/'):
                        path = '/' + path
                    if not path.startswith('/web_uploads/'):
                        record['upload_file_path'] = f"/web_uploads{path}"
                    else:
                        record['upload_file_path'] = path

                # 添加 STL 參考圖片路徑 - 找出最相似的圖片
                if record.get('predicted_class') and record.get('upload_file_path'):
                    import os
                    import cv2
                    import numpy as np

                    class_name = record['predicted_class']
                    dataset_path = f'dataset/{class_name}'

                    # 移除路徑前綴以獲取實際檔案路徑
                    upload_path = record['upload_file_path']
                    if upload_path.startswith('/web_uploads/'):
                        upload_path = 'web_uploads/' + upload_path[len('/web_uploads/'):]

                    # 檢查資料夾是否存在
                    if os.path.exists(dataset_path) and os.path.exists(upload_path):
                        try:
                            # 讀取上傳的圖片
                            upload_img = cv2.imread(upload_path)
                            if upload_img is None:
                                record['stl_reference_image'] = None
                                continue

                            # 調整大小以加快比對速度
                            upload_img = cv2.resize(upload_img, (256, 256))
                            upload_gray = cv2.cvtColor(upload_img, cv2.COLOR_BGR2GRAY)

                            # 獲取該類別的所有圖片
                            images = [f for f in os.listdir(dataset_path) if f.endswith('.png')]

                            if images:
                                # 儲存所有匹配結果的列表 (圖片名稱, 相似度分數)
                                matches = []

                                # 只比對前30張圖片以節省時間（或全部比對如果少於30張）
                                sample_images = images[:min(30, len(images))]

                                for img_name in sample_images:
                                    img_path = os.path.join(dataset_path, img_name)
                                    ref_img = cv2.imread(img_path)

                                    if ref_img is not None:
                                        # 調整大小
                                        ref_img = cv2.resize(ref_img, (256, 256))
                                        ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)

                                        # 使用結構相似性指數（SSIM）或簡單的直方圖比對
                                        # 這裡使用直方圖比對，更快速
                                        upload_hist = cv2.calcHist([upload_gray], [0], None, [256], [0, 256])
                                        ref_hist = cv2.calcHist([ref_gray], [0], None, [256], [0, 256])

                                        # 歸一化
                                        upload_hist = cv2.normalize(upload_hist, upload_hist).flatten()
                                        ref_hist = cv2.normalize(ref_hist, ref_hist).flatten()

                                        # 計算相關性
                                        score = cv2.compareHist(upload_hist, ref_hist, cv2.HISTCMP_CORREL)

                                        # 將相關性分數轉換為百分比 (範圍 -1 到 1，轉為 0 到 100)
                                        similarity_percent = max(0, min(100, (score + 1) * 50))

                                        matches.append({
                                            'image': img_name,
                                            'score': score,
                                            'similarity_percent': round(similarity_percent, 2)
                                        })

                                # 按相似度分數排序，取前三名
                                matches.sort(key=lambda x: x['score'], reverse=True)
                                top_matches = matches[:3]

                                if top_matches:
                                    # 儲存前三張最相似的圖片
                                    record['stl_reference_images'] = [
                                        {
                                            'path': f'/dataset/{class_name}/{match["image"]}',
                                            'similarity': match['similarity_percent']
                                        }
                                        for match in top_matches
                                    ]
                                    # 保留最高相似度作為主要分數
                                    record['similarity_score'] = top_matches[0]['similarity_percent']
                                    # 向下兼容：第一張圖片作為主要參考圖
                                    record['stl_reference_image'] = record['stl_reference_images'][0]['path']
                                else:
                                    record['stl_reference_images'] = []
                                    record['stl_reference_image'] = None
                                    record['similarity_score'] = 0
                            else:
                                record['stl_reference_image'] = None
                                record['similarity_score'] = 0
                        except Exception as e:
                            print(f"圖片比對錯誤: {e}")
                            # 如果比對失敗，使用第一張圖片作為後備
                            images = [f for f in os.listdir(dataset_path) if f.endswith('.png')]
                            if images:
                                record['stl_reference_image'] = f'/dataset/{class_name}/{images[0]}'
                            else:
                                record['stl_reference_image'] = None
                            record['similarity_score'] = 0
                    else:
                        record['stl_reference_image'] = None
                        record['similarity_score'] = 0
                else:
                    record['stl_reference_image'] = None
                    record['similarity_score'] = 0

            # 獲取總數
            cursor.execute('SELECT COUNT(*) FROM recognition_history')
            total = cursor.fetchone()[0]

        return jsonify({'success': True, 'data': records, 'records': records, 'total': total, 'page': page})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/training_history')
def get_training_history_api():
    """獲取訓練歷史"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit

        records = data_manager.get_training_history(limit=limit, offset=offset)
        return jsonify({'success': True, 'records': records, 'page': page})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/models_detailed')
def get_models_detailed():
    """獲取詳細的模型列表"""
    try:
        models = model_manager.scan_models()
        summary = model_manager.get_model_summary()
        return jsonify({
            'success': True,
            'models': models,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/activate_model', methods=['POST'])
def activate_model():
    """啟用指定模型"""
    try:
        data = request.json
        model_path = data.get('model_path')

        if model_manager.load_model(model_path):
            # 更新全域模型變數
            global model, model_loaded, model_info
            model = model_manager.get_current_model()
            model_loaded = True
            model_info['path'] = model_path

            # 註冊到資料管理器
            data_manager.set_active_model(model_path)

            return jsonify({'success': True, 'message': '模型已啟用'})
        else:
            return jsonify({'success': False, 'error': '模型載入失敗'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/backup_model', methods=['POST'])
def backup_model_api():
    """備份模型"""
    try:
        data = request.json
        model_path = data.get('model_path')

        if model_manager.backup_model(model_path):
            return jsonify({'success': True, 'message': '模型已備份'})
        else:
            return jsonify({'success': False, 'error': '備份失敗'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/export_data')
def export_data_api():
    """匯出系統資料"""
    try:
        export_type = request.args.get('type', 'all')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f'export_{export_type}_{timestamp}.json'

        table_map = {
            'upload': 'upload_history',
            'recognition': 'recognition_history',
            'training': 'training_history',
            'all': None
        }

        table_name = table_map.get(export_type)
        data_manager.export_data(output_path, table_name)

        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/clear_old_data', methods=['POST'])
def clear_old_data_api():
    """清理舊資料"""
    try:
        days = int(request.json.get('days', 30))
        data_manager.clear_old_records(days=days)
        return jsonify({'success': True, 'message': f'已清理 {days} 天前的資料'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# 完整重新訓練相關 API
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

@app.route('/api/generate_all_images', methods=['POST'])
def generate_all_images_api():
    """生成所有圖片"""
    global image_generation_status

    try:
        # 獲取模式參數
        data = request.get_json() or {}
        mode = data.get('mode', 'normal')  # 'normal' 或 'precision'

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
            'total_images': 0,
            'mode': mode
        }

        # 掃描 STL 檔案
        stl_files = glob.glob('STL/*.stl')
        image_generation_status['total_models'] = len(stl_files)

        # 在背景執行圖片生成
        import threading
        thread = threading.Thread(target=generate_images_thread, args=(stl_files, mode))
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'stl_count': len(stl_files),
            'mode': mode
        })
    except Exception as e:
        image_generation_status['is_generating'] = False
        image_generation_status['error'] = str(e)
        return jsonify({'success': False, 'error': str(e)})

def generate_images_thread(stl_files, mode='normal'):
    """背景執行緒：生成圖片"""
    global image_generation_status

    try:
        total = len(stl_files)
        images_per_model = 60 if mode == 'normal' else 360

        mode_name = '正常訓練' if mode == 'normal' else '精準訓練'
        image_generation_status['log_lines'].append(f'📸 開始生成 {total} 個模型的圖片 ({mode_name})')
        image_generation_status['log_lines'].append(f'📊 每個模型將生成 {images_per_model} 張圖片')

        if mode == 'precision':
            image_generation_status['log_lines'].append(f'✨ 精準訓練模式：包含光照干擾和背景干擾')

        estimated_time = total * (1 if mode == 'normal' else 3)
        image_generation_status['log_lines'].append(f'⏱️ 預計耗時: {estimated_time} 分鐘')

        # 根據模式選擇不同的生成腳本
        if mode == 'normal':
            # 正常訓練：60張，使用簡化版本
            result = subprocess.run(
                ['python', 'generate_images_normal.py'],
                capture_output=True,
                text=True,
                timeout=1800  # 30分鐘超時
            )
        else:
            # 精準訓練：360張，使用完整版本（含干擾）
            result = subprocess.run(
                ['python', 'generate_images_color.py'],
                capture_output=True,
                text=True,
                timeout=3600  # 60分鐘超時
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

@app.route('/api/image_generation_status')
def image_generation_status_api():
    """查詢圖片生成狀態"""
    return jsonify(image_generation_status)

@app.route('/api/generate_images', methods=['POST'])
def generate_single_stl_images():
    """為單個 STL 檔案生成圖片"""
    try:
        data = request.get_json()
        stl_file = data.get('stl_file')

        if not stl_file:
            return jsonify({'success': False, 'error': '未提供 STL 檔案名稱'}), 400

        stl_path = os.path.join('STL', stl_file)

        if not os.path.exists(stl_path):
            return jsonify({'success': False, 'error': 'STL 檔案不存在'}), 404

        # 在背景執行圖片生成
        import threading
        thread = threading.Thread(target=generate_single_images_thread, args=(stl_file,))
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': f'開始為 {stl_file} 生成圖片'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_single_images_thread(stl_file):
    """背景執行緒：為單個 STL 生成圖片"""
    try:
        # 使用 generate_images_color.py，只處理指定的 STL
        model_name = os.path.splitext(stl_file)[0]

        # 創建臨時 Python 腳本來生成單個模型的圖片
        script_content = f'''
import sys
sys.path.insert(0, '.')
from generate_images_color import generate_images_for_model

# 只生成指定模型的圖片
stl_path = "STL/{stl_file}"
generate_images_for_model(stl_path, "{model_name}")
print(f"✅ {{model_name}} 圖片生成完成")
'''

        # 寫入臨時腳本
        temp_script = f'temp_generate_{model_name}.py'
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 執行生成
        result = subprocess.run(
            ['python', temp_script],
            capture_output=True,
            text=True,
            timeout=600  # 10分鐘超時
        )

        # 清理臨時檔案
        if os.path.exists(temp_script):
            os.remove(temp_script)

    except Exception as e:
        logger.error(f"生成圖片失敗: {e}")

@app.route('/api/delete_stl', methods=['POST'])
def delete_stl_file():
    """刪除 STL 檔案及其對應的資料集"""
    try:
        data = request.get_json()
        filename = data.get('filename')

        if not filename:
            return jsonify({'success': False, 'error': '未提供檔案名稱'}), 400

        stl_path = os.path.join('STL', filename)

        if not os.path.exists(stl_path):
            return jsonify({'success': False, 'error': 'STL 檔案不存在'}), 404

        # 刪除 STL 檔案
        os.remove(stl_path)

        # 刪除對應的資料集資料夾
        model_name = os.path.splitext(filename)[0]
        dataset_path = os.path.join('dataset', model_name)

        if os.path.exists(dataset_path):
            import shutil
            shutil.rmtree(dataset_path)

        return jsonify({
            'success': True,
            'message': f'已刪除 {filename} 及其資料集'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8082)