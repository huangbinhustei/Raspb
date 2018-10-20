# -- coding: utf-8 --
import time
import threading
import queue

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
import RPi.GPIO as GPIO
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


class OLED:
    def __init__(self):
        # Raspberry Pi pin configuration:
        RST = 25
        # Note the following are only used with SPI:
        DC = 24
        SPI_PORT = 0
        SPI_DEVICE = 0
        # 128x64 display with hardware SPI:
        self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

        # Initialize library.
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
        

    def show(self, msg, x=0):
        self.draw.rectangle((0, 0, self.disp.width, self.disp.height), outline=0, fill=0)
        msg[0] = msg[0][4:]

        for i in range(len(msg)):
            self.draw.text((x, self.top + self.offset * i), msg[i], font=self.font, fill=255)

        # Display image.
        self.disp.image(self.image)
        self.disp.display()
        self.show_lock = time.time()
        # time.sleep(0.1)

    def cls(self):
        if time.time() - self.show_lock >= 5:
            # print('Clean')
            self.disp.clear()
            self.disp.display()
        # else:
            # print("Can't clean because show recenty")



# def cls():
#     draw.rectangle((0, 0, width, height), outline=0, fill=0)
#     disp.image(image)
#     disp.display()


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
