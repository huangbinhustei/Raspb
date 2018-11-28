# -*- coding: utf-8 -*-
import requests
import os
import time
import threading
import glob
from functools import wraps
from collections import defaultdict, deque

import RPi.GPIO as GPIO

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


class OLED:
    def __init__(self):
        self.scroll_task = deque(maxlen=3)
        RST = 25  # Raspberry Pi pin configuration:
        DC = 24     # Note the following are only used with SPI
        SPI_PORT = 0    # Note the following are only used with SPI
        SPI_DEVICE = 0  # Note the following are only used with SPI
        
        # 128x64 display with hardware SPI:
        self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

        self.alart_lock = 0 # scroll 不需要 lock，alart 需要。
        self.last_scroll = 0

        # Initialize library.
        self.disp.begin()
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
        self.offset = 21
        self.needDel = True
        self.delling()

    def delling(self):
        self.needDel = True
        t1 = threading.Thread(target=self.__deling, args=())
        t1.start()
        

    def __deling(self):
        while self.needDel:
            time.sleep(1)
            if time.time() - self.last_scroll >= 3:
                self.scroll(' ')


    def scroll(self, line, x=0):
        # 优先级最低的展示方式，每次只能一行
        if time.time() - self.alart_lock <= 2:
            return
        
        self.draw.rectangle((0, 0, self.disp.width, self.disp.height), outline=0, fill=0)
        self.scroll_task.append(line)
        for i in range(len(self.scroll_task)):
            self.draw.text((x, self.top + self.offset * i), self.scroll_task[i], font=self.font, fill=255)

        # Display image.
        self.disp.clear()
        self.disp.image(self.image)
        self.disp.display()
        time.sleep(0.1)
        self.last_scroll = time.time()

    def __alert(self, msgs, life_time, x):
        self.draw.rectangle((0, 0, self.disp.width, self.disp.height), outline=0, fill=0)
        for i in range(len(msgs)):
            self.draw.text((x, self.top + self.offset * i), msgs[i], font=self.font, fill=255)

        # Display image.
        self.disp.clear()
        self.disp.image(self.image)
        self.disp.display()

        self.alart_lock = time.time()
        if 0 != life_time:
            time.sleep(life_time)
            if time.time() - self.alart_lock > life_time - 0.1:
                self.cls()

    def alert(self, msgs, life_time=2, x=0):
        t_alert = threading.Thread(target=self.__alert, args=(msgs, life_time, x))
        t_alert.start()

    def cls(self):
        self.disp.clear()
        self.disp.display()
        self.needDel = False
