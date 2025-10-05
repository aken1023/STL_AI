"""
模型識別 Blueprint
處理圖片上傳識別、相機識別、批次識別等功能
"""

from flask import Blueprint, render_template, request, jsonify

recognition_bp = Blueprint('recognition', __name__, url_prefix='/recognition')

@recognition_bp.route('/')
def index():
    """識別主頁"""
    return render_template('recognition/index.html')

@recognition_bp.route('/upload')
def upload_page():
    """上傳圖片識別頁面"""
    return render_template('recognition/upload.html')

@recognition_bp.route('/camera')
def camera_page():
    """相機拍照識別頁面"""
    return render_template('recognition/camera.html')

@recognition_bp.route('/batch')
def batch_page():
    """批次識別頁面"""
    return render_template('recognition/batch.html')
