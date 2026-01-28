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
    echo "Description:"
    echo "  Remove Pi-Star ModeKey service and installed files."
    echo
    echo "What will be removed:"
    echo "  - systemd service: pi-star-modekey.service"
    echo "  - install directory: /opt/pi-star-modekey"
    echo
    echo "What will NOT be removed:"
    echo "  - python libraries (GPIO / RPLCD / smbus)"
    echo "  - Pi-Star configuration files"
    echo
    echo "Notes:"
    echo "  - Run 'rpi-rw' before uninstalling"
    echo
    echo "73! BI1OHC"
}

# ---- help 参数 ----
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

echo "============================================"
echo " Pi-Star ModeKey DMR / C4FM Uninstaller"
echo "============================================"
echo

if mount | grep 'on / type' | grep -q '(ro,'; then
    echo "⚠️ 当前系统为只读模式（ro）"
    echo "👉 请先执行: rpi-rw"
    exit 1
fi

if systemctl list-unit-files | grep -q pi-star-modekey.service; then
    sudo systemctl stop pi-star-modekey.service || true
    sudo systemctl disable pi-star-modekey.service || true
fi

if [ -f "$SERVICE_FILE" ]; then
    sudo rm -f "$SERVICE_FILE"
    sudo systemctl daemon-reload
fi

if [ -d "$INSTALL_DIR" ]; then
    sudo rm -rf "$INSTALL_DIR"
fi

echo
echo "✅ 卸载完成！"
