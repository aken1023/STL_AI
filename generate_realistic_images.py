#!/usr/bin/env python3
"""
生成更真實的 STL 渲染圖片用於訓練
包含多種材質、顏色、光照條件和數據增強
"""
import os
import sys
import numpy as np
import pyvista as pv
import trimesh
from PIL import Image, ImageEnhance, ImageFilter
import random

def generate_realistic_images(stl_file, output_dir, num_images=100):
    """
    為單個 STL 檔案生成多樣化的真實感渲染圖

    參數：
    - stl_file: STL 檔案路徑
    - output_dir: 輸出目錄
    - num_images: 要生成的圖片數量
    """
    # 取得模型名稱
    model_name = os.path.splitext(os.path.basename(stl_file))[0]
    print(f"🎨 處理模型: {model_name}")

    # 建立輸出目錄
    os.makedirs(output_dir, exist_ok=True)

    # 載入 STL 模型
    try:
        mesh = pv.read(stl_file)
    except Exception as e:
        print(f"❌ 無法載入 STL 檔案: {e}")
        return

    # 材質配置（模擬金屬、塑料等）
    materials = [
        # 金色金屬
        {
            'name': 'gold',
            'color': [255, 215, 0],
            'ambient': 0.3,
            'diffuse': 0.7,
            'specular': 1.0,
            'specular_power': 100
        },
        # 銀色金屬
        {
            'name': 'silver',
            'color': [192, 192, 192],
            'ambient': 0.3,
            'diffuse': 0.6,
            'specular': 1.0,
            'specular_power': 120
        },
        # 銅色金屬
        {
            'name': 'copper',
            'color': [184, 115, 51],
            'ambient': 0.3,
            'diffuse': 0.7,
            'specular': 0.9,
            'specular_power': 90
        },
        # 白色塑料
        {
            'name': 'white_plastic',
            'color': [240, 240, 240],
            'ambient': 0.4,
            'diffuse': 0.8,
            'specular': 0.3,
            'specular_power': 30
        },
        # 灰色塑料
        {
            'name': 'gray_plastic',
            'color': [128, 128, 128],
            'ambient': 0.4,
            'diffuse': 0.7,
            'specular': 0.2,
            'specular_power': 25
        }
    ]

    # 背景配置
    backgrounds = [
        [255, 255, 255],  # 白色
        [240, 240, 240],  # 淺灰
        [200, 200, 200],  # 中灰
        [230, 230, 250],  # 淺藍
        [245, 245, 220],  # 米色
    ]

    image_count = 0
    images_per_config = num_images // (len(materials) * 4)  # 每種材質和角度配置

    for material_idx, material in enumerate(materials):
        print(f"  📦 材質 {material_idx+1}/{len(materials)}: {material['name']}")

        # 每種材質生成多個角度
        for angle_set in range(4):
            # 設置角度
            azimuth_base = angle_set * 90
            elevation_angles = [-30, 0, 15, 30, 45]

            for elev in elevation_angles:
                for i in range(images_per_config // len(elevation_angles)):
                    azimuth = azimuth_base + (i * 360 / images_per_config)

                    # 選擇隨機背景
                    bg_color = random.choice(backgrounds)

                    # 創建渲染器
                    plotter = pv.Plotter(off_screen=True, window_size=[512, 512])
                    plotter.set_background(color=[c/255.0 for c in bg_color])

                    # 添加模型
                    plotter.add_mesh(
                        mesh,
                        color=[c/255.0 for c in material['color']],
                        ambient=material['ambient'],
                        diffuse=material['diffuse'],
                        specular=material['specular'],
                        specular_power=material['specular_power'],
                        smooth_shading=True
                    )

                    # 設置多個光源（模擬真實環境光照）
                    # 主光源
                    light1 = pv.Light(position=(2, 2, 3), light_type='cameralight')
                    light1.intensity = 0.8
                    plotter.add_light(light1)

                    # 補光
                    light2 = pv.Light(position=(-2, 1, 2), light_type='cameralight')
                    light2.intensity = 0.4
                    plotter.add_light(light2)

                    # 背光
                    light3 = pv.Light(position=(0, -2, 1), light_type='cameralight')
                    light3.intensity = 0.3
                    plotter.add_light(light3)

                    # 設置相機角度
                    plotter.camera_position = 'iso'
                    plotter.camera.azimuth = azimuth
                    plotter.camera.elevation = elev
                    plotter.reset_camera()

                    # 渲染並保存
                    img_filename = f"img_{image_count:04d}.png"
                    img_path = os.path.join(output_dir, img_filename)
                    plotter.screenshot(img_path)
                    plotter.close()

                    # 數據增強
                    apply_data_augmentation(img_path)

                    image_count += 1

                    if image_count % 20 == 0:
                        progress = (image_count / num_images) * 100
                        print(f"    ⏳ 進度: {image_count}/{num_images} ({progress:.1f}%)")

    print(f"  ✅ 完成！生成 {image_count} 張圖片")

def apply_data_augmentation(image_path):
    """
    對圖片應用數據增強
    """
    img = Image.open(image_path)

    # 隨機調整亮度
    if random.random() > 0.5:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(random.uniform(0.8, 1.2))

    # 隨機調整對比度
    if random.random() > 0.5:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(random.uniform(0.9, 1.1))

    # 隨機調整銳度
    if random.random() > 0.3:
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(random.uniform(0.8, 1.2))

    # 輕微模糊（模擬相機對焦）
    if random.random() > 0.7:
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.8)))

    # 添加輕微噪點
    if random.random() > 0.6:
        img_array = np.array(img)
        noise = np.random.normal(0, 3, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(img_array)

    # 保存增強後的圖片
    img.save(image_path)

def main():
    """主函數"""
    stl_dir = "STL"
    dataset_dir = "dataset_realistic"

    if not os.path.exists(stl_dir):
        print(f"❌ STL 目錄不存在: {stl_dir}")
        return

    # 獲取所有 STL 檔案
    stl_files = [f for f in os.listdir(stl_dir) if f.lower().endswith('.stl')]

    if not stl_files:
        print(f"❌ 在 {stl_dir} 中沒有找到 STL 檔案")
        return

    print(f"🚀 開始生成真實感訓練圖片")
    print(f"📂 STL 檔案數量: {len(stl_files)}")
    print(f"📊 每個模型生成: 100 張圖片")
    print(f"🎨 材質種類: 5 種（金、銀、銅、白色、灰色）")
    print(f"💡 光照: 多光源設置")
    print(f"🔄 數據增強: 亮度、對比度、銳度、模糊、噪點")
    print("=" * 60)

    for idx, stl_file in enumerate(sorted(stl_files), 1):
        print(f"\n[{idx}/{len(stl_files)}] 處理: {stl_file}")

        stl_path = os.path.join(stl_dir, stl_file)
        model_name = os.path.splitext(stl_file)[0]
        output_dir = os.path.join(dataset_dir, model_name)

        generate_realistic_images(stl_path, output_dir, num_images=100)

    print("\n" + "=" * 60)
    print("✅ 所有圖片生成完成！")
    print(f"📁 輸出目錄: {dataset_dir}")
    print(f"📊 總共生成: {len(stl_files) * 100} 張圖片")
    print("\n下一步：使用這些圖片訓練 FAISS 模型")
    print("指令：在 /training 頁面點擊「開始訓練」")

if __name__ == "__main__":
    main()
