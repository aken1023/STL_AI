#!/bin/bash
# 監控圖片生成進度

echo "=== STL 圖片生成進度監控 ==="
echo ""

# 檢查進程是否運行
if ps aux | grep -v grep | grep "python generate_images_color.py" > /dev/null; then
    echo "✅ 生成程序運行中"
else
    echo "❌ 生成程序未運行"
    exit 1
fi

echo ""
echo "📊 當前進度:"
echo "----------------------------------------"

# 最新日誌
echo "🔄 最新狀態:"
tail -5 generate_60_images.log | grep "Rendering\|Processing\|Completed" 2>/dev/null || tail -5 generate_optimized.log | grep "Rendering\|Processing\|Completed" 2>/dev/null

echo ""
echo "📁 已生成的模型:"
for dir in dataset/*/; do
    if [ -d "$dir" ]; then
        model_name=$(basename "$dir")
        image_count=$(ls -1 "$dir"/*.png 2>/dev/null | wc -l)
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)

        if [ $image_count -gt 0 ]; then
            if [ $image_count -eq 60 ]; then
                echo "  ✅ $model_name: $image_count 張 ($size)"
            else
                echo "  ⏳ $model_name: $image_count/60 張 ($size)"
            fi
        fi
    fi
done

echo ""
echo "💾 總計:"
total_images=$(find dataset/ -name "*.png" 2>/dev/null | wc -l)
total_size=$(du -sh dataset/ 2>/dev/null | cut -f1)
echo "  - 圖片總數: $total_images"
echo "  - 總大小: $total_size"

echo ""
echo "----------------------------------------"
echo "使用 'tail -f generate_optimized.log' 查看詳細日誌"
