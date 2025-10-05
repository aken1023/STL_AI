"""
Blueprint 模組初始化
"""

from .stl_management import stl_bp
from .recognition import recognition_bp
from .training import training_bp
from .search import search_bp

__all__ = ['stl_bp', 'recognition_bp', 'training_bp', 'search_bp']
