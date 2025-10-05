#!/usr/bin/env python3
"""
資料管理模組 - 處理上傳歷史、辨識紀錄和資料持久化
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from typing import List, Dict, Optional
import threading

class DataManager:
    """資料管理器 - 使用 SQLite 儲存系統資料"""

    def __init__(self, db_path='system_data.db'):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """初始化資料庫"""
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

            # 辨識紀錄表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recognition_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    upload_id INTEGER,
                    method TEXT NOT NULL,
                    predicted_class TEXT,
                    confidence REAL,
                    inference_time REAL,
                    result_image_path TEXT,
                    success INTEGER DEFAULT 1,
                    error_message TEXT,
                    FOREIGN KEY (upload_id) REFERENCES upload_history(id)
                )
            ''')

            # 訓練歷史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    model_type TEXT,
                    epochs INTEGER,
                    batch_size INTEGER,
                    final_accuracy REAL,
                    final_map REAL,
                    training_time REAL,
                    model_path TEXT,
                    client_ip TEXT,
                    status TEXT DEFAULT 'completed'
                )
            ''')

            # 模型管理表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT UNIQUE NOT NULL,
                    model_type TEXT,
                    model_path TEXT NOT NULL,
                    created_time TEXT NOT NULL,
                    file_size INTEGER,
                    epochs INTEGER,
                    accuracy REAL,
                    map_score REAL,
                    is_active INTEGER DEFAULT 0,
                    description TEXT
                )
            ''')

            # 系統設定表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            ''')

            conn.commit()

    def add_upload_record(self, filename: str, file_size: int, file_path: str,
                         client_ip: str = None, user_agent: str = None) -> int:
        """添加上傳記錄"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO upload_history
                    (timestamp, filename, file_size, file_path, client_ip, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    filename,
                    file_size,
                    file_path,
                    client_ip,
                    user_agent
                ))
                conn.commit()
                return cursor.lastrowid

    def add_recognition_record(self, upload_id: int, method: str,
                             predicted_class: str = None, confidence: float = None,
                             inference_time: float = None, result_image_path: str = None,
                             success: bool = True, error_message: str = None):
        """添加辨識記錄"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO recognition_history
                    (timestamp, upload_id, method, predicted_class, confidence,
                     inference_time, result_image_path, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    upload_id,
                    method,
                    predicted_class,
                    confidence,
                    inference_time,
                    result_image_path,
                    1 if success else 0,
                    error_message
                ))
                conn.commit()

    def add_training_record(self, model_name: str, model_type: str,
                          epochs: int = None, batch_size: int = None,
                          final_accuracy: float = None, final_map: float = None,
                          training_time: float = None, model_path: str = None,
                          client_ip: str = None, status: str = 'completed'):
        """添加訓練記錄"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO training_history
                    (timestamp, model_name, model_type, epochs, batch_size,
                     final_accuracy, final_map, training_time, model_path, client_ip, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    model_name,
                    model_type,
                    epochs,
                    batch_size,
                    final_accuracy,
                    final_map,
                    training_time,
                    model_path,
                    client_ip,
                    status
                ))
                conn.commit()

    def get_upload_history(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """獲取上傳歷史"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM upload_history
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_recognition_history(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """獲取辨識歷史（含上傳資訊）"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    r.*,
                    u.filename,
                    u.file_path,
                    u.client_ip
                FROM recognition_history r
                LEFT JOIN upload_history u ON r.upload_id = u.id
                ORDER BY r.timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_training_history(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """獲取訓練歷史"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM training_history
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict:
        """獲取統計資訊"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 總上傳數
            cursor.execute('SELECT COUNT(*) FROM upload_history')
            total_uploads = cursor.fetchone()[0]

            # 總辨識數
            cursor.execute('SELECT COUNT(*) FROM recognition_history')
            total_recognitions = cursor.fetchone()[0]

            # 成功辨識數
            cursor.execute('SELECT COUNT(*) FROM recognition_history WHERE success = 1')
            successful_recognitions = cursor.fetchone()[0]

            # 平均準確率
            cursor.execute('SELECT AVG(confidence) FROM recognition_history WHERE success = 1')
            avg_confidence = cursor.fetchone()[0] or 0

            # 平均推論時間
            cursor.execute('SELECT AVG(inference_time) FROM recognition_history WHERE success = 1')
            avg_inference_time = cursor.fetchone()[0] or 0

            # 訓練次數
            cursor.execute('SELECT COUNT(*) FROM training_history')
            total_trainings = cursor.fetchone()[0]

            # 各方法使用次數
            cursor.execute('''
                SELECT method, COUNT(*) as count
                FROM recognition_history
                GROUP BY method
            ''')
            method_usage = {row[0]: row[1] for row in cursor.fetchall()}

            # 各類別辨識次數
            cursor.execute('''
                SELECT predicted_class, COUNT(*) as count
                FROM recognition_history
                WHERE success = 1 AND predicted_class IS NOT NULL
                GROUP BY predicted_class
                ORDER BY count DESC
            ''')
            class_distribution = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                'total_uploads': total_uploads,
                'total_recognitions': total_recognitions,
                'successful_recognitions': successful_recognitions,
                'recognition_success_rate': (successful_recognitions / total_recognitions * 100) if total_recognitions > 0 else 0,
                'avg_confidence': round(avg_confidence, 4),
                'avg_inference_time': round(avg_inference_time, 2),
                'total_trainings': total_trainings,
                'method_usage': method_usage,
                'class_distribution': class_distribution
            }

    def register_model(self, model_name: str, model_path: str, model_type: str,
                      epochs: int = None, accuracy: float = None, map_score: float = None,
                      description: str = None):
        """註冊模型到管理系統"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                file_size = os.path.getsize(model_path) if os.path.exists(model_path) else 0

                cursor.execute('''
                    INSERT OR REPLACE INTO model_registry
                    (model_name, model_type, model_path, created_time, file_size,
                     epochs, accuracy, map_score, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    model_name,
                    model_type,
                    model_path,
                    datetime.now().isoformat(),
                    file_size,
                    epochs,
                    accuracy,
                    map_score,
                    description
                ))
                conn.commit()

    def get_registered_models(self) -> List[Dict]:
        """獲取已註冊的模型列表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM model_registry
                ORDER BY created_time DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def set_active_model(self, model_name: str):
        """設定活躍模型"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 先將所有模型設為非活躍
                cursor.execute('UPDATE model_registry SET is_active = 0')
                # 設定指定模型為活躍
                cursor.execute('''
                    UPDATE model_registry SET is_active = 1
                    WHERE model_name = ?
                ''', (model_name,))
                conn.commit()

    def delete_model_record(self, model_name: str):
        """刪除模型記錄"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM model_registry WHERE model_name = ?', (model_name,))
                conn.commit()

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """獲取系統設定"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM system_settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            return result[0] if result else default

    def set_setting(self, key: str, value: str):
        """設定系統設定"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO system_settings (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, value, datetime.now().isoformat()))
                conn.commit()

    def clear_old_records(self, days: int = 30):
        """清理舊記錄"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()

        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 刪除舊的上傳記錄
                cursor.execute('''
                    DELETE FROM upload_history
                    WHERE timestamp < ? AND status != 'important'
                ''', (cutoff_str,))

                # 刪除舊的辨識記錄
                cursor.execute('''
                    DELETE FROM recognition_history
                    WHERE timestamp < ?
                ''', (cutoff_str,))

                conn.commit()

    def export_data(self, output_path: str, table_name: str = None):
        """匯出資料到 JSON"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            data = {}

            if table_name:
                cursor.execute(f'SELECT * FROM {table_name}')
                data[table_name] = [dict(row) for row in cursor.fetchall()]
            else:
                # 匯出所有表
                tables = ['upload_history', 'recognition_history', 'training_history', 'model_registry']
                for table in tables:
                    cursor.execute(f'SELECT * FROM {table}')
                    data[table] = [dict(row) for row in cursor.fetchall()]

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

# 全域單例
_data_manager = None

def get_data_manager() -> DataManager:
    """獲取資料管理器單例"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager
