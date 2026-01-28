#!/bin/bash
# ============================================
# Pi-Star ModeKey DMR / C4FM Installer
# For Raspberry Pi / Pi-Star
# 2026-01-25 | BI1OHC 73!
# ============================================

set -e

INSTALL_DIR="/opt/pi-star-modekey"
SERVICE_FILE="/etc/systemd/system/pi-star-modekey.service"

echo "============================================"
echo " Pi-Star ModeKey DMR / C4FM Installer"
echo "============================================"
echo
echo "请选择你要安装的版本："
echo
echo "  1) 无 LCD 版本（仅按键 + LED）"
echo "  2) LCD 版本（按键 + LED + I2C LCD）"
echo
read -p "请输入 1 或 2 并回车: " MODE

if [[ "$MODE" != "1" && "$MODE" != "2" ]]; then
    echo "❌ 输入无效，安装已终止"
    exit 1
fi

echo
echo "📁 创建安装目录: $INSTALL_DIR"
sudo mkdir -p "$INSTALL_DIR"

echo "🧹 清理旧文件（如存在）"
sudo rm -f "$INSTALL_DIR/switcher.py"
sudo rm -f "$INSTALL_DIR/switcher-lcd.py"
sudo rm -f "$SERVICE_FILE"

echo
echo "📦 安装基础依赖（GPIO）"
sudo apt update
sudo apt install -y python3 python3-rpi.gpio

# ============================
# 无 LCD 版本
# ============================
if [[ "$MODE" == "1" ]]; then
    echo
    echo "➡️ 选择：无 LCD 版本"

    echo "📄 安装 switcher.py"
    sudo cp switcher.py "$INSTALL_DIR/"
    sudo chmod +x "$INSTALL_DIR/switcher.py"

    echo "🧩 创建 systemd 服务"
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Pi-Star ModeKey Switcher (No LCD)
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_DIR/switcher.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# ============================
# LCD 版本
# ============================
else
    echo
    echo "➡️ 选择：LCD 版本"

    echo "📦 安装 I2C / LCD 相关依赖"
    sudo apt install -y python3-smbus i2c-tools
    sudo pip3 install RPLCD

    echo "📄 安装 switcher-lcd.py"
    sudo cp switcher-lcd.py "$INSTALL_DIR/"
    sudo chmod +x "$INSTALL_DIR/switcher-lcd.py"

    echo "🧩 创建 systemd 服务"
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Pi-Star ModeKey Switcher (LCD)
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_DIR/switcher-lcd.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
fi

echo
echo "🔄 重新加载 systemd"
sudo systemctl daemon-reload
sudo systemctl enable pi-star-modekey.service
sudo systemctl restart pi-star-modekey.service

echo
echo "✅ 安装完成！"
echo
echo "👉 当前运行脚本："
systemctl cat pi-star-modekey.service | grep ExecStart

echo
echo "👉 查看运行状态："
echo "   systemctl status pi-star-modekey.service"
echo
