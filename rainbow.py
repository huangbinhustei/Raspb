# -*- coding: utf-8 -*-
import requests
import os
import time
import threading
import glob
from functools import wraps
from collections import defaultdict, deque
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
        self.keys_pin = [6, 13, 19, 26]
        self.keys_name = ['Red', 'Yellow', 'Blue', 'Orange'] 
        self.handle = {}
        self.register()
        self.run_flag = False
        GPIO.setmode(GPIO.BCM)

    def when_press(self, key):
        pass

    def when_pressed(self, key):
        pass

    def red(self, key):
        pass

    def yellow(self, key):
        pass

    def blue(self, key):
        pass

    def orange(self, key):
        pass

    def register(self):
        self.handle = {
                    6: self.red,
                    13: self.yellow,
                    19: self.blue,
                    26: self.orange,
                }

    def key_interrupt(self, key):
        self.when_press(key)
        self.handle[key](key)
        self.when_pressed(key)

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
        t1 = threading.Thread(target=self.__deling, args=())
        t1.start()

    def __deling(self):
        while True:
            time.sleep(1)
            if time.time() - self.last_scroll >= 1:
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

    def clean(self):
        GPIO.output(self.buzzer_pin, GPIO.HIGH)
        GPIO.cleanup()


class LED:
    def __init__(self):
        self.led_pin = [23, 27, 22, 5]
        self.shine = [0, 0, 0, 0]
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
            self.shine[i] = 1
            GPIO.output(self.led_pin[i], GPIO.LOW)
        else:
            print('Wrong Index')
    
    def off(self, i):
        if i >= 0 and i <= 3:
            self.shine[i] = 0
            GPIO.output(self.led_pin[i], GPIO.HIGH)
        else:
            print('Wrong Index')

    def __blink(self, i, delay=0.5):
        GPIO.output(self.led_pin[i], GPIO.LOW)
        time.sleep(delay)
        GPIO.output(self.led_pin[i], GPIO.HIGH)
        

    def blink(self, i, delay=0.5):
        if i >= 0 and i <= 3:
            t1 = threading.Thread(target=self.__blink, args=(i, delay))
            t1.start()
        else:
            print('Wrong Index')

    def clean(self):
        GPIO.cleanup()

    def __flow(self, delay, loop, reverse):
        for j in range(loop):
            for i in range(4):
                if reverse:
                    self.__blink(3 - i, delay)
                else:
                    self.__blink(i, delay)
        for ind, _flag in enumerate(self.shine):
            if _flag:
                GPIO.output(self.led_pin[ind], GPIO.LOW)
            else:
                GPIO.output(self.led_pin[ind], GPIO.HIGH)

    def flow(self, delay=0.25, loop=1, reverse=False):
        t1 = threading.Thread(target=self.__flow, args=(delay, loop, reverse))
        t1.start()

    def __msg_starting(self):
        for i in range(4):
            GPIO.output(self.led_pin[i], GPIO.HIGH)
        for i in range(4):
            GPIO.output(self.led_pin[i], GPIO.LOW)
            time.sleep(0.25)
        for i in range(4):
            GPIO.output(self.led_pin[i], GPIO.HIGH)
        time.sleep(0.1)

    def __msg_stopping(self):
        for i in range(4):
            GPIO.output(self.led_pin[i], GPIO.LOW)
        for i in range(4):
            time.sleep(0.25)
            GPIO.output(self.led_pin[3 - i], GPIO.HIGH)
        for i in range(4):
            GPIO.output(self.led_pin[i], GPIO.HIGH)
        time.sleep(0.1)

    def msg(self, starting=True):
        if starting:
            t1 = threading.Thread(target=self.__msg_starting)
        else:
            t1 = threading.Thread(target=self.__msg_stopping)
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