"""
模型訓練 Blueprint
處理訓練控制、監控、歷史等功能
"""

from flask import Blueprint, render_template, request, jsonify

training_bp = Blueprint('training', __name__, url_prefix='/training')

@training_bp.route('/')
def index():
    """訓練控制台主頁"""
    return render_template('training/index.html')

@training_bp.route('/new')
def new_training():
    """新訓練任務頁面"""
    return render_template('training/new.html')

@training_bp.route('/monitor')
def monitor_page():
    """訓練監控頁面"""
    return render_template('training/monitor.html')

@training_bp.route('/history')
def history_page():
    """訓練歷史頁面"""
    return render_template('training/history.html')
