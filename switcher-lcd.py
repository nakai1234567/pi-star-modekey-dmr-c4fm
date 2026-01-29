#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-01-25  |  BI1OHC 73!

import RPi.GPIO as GPIO
import time
import subprocess
import os
import signal
import sys

BUTTON_PIN = 17
LED_PIN = 27
CFG_PATH = "/etc/mmdvmhost"

LCD_ENABLED = False
lcd = None

def cleanup(signum=None, frame=None):
    print("\n🛑 Switcher exiting, GPIO cleanup")
    if LCD_ENABLED and lcd:
        try: 
            lcd.clear()
            lcd.close(clear=True)
        except: pass
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def run_cmd(cmd):

    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def init_lcd():
    
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

    if LCD_ENABLED and lcd:
        try: 
            lcd.clear() 
        except: 
            pass
    
    print(f"正在安全同步配置至: {target_mode} ...")
    
    run_cmd("sudo mount -o remount,rw /")
    
    if target_mode == "C4FM":
        run_cmd(f"sudo sed -i '/\\[System Fusion\\]/,/Enable=/ s/Enable=0/Enable=1/' {CFG_PATH}")
        run_cmd(f"sudo sed -i '/\\[System Fusion Network\\]/,/Enable=/ s/Enable=0/Enable=1/' {CFG_PATH}")
        run_cmd(f"sudo sed -i '/\\[DMR\\]/,/Enable=/ s/Enable=1/Enable=0/' {CFG_PATH}")
        run_cmd(f"sudo sed -i '/\\[DMR Network\\]/,/Enable=/ s/Enable=1/Enable=0/' {CFG_PATH}")
    else:
        run_cmd(f"sudo sed -i '/\\[DMR\\]/,/Enable=/ s/Enable=0/Enable=1/' {CFG_PATH}")
        run_cmd(f"sudo sed -i '/\\[DMR Network\\]/,/Enable=/ s/Enable=0/Enable=1/' {CFG_PATH}")
        run_cmd(f"sudo sed -i '/\\[System Fusion\\]/,/Enable=/ s/Enable=1/Enable=0/' {CFG_PATH}")
        run_cmd(f"sudo sed -i '/\\[System Fusion Network\\]/,/Enable=/ s/Enable=1/Enable=0/' {CFG_PATH}")
    
    run_cmd("sync")
    run_cmd("sudo systemctl restart mmdvmhost")
    run_cmd("sudo mount -o remount,ro /")

    print("切换中，请稍候...")
    for _ in range(4):
        GPIO.output(LED_PIN, GPIO.HIGH); time.sleep(0.2)
        GPIO.output(LED_PIN, GPIO.LOW); time.sleep(0.8)

    if LCD_ENABLED and lcd:
        try:
            lcd.clear()
            lcd.write_string(f"{target_mode} OK!".ljust(16))
        except: 
            pass

    if target_mode == "DMR":
        for _ in range(5): # DMR: 快闪 5 次
            GPIO.output(LED_PIN, GPIO.HIGH); time.sleep(0.1)
            GPIO.output(LED_PIN, GPIO.LOW); time.sleep(0.1)
    else:
        GPIO.output(LED_PIN, GPIO.HIGH); time.sleep(2) # C4FM: 长亮 2 秒
        GPIO.output(LED_PIN, GPIO.LOW)
    
    print(f"切换成功！当前模式: {target_mode}")

def get_current_mode():

    current_mode = "DMR"
    try:
        if os.path.exists(CFG_PATH):
            with open(CFG_PATH, 'r') as f:
                content = f.read()

                if "[DMR]" in content:
                    start = content.find("[DMR]")
                    end = content.find("[", start + 1)
                    section = content[start:end] if end != -1 else content[start:]
                    if "Enable=1" in section:
                        current_mode = "DMR"

                if "[System Fusion]" in content:
                    start = content.find("[System Fusion]")
                    end = content.find("[", start + 1)
                    section = content[start:end] if end != -1 else content[start:]
                    if "Enable=1" in section:
                        current_mode = "C4FM"
    except: 
        pass
    return current_mode

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LED_PIN, GPIO.OUT)

 
    current_mode = get_current_mode()
    print(f"当前模式: {current_mode}")

    time.sleep(2)
    init_lcd()
    
    if current_mode == "DMR":
        for _ in range(3):
            GPIO.output(LED_PIN, GPIO.HIGH); time.sleep(0.1)
            GPIO.output(LED_PIN, GPIO.LOW); time.sleep(0.1)
    else:
        GPIO.output(LED_PIN, GPIO.HIGH); time.sleep(1)
        GPIO.output(LED_PIN, GPIO.LOW)
    
    if LCD_ENABLED and lcd:
        try: 
            lcd.write_string(f"{current_mode} OK!".ljust(16))
        except: 
            pass

    print(f"2026 Pi-Star Switcher Ready. Current: {current_mode}")

    heartbeat_counter = 0
    last_button_press = 0
    button_debounce = 0.5 

    try:
        while True:
            current_time = time.time()
            
            if GPIO.input(BUTTON_PIN) == GPIO.LOW and (current_time - last_button_press) > button_debounce:
                last_button_press = current_time
                
                GPIO.output(LED_PIN, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(LED_PIN, GPIO.LOW)
                
                new_mode = "C4FM" if current_mode == "DMR" else "DMR"
                print(f"\n检测到按键！切换目标: {new_mode}")
                clean_and_switch(new_mode)
                current_mode = new_mode
                heartbeat_counter = 0
                time.sleep(0.5)  # 防抖
            
            if heartbeat_counter >= 100:  # 0.1s * 100 = 10秒
                if current_mode == "DMR":
                    GPIO.output(LED_PIN, GPIO.HIGH); time.sleep(0.03)
                    GPIO.output(LED_PIN, GPIO.LOW)
                else:
                    for _ in range(2):
                        GPIO.output(LED_PIN, GPIO.HIGH); time.sleep(0.03)
                        GPIO.output(LED_PIN, GPIO.LOW); time.sleep(0.15)
                
                heartbeat_counter = 0

            time.sleep(0.1)
            heartbeat_counter += 1

    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
