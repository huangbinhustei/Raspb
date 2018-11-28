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
        self.going = False
        self.last_interrupt = 0
        self.turn = True
        # self.ongoing()

    def turn_off(self):
        # 不改变状态，关闭所有的灯
        for i in range(4):
            GPIO.output(self.led_pin[i], GPIO.HIGH)
        self.turn = False

    def turn_on(self):
        # 按照shine状态显示灯
        for ind, _flag in enumerate(self.shine):
            if _flag:
                GPIO.output(self.led_pin[ind], GPIO.LOW)
            else:
                GPIO.output(self.led_pin[ind], GPIO.HIGH)
        self.turn = True

    def __ongoing(self, gap, shine):
        while self.going:
            if time.time() - self.last_interrupt <= 30:
                time.sleep(5)
                continue
            for i in range(4):
                # 全部熄灭
                GPIO.output(self.led_pin[i], GPIO.HIGH)
            time.sleep(gap)
            for ind, _flag in enumerate(self.shine):
                if _flag:
                    GPIO.output(self.led_pin[ind], GPIO.LOW)
                else:
                    GPIO.output(self.led_pin[ind], GPIO.HIGH)
            time.sleep(shine)

    def ongoing(self, gap=5, shine=0.1):
        self.going = True
        t1 = threading.Thread(target=self.__ongoing, args=(gap, shine))
        t1.start()

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

    def flow(self, delay=0.25, loop=1, reverse=False, wait=False):
        t1 = threading.Thread(target=self.__flow, args=(delay, loop, reverse))
        t1.start()
        if wait:
            t1.join()

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

    def msg(self, starting=True, wait=False):
        if starting:
            t1 = threading.Thread(target=self.__msg_starting)
        else:
            t1 = threading.Thread(target=self.__msg_stopping)
        t1.start()
        if wait:
            t1.join()


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