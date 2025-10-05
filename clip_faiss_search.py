"""
CLIP + FAISS Image Similarity Search Engine
CLIP 特徵 + FAISS 索引的圖像相似性搜尋引擎

支援三種搜尋模式：
1. 圖像搜尋 (Image-to-Image)
2. 文字搜尋 (Text-to-Image)
3. 混合搜尋 (Hybrid Search)
"""

import numpy as np
import faiss
import pickle
from pathlib import Path
from typing import List, Tuple, Dict, Union
import logging
from PIL import Image

from clip_feature_extractor import CLIPFeatureExtractor

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CLIPFAISSSearch:
    """CLIP + FAISS 搜尋引擎"""

    def __init__(self, feature_file: str = "clip_features.npy",
                 label_file: str = "clip_labels.pkl",
                 path_file: str = "clip_paths.pkl",
                 model_name: str = "ViT-B/32"):
        """
        初始化搜尋引擎

        Args:
            feature_file: CLIP 特徵檔案
            label_file: 標籤檔案
            path_file: 路徑檔案
            model_name: CLIP 模型名稱
        """
        self.feature_file = Path(feature_file)
        self.label_file = Path(label_file)
        self.path_file = Path(path_file)

        # 初始化 CLIP 模型
        logger.info("🚀 初始化 CLIP 模型...")
        self.extractor = CLIPFeatureExtractor(model_name=model_name)

        # 載入特徵和標籤
        self.features = None
        self.labels = None
        self.paths = None
        self.index = None

        self._load_features()
        self._build_faiss_index()

    def _load_features(self):
        """載入 CLIP 特徵和標籤"""
        if not self.feature_file.exists():
            raise FileNotFoundError(f"找不到特徵檔案: {self.feature_file}")

        logger.info(f"📂 載入特徵: {self.feature_file}")
        self.features = np.load(self.feature_file)

        logger.info(f"📂 載入標籤: {self.label_file}")
        with open(self.label_file, 'rb') as f:
            self.labels = pickle.load(f)

        logger.info(f"📂 載入路徑: {self.path_file}")
        with open(self.path_file, 'rb') as f:
            self.paths = pickle.load(f)

        logger.info(f"✅ 載入完成: {len(self.features)} 個特徵向量")

    def _build_faiss_index(self):
        """建立 FAISS 索引"""
        logger.info("🔨 建立 FAISS 索引...")

        # 使用 Inner Product (IP) 索引，因為 CLIP 特徵已經過 L2 正規化
        # IP 索引在正規化向量上等同於餘弦相似度
        d = self.features.shape[1]  # 特徵維度
        self.index = faiss.IndexFlatIP(d)

        # 添加特徵向量
        self.index.add(self.features.astype('float32'))

        logger.info(f"✅ FAISS 索引建立完成！總數: {self.index.ntotal}")

    def search_by_image(self, image_path: Union[str, Path], k: int = 5) -> List[Dict]:
        """
        使用圖片進行搜尋

        Args:
            image_path: 查詢圖片路徑
            k: 返回前 K 個結果

        Returns:
            搜尋結果列表
        """
        logger.info(f"🔍 圖片搜尋: {image_path}")

        # 提取查詢圖片的 CLIP 特徵
        query_features = self.extractor.extract_image_features(image_path)

        if query_features is None:
            return []

        # FAISS 搜尋
        query_features = query_features.reshape(1, -1).astype('float32')
        distances, indices = self.index.search(query_features, k)

        # 整理結果
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            results.append({
                'rank': i + 1,
                'class_name': self.labels[idx],
                'image_path': self.paths[idx],
                'similarity': float(dist),  # 餘弦相似度 (0-1)
                'confidence': float(dist * 100)  # 百分比
            })

        return results

    def search_by_text(self, text: str, k: int = 5) -> List[Dict]:
        """
        使用文字描述進行搜尋

        Args:
            text: 查詢文字
            k: 返回前 K 個結果

        Returns:
            搜尋結果列表
        """
        logger.info(f"🔍 文字搜尋: {text}")

        # 提取文字的 CLIP 特徵
        query_features = self.extractor.extract_text_features(text)

        if query_features is None:
            return []

        # FAISS 搜尋
        query_features = query_features.reshape(1, -1).astype('float32')
        distances, indices = self.index.search(query_features, k)

        # 整理結果
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            results.append({
                'rank': i + 1,
                'class_name': self.labels[idx],
                'image_path': self.paths[idx],
                'similarity': float(dist),
                'confidence': float(dist * 100)
            })

        return results

    def search_hybrid(self, image_path: Union[str, Path] = None,
                     text: str = None, k: int = 5,
                     image_weight: float = 0.7) -> List[Dict]:
        """
        混合搜尋：結合圖片和文字

        Args:
            image_path: 查詢圖片路徑（可選）
            text: 查詢文字（可選）
            k: 返回前 K 個結果
            image_weight: 圖片權重 (0-1)，文字權重 = 1 - image_weight

        Returns:
            搜尋結果列表
        """
        if image_path is None and text is None:
            logger.error("❌ 必須提供圖片或文字至少一種")
            return []

        logger.info(f"🔍 混合搜尋 - 圖片: {image_path}, 文字: {text}")

        query_features = None

        # 提取圖片特徵
        if image_path is not None:
            image_features = self.extractor.extract_image_features(image_path)
            if image_features is not None:
                query_features = image_features * image_weight

        # 提取文字特徵
        if text is not None:
            text_features = self.extractor.extract_text_features(text)
            if text_features is not None:
                if query_features is None:
                    query_features = text_features * (1 - image_weight)
                else:
                    query_features += text_features * (1 - image_weight)

        if query_features is None:
            return []

        # L2 正規化混合特徵
        query_features = query_features / np.linalg.norm(query_features)

        # FAISS 搜尋
        query_features = query_features.reshape(1, -1).astype('float32')
        distances, indices = self.index.search(query_features, k)

        # 整理結果
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            results.append({
                'rank': i + 1,
                'class_name': self.labels[idx],
                'image_path': self.paths[idx],
                'similarity': float(dist),
                'confidence': float(dist * 100)
            })

        return results

    def get_statistics(self) -> Dict:
        """取得索引統計資訊"""
        unique_classes = set(self.labels)

        class_counts = {}
        for label in self.labels:
            class_counts[label] = class_counts.get(label, 0) + 1

        return {
            'total_images': len(self.features),
            'total_classes': len(unique_classes),
            'feature_dim': self.features.shape[1],
            'class_distribution': class_counts,
            'index_type': type(self.index).__name__
        }

    def save_index(self, output_path: str = "clip_faiss.index"):
        """儲存 FAISS 索引"""
        faiss.write_index(self.index, output_path)
        logger.info(f"💾 FAISS 索引已儲存至: {output_path}")

    @classmethod
    def load_index(cls, index_path: str = "clip_faiss.index", **kwargs):
        """載入已儲存的 FAISS 索引"""
        instance = cls(**kwargs)
        instance.index = faiss.read_index(index_path)
        logger.info(f"📂 FAISS 索引已載入: {index_path}")
        return instance


def demo_search():
    """示範搜尋功能"""
    print("=" * 60)
    print("🚀 CLIP + FAISS Image Similarity Search Demo")
    print("=" * 60)

    # 初始化搜尋引擎
    search_engine = CLIPFAISSSearch()

    # 顯示統計資訊
    stats = search_engine.get_statistics()
    print(f"\n📊 索引統計:")
    print(f"  總圖片數: {stats['total_images']}")
    print(f"  總類別數: {stats['total_classes']}")
    print(f"  特徵維度: {stats['feature_dim']}")
    print(f"  索引類型: {stats['index_type']}")

    # 儲存 FAISS 索引
    search_engine.save_index("clip_faiss.index")

    print("\n" + "=" * 60)
    print("✅ 搜尋引擎初始化完成！")
    print("=" * 60)

    # 示範搜尋
    print("\n🔍 示範功能:")
    print("  1. search_by_image(image_path, k=5)")
    print("  2. search_by_text(text, k=5)")
    print("  3. search_hybrid(image_path, text, k=5)")

    # 範例：圖片搜尋
    dataset_dir = Path("dataset")
    if dataset_dir.exists():
        # 隨機選擇一張圖片測試
        all_images = list(dataset_dir.glob("*/*.png"))
        if len(all_images) > 0:
            test_image = all_images[0]
            print(f"\n🧪 測試圖片搜尋: {test_image}")
            results = search_engine.search_by_image(test_image, k=3)

            print("\n📋 搜尋結果:")
            for result in results:
                print(f"  {result['rank']}. {result['class_name']} - "
                      f"相似度: {result['confidence']:.2f}%")

    # 範例：文字搜尋
    print(f"\n🧪 測試文字搜尋: 'a metallic ring'")
    results = search_engine.search_by_text("a metallic ring", k=3)

    print("\n📋 搜尋結果:")
    for result in results:
        print(f"  {result['rank']}. {result['class_name']} - "
              f"相似度: {result['confidence']:.2f}%")


if __name__ == "__main__":
    demo_search()
