#!/bin/bash
# ============================================
# Pi-Star ModeKey DMR / C4FM Installer
# For Raspberry Pi 3B+
# BI1OHC 73！
# ============================================

set -e

echo "============================================"
echo " Pi-Star ModeKey DMR / C4FM Installer"
echo " Target: Raspberry Pi / Pi-Star"
echo "============================================"

# --- 必须是 root ---
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root:"
  echo "   sudo ./install.sh"
  exit 1
fi

echo "▶ Updating system package list..."
apt update

echo "▶ Installing system dependencies..."
apt install -y \
  python3 \
  python3-pip \
  python3-rpi.gpio \
  python3-smbus \
  i2c-tools

echo "▶ Installing Python libraries..."
pip3 install --no-cache-dir RPLCD smbus2

# --- I2C 提示 ---
echo
echo "▶ Checking I2C status..."
if ! lsmod | grep -q i2c_bcm; then
  echo "⚠ I2C kernel module not loaded."
  echo "  Please ensure I2C is enabled:"
  echo "  sudo raspi-config → Interface Options → I2C"
else
  echo "✔ I2C module detected."
fi

# --- 脚本安装位置 ---
INSTALL_DIR="/opt/pi-star-modekey"
SCRIPT_NAME="switcher.py"

echo
echo "▶ Installing switcher script..."
mkdir -p $INSTALL_DIR
cp $SCRIPT_NAME $INSTALL_DIR/
chmod +x $INSTALL_DIR/$SCRIPT_NAME

# --- systemd 服务 ---
SERVICE_FILE="/etc/systemd/system/pi-star-modekey.service"

echo "▶ Creating systemd service..."
cat > $SERVICE_FILE << EOF
[Unit]
Description=Pi-Star ModeKey DMR/C4FM Switcher
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/pi-star-modekey/switcher.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

echo "▶ Enabling service..."
systemctl daemon-reload
systemctl enable pi-star-modekey.service

echo
echo "============================================"
echo " ✅ Installation completed successfully"
echo " ▶ Reboot recommended"
echo " ▶ Service name: pi-star-modekey"
echo "============================================"
echo 
