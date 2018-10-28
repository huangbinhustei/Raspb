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


class SR04:
    def __init__(self):
        self.trig = 16
        self.echo = 20
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trig, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.echo, GPIO.IN)

    def detect(self):
        GPIO.output(self.trig, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.trig, GPIO.LOW)
        while GPIO.input(self.echo) == 0:
            pass
        pulse_start = time.time()
        while GPIO.input(self.echo) == 1:
            pass
        pulse_end = time.time()
        return round((pulse_end - pulse_start) * 17150, 2)
    
    def clean(self):
        GPIO.cleanup()



class SG90:
    def __init__(self):
        self.pin = 21
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)
        self.p = GPIO.PWM(self.pin, 50)
        self.p.start(2.5)

    def set_dir(self, d):
        if d < 0 or d > 180:
            print('角度必须在 0~ 180 之间')
            return
        duty = 2.5 + d * 10 / 180
        self.p.ChangeDutyCycle(duty)
        time.sleep(0.1)


    def run(self):
        # 0 ~ 10 对应 0 ~ 180°
        for t in range(0, 198, 18):
            self.set_dir(t)
        time.sleep(0.3)
        for t in range(0, 198, 18):
            self.set_dir(180 - t)

        self.p.stop()
        GPIO.cleanup()


class RADAR(SG90, SR04):
    def __init__(self):
        SG90.__init__(self)
        SR04.__init__(self)

    def run(self):
        result = []
        for t in range(0, 181, 45):
            self.set_dir(t)
            time.sleep(0.5)
            distance = self.detect()
            if distance >= 400:
                distance = 'Failed'
            else:
                distance = int(distance)
            result.append(str(distance))
            # if distance >= 400:
            #     print(str(t) + '\t:' + '测距失败，可能是角度过大')
            # else:
            #     print(str(t) + '\t:' + str(self.detect()) + 'cm')
            time.sleep(0.5)
        print('\t'.join(['', '', result[2], '', '']))
        print('\t'.join(['', result[3], '', result[1], '']))
        print('\t'.join([result[4], '', '', '', result[0]]))
            



class MK433:
    def __init__(self):
        # MK433 和 SR04 公用了一个管脚，同时只能用一个。
        self.pin = 20
        GPIO.setmode(GPIO.BCM)
        #循环遍历存放引脚的数组
        GPIO.setup(self.pin, GPIO.OUT)

    def on(self):
        GPIO.output(self.pin, GPIO.HIGH)
        
    def off(self):
        GPIO.output(self.pin, GPIO.LOW)
    
    def __blink(self, on_time, off_time, loop):
        for _ in range(loop):
            self.on()
            time.sleep(on_time)
            self.off()
            time.sleep(off_time)

    def blink(self, on_time=1, off_time=1, loop=2):
        if not isinstance(loop, int) or loop <= 0:
            print('loop <= 0')
            return
        t1 = threading.Thread(target=self.__blink, args=(on_time, off_time, loop))
        t1.start()

    def clean(self):
        GPIO.cleanup()


# m = MK433()
# m.blink(on_time=2, off_time=2, loop=2)
# print("任务开始")

# s = SG90()
# print("任务开始")
# s.run()

# s = SR04()
# print("任务开始")
# s.run()

s = RADAR()
print("任务开始")
s.run()