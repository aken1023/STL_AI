"""
Search Blueprint - CLIP + FAISS 圖像相似性搜尋
支援三種搜尋模式：
1. 圖像搜尋 (Image-to-Image)
2. 文字搜尋 (Text-to-Image)
3. 混合搜尋 (Hybrid Search)
"""

from flask import Blueprint, render_template, request, jsonify
from pathlib import Path
import os
from werkzeug.utils import secure_filename
import logging

# 設定日誌
logger = logging.getLogger(__name__)

# 創建 Blueprint
search_bp = Blueprint('search', __name__, url_prefix='/search')

# 上傳設定
SEARCH_UPLOAD_FOLDER = 'search_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# 確保上傳目錄存在
os.makedirs(SEARCH_UPLOAD_FOLDER, exist_ok=True)

# 全域搜尋引擎實例
search_engine = None


def allowed_file(filename):
    """檢查檔案類型是否允許"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def init_search_engine():
    """初始化 CLIP + FAISS 搜尋引擎"""
    global search_engine

    if search_engine is not None:
        return search_engine

    try:
        from clip_faiss_search import CLIPFAISSSearch

        # 檢查索引檔案是否存在
        if not Path('clip_features.npy').exists():
            logger.warning("⚠️ CLIP 特徵索引不存在，請先執行 clip_feature_extractor.py")
            return None

        logger.info("🚀 初始化 CLIP + FAISS 搜尋引擎...")
        search_engine = CLIPFAISSSearch()
        logger.info("✅ 搜尋引擎初始化成功！")

        return search_engine

    except Exception as e:
        logger.error(f"❌ 搜尋引擎初始化失敗: {e}")
        return None


@search_bp.route('/')
def index():
    """搜尋主頁"""
    # 檢查搜尋引擎狀態
    engine = init_search_engine()

    if engine is None:
        index_exists = False
        stats = None
    else:
        index_exists = True
        stats = engine.get_statistics()

    return render_template('search/index.html',
                         index_exists=index_exists,
                         stats=stats)


@search_bp.route('/api/search/image', methods=['POST'])
def api_search_by_image():
    """
    API: 圖像搜尋 (Image-to-Image)

    POST /api/search/image
    Form Data:
        - image: 圖片檔案
        - k: 返回結果數量 (預設 5)
    """
    engine = init_search_engine()
    if engine is None:
        return jsonify({
            'success': False,
            'error': 'CLIP 搜尋引擎未初始化，請先建立索引'
        }), 500

    # 檢查檔案
    if 'image' not in request.files:
        return jsonify({
            'success': False,
            'error': '未提供圖片檔案'
        }), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({
            'success': False,
            'error': '未選擇檔案'
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': '不支援的檔案格式'
        }), 400

    # 儲存上傳的圖片
    filename = secure_filename(file.filename)
    filepath = os.path.join(SEARCH_UPLOAD_FOLDER, filename)
    file.save(filepath)

    # 取得參數
    k = int(request.form.get('k', 5))

    try:
        # 執行搜尋
        results = engine.search_by_image(filepath, k=k)

        # 轉換路徑為可訪問的 URL
        for result in results:
            # dataset/xxx/img_001.png -> /static/dataset/xxx/img_001.png
            result['image_url'] = '/' + result['image_path']

        return jsonify({
            'success': True,
            'query_image': filepath,
            'results': results,
            'total': len(results)
        })

    except Exception as e:
        logger.error(f"❌ 圖像搜尋失敗: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/api/search/text', methods=['POST'])
def api_search_by_text():
    """
    API: 文字搜尋 (Text-to-Image)

    POST /api/search/text
    JSON:
        - text: 搜尋文字
        - k: 返回結果數量 (預設 5)
    """
    engine = init_search_engine()
    if engine is None:
        return jsonify({
            'success': False,
            'error': 'CLIP 搜尋引擎未初始化，請先建立索引'
        }), 500

    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({
            'success': False,
            'error': '未提供搜尋文字'
        }), 400

    text = data['text']
    k = int(data.get('k', 5))

    if not text.strip():
        return jsonify({
            'success': False,
            'error': '搜尋文字不能為空'
        }), 400

    try:
        # 執行搜尋
        results = engine.search_by_text(text, k=k)

        # 轉換路徑
        for result in results:
            result['image_url'] = '/' + result['image_path']

        return jsonify({
            'success': True,
            'query_text': text,
            'results': results,
            'total': len(results)
        })

    except Exception as e:
        logger.error(f"❌ 文字搜尋失敗: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/api/search/hybrid', methods=['POST'])
def api_search_hybrid():
    """
    API: 混合搜尋 (Hybrid Search)

    POST /api/search/hybrid
    Form Data:
        - image: 圖片檔案 (可選)
        - text: 搜尋文字 (可選)
        - k: 返回結果數量 (預設 5)
        - image_weight: 圖片權重 0-1 (預設 0.7)
    """
    engine = init_search_engine()
    if engine is None:
        return jsonify({
            'success': False,
            'error': 'CLIP 搜尋引擎未初始化，請先建立索引'
        }), 500

    # 取得參數
    text = request.form.get('text', '').strip()
    k = int(request.form.get('k', 5))
    image_weight = float(request.form.get('image_weight', 0.7))

    image_path = None

    # 處理圖片
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(SEARCH_UPLOAD_FOLDER, filename)
            file.save(image_path)

    # 檢查至少提供一種搜尋方式
    if not text and not image_path:
        return jsonify({
            'success': False,
            'error': '必須提供圖片或文字至少一種'
        }), 400

    try:
        # 執行混合搜尋
        results = engine.search_hybrid(
            image_path=image_path,
            text=text if text else None,
            k=k,
            image_weight=image_weight
        )

        # 轉換路徑
        for result in results:
            result['image_url'] = '/' + result['image_path']

        return jsonify({
            'success': True,
            'query_image': image_path,
            'query_text': text,
            'image_weight': image_weight,
            'results': results,
            'total': len(results)
        })

    except Exception as e:
        logger.error(f"❌ 混合搜尋失敗: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/api/search/rebuild_index', methods=['POST'])
def api_rebuild_index():
    """
    API: 重建 CLIP 索引

    POST /api/search/rebuild_index
    """
    try:
        from clip_feature_extractor import CLIPFeatureExtractor

        logger.info("🔨 開始重建 CLIP 索引...")

        # 初始化特徵提取器
        extractor = CLIPFeatureExtractor(model_name="ViT-B/32")

        # 建立索引
        success = extractor.build_dataset_index(
            dataset_dir="dataset",
            output_dir=".",
            batch_size=32
        )

        if success:
            # 重新初始化搜尋引擎
            global search_engine
            search_engine = None
            init_search_engine()

            return jsonify({
                'success': True,
                'message': 'CLIP 索引重建成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '索引重建失敗'
            }), 500

    except Exception as e:
        logger.error(f"❌ 重建索引失敗: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/api/search/stats', methods=['GET'])
def api_search_stats():
    """
    API: 取得搜尋引擎統計資訊

    GET /api/search/stats
    """
    engine = init_search_engine()

    if engine is None:
        return jsonify({
            'success': False,
            'error': 'CLIP 搜尋引擎未初始化'
        }), 500

    try:
        stats = engine.get_statistics()

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"❌ 取得統計資訊失敗: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
