#!/usr/bin/env python3
"""
測試單個 STL 檔案的圖片生成和自動裁切功能
"""
import os
import sys
from generate_images_color import render_stl_with_colors

# 測試第一個 STL 檔案
stl_dir = "./STL"
stl_files = [f for f in os.listdir(stl_dir) if f.endswith(".stl")]

if not stl_files:
    print("❌ 沒有找到 STL 檔案")
    sys.exit(1)

# 只取第一個檔案測試
test_file = stl_files[0]
print(f"🧪 測試檔案: {test_file}")

model_name = os.path.splitext(test_file)[0]
output_folder = os.path.join("dataset", model_name)

print(f"📂 輸出資料夾: {output_folder}")
print(f"📸 生成 10 張測試圖片（自動裁切 + 壓縮）")

# 只生成 10 張圖片用於測試
render_stl_with_colors(
    os.path.join(stl_dir, test_file),
    output_folder,
    total_images=10
)

print("\n✅ 測試完成！")
print(f"📁 請檢查 {output_folder} 資料夾")

# 顯示檔案大小統計
if os.path.exists(output_folder):
    images = [f for f in os.listdir(output_folder) if f.endswith('.png')]
    if images:
        total_size = sum(os.path.getsize(os.path.join(output_folder, img)) for img in images)
        avg_size = total_size / len(images)
        print(f"\n📊 統計:")
        print(f"   - 圖片數量: {len(images)}")
        print(f"   - 總大小: {total_size / 1024:.2f} KB")
        print(f"   - 平均大小: {avg_size / 1024:.2f} KB/張")
        print(f"   - 預估 360 張: {avg_size * 360 / 1024 / 1024:.2f} MB")
