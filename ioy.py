# -*- coding: utf-8 -*-
import requests
import os
import time
import threading
import glob
import math
from functools import wraps
from collections import defaultdict, deque

import RPi.GPIO as GPIO


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

    def test(self):
        # 0 ~ 10 对应 0 ~ 180°
        for t in range(0, 181, 18):
            self.set_dir(t)
        time.sleep(0.3)
        for t in range(0, 181, 18):
            self.set_dir(180 - t)
        self.p.stop()


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
            if distance >= 100:
                distance = 'NA'
            else:
                distance = int(distance)
            result.append(str(distance))
            time.sleep(0.5)
        print(''.join(['  ', '  ', result[2], '  ', '  ']))
        print(''.join(['  ', result[3], '  ', result[1], '  ']))
        print(''.join([result[4], '  ', '  ', '  ', result[0]]))


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


class RGB:
    def __init__(self):
        self.breathing = False
        self.R = 16
        self.G = 20
        self.B = 21
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.R, GPIO.OUT)
        GPIO.output(self.R, GPIO.HIGH)
        self.pwmR = GPIO.PWM(self.R, 1000)
        self.pwmR.start(0)

        GPIO.setup(self.G, GPIO.OUT)
        GPIO.output(self.G, GPIO.HIGH)
        self.pwmG = GPIO.PWM(self.G, 1000)
        self.pwmG.start(0)

        GPIO.setup(self.B, GPIO.OUT)
        GPIO.output(self.B, GPIO.HIGH)
        self.pwmB = GPIO.PWM(self.B, 1000)
        self.pwmB.start(0)
    
    def __color(self, r, g, b, t=1):
        self.pwmR.ChangeDutyCycle(int(r/2.55))
        self.pwmG.ChangeDutyCycle(int(g/2.55))
        self.pwmB.ChangeDutyCycle(int(b/2.55))
        time.sleep(t)

    def color(self, r, g, b, t=1):
        t1 = threading.Thread(target=self.__color, args=(r, g, b, t))
        t1.start()

    def __breath(self, tinct, loops, top, bottom, t, gap):
        self.breathing = True
        for x in range(loops):
            for i in range(bottom, top):
                self.__color(tinct[0] * i // top, tinct[1] * i // top, tinct[2] * i // top, t)
            for i in range(0, top - bottom):
                self.__color(tinct[0] * (top - i) // top, tinct[1] * (top - i) // top, tinct[2] * (top - i) // top, t)
            time.sleep(gap)
        
        self.breathing = False    
    
    def __breath_sin(self, tinct, loops, top, bottom, t, gap):
        self.breathing = True
        step = math.pi/100
        for x in range(loops):
            for i in range(101):
                p = math.sin(step * i) * math.sin(step * i)
                self.__color(
                    tinct[0] * p, 
                    tinct[1] * p, 
                    tinct[2] * p, 
                    t)
            time.sleep(gap)
        
        self.breathing = False    

    def breath(self, tinct=(0, 200, 0), loops=2, top=200, bottom=1, t=0.02, gap=1, wait=False):
        if self.breathing:
            return
        t1 = threading.Thread(target=self.__breath_sin, args=(tinct, loops, top, bottom, t, gap))
        t1.start()
        if wait:
            t1.join()

    def quit(self):
        self.pwmR.stop()
        self.pwmG.stop()
        self.pwmB.stop()

if __name__ == '__main__':
    # m = MK433()
    # m.blink(on_time=2, off_time=2, loop=2)
    # print("任务开始")

    # s = SG90()
    # print("任务开始")
    # s.run()

    # s = SR04()
    # print("任务开始")
    # s.run()

    s = RGB()
    s.breath(tinct=(0, 200, 0), wait=True)
    s.breath(tinct=(0, 200, 200), wait=True)
    s.breath(tinct=(50, 200, 200), wait=True)
    s.quit()
    GPIO.cleanup()
