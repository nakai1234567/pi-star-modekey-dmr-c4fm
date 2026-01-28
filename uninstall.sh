#!/bin/bash
# ============================================
# Pi-Star ModeKey DMR / C4FM Uninstaller
# For Raspberry Pi / Pi-Star
# 2026-01-25 | BI1OHC 73!
# ============================================

set -e

INSTALL_DIR="/opt/pi-star-modekey"
SERVICE_FILE="/etc/systemd/system/pi-star-modekey.service"

show_help() {
    echo "Pi-Star ModeKey DMR / C4FM Uninstaller"
    echo
    echo "Usage:"
    echo "  bash uninstall.sh"
    echo "  bash uninstall.sh --help"
    echo
    echo "This will:"
    echo "  - Stop the pi-star-modekey service"
    echo "  - Remove systemd service file"
    echo "  - Remove installed scripts in $INSTALL_DIR"
}

if [[ "$1" == "--help" ]]; then
    show_help
    exit 0
fi

echo
echo "🛑 停止 systemd 服务（如果存在）"
if systemctl list-units --full -all | grep -q pi-star-modekey.service; then
    sudo systemctl stop pi-star-modekey.service || true
    sudo systemctl disable pi-star-modekey.service || true
else
    echo "⚠️ 服务未找到，无需停止"
fi

echo
echo "🧹 删除 systemd 服务文件"
sudo rm -f "$SERVICE_FILE"
sudo systemctl daemon-reload

echo
echo "🗑️ 删除安装目录及脚本"
sudo rm -rf "$INSTALL_DIR"

echo
echo "✅ 卸载完成！"
echo "⚡ GPIO 清理和 systemd 相关配置已处理"
