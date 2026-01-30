#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-01-25  |  BI1OHC 73!

import time
import subprocess
import signal
import sys
import RPi.GPIO as GPIO

BUTTON_PIN = 17   # 物理引脚 11
LED_PIN    = 27   # 物理引脚 13
# GND -> 公用物理引脚 14
CFG_PATH = "/etc/mmdvmhost"

def gpio_init():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.output(LED_PIN, GPIO.LOW)

def run_cmd(cmd):
    try:
        subprocess.run(
            cmd,
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except Exception:
        return False

def update_config_file(target_mode):

    run_cmd("sudo mount -o remount,rw /")
    
    try:
        with open(CFG_PATH, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            if line.strip() == '[DMR]':
                new_lines.append(line)
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('['):
                    if lines[i].strip().startswith('Enable='):

                        if target_mode == "DMR":
                            new_lines.append('Enable=1')
                        else:
                            new_lines.append('Enable=0')
                    else:
                        new_lines.append(lines[i])
                    i += 1
            
            elif line.strip() == '[System Fusion]':
                new_lines.append(line)
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('['):
                    if lines[i].strip().startswith('Enable='):

                        if target_mode == "C4FM":
                            new_lines.append('Enable=1')
                        else:
                            new_lines.append('Enable=0')
                    else:
                        new_lines.append(lines[i])
                    i += 1
            
            elif line.strip() == '[DMR Network]':
                new_lines.append(line)
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('['):
                    if lines[i].strip().startswith('Enable='):
                        # 只修改 Enable 参数
                        if target_mode == "DMR":
                            new_lines.append('Enable=1')
                        else:
                            new_lines.append('Enable=0')
                    else:
                        new_lines.append(lines[i]) 
                    i += 1
            
            elif line.strip() == '[System Fusion Network]':
                new_lines.append(line)
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('['):
                    if lines[i].strip().startswith('Enable='):

                        if target_mode == "C4FM":
                            new_lines.append('Enable=1')
                        else:
                            new_lines.append('Enable=0')
                    else:
                        new_lines.append(lines[i])
                    i += 1
            
            else:
                new_lines.append(line)
                i += 1
        
        with open(CFG_PATH, 'w') as f:
            f.write('\n'.join(new_lines))
        
        return True
        
    except Exception as e:
        print(f"配置文件更新失败: {e}")
        return False
    finally:
        run_cmd("sync")
        run_cmd("sudo mount -o remount,ro /")

def set_mode(mode):

    print(f"正在安全同步配置至: {mode} ...")
    
    if update_config_file(mode):
        run_cmd("sudo systemctl restart mmdvmhost")
        return True
    return False

def led_indicator(mode):

    if mode == "DMR":
        for _ in range(5):
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.1)
    else:
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(2)
        GPIO.output(LED_PIN, GPIO.LOW)

class Heartbeat:
    def __init__(self):
        self.counter = 0
        self.interval = 100  # 100 × 0.1s ≈ 10 秒

    def tick(self, mode):
        self.counter += 1
        if self.counter >= self.interval:
            if mode == "DMR":
                GPIO.output(LED_PIN, GPIO.HIGH)
                time.sleep(0.03)
                GPIO.output(LED_PIN, GPIO.LOW)
            else:
                for _ in range(2):
                    GPIO.output(LED_PIN, GPIO.HIGH)
                    time.sleep(0.03)
                    GPIO.output(LED_PIN, GPIO.LOW)
                    time.sleep(0.15)
            self.counter = 0

def cleanup(signum=None, frame=None):
    print("\n🛑 Switcher exiting, GPIO cleanup")
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def main():
    gpio_init()
    heartbeat = Heartbeat()
    current_mode = "DMR"
    last_button_time = 0
    debounce_time = 0.5

    while True:
        current_time = time.time()
        

        if GPIO.input(BUTTON_PIN) == GPIO.LOW and (current_time - last_button_time) > debounce_time:
            last_button_time = current_time
            
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(LED_PIN, GPIO.LOW)
            
            new_mode = "C4FM" if current_mode == "DMR" else "DMR"
            print(f"\n检测到按键！切换目标: {new_mode}")
            
            if set_mode(new_mode):

                current_mode = new_mode
                led_indicator(current_mode)
                print(f"切换成功！当前模式: {current_mode}")
            else:

                print("切换失败！")
                for _ in range(10):
                    GPIO.output(LED_PIN, GPIO.HIGH)
                    time.sleep(0.1)
                    GPIO.output(LED_PIN, GPIO.LOW)
                    time.sleep(0.1)
            
            heartbeat.counter = 0
            time.sleep(0.5)

        heartbeat.tick(current_mode)
        time.sleep(0.1)

if __name__ == "__main__":
    main()
