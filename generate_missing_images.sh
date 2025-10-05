#!/bin/bash
# 自動生成缺失圖片的腳本
# 建立時間: 2025-10-02

echo "╔════════════════════════════════════════════════╗"
echo "║   STL 缺失圖片自動生成工具                   ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 缺失的 STL 檔案列表
MISSING_STLS=(
    "H09-EC11X8"
    "N9000151"
    "R8113139-TW"
    "R8113597-10.5-"
    "R8113743"
    "R8113930-"
    "R8113978"
    "R8126257-A--ok"
    "R8128946-A--OK"
)

echo "📦 發現 ${#MISSING_STLS[@]} 個 STL 檔案缺少圖片資料集"
echo ""
echo "缺失的 STL:"
for stl in "${MISSING_STLS[@]}"; do
    echo "  • ${stl}.stl"
done
echo ""

# 確認執行
read -p "是否開始生成圖片？(y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "❌ 已取消"
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 步驟 1/3: 複製 STL 檔案到 STL/ 資料夾"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

copied=0
failed=0

for stl in "${MISSING_STLS[@]}"; do
    source_file="training_stl/${stl}.stl"
    dest_file="STL/${stl}.stl"

    if [ -f "$source_file" ]; then
        if [ -f "$dest_file" ]; then
            echo "  ⚠️  已存在: ${stl}.stl (跳過)"
        else
            cp "$source_file" "$dest_file"
            if [ $? -eq 0 ]; then
                echo "  ✅ 已複製: ${stl}.stl"
                ((copied++))
            else
                echo "  ❌ 複製失敗: ${stl}.stl"
                ((failed++))
            fi
        fi
    else
        echo "  ❌ 找不到: ${stl}.stl"
        ((failed++))
    fi
done

echo ""
echo "複製結果: $copied 個成功, $failed 個失敗"
echo ""

if [ $copied -eq 0 ] && [ $failed -gt 0 ]; then
    echo "❌ 沒有檔案被複製，終止執行"
    exit 1
fi

# 檢查 Python 環境
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 步驟 2/3: 檢查 Python 環境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "❌ 找不到 python3，請先安裝 Python"
    exit 1
fi

echo "  ✅ Python: $(python3 --version)"

# 檢查必要的 Python 套件
echo "  🔍 檢查必要套件..."
python3 -c "import pyvista, trimesh, PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "  ⚠️  缺少必要套件，正在安裝..."
    pip install pyvista trimesh pillow
fi

echo ""

# 生成圖片
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 步驟 3/3: 生成多角度圖片"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏱️  預計時間: 15-30 分鐘"
echo "📊 將生成: $((${#MISSING_STLS[@]} * 360)) 張圖片"
echo ""

# 檢查生成腳本
if [ -f "generate_images_color.py" ]; then
    echo "🎨 使用彩色渲染版本..."
    script="generate_images_color.py"
elif [ -f "generate_images.py" ]; then
    echo "🎨 使用基本渲染版本..."
    script="generate_images.py"
else
    echo "❌ 找不到圖片生成腳本"
    exit 1
fi

echo ""
echo "🚀 開始生成..."
echo ""

# 執行圖片生成
python3 "$script"

if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ 圖片生成完成！"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # 驗證結果
    echo "📊 生成結果統計:"
    echo ""

    total_images=0
    for stl in "${MISSING_STLS[@]}"; do
        if [ -d "dataset/${stl}" ]; then
            count=$(ls dataset/${stl}/*.png 2>/dev/null | wc -l)
            if [ $count -eq 360 ]; then
                echo "  ✅ ${stl}: ${count} 張圖片"
            elif [ $count -gt 0 ]; then
                echo "  ⚠️  ${stl}: ${count} 張圖片 (不完整)"
            else
                echo "  ❌ ${stl}: 沒有圖片"
            fi
            total_images=$((total_images + count))
        else
            echo "  ❌ ${stl}: 資料夾不存在"
        fi
    done

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "總計生成: ${total_images} 張圖片"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # 下一步提示
    echo "🎯 下一步建議:"
    echo ""
    echo "  1. 檢查圖片品質:"
    echo "     ls dataset/H09-EC11X8/"
    echo ""
    echo "  2. 更新 YOLO 配置檔 (dataset.yaml):"
    echo "     - 類別數量: 5 → 14"
    echo "     - 添加新類別名稱"
    echo ""
    echo "  3. 重新訓練模型:"
    echo "     python3 train_yolo_enhanced.py"
    echo ""
    echo "  4. 或透過 Web 介面訓練:"
    echo "     http://localhost:8082/"
    echo ""

else
    echo ""
    echo "❌ 圖片生成失敗"
    echo ""
    echo "請檢查錯誤訊息並重試"
    exit 1
fi

echo "✨ 完成！"
