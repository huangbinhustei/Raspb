# -- coding: utf-8 --
import time
import os
import sys
# from functools import wraps

# import RPi.GPIO as GPIO

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, os.path.pardir))
from base.RasGpio.rainbow import OLED, BUZZER, KEYBOARD, DS18B20, LED


class Information:
    def __init__(self):
        self.oled = OLED()
        self.ds = DS18B20()
        self.led = LED()
        self.led.turn_off()
    
    def test(self):
        ret, temp = self.ds.get_temperature()
        if not ret:
            print('温度读取失败')
            return
        self.oled.scroll('温度：' + str(temp))
        print('温度：' + str(temp))

i = Information()
for j in range(10):
    i.test()
    time.sleep(1)
time.sleep(5)
i.oled.cls()