"""
CLIP Feature Extractor for STL Image Recognition
使用 CLIP 模型進行多模態特徵提取

支援功能：
- 圖像特徵提取（CLIP Vision Encoder）
- 文字特徵提取（CLIP Text Encoder）
- 批次處理
- GPU 加速
"""

import os
import torch
import clip
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Union, Tuple
import pickle
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CLIPFeatureExtractor:
    """CLIP 特徵提取器"""

    def __init__(self, model_name: str = "ViT-B/32", device: str = None):
        """
        初始化 CLIP 模型

        Args:
            model_name: CLIP 模型名稱
                - ViT-B/32: 基礎版本，速度快（512 維）
                - ViT-B/16: 中等版本，平衡性能（512 維）
                - ViT-L/14: 大型版本，準確度高（768 維）
            device: 運算裝置 ('cuda' 或 'cpu')
        """
        # 自動選擇裝置
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        logger.info(f"🚀 初始化 CLIP 模型: {model_name}")
        logger.info(f"💻 使用裝置: {self.device}")

        # 載入 CLIP 模型
        self.model, self.preprocess = clip.load(model_name, device=self.device)
        self.model.eval()  # 設定為評估模式

        # 取得特徵維度
        self.feature_dim = self.model.visual.output_dim
        logger.info(f"✅ 模型載入成功！特徵維度: {self.feature_dim}")

    def extract_image_features(self, image_path: Union[str, Path]) -> np.ndarray:
        """
        從單張圖片提取 CLIP 特徵

        Args:
            image_path: 圖片路徑

        Returns:
            特徵向量 (numpy array)
        """
        try:
            # 載入並預處理圖片
            image = Image.open(image_path).convert('RGB')
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)

            # 提取特徵
            with torch.no_grad():
                features = self.model.encode_image(image_input)
                # L2 正規化
                features = features / features.norm(dim=-1, keepdim=True)

            return features.cpu().numpy().flatten()

        except Exception as e:
            logger.error(f"❌ 提取圖片特徵失敗 {image_path}: {e}")
            return None

    def extract_text_features(self, text: str) -> np.ndarray:
        """
        從文字描述提取 CLIP 特徵

        Args:
            text: 文字描述

        Returns:
            特徵向量 (numpy array)
        """
        try:
            # 將文字轉換為 token
            text_input = clip.tokenize([text]).to(self.device)

            # 提取特徵
            with torch.no_grad():
                features = self.model.encode_text(text_input)
                # L2 正規化
                features = features / features.norm(dim=-1, keepdim=True)

            return features.cpu().numpy().flatten()

        except Exception as e:
            logger.error(f"❌ 提取文字特徵失敗: {e}")
            return None

    def extract_batch_image_features(self, image_paths: List[Union[str, Path]],
                                     batch_size: int = 32) -> Tuple[np.ndarray, List[str]]:
        """
        批次提取圖片特徵

        Args:
            image_paths: 圖片路徑列表
            batch_size: 批次大小

        Returns:
            (特徵矩陣, 成功處理的圖片路徑列表)
        """
        features_list = []
        valid_paths = []

        total = len(image_paths)
        logger.info(f"📊 開始批次處理 {total} 張圖片...")

        for i in range(0, total, batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_images = []
            batch_valid_paths = []

            # 載入批次圖片
            for path in batch_paths:
                try:
                    image = Image.open(path).convert('RGB')
                    batch_images.append(self.preprocess(image))
                    batch_valid_paths.append(str(path))
                except Exception as e:
                    logger.warning(f"⚠️ 跳過損壞的圖片 {path}: {e}")
                    continue

            if len(batch_images) == 0:
                continue

            # 批次處理
            try:
                batch_input = torch.stack(batch_images).to(self.device)

                with torch.no_grad():
                    batch_features = self.model.encode_image(batch_input)
                    # L2 正規化
                    batch_features = batch_features / batch_features.norm(dim=-1, keepdim=True)

                features_list.append(batch_features.cpu().numpy())
                valid_paths.extend(batch_valid_paths)

                # 顯示進度
                processed = min(i + batch_size, total)
                logger.info(f"⏳ 進度: {processed}/{total} ({processed/total*100:.1f}%)")

            except Exception as e:
                logger.error(f"❌ 批次處理失敗: {e}")
                continue

        if len(features_list) == 0:
            logger.error("❌ 沒有成功提取任何特徵")
            return None, []

        # 合併所有批次
        all_features = np.vstack(features_list)
        logger.info(f"✅ 成功提取 {len(valid_paths)} 張圖片的特徵")

        return all_features, valid_paths

    def build_dataset_index(self, dataset_dir: Union[str, Path],
                           output_dir: Union[str, Path] = ".",
                           batch_size: int = 32) -> bool:
        """
        為整個資料集建立 CLIP 特徵索引

        Args:
            dataset_dir: 資料集目錄 (如 'dataset/')
            output_dir: 輸出目錄
            batch_size: 批次大小

        Returns:
            是否成功
        """
        dataset_dir = Path(dataset_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        logger.info(f"🔨 開始建立資料集索引: {dataset_dir}")

        # 收集所有圖片
        image_paths = []
        labels = []

        for class_dir in sorted(dataset_dir.iterdir()):
            if not class_dir.is_dir():
                continue

            class_name = class_dir.name
            class_images = list(class_dir.glob('*.png')) + list(class_dir.glob('*.jpg'))

            logger.info(f"📁 類別: {class_name} - {len(class_images)} 張圖片")

            for img_path in class_images:
                image_paths.append(img_path)
                labels.append(class_name)

        if len(image_paths) == 0:
            logger.error(f"❌ 在 {dataset_dir} 中找不到圖片")
            return False

        logger.info(f"📊 總計: {len(image_paths)} 張圖片, {len(set(labels))} 個類別")

        # 批次提取特徵
        features, valid_paths = self.extract_batch_image_features(image_paths, batch_size)

        if features is None:
            return False

        # 更新標籤（只保留成功處理的）
        valid_labels = []
        path_to_label = {str(path): label for path, label in zip(image_paths, labels)}
        for path in valid_paths:
            valid_labels.append(path_to_label[path])

        # 儲存特徵和標籤
        feature_file = output_dir / "clip_features.npy"
        label_file = output_dir / "clip_labels.pkl"
        path_file = output_dir / "clip_paths.pkl"

        np.save(feature_file, features)

        with open(label_file, 'wb') as f:
            pickle.dump(valid_labels, f)

        with open(path_file, 'wb') as f:
            pickle.dump(valid_paths, f)

        logger.info(f"💾 特徵已儲存至: {feature_file}")
        logger.info(f"💾 標籤已儲存至: {label_file}")
        logger.info(f"💾 路徑已儲存至: {path_file}")
        logger.info(f"✅ 索引建立完成！")

        return True


def main():
    """主程式 - 建立 CLIP 特徵索引"""

    print("=" * 60)
    print("🚀 CLIP Feature Extractor for STL Recognition")
    print("=" * 60)

    # 初始化 CLIP 模型
    extractor = CLIPFeatureExtractor(model_name="ViT-B/32")

    # 建立資料集索引
    dataset_dir = Path("dataset")

    if not dataset_dir.exists():
        logger.error(f"❌ 資料集目錄不存在: {dataset_dir}")
        return

    success = extractor.build_dataset_index(
        dataset_dir=dataset_dir,
        output_dir=".",
        batch_size=32
    )

    if success:
        print("\n" + "=" * 60)
        print("✅ CLIP 特徵索引建立成功！")
        print("=" * 60)
        print("\n生成的檔案：")
        print("  📄 clip_features.npy - CLIP 特徵向量")
        print("  📄 clip_labels.pkl - 類別標籤")
        print("  📄 clip_paths.pkl - 圖片路徑")
        print("\n下一步：執行 clip_faiss_search.py 建立 FAISS 索引")
    else:
        print("\n" + "=" * 60)
        print("❌ 索引建立失敗")
        print("=" * 60)


if __name__ == "__main__":
    main()
