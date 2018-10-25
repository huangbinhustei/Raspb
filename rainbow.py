# -*- coding: utf-8 -*-
import requests
import os
import time
import threading
import glob
from functools import wraps
from collections import defaultdict
import asyncio

import RPi.GPIO as GPIO

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


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

    def red(self):
        pass

    def yellow(self):
        pass

    def blue(self):
        pass

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

    def patrol(self):
        pass

    def _running(self):
        for i in self.keys_pin:
            GPIO.setup(i, GPIO.IN, GPIO.PUD_UP)
            GPIO.add_event_detect(i, GPIO.FALLING, self.key_interrupt, 200)
        print('Keyboard is ready')
        while self.run_flag:
            self.patrol()
            time.sleep(1)
        print('Keyboard is out of ready')

    def before_start(self):
        pass

    def start(self):
        self.before_start()
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

        self.show_lock = [0, 0, 0, 0] # 四个优先级的展示顺序

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

        self.font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 14)
        self.offset = 18
        
    def show(self, msgs, x=0, level=0):
        if level < 3 and time.time() - max(self.show_lock[level + 1:]) <= 3:
            print('有优先级更高的内容显示中，暂不显示')
            return
        
        self.draw.rectangle((0, 0, self.disp.width, self.disp.height), outline=0, fill=0)
        for i in range(len(msgs)):
            self.draw.text((x, self.top + self.offset * i), msgs[i], font=self.font, fill=255)

        # Display image.
        self.disp.clear()
        self.disp.image(self.image)
        self.disp.display()
        self.show_lock[level] = time.time()
        time.sleep(0.1)

    def cls(self, level=0):
        if level > 3 or time.time() - max(self.show_lock[level:]) >= 3:
        	# 3 秒后清空显示内容
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
        self.running = False

    def __on(self):
        #定义蜂鸣器开启函数
        GPIO.output(self.buzzer_pin, GPIO.LOW)

    def __off(self):
        #定义报警鸣叫函数beep(gap_time,on_time),on_time为鸣叫时长，gap_time为鸣叫间隔 单位为秒
        GPIO.output(self.buzzer_pin, GPIO.HIGH)

    def __beep(self, on_time, gap_time):
        self.running = True
        self.__off()
        time.sleep(on_time)
        self.__on()
        time.sleep(gap_time)
        self.running = False

    def beep(self, on_time, gap_time):
        if not self.running:
            t1 = threading.Thread(target=self.__beep, args=(on_time, gap_time))
            t1.start()

    async def __new_beep(self, on_time, gap_time):
        self.running = True
        self.__off()
        await asyncio.sleep(on_time)
        self.__on()
        await asyncio.sleep(gap_time)
        self.running = False

    def new_beep(self, on_time, gap_time):
        if not self.running:
            async.get_event_loop().run_until_complete(__new_beep())

    def clean(self):
        GPIO.output(self.buzzer_pin, GPIO.HIGH)
        GPIO.cleanup()


class LED:
    def __init__(self):
        self.led_pin = [23, 27, 22, 5]
        GPIO.setmode(GPIO.BCM)
        for i in self.led_pin:
            try:
                GPIO.setup(i, GPIO.OUT)
            except:
                print(str(i) + 'is using')
        for i in self.led_pin:
            GPIO.output(i, GPIO.HIGH)

    def on(self, i):
        if i >= 0 and i <= 3:
            GPIO.output(self.led_pin[i], GPIO.LOW)
        else:
            print('Wrong Index')
    
    def off(self, i):
        if i >= 0 and i <= 3:
            GPIO.output(self.led_pin[i], GPIO.HIGH)
        else:
            print('Wrong Index')

    def blink(self, i, delay=0.5):
        self.on(i)
        time.sleep(delay)
        self.off(i)

    def clean(self):
        GPIO.cleanup()

    def __flow(self, delay, loop):
        # 闪 loop 个轮次
        for j in range(loop):
            for i in range(4):
                self.blink(i, delay)

    def flow(self, delay=0.25, loop=1):
        t1 = threading.Thread(target=self.__flow, args=(delay, loop))
        t1.start()


class DS18B20:
    def __init__(self):
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
        target_dir = '/sys/bus/w1/devices/'
        device_folder = glob.glob(target_dir + '28*')[0]
        self.__device_file = device_folder + '/w1_slave'
        self.__name_file = device_folder + '/name'

    def __read_rom(self):
        # 似乎返回端是文件名，但是不知道意义何在
        with open(self.__name_file, 'r') as f:
            return f.readline()

    def __read_temp_raw(self):
        with open(self.__device_file, 'r') as f:
            return f.readlines()

    def get_temperature(self):
        lines = self.__read_temp_raw()
        if not lines[0].strip().endswith('YES'):
            return False, 'Loading Failed'
        info = lines[1].split('t=')
        if len(info) == 1:
            return False, 'No Results'
        return True, round(float(info[1]) / 1000, 1)

    def get_side_info(self):
        return self.__read_rom()


if __name__ == '__main__':
    t = time.time()
    reader = DS18B20()
    flag, ret = reader.get_temperature()
    if flag:
        print(ret)
    else:
        print(ret)
        print(reader.get_side_info())
    print(round(time.time() - t, 4) * 1000)
    