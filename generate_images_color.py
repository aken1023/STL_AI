import os
import sys
import trimesh
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageChops
import math
import random

# 強制實時輸出
sys.stdout.flush()
sys.stderr.flush()

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
    # 假設背景是白色或淺色
    bg_color = gray.getpixel((0, 0))  # 取左上角作為背景顏色

    # 創建二值化圖像（檢測與背景不同的區域）
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
        # 縮放到 400x400 以減少檔案大小，但保持品質
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

def render_stl_with_colors(file_path, output_folder, total_images=60):
    """使用 PyVista 進行彩色 STL 渲染，確保真正的多角度視角"""
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
        images_per_elevation = 6  # 垂直方向分6層
        images_per_azimuth = total_images // images_per_elevation  # 每層水平角度數
        
        # 預定義多種顏色方案
        color_schemes = [
            {'base': 'lightblue', 'ambient': 0.3, 'diffuse': 0.8, 'specular': 0.2},
            {'base': 'lightcoral', 'ambient': 0.2, 'diffuse': 0.9, 'specular': 0.3},
            {'base': 'lightgreen', 'ambient': 0.4, 'diffuse': 0.7, 'specular': 0.1},
            {'base': 'gold', 'ambient': 0.3, 'diffuse': 0.8, 'specular': 0.4},
            {'base': 'silver', 'ambient': 0.2, 'diffuse': 0.6, 'specular': 0.5},
            {'base': 'orange', 'ambient': 0.3, 'diffuse': 0.8, 'specular': 0.2},
        ]
        
        image_count = 0
        
        for elev_idx in range(images_per_elevation):
            # 垂直角度：從-75度到75度
            elevation = -75 + (elev_idx * 150 / (images_per_elevation - 1))
            
            # 每個垂直層使用不同的顏色方案
            color_scheme = color_schemes[elev_idx % len(color_schemes)]
            
            for az_idx in range(images_per_azimuth):
                if image_count >= total_images:
                    break
                    
                # 水平角度：完整360度旋轉
                azimuth = (az_idx * 360.0 / images_per_azimuth)
                
                # 設定 off-screen 渲染
                plotter = pv.Plotter(off_screen=True, window_size=(512, 512))
                
                # 設定光照和材質
                plotter.add_mesh(
                    mesh, 
                    color=color_scheme['base'],
                    show_edges=False,
                    lighting=True,
                    ambient=color_scheme['ambient'],
                    diffuse=color_scheme['diffuse'],
                    specular=color_scheme['specular'],
                    metallic=0.1,
                    roughness=0.3
                )
                
                # 設定多重光源
                plotter.add_light(pv.Light(position=(100, 100, 100), intensity=0.8, color='white'))
                plotter.add_light(pv.Light(position=(-100, -100, 50), intensity=0.4, color='lightblue'))
                plotter.add_light(pv.Light(position=(0, 0, -100), intensity=0.3, color='#FFF3E0'))
                
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
                
                # 設定背景漸層
                if image_count % 60 < 20:
                    plotter.set_background('white', top='lightgray')
                elif image_count % 60 < 40:
                    plotter.set_background('lightblue', top='white')
                else:
                    plotter.set_background('lightgray', top='white')
                
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

                # 即時顯示每張圖片的進度（每10張顯示一次）
                if image_count % 10 == 0 or image_count == total_images:
                    progress_pct = (image_count / total_images * 100)
                    import time
                    current_time = time.strftime('%H:%M:%S')
                    print(f"[{current_time}] ⏳ 進度: {image_count}/{total_images} ({progress_pct:.1f}%) | 角度: Az={azimuth:.1f}° El={elevation:.1f}° | 顏色: {color_scheme['base']}")
                    sys.stdout.flush()

        print(f"✅ 完成: {image_count} 張彩色圖片已儲存至 {output_folder}")
        sys.stdout.flush()
        
    except ImportError:
        print("PyVista not available, using matplotlib colorful fallback")
        render_stl_matplotlib_color_fallback(file_path, output_folder, total_images)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def render_stl_matplotlib_color_fallback(file_path, output_folder, total_images=60):
    """使用 matplotlib 的彩色後備渲染方案"""
    try:
        mesh = trimesh.load(file_path)
        
        os.makedirs(output_folder, exist_ok=True)
        
        # 清理舊圖片
        for old_file in os.listdir(output_folder):
            if old_file.endswith('.png'):
                os.remove(os.path.join(output_folder, old_file))
        
        # 正規化網格到標準大小
        mesh.vertices = mesh.vertices - mesh.centroid
        scale = 50.0 / mesh.scale
        mesh.vertices *= scale
        
        images_per_elevation = 6
        images_per_azimuth = total_images // images_per_elevation
        
        # 彩色方案
        colors = ['lightblue', 'lightcoral', 'lightgreen', 'gold', 'orange', 'silver']
        cmaps = ['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'turbo']
        
        image_count = 0
        
        for elev_idx in range(images_per_elevation):
            elevation = -60 + (elev_idx * 120 / (images_per_elevation - 1))
            color = colors[elev_idx % len(colors)]
            cmap = cmaps[elev_idx % len(cmaps)]
            
            for az_idx in range(images_per_azimuth):
                if image_count >= total_images:
                    break
                    
                azimuth = (az_idx * 360.0 / images_per_azimuth)
                
                # 創建旋轉矩陣
                y_rot = trimesh.transformations.rotation_matrix(
                    np.radians(azimuth), [0, 1, 0]
                )
                x_rot = trimesh.transformations.rotation_matrix(
                    np.radians(elevation), [1, 0, 0]
                )
                
                # 組合旋轉
                combined_rot = trimesh.transformations.concatenate_matrices(x_rot, y_rot)
                
                # 應用旋轉
                rotated_mesh = mesh.copy()
                rotated_mesh.apply_transform(combined_rot)
                
                # 使用 matplotlib 繪製
                fig = plt.figure(figsize=(5.12, 5.12), dpi=100)
                ax = fig.add_subplot(111, projection='3d')
                
                # 計算面的顏色 (基於法向量)
                face_normals = rotated_mesh.face_normals
                z_normals = face_normals[:, 2]  # Z方向的法向量
                
                # 繪製三角面 - 使用彩色映射
                surf = ax.plot_trisurf(rotated_mesh.vertices[:, 0], 
                                     rotated_mesh.vertices[:, 1], 
                                     rotated_mesh.vertices[:, 2], 
                                     triangles=rotated_mesh.faces,
                                     cmap=cmap, 
                                     alpha=0.9, 
                                     shade=True,
                                     facecolors=plt.cm.get_cmap(cmap)(z_normals))
                
                # 設定視角和光照
                ax.view_init(elev=20, azim=azimuth)
                ax.set_xlim3d(-30, 30)
                ax.set_ylim3d(-30, 30)
                ax.set_zlim3d(-30, 30)
                ax.axis('off')
                
                # 設定背景顏色
                bg_colors = ['white', 'lightgray', 'aliceblue', 'lavender', 'honeydew', 'seashell']
                ax.set_facecolor(bg_colors[elev_idx % len(bg_colors)])
                
                image_count += 1
                out_path = os.path.join(output_folder, f"img_{image_count:03d}.png")

                # 先保存到暫存路徑
                temp_path = out_path + '.tmp'
                plt.savefig(temp_path, bbox_inches='tight', pad_inches=0,
                           dpi=100, facecolor=bg_colors[elev_idx % len(bg_colors)])
                plt.close(fig)

                # 讀取並裁切圖片
                temp_img = Image.open(temp_path)
                cropped_img = auto_crop_image(temp_img)
                cropped_img.save(out_path, optimize=True, quality=85)

                # 刪除暫存檔
                os.remove(temp_path)

                # 即時顯示每張圖片的進度
                print(f"⏳ Rendering [{image_count}/{total_images}] Az: {azimuth:.1f}°, El: {elevation:.1f}°, ColorMap: {cmap}")
                    
        print(f"Completed: {image_count} colored images saved to {output_folder}")
        
    except Exception as e:
        print(f"Error in matplotlib color fallback {file_path}: {e}")

if __name__ == "__main__":
    import time

    # 預設生成 360 張圖片（精準訓練模式）
    TOTAL_IMAGES = 360

    start_time = time.time()
    current_time = time.strftime('%H:%M:%S')

    print(f"[{current_time}] 🚀 開始精準 STL 圖片轉換...")
    sys.stdout.flush()
    print(f"[{current_time}] 模式: 精準訓練 (每個模型 {TOTAL_IMAGES} 張圖片)")
    print(f"[{current_time}] 特色: 多種顏色、光照效果、漸層背景、干擾")
    print(f"[{current_time}] 策略: 6 層垂直角度 × {TOTAL_IMAGES // 6} 個水平角度 = {TOTAL_IMAGES} 個獨特視角")
    print(f"[{current_time}] 顏色: 每個垂直層使用不同色彩方案")
    print(f"[{current_time}] 垂直範圍: -75° 到 +75°")
    print(f"[{current_time}] 水平範圍: 0° 到 360° (完整覆蓋)")
    sys.stdout.flush()

    stl_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".stl")]
    current_time = time.strftime('%H:%M:%S')
    print(f"\n[{current_time}] 📦 找到 {len(stl_files)} 個 STL 檔案")
    print(f"[{current_time}] 📊 預計總共生成: {len(stl_files) * TOTAL_IMAGES} 張圖片")
    sys.stdout.flush()

    for idx, file in enumerate(stl_files, 1):
        model_start_time = time.time()
        current_time = time.strftime('%H:%M:%S')

        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"[{current_time}] 🔄 處理模型 [{idx}/{len(stl_files)}]: {file}")
        print(f"[{current_time}] 📊 準備生成 {TOTAL_IMAGES} 張圖片...")
        sys.stdout.flush()

        model_name = os.path.splitext(file)[0]
        render_stl_with_colors(os.path.join(INPUT_DIR, file), os.path.join(OUTPUT_DIR, model_name), total_images=TOTAL_IMAGES)

        model_elapsed = time.time() - model_start_time
        overall_progress = (idx / len(stl_files) * 100)
        current_time = time.strftime('%H:%M:%S')

        print(f"[{current_time}] ✅ {file} 完成 - {TOTAL_IMAGES} 張圖片已儲存")
        print(f"[{current_time}] ⏱️  本模型耗時: {model_elapsed:.1f} 秒 ({model_elapsed/60:.1f} 分鐘)")
        print(f"[{current_time}] 📈 總體進度: {idx}/{len(stl_files)} 模型 ({overall_progress:.1f}%)")

        # 預估剩餘時間
        if idx < len(stl_files):
            avg_time_per_model = (time.time() - start_time) / idx
            remaining_models = len(stl_files) - idx
            estimated_remaining = avg_time_per_model * remaining_models
            print(f"[{current_time}] 🕐 預估剩餘時間: {estimated_remaining/60:.1f} 分鐘")

        sys.stdout.flush()

    total_elapsed = time.time() - start_time
    current_time = time.strftime('%H:%M:%S')

    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"[{current_time}] 🎉 精準轉換完成！")
    print(f"[{current_time}] 📊 總共生成: {len(stl_files) * TOTAL_IMAGES} 張圖片")
    print(f"[{current_time}] ⏱️  總耗時: {total_elapsed:.1f} 秒 ({total_elapsed/60:.1f} 分鐘)")
    print(f"[{current_time}] ⚡ 平均每個模型: {total_elapsed/len(stl_files):.1f} 秒")
    print(f"[{current_time}] ✨ 每個模型現在有 {TOTAL_IMAGES} 張圖片用於精準訓練！")
    sys.stdout.flush()