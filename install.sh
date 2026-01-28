#!/usr/bin/env bash
# ============================================================
# Pi-Star ModeKey Switcher Installer
# Author : BI1OHC
# Date   : 2026-01-25
#
# Interactive installer:
#   1) No LCD
#   2) I2C LCD (HD44780 / PCF8574)
# ============================================================

set -e

PROJECT_NAME="pi-star-modekey"
INSTALL_DIR="/opt/${PROJECT_NAME}"

USE_LCD=false

# ------------------------------------------------------------
# Root check
# ------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    echo "❌ Please run as root"
    echo "   sudo ./install.sh"
    exit 1
fi

# ------------------------------------------------------------
# Welcome
# ------------------------------------------------------------
clear
echo "============================================================"
echo " Pi-Star ModeKey Installer"
echo " Author : BI1OHC"
echo "============================================================"
echo
echo "Please select installation type:"
echo
echo "  1) No LCD (Button + LED only)"
echo "  2) With I2C LCD (HD44780 / PCF8574)"
echo
read -rp "Enter choice [1-2]: " choice

case "$choice" in
    1)
        USE_LCD=false
        ;;
    2)
        USE_LCD=true
        ;;
    *)
        echo "❌ Invalid selection"
        exit 1
        ;;
esac

echo
echo "------------------------------------------------------------"
echo " LCD support : ${USE_LCD}"
echo "------------------------------------------------------------"
echo

# ------------------------------------------------------------
# System update
# ------------------------------------------------------------
echo "📦 Updating system packages..."
apt update

# ------------------------------------------------------------
# Base dependencies
# ------------------------------------------------------------
echo "📦 Installing base dependencies..."
apt install -y \
    python3 \
    python3-pip

# ------------------------------------------------------------
# LCD dependencies (only if selected)
# ------------------------------------------------------------
if [[ "${USE_LCD}" == true ]]; then
    echo "📟 Installing LCD / I2C dependencies..."
    apt install -y \
        python3-smbus \
        i2c-tools

    if command -v raspi-config >/dev/null 2>&1; then
        echo "🔧 Enabling I2C interface..."
        raspi-config nonint do_i2c 0
    else
        echo "⚠️ raspi-config not found, enable I2C manually if needed"
    fi
else
    echo "🚫 Skipping LCD dependencies"
fi

# ------------------------------------------------------------
# Install files
# ------------------------------------------------------------
echo
echo "📂 Installing files to ${INSTALL_DIR}"

mkdir -p "${INSTALL_DIR}"

cp -v switcher.py "${INSTALL_DIR}/"

if [[ "${USE_LCD}" == true ]]; then
    cp -v switcher-lcd.py "${INSTALL_DIR}/"
fi

chmod +x "${INSTALL_DIR}/switcher.py"

if [[ "${USE_LCD}" == true ]]; then
    chmod +x "${INSTALL_DIR}/switcher-lcd.py"
fi

# ------------------------------------------------------------
# Finish
# ------------------------------------------------------------
echo
echo "============================================================"
echo " ✅ Installation completed successfully"
echo "------------------------------------------------------------"
echo " Install path : ${INSTALL_DIR}"
echo " LCD support : ${USE_LCD}"
echo

if [[ "${USE_LCD}" == true ]]; then
    echo " Next steps:"
    echo "   1. Reboot system"
    echo "   2. Check I2C: i2cdetect -y 1"
    echo "   3. Run: python3 ${INSTALL_DIR}/switcher-lcd.py"
else
    echo " Next steps:"
    echo "   Run: python3 ${INSTALL_DIR}/switcher.py"
fi

echo
echo " BI1OHC 73!"
echo "============================================================"
