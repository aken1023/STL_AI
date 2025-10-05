#!/bin/bash

echo "🌐 STL 物件識別系統 - 公網訪問設定"
echo "=" * 60

# 檢查防火牆狀態
echo "🔍 檢查防火牆狀態..."
sudo ufw status

echo ""
echo "🔧 設定防火牆開放 8080 端口..."
sudo ufw allow 8080/tcp

echo ""
echo "📋 網路介面資訊:"
echo "本機 IP 位址:"
hostname -I

echo ""
echo "公網 IP 位址:"
curl -s https://api.ipify.org

echo ""
echo ""
echo "🚀 啟動公網訪問版網頁介面..."
echo "📍 訪問地址將在啟動後顯示"
echo ""

# 啟動公網版本
python web_interface_public.py