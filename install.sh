#!/bin/bash
# ============================================
# Pi-Star ModeKey DMR / C4FM Installer
# For Raspberry Pi / Pi-Star
# 2026-01-25 | BI1OHC 73!
# ============================================

set -e

INSTALL_DIR="/opt/pi-star-modekey"
SERVICE_FILE="/etc/systemd/system/pi-star-modekey.service"

show_help() {
    echo "Pi-Star ModeKey DMR / C4FM Installer"
    echo
    echo "Usage:"
    echo "  bash install.sh"
    echo "  bash install.sh --help"
    echo
    echo "Description:"
    echo "  Install Pi-Star ModeKey service with physical button + LED"
    echo "  Optional I2C LCD support is selectable during installation."
    echo
    echo "Options:"
    echo "  --help    Show this help message and exit"
    echo
    echo "Notes:"
    echo "  - Run 'rpi-rw' before installation (Pi-Star default is read-only)"
    echo "  - Installation directory: /opt/pi-star-modekey"
    echo "  - A systemd service will be created and enabled automatically"
    echo
    echo "73! BI1OHC"
}

# ---- help 参数 ----
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

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

if [[ "$MODE" == "1" ]]; then
    echo
    echo "➡️ 选择：无 LCD 版本"

    sudo cp switcher.py "$INSTALL_DIR/"
    sudo chmod +x "$INSTALL_DIR/switcher.py"

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
else
    echo
    echo "➡️ 选择：LCD 版本"

    sudo apt install -y python3-smbus i2c-tools
    sudo pip3 install RPLCD

    sudo cp switcher-lcd.py "$INSTALL_DIR/"
    sudo chmod +x "$INSTALL_DIR/switcher-lcd.py"

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
systemctl cat pi-star-modekey.service | grep ExecStart
