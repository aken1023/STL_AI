#!/usr/bin/env python3
"""
FAISS-based Image Recognition System
使用 FAISS 相似度搜索進行圖片識別
"""
import os
import numpy as np
import cv2
import faiss
import pickle
from PIL import Image
import time
from sklearn.preprocessing import normalize
from torchvision import transforms, models
import torch
import torch.nn as nn

class FAISSRecognitionEngine:
    def __init__(self):
        self.index = None
        self.labels = None
        self.feature_extractor = None
        self.classes = []
        self.index_file = "faiss_features.index"
        self.labels_file = "faiss_labels.pkl"
        self.loaded = False

        # 預處理轉換
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                               std=[0.229, 0.224, 0.225])
        ])

    def load_feature_extractor(self):
        """載入特徵提取模型"""
        import time
        current_time = time.strftime('%H:%M:%S')
        print(f"[{current_time}] 📦 載入 ResNet50 特徵提取器...")

        # 使用預訓練的 ResNet50 (新版 API)
        import warnings
        warnings.filterwarnings('ignore', category=UserWarning)

        try:
            # 嘗試使用新版 API (torchvision >= 0.13)
            from torchvision.models import ResNet50_Weights
            self.feature_extractor = models.resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
        except (ImportError, AttributeError):
            # 降級到舊版 API
            self.feature_extractor = models.resnet50(pretrained=True)

        self.feature_extractor = nn.Sequential(*list(self.feature_extractor.children())[:-1])
        self.feature_extractor.eval()

        # 移動到 GPU（如果可用）
        current_time = time.strftime('%H:%M:%S')
        if torch.cuda.is_available():
            self.feature_extractor = self.feature_extractor.cuda()
            print(f"[{current_time}] 🚀 使用 GPU 加速")
        else:
            print(f"[{current_time}] 💻 使用 CPU 運算")

    def extract_features(self, image_path):
        """從圖片提取特徵向量"""
        try:
            # 載入和預處理圖片
            image = Image.open(image_path).convert('RGB')
            input_tensor = self.transform(image).unsqueeze(0)

            if torch.cuda.is_available():
                input_tensor = input_tensor.cuda()

            with torch.no_grad():
                features = self.feature_extractor(input_tensor)
                features = features.flatten().cpu().numpy()

            # 正規化特徵向量
            features = normalize([features])[0]
            return features

        except Exception as e:
            print(f"❌ 特徵提取失敗 {image_path}: {e}")
            return None

    def build_index(self, dataset_dir=None):
        """建立 FAISS 索引"""
        if dataset_dir is None:
            # 使用標準資料集目錄
            dataset_dir = "dataset"

        if not os.path.exists(dataset_dir):
            print("❌ 找不到資料集目錄")
            return False

        print(f"🏗️  建立 FAISS 索引從 {dataset_dir}")

        # 載入特徵提取器
        if self.feature_extractor is None:
            self.load_feature_extractor()

        features_list = []
        labels_list = []

        # 掃描所有類別
        classes = [d for d in os.listdir(dataset_dir) if os.path.isdir(os.path.join(dataset_dir, d))]
        self.classes = sorted(classes)

        import time
        start_time = time.time()
        current_time = time.strftime('%H:%M:%S')

        print(f"[{current_time}] 📂 找到 {len(self.classes)} 個類別: {', '.join(self.classes[:5])}{'...' if len(self.classes) > 5 else ''}")

        # 計算總圖片數
        total_images = 0
        for class_name in self.classes:
            class_dir = os.path.join(dataset_dir, class_name)
            images = [f for f in os.listdir(class_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            total_images += len(images)

        current_time = time.strftime('%H:%M:%S')
        print(f"[{current_time}] 📊 總共需要處理 {total_images} 張圖片 (來自 {len(self.classes)} 個類別)")
        print(f"[{current_time}] ⚡ 平均每個類別: {total_images // len(self.classes)} 張圖片")

        processed_count = 0

        for class_id, class_name in enumerate(self.classes):
            class_start_time = time.time()
            class_dir = os.path.join(dataset_dir, class_name)
            images = [f for f in os.listdir(class_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

            current_time = time.strftime('%H:%M:%S')
            print(f"[{current_time}] 🔍 處理類別 [{class_id+1}/{len(self.classes)}] {class_name}: {len(images)} 張圖片")

            for img_idx, img_name in enumerate(images):
                img_path = os.path.join(class_dir, img_name)
                features = self.extract_features(img_path)

                if features is not None:
                    features_list.append(features)
                    labels_list.append({
                        'class_id': class_id,
                        'class_name': class_name,
                        'image_path': img_path
                    })

                processed_count += 1

                # 每處理10張圖片輸出一次進度
                if processed_count % 10 == 0 or processed_count == total_images:
                    progress_percent = (processed_count / total_images * 100)
                    elapsed = time.time() - start_time
                    if processed_count > 0:
                        avg_time_per_image = elapsed / processed_count
                        remaining_images = total_images - processed_count
                        estimated_remaining = avg_time_per_image * remaining_images
                        current_time = time.strftime('%H:%M:%S')
                        print(f"[{current_time}] ⏳ 進度: {processed_count}/{total_images} 張圖片 ({progress_percent:.1f}%) | 預估剩餘: {estimated_remaining/60:.1f} 分鐘")

            # 每個類別完成後輸出進度
            class_elapsed = time.time() - class_start_time
            class_progress = ((class_id + 1) / len(self.classes) * 100)
            current_time = time.strftime('%H:%M:%S')
            print(f"[{current_time}] ✅ 類別 {class_name} 處理完成 ({len(images)} 張, {class_elapsed:.1f}秒) | 總進度: {class_progress:.1f}%")

        if len(features_list) == 0:
            current_time = time.strftime('%H:%M:%S')
            print(f"[{current_time}] ❌ 沒有成功提取任何特徵")
            return False

        # 轉換為 numpy 陣列
        current_time = time.strftime('%H:%M:%S')
        print(f"[{current_time}] 🔄 轉換特徵為 numpy 陣列...")
        features_array = np.array(features_list, dtype=np.float32)

        current_time = time.strftime('%H:%M:%S')
        print(f"[{current_time}] 📊 特徵維度: {features_array.shape}")
        print(f"[{current_time}] 📊 特徵向量數: {features_array.shape[0]} 個")
        print(f"[{current_time}] 📊 特徵維度大小: {features_array.shape[1]} 維")

        # 建立 FAISS 索引
        current_time = time.strftime('%H:%M:%S')
        print(f"[{current_time}] 🏗️  建立 FAISS 索引 (IndexFlatIP)...")
        dimension = features_array.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # 使用內積相似度
        self.index.add(features_array)
        self.labels = labels_list

        # 儲存索引
        current_time = time.strftime('%H:%M:%S')
        print(f"[{current_time}] 💾 儲存 FAISS 索引...")
        self.save_index()

        total_elapsed = time.time() - start_time
        current_time = time.strftime('%H:%M:%S')
        print(f"[{current_time}] ✅ FAISS 索引建立完成！")
        print(f"[{current_time}] 📊 特徵向量總數: {self.index.ntotal} 個")
        print(f"[{current_time}] 📂 類別總數: {len(self.classes)} 個")
        print(f"[{current_time}] ⏱️  總耗時: {total_elapsed:.1f} 秒 ({total_elapsed/60:.1f} 分鐘)")
        print(f"[{current_time}] ⚡ 平均處理速度: {processed_count/total_elapsed:.1f} 張圖片/秒")
        return True

    def save_index(self):
        """儲存 FAISS 索引和標籤"""
        try:
            faiss.write_index(self.index, self.index_file)
            with open(self.labels_file, 'wb') as f:
                pickle.dump({
                    'labels': self.labels,
                    'classes': self.classes
                }, f)
            print(f"💾 索引已儲存至 {self.index_file} 和 {self.labels_file}")
        except Exception as e:
            print(f"❌ 儲存索引失敗: {e}")

    def load_index(self):
        """載入 FAISS 索引和標籤"""
        try:
            if not os.path.exists(self.index_file) or not os.path.exists(self.labels_file):
                print("⚠️  索引檔案不存在，需要先建立索引")
                return False

            self.index = faiss.read_index(self.index_file)
            with open(self.labels_file, 'rb') as f:
                data = pickle.load(f)
                self.labels = data['labels']
                self.classes = data['classes']

            # 載入特徵提取器
            if self.feature_extractor is None:
                self.load_feature_extractor()

            self.loaded = True
            print(f"✅ FAISS 索引載入成功，包含 {self.index.ntotal} 個特徵向量")
            print(f"📋 類別: {', '.join(self.classes)}")
            return True

        except Exception as e:
            print(f"❌ 載入索引失敗: {e}")
            return False

    def predict(self, image_path, k=5):
        """使用 FAISS 進行圖片識別"""
        if not self.loaded:
            print("❌ FAISS 索引未載入")
            return None

        start_time = time.time()

        # 提取查詢圖片的特徵
        query_features = self.extract_features(image_path)
        if query_features is None:
            return None

        # 搜索最相似的特徵
        query_features = query_features.reshape(1, -1).astype(np.float32)
        similarities, indices = self.index.search(query_features, k)

        inference_time = (time.time() - start_time) * 1000

        # 整理結果
        predictions = []
        for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
            if idx < len(self.labels):
                label = self.labels[idx]
                predictions.append({
                    'class_id': label['class_id'],
                    'class_name': label['class_name'],
                    'confidence': float(similarity),
                    'rank': i + 1,
                    'reference_image': label['image_path']
                })

        # 按類別統計投票
        class_votes = {}
        for pred in predictions:
            class_name = pred['class_name']
            if class_name not in class_votes:
                class_votes[class_name] = {'count': 0, 'total_confidence': 0}
            class_votes[class_name]['count'] += 1
            class_votes[class_name]['total_confidence'] += pred['confidence']

        # 計算最終結果
        final_predictions = []
        for class_name, vote_data in class_votes.items():
            avg_confidence = vote_data['total_confidence'] / vote_data['count']
            final_predictions.append({
                'class_id': self.classes.index(class_name),
                'class_name': class_name,
                'confidence': avg_confidence,
                'vote_count': vote_data['count']
            })

        # 按置信度排序
        final_predictions.sort(key=lambda x: x['confidence'], reverse=True)

        return {
            'predictions': final_predictions,
            'detailed_results': predictions,
            'inference_time': inference_time,
            'method': 'FAISS',
            'success': True
        }

# 全域 FAISS 引擎實例
faiss_engine = FAISSRecognitionEngine()

def initialize_faiss():
    """初始化 FAISS 引擎"""
    print("🚀 初始化 FAISS 識別引擎")

    # 嘗試載入現有索引
    if not faiss_engine.load_index():
        print("📚 索引不存在，開始建立新索引...")
        if faiss_engine.build_index():
            print("✅ FAISS 初始化成功")
            return True
        else:
            print("❌ FAISS 初始化失敗")
            return False
    else:
        print("✅ FAISS 初始化成功")
        return True

def predict_with_faiss(image_path):
    """使用 FAISS 進行預測"""
    if not faiss_engine.loaded:
        print("⚠️  FAISS 未初始化，嘗試初始化...")
        if not initialize_faiss():
            return None

    return faiss_engine.predict(image_path)

if __name__ == "__main__":
    # 測試 FAISS 引擎
    print("🧪 測試 FAISS 識別引擎")

    if initialize_faiss():
        # 測試預測
        test_images = []
        for root, dirs, files in os.walk("dataset"):
            for file in files[:1]:  # 每個目錄測試一張圖片
                if file.lower().endswith(('.png', '.jpg')):
                    test_images.append(os.path.join(root, file))

        for img_path in test_images[:3]:  # 測試前3張
            print(f"\n🔍 測試圖片: {img_path}")
            result = predict_with_faiss(img_path)
            if result:
                print(f"⏱️  推論時間: {result['inference_time']:.1f}ms")
                for pred in result['predictions'][:3]:
                    print(f"  📊 {pred['class_name']}: {pred['confidence']:.3f} (投票: {pred['vote_count']})")
    else:
        print("❌ FAISS 引擎測試失敗")