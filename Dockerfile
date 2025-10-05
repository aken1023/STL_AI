# STL 物件識別系統 - Docker 映像檔
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 設定環境變數
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Taipei \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安裝系統依賴（分層安裝以優化快取）
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基本工具
    wget \
    curl \
    ca-certificates \
    procps \
    # 圖像處理相關（OpenCV 需要）
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libfontconfig1 \
    # 3D 渲染相關（PyVista 需要）
    xvfb \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libegl1 \
    libx11-6 \
    libxt6 \
    # 清理快取
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 複製 requirements.txt 並安裝 Python 依賴（利用 Docker 層級快取）
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir Flask gunicorn && \
    # 驗證關鍵套件安裝
    python -c "import cv2; import pyvista; import ultralytics; print('✓ 關鍵套件已安裝')"

# 複製應用程式檔案（排除 .dockerignore 中的項目）
COPY . .

# 創建必要的目錄結構
RUN mkdir -p \
    STL \
    dataset \
    yolo_dataset/train/images \
    yolo_dataset/train/labels \
    yolo_dataset/val/images \
    yolo_dataset/val/labels \
    runs/detect \
    static/uploads \
    web_uploads \
    training_logs \
    logs \
    templates && \
    # 設定權限
    chmod -R 755 /app && \
    chmod +x /app/*.sh 2>/dev/null || true

# 設定虛擬顯示器環境變數（用於 PyVista 無頭渲染）
ENV DISPLAY=:99 \
    PYVISTA_OFF_SCREEN=true \
    PYVISTA_USE_PANEL=false

# 暴露端口
EXPOSE 5000

# 創建優化的啟動腳本
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "========================================"\n\
echo "  STL 物件識別系統 Docker 容器啟動"\n\
echo "========================================"\n\
\n\
# 啟動虛擬顯示器（PyVista 3D 渲染需要）\n\
echo "🖥️  啟動虛擬顯示器 (Xvfb)..."\n\
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset > /dev/null 2>&1 &\n\
XVFB_PID=$!\n\
\n\
# 等待 Xvfb 完全啟動\n\
sleep 3\n\
\n\
# 檢查 Xvfb 是否正常運行\n\
if ! ps -p $XVFB_PID > /dev/null; then\n\
    echo "❌ Xvfb 啟動失敗"\n\
    exit 1\n\
fi\n\
echo "✅ Xvfb 已啟動 (PID: $XVFB_PID)"\n\
\n\
# 顯示系統資訊\n\
echo ""\n\
echo "📊 系統資訊:"\n\
echo "   Python: $(python3 --version)"\n\
echo "   工作目錄: $(pwd)"\n\
echo "   STL 檔案數: $(ls -1 STL/*.stl 2>/dev/null | wc -l)"\n\
\n\
# 檢查必要檔案\n\
if [ ! -f "web_interface.py" ]; then\n\
    echo "❌ 找不到 web_interface.py"\n\
    exit 1\n\
fi\n\
\n\
# 啟動 Web 服務\n\
echo ""\n\
echo "🚀 啟動 STL 物件識別 Web 服務..."\n\
echo "   訪問地址: http://localhost:5000"\n\
echo "========================================"\n\
echo ""\n\
\n\
# 使用 gunicorn 啟動（生產環境）或 Flask 開發模式\n\
if [ "$FLASK_ENV" = "development" ]; then\n\
    exec python3 web_interface.py\n\
else\n\
    exec gunicorn --bind 0.0.0.0:5000 \\\n\
        --workers 2 \\\n\
        --threads 4 \\\n\
        --timeout 300 \\\n\
        --access-logfile - \\\n\
        --error-logfile - \\\n\
        --log-level info \\\n\
        "web_interface:app"\n\
fi\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# 啟動命令
ENTRYPOINT ["/app/entrypoint.sh"]