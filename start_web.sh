#!/bin/bash

echo "🚀 STL 物件識別系統 - 網頁介面啟動器"
echo "=" * 50

# 檢查模型檔案
if [ ! -f "runs/detect/cropped_simple/weights/best.pt" ]; then
    echo "❌ 找不到訓練好的模型檔案"
    echo "💡 請先執行訓練：python simple_cropped_training.py"
    exit 1
fi

# 檢查必要目錄
mkdir -p web_uploads
mkdir -p static/results
mkdir -p templates

# 啟動網頁伺服器
echo "🌐 啟動網頁伺服器..."
echo "📍 本地訪問: http://localhost:8082"
echo "📍 網路訪問: http://$(hostname -I | cut -d' ' -f1):8082"
echo ""
echo "🔧 功能說明:"
echo "  • 檔案上傳：上傳 STL 相關圖片進行識別"
echo "  • 樣本測試：測試訓練數據集中的樣本"
echo "  • 效能測試：測試模型推論速度"
echo "  • 批次測試：計算整體準確率"
echo ""
echo "⚠️  按 Ctrl+C 停止伺服器"
echo ""

python web_interface.py