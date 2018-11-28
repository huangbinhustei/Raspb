# -- coding: utf-8 --
import time
import os
import sys
# from functools import wraps

# import RPi.GPIO as GPIO

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, os.path.pardir))
from base.RasGpio.rainbow import BUZZER, KEYBOARD, DS18B20, LED
# from base.RasGpio.rainbow_oled import OLED


class Information:
    def __init__(self):
        self.ds = DS18B20()
        self.led = LED()
        self.led.turn_off()
        # self.oled = OLED()
    
    def test(self):
        ret, temp = self.ds.get_temperature()
        if not ret:
            print('温度读取失败')
            return
        print('温度：' + str(temp))
        # self.oled.scroll('温度：' + str(temp))

i = Information()
i.led.blink(3)
for j in range(10):
    i.test()
    time.sleep(1)
i.led.blink(2)
time.sleep(6)