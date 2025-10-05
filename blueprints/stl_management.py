"""
STL 檔案管理 Blueprint
處理 STL 檔案的上傳、列表、生成等功能
"""

from flask import Blueprint, render_template, request, jsonify
import os

stl_bp = Blueprint('stl', __name__, url_prefix='/stl')

@stl_bp.route('/')
def index():
    """STL 管理主頁 - 顯示 STL 列表"""
    return render_template('stl/list.html')

@stl_bp.route('/upload')
def upload_page():
    """STL 上傳頁面"""
    return render_template('stl/upload.html')

@stl_bp.route('/generate')
def generate_page():
    """圖片生成頁面"""
    return render_template('stl/generate.html')

@stl_bp.route('/list')
def list_page():
    """STL 列表頁面"""
    return render_template('stl/list.html')
