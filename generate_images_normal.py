import os
import trimesh
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import math

INPUT_DIR = "./STL"
OUTPUT_DIR = "./dataset"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def auto_crop_image(img, margin=10):
    """
    自動裁切圖片的空白邊緣，保留物件並加上少量邊距

    Args:
        img: PIL Image 物件
        margin: 保留的邊距像素（預設10px）

    Returns:
        裁切後的 PIL Image
    """
    # 轉換為 RGB（如果是 RGBA）
    if img.mode == 'RGBA':
        # 創建白色背景
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])  # 使用 alpha 通道作為遮罩
        img = bg

    # 轉換為灰度以便檢測邊緣
    gray = img.convert('L')

    # 使用反轉來找到非白色區域
    threshold = 240  # 接近白色的閾值
    binary = gray.point(lambda x: 0 if x > threshold else 255)

    # 獲取包含內容的邊界框
    bbox = binary.getbbox()

    if bbox:
        # 添加邊距
        left = max(0, bbox[0] - margin)
        top = max(0, bbox[1] - margin)
        right = min(img.width, bbox[2] + margin)
        bottom = min(img.height, bbox[3] + margin)

        # 裁切圖片
        cropped = img.crop((left, top, right, bottom))

        # 調整大小回固定尺寸（保持比例）
        max_size = 400
        cropped.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # 創建正方形畫布（白色背景）
        final_img = Image.new('RGB', (max_size, max_size), (255, 255, 255))

        # 將裁切的圖片置中貼上
        offset_x = (max_size - cropped.width) // 2
        offset_y = (max_size - cropped.height) // 2
        final_img.paste(cropped, (offset_x, offset_y))

        return final_img
    else:
        # 如果無法找到邊界，返回原圖縮小版
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        return img

def render_stl_normal(file_path, output_folder, total_images=60):
    """正常訓練模式：使用 PyVista 進行簡單渲染，60張圖片，無額外干擾"""
    try:
        import pyvista as pv

        # 載入 STL 檔案
        mesh = pv.read(file_path)

        os.makedirs(output_folder, exist_ok=True)

        # 清理舊圖片
        for old_file in os.listdir(output_folder):
            if old_file.endswith('.png'):
                os.remove(os.path.join(output_folder, old_file))

        # 設定球面座標系統來產生均勻分佈的視角
        # 正常模式：6層垂直角度 × 10個水平角度 = 60張
        images_per_elevation = 6
        images_per_azimuth = total_images // images_per_elevation

        # 固定簡單的顏色方案（淺灰色）
        base_color = 'lightgray'

        image_count = 0

        for elev_idx in range(images_per_elevation):
            # 垂直角度：從-75度到75度
            elevation = -75 + (elev_idx * 150 / (images_per_elevation - 1))

            for az_idx in range(images_per_azimuth):
                if image_count >= total_images:
                    break

                # 水平角度：完整360度旋轉
                azimuth = (az_idx * 360.0 / images_per_azimuth)

                # 設定 off-screen 渲染
                plotter = pv.Plotter(off_screen=True, window_size=(512, 512))

                # 設定簡單光照和材質
                plotter.add_mesh(
                    mesh,
                    color=base_color,
                    show_edges=False,
                    lighting=True,
                    ambient=0.3,
                    diffuse=0.7,
                    specular=0.2
                )

                # 單一主光源（簡單設定）
                plotter.add_light(pv.Light(position=(100, 100, 100), intensity=0.8, color='white'))

                # 計算相機位置 (球面座標轉笛卡爾座標)
                distance = 100  # 相機距離
                elev_rad = math.radians(elevation)
                azim_rad = math.radians(azimuth)

                # 球面座標轉換
                x = distance * math.cos(elev_rad) * math.cos(azim_rad)
                y = distance * math.cos(elev_rad) * math.sin(azim_rad)
                z = distance * math.sin(elev_rad)

                # 設定相機位置和焦點
                plotter.camera_position = [(x, y, z), (0, 0, 0), (0, 0, 1)]
                plotter.camera.zoom(1.0)

                # 固定白色背景
                plotter.set_background('white')

                # 渲染圖像
                image = plotter.screenshot(transparent_background=False, return_img=True)

                # 儲存圖像（自動裁切空白區域）
                image_count += 1
                out_path = os.path.join(output_folder, f"img_{image_count:03d}.png")
                pil_image = Image.fromarray(image)

                # 自動裁切空白邊緣，減少檔案大小
                pil_image = auto_crop_image(pil_image)

                # 使用最佳化壓縮儲存
                pil_image.save(out_path, optimize=True, quality=85)

                plotter.close()

                # 即時顯示每張圖片的進度
                print(f"⏳ Rendering [{image_count}/{total_images}] Az: {azimuth:.1f}°, El: {elevation:.1f}°")

        print(f"Completed: {image_count} images saved to {output_folder}")

    except ImportError:
        print("PyVista not available, using matplotlib fallback")
        render_stl_matplotlib_fallback(file_path, output_folder, total_images)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def render_stl_matplotlib_fallback(file_path, output_folder, total_images=60):
    """使用 matplotlib 的後備渲染方案"""
    try:
        mesh = trimesh.load(file_path)

        os.makedirs(output_folder, exist_ok=True)

        # 清理舊圖片
        for old_file in os.listdir(output_folder):
            if old_file.endswith('.png'):
                os.remove(os.path.join(output_folder, old_file))

        # 正常模式：6層垂直角度 × 10個水平角度 = 60張
        images_per_elevation = 6
        images_per_azimuth = total_images // images_per_elevation

        image_count = 0

        for elev_idx in range(images_per_elevation):
            elevation = -75 + (elev_idx * 150 / (images_per_elevation - 1))

            for az_idx in range(images_per_azimuth):
                if image_count >= total_images:
                    break

                azimuth = (az_idx * 360.0 / images_per_azimuth)

                # 旋轉網格
                elev_rad = math.radians(elevation)
                azim_rad = math.radians(azimuth)

                rotation_matrix = trimesh.transformations.euler_matrix(elev_rad, 0, azim_rad)
                rotated_mesh = mesh.copy()
                rotated_mesh.apply_transform(rotation_matrix)

                fig = plt.figure(figsize=(5, 5), facecolor='white')
                ax = fig.add_subplot(111, projection='3d')

                # 繪製簡單網格
                ax.plot_trisurf(
                    rotated_mesh.vertices[:, 0],
                    rotated_mesh.vertices[:, 1],
                    rotated_mesh.vertices[:, 2],
                    triangles=rotated_mesh.faces,
                    color='lightgray',
                    shade=True,
                    alpha=1.0
                )

                ax.set_box_aspect([1, 1, 1])
                ax.axis('off')
                ax.set_facecolor('white')

                image_count += 1
                out_path = os.path.join(output_folder, f"img_{image_count:03d}.png")

                # 先保存到暫存路徑
                temp_path = out_path + '.tmp'
                plt.savefig(temp_path, bbox_inches='tight', pad_inches=0,
                           dpi=100, facecolor='white')
                plt.close(fig)

                # 讀取並裁切圖片
                temp_img = Image.open(temp_path)
                cropped_img = auto_crop_image(temp_img)
                cropped_img.save(out_path, optimize=True, quality=85)

                # 刪除暫存檔
                os.remove(temp_path)

                # 即時顯示每張圖片的進度
                print(f"⏳ Rendering [{image_count}/{total_images}] Az: {azimuth:.1f}°, El: {elevation:.1f}°")

        print(f"Completed: {image_count} images saved to {output_folder}")

    except Exception as e:
        print(f"Error in matplotlib fallback {file_path}: {e}")

if __name__ == "__main__":
    print("Starting NORMAL STL to image conversion...")
    print("Mode: Normal Training (60 images per model)")
    print("Features: Simple rendering, no interference")
    print("Strategy: 6 elevation layers × 10 azimuth angles = 60 viewpoints")
    print("Elevation range: -75° to +75°")
    print("Azimuth range: 0° to 360°")

    stl_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".stl")]
    print(f"Found {len(stl_files)} STL files")

    for idx, file in enumerate(stl_files, 1):
        print(f"\n🔄 Processing STL: {file} ({idx}/{len(stl_files)})")
        print(f"📊 Generating 60 images for {file}")
        model_name = os.path.splitext(file)[0]
        render_stl_normal(os.path.join(INPUT_DIR, file), os.path.join(OUTPUT_DIR, model_name))
        print(f"✅ Completed {file} - 60 images saved")

    print(f"\nNormal training conversion complete!")
    print(f"Total images generated: {len(stl_files) * 60}")
    print("Each model now has 60 images for normal training!")
