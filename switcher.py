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

def set_mode(mode):

    print(f"正在安全同步配置至: {mode} ...")

    run_cmd("sudo mount -o remount,rw /")
    cfg = "/etc/mmdvmhost"

    if mode == "C4FM":
        run_cmd(f"sudo sed -i '/\\[System Fusion\\]/,/Enable=/ s/Enable=0/Enable=1/' {cfg}")
        run_cmd(f"sudo sed -i '/\\[System Fusion Network\\]/,/Enable=/ s/Enable=0/Enable=1/' {cfg}")
        run_cmd(f"sudo sed -i '/\\[DMR\\]/,/Enable=/ s/Enable=1/Enable=0/' {cfg}")
        run_cmd(f"sudo sed -i '/\\[DMR Network\\]/,/Enable=/ s/Enable=1/Enable=0/' {cfg}")
    else:
        run_cmd(f"sudo sed -i '/\\[DMR\\]/,/Enable=/ s/Enable=0/Enable=1/' {cfg}")
        run_cmd(f"sudo sed -i '/\\[DMR Network\\]/,/Enable=/ s/Enable=0/Enable=1/' {cfg}")
        run_cmd(f"sudo sed -i '/\\[System Fusion\\]/,/Enable=/ s/Enable=1/Enable=0/' {cfg}")
        run_cmd(f"sudo sed -i '/\\[System Fusion Network\\]/,/Enable=/ s/Enable=1/Enable=0/' {cfg}")

    run_cmd("sync")
    run_cmd("sudo systemctl restart mmdvmhost")
    run_cmd("sudo mount -o remount,ro /")

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

    while True:
        
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            current_mode = "C4FM" if current_mode == "DMR" else "DMR"

            print(f"\n检测到按键！切换目标: {current_mode}")
            set_mode(current_mode)
            led_indicator(current_mode)
            print(f"切换成功！当前模式: {current_mode}")

            heartbeat.counter = 0
            time.sleep(3)  

        heartbeat.tick(current_mode)
        time.sleep(0.1)


# Entry Point

if __name__ == "__main__":
    main()
