#!/bin/bash
# ============================================
# Pi-Star ModeKey DMR / C4FM Uninstaller
# For Raspberry Pi / Pi-Star
# 2026-01-25 | BI1OHC 73!
# ============================================

set -e

INSTALL_DIR="/opt/pi-star-modekey"
SERVICE_FILE="/etc/systemd/system/pi-star-modekey.service"

echo "============================================"
echo " Pi-Star ModeKey DMR / C4FM Uninstaller"
echo "============================================"
echo

# 检查是否为只读模式
if mount | grep 'on / type' | grep -q '(ro,'; then
    echo "⚠️ 当前系统为只读模式（ro）"
    echo "👉 请先执行: rpi-rw"
    echo "👉 然后重新运行本卸载脚本"
    exit 1
fi

# 停止并禁用服务
if systemctl list-unit-files | grep -q pi-star-modekey.service; then
    echo "🛑 停止并禁用服务"
    sudo systemctl stop pi-star-modekey.service || true
    sudo systemctl disable pi-star-modekey.service || true
else
    echo "ℹ️ 未检测到 systemd 服务，跳过"
fi

# 删除 service 文件
if [ -f "$SERVICE_FILE" ]; then
    echo "🧹 删除 systemd 服务文件"
    sudo rm -f "$SERVICE_FILE"
    sudo systemctl daemon-reload
else
    echo "ℹ️ 未发现 service 文件，跳过"
fi

# 删除安装目录
if [ -d "$INSTALL_DIR" ]; then
    echo "🧹 删除安装目录: $INSTALL_DIR"
    sudo rm -rf "$INSTALL_DIR"
else
    echo "ℹ️ 未发现安装目录，跳过"
fi

echo
echo "✅ 卸载完成！"
echo
echo "📌 说明："
echo " - 未卸载任何 Python / GPIO / LCD 相关库"
echo " - 不影响 Pi-Star 其他功能"
echo
echo "如需重新安装，请重新运行 install.sh"
