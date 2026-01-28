#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-01-25  |  BI1OHC 73!

import RPi.GPIO as GPIO
import time
import subprocess
import os

# === 硬件引脚配置 ===
BUTTON_PIN = 17
LED_PIN = 27
CFG_PATH = "/etc/mmdvmhost"

# === 全局变量 ===
LCD_ENABLED = False
lcd = None

def run_cmd(cmd):
    """静默执行系统命令"""
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def init_lcd():
    """LCD 初始化"""
    global LCD_ENABLED, lcd
    try:
        from RPLCD.i2c import CharLCD
        for addr in [0x27, 0x3f]:
            try:
                lcd = CharLCD(i2c_expander='PCF8574', address=addr, port=1, cols=16, rows=2)
                lcd.clear()
                LCD_ENABLED = True
                return True
            except: continue
    except: pass
    return False

def clean_and_switch(target_mode):
    """切换逻辑：包含切换时的 4 秒 LED 呼吸反馈"""
    if LCD_ENABLED and lcd:
        try: lcd.clear()
        except: pass
    
    # 核心配置文件修改
    run_cmd("sudo mount -o remount,rw /")
    if target_mode == "C4FM":
        run_cmd(f"sudo sed -i '/\[System Fusion\]/,/Enable=/ s/Enable=.*/Enable=1/' {CFG_PATH}")
        run_cmd(f"sudo sed -i '/\[DMR\]/,/Enable=/ s/Enable=.*/Enable=0/' {CFG_PATH}")
    else:
        run_cmd(f"sudo sed -i '/\[DMR\]/,/Enable=/ s/Enable=.*/Enable=1/' {CFG_PATH}")
        run_cmd(f"sudo sed -i '/\[System Fusion\]/,/Enable=/ s/Enable=.*/Enable=0/' {CFG_PATH}")
    
    run_cmd("sync")
    run_cmd("sudo systemctl restart mmdvmhost")
    run_cmd("sudo mount -o remount,ro /")

    # 切换中：LED 慢速呼吸闪烁 (4秒)
    for _ in range(4):
        GPIO.output(LED_PIN, GPIO.HIGH); time.sleep(0.2)
        GPIO.output(LED_PIN, GPIO.LOW); time.sleep(0.8)

    # 切换后 LCD 显示
    if LCD_ENABLED and lcd:
        try:
            lcd.clear()
            lcd.write_string(f"{target_mode} OK!".ljust(16))
        except: init_lcd()

    # 切换后 LED 最终确认反馈
    if target_mode == "DMR":
        for _ in range(5): # DMR: 快闪 5 次
            GPIO.output(LED_PIN, GPIO.HIGH); time.sleep(0.1)
            GPIO.output(LED_PIN, GPIO.LOW); time.sleep(0.1)
    else:
        GPIO.output(LED_PIN, GPIO.HIGH); time.sleep(2) # C4FM: 长亮 2 秒
        GPIO.output(LED_PIN, GPIO.LOW)

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LED_PIN, GPIO.OUT)

    # 初始状态探测
    current_mode = "DMR"
    try:
        if os.path.exists(CFG_PATH):
            with open(CFG_PATH, 'r') as f:
                content = f.read()
                if "Enable=1" in content.split("[System Fusion]").split("["):
                    current_mode = "C4FM"
    except: pass

    # 启动缓冲
    time.sleep(2)
    init_lcd()
    if LCD_ENABLED and lcd:
        try: lcd.write_string(f"{current_mode} OK!".ljust(16))
        except: pass

    print(f"2026 Pi-Star Switcher Ready. Current: {current_mode}")

    # 心跳计数器
    heartbeat_counter = 0

    try:
        while True:
            # --- 1. 按键检测 ---
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                current_mode = "C4FM" if current_mode == "DMR" else "DMR"
                print(f"Switching to {current_mode}...")
                clean_and_switch(current_mode)
                heartbeat_counter = 0 # 切换后重置心跳
                time.sleep(1) # 防抖
            
            # --- 2. 智能心跳灯逻辑 (每 30 秒触发一次) ---
            # 循环是 0.1s 一次，所以 300 次 = 30 秒
            if heartbeat_counter >= 100:
                if current_mode == "DMR":
                    # DMR 模式：单次微闪 (滴)
                    GPIO.output(LED_PIN, GPIO.HIGH); time.sleep(0.03)
                    GPIO.output(LED_PIN, GPIO.LOW)
                else:
                    # C4FM 模式：双次微闪 (滴-滴)
                    GPIO.output(LED_PIN, GPIO.HIGH); time.sleep(0.03)
                    GPIO.output(LED_PIN, GPIO.LOW);  time.sleep(0.15)
                    GPIO.output(LED_PIN, GPIO.HIGH); time.sleep(0.03)
                    GPIO.output(LED_PIN, GPIO.LOW)
                
                heartbeat_counter = 0
                print(f"💓 Heartbeat Check: {current_mode} Mode Active")

            time.sleep(0.1)
            heartbeat_counter += 1

    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
