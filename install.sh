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
    echo "  bash install.sh          # 交互选择安装版本"
    echo "  bash install.sh --help   # 显示此帮助"
    echo
    echo "说明："
    echo "  1) 无 LCD 版本：仅按键 + LED"
    echo "  2) LCD 版本：按键 + LED + I2C LCD"
    exit 0
}

if [[ "$1" == "--help" ]]; then
    show_help
fi

echo "🔍 检查系统 apt 源..."
BACKPORTS_LINE=$(grep -n "httpredir.debian.org/debian.*bullseye-backports" /etc/apt/sources.list /etc/apt/sources.list.d/*.list 2>/dev/null || true)

if [[ -n "$BACKPORTS_LINE" ]]; then
    echo "⚠️ 发现无效 bullseye-backports 源，临时注释处理..."
    while IFS= read -r line; do
        file=$(echo "$line" | cut -d: -f1)
        lineno=$(echo "$line" | cut -d: -f2)
        sudo sed -i "${lineno}s/^/#DISABLED_BACKPORTS /" "$file"
    done <<< "$BACKPORTS_LINE"
else
    echo "✅ 没有发现失效 backports 源"
fi

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
    # --------- 无 LCD 版本 ---------
    echo
    echo "➡️ 安装无 LCD 版本"
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

else
    # --------- LCD 版本 ---------
    echo
    echo "➡️ 安装 LCD 版本"

    echo "📦 安装 I2C / LCD 相关依赖"
    sudo apt install -y python3-smbus i2c-tools
    sudo pip3 install --upgrade RPLCD

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
