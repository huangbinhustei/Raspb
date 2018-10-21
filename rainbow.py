# -*- coding: utf-8 -*-
import requests
import os
import time
import threading
from functools import wraps
from collections import defaultdict

import RPi.GPIO as GPIO

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
import RPi.GPIO as GPIO
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


def introduce(func):
    @wraps(func)
    def yelling(*args, **kw):
        stamp = time.strftime('%Y%m%d_%X', time.gmtime())
        _key = func.__name__
        print(stamp + '\t' + _key + 'PRESS')
        ret = func(*args, **kw)
        return ret
    return yelling


class KEYBOARD:
    """
    仅用于彩虹板的控制
    """
    def __init__(self):
        self.keys_pin = [6, 13, 19, 26] # ['Red', 'Yellow', 'Blue', 'Orange']
        self.handle = {}
        self.register()
        self.run_flag = False
        GPIO.setmode(GPIO.BCM)
        

    @introduce
    def red(self):
        pass

    @introduce
    def yellow(self):
        pass

    @introduce
    def blue(self):
        pass

    @introduce
    def orange(self):
        pass

    def register(self):
        self.handle = {
                    0: self.red,
                    1: self.yellow,
                    2: self.blue,
                    3: self.orange,
                }

    def key_interrupt(self, key):
        target = self.keys_pin.index(key)
        self.handle[target]()

    def _running(self):
        for i in self.keys_pin:
            GPIO.setup(i, GPIO.IN, GPIO.PUD_UP)
            GPIO.add_event_detect(i, GPIO.FALLING, self.key_interrupt, 200)
        print('Keyboard is ready')
        while self.run_flag:
            time.sleep(1)
        print('Keyboard is out of ready')

    def start(self):
        self.run_flag = True
        t1 = threading.Thread(target=self._running)
        t1.start()

    def stop(self):
        self.run_flag = False


class OLED:
    def __init__(self):
        RST = 25  # Raspberry Pi pin configuration:
        DC = 24     # Note the following are only used with SPI
        SPI_PORT = 0    # Note the following are only used with SPI
        SPI_DEVICE = 0  # Note the following are only used with SPI
        
        # 128x64 display with hardware SPI:
        self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

        # Initialize library
        self.disp.begin()
        # Clear display.
        self.show_lock = 0
        self.cls()
                
        self.image = Image.new('1', (self.disp.width, self.disp.height))
        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)

        # Draw a black filled box to clear the image.
        self.draw.rectangle((0, 0, self.disp.width, self.disp.height), outline=0, fill=0)

        # Draw some shapes.
        # First define some constants to allow easy resizing of shapes.
        padding = -2
        self.top = padding
        self.bottom = self.disp.height - padding

        self.font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 16)
        self.offset = 22
        
    def show(self, msgs, x=0):
        self.draw.rectangle((0, 0, self.disp.width, self.disp.height), outline=0, fill=0)
        for i in range(len(msgs)):
            self.draw.text((x, self.top + self.offset * i), msgs[i], font=self.font, fill=255)

        # Display image.
        self.disp.clear()
        self.disp.image(self.image)
        self.disp.display()
        self.show_lock = time.time()
        time.sleep(0.1)

    def cls(self):
        if time.time() - self.show_lock >= 3:
        	# 3 秒后清空显示内容
            # print('Clean')
            self.disp.clear()
            self.disp.display()
        # else:
            # print("Can't clean because show recenty")


class BUZZER:
    def __init__(self):
        #定义一个存放led引脚号的列表
        self.buzzer_pin = 12
        #设置引脚模式为BCM引脚号模式
        GPIO.setmode(GPIO.BCM)
        #循环遍历存放引脚的数组
        GPIO.setup(self.buzzer_pin, GPIO.OUT)
        #定义蜂鸣器开启函数

    def __on(self):
        #定义蜂鸣器开启函数
        GPIO.output(self.buzzer_pin, GPIO.LOW)

    def __off(self):
        #定义报警鸣叫函数beep(gap_time,on_time),on_time为鸣叫时长，gap_time为鸣叫间隔 单位为秒
        GPIO.output(self.buzzer_pin, GPIO.HIGH)

    def beep(self, on_time, gap_time):
        self.__off()
        time.sleep(on_time)
        self.__on()
        time.sleep(gap_time)

    def clean(self):
        GPIO.output(self.buzzer_pin, GPIO.HIGH)
        GPIO.cleanup()