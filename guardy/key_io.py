# -- coding: utf-8 --
import time
import os
import sys
from functools import wraps

import RPi.GPIO as GPIO

from photo_guard import REPORTER, GUARDOR
basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, os.path.pardir))
from bxin import face, send_msg, qiniu_put
from rainbow import OLED, BUZZER, KEYBOARD, DS18B20, LED


TRANSLATE = ('OFF', 'ON')
keys_pin = [6, 13, 19, 26]
keys_name = ['Red', 'Yellow', 'Blue', 'Orange']
last_press = 0
time_gap = 0.1


def introduce(func):
    @wraps(func)
    def yelling(*args, **kw):
        stamp = time.strftime('%Y%m%d_%X', time.gmtime())
        _key = func.__name__.upper()
        global last_press
        global time_gap
        print(stamp + '\t' + _key + ' PRESS')
        if time.time() - last_press >= time_gap:
            ret = func(*args, **kw)
            last_press = time.time()
        else:
            print('should not reponse')
            ret = False
        return ret
    return yelling


class Maintance(KEYBOARD):
    def __init__(self):
        super(Maintance, self).__init__()
        self.reporter = REPORTER()
        self.guardor = GUARDOR()
        self.thermometer = DS18B20()
        self.led = LED()

    @introduce
    def red(self):
        self.reporter.buzzer.beep(0.04, 0.05)
        if self.guardor.run_flag or self.reporter.run_flag:
            # self.reporter.oleder.show(['Red Press', 'Task stopping'])
            # 当前运行中
            self.reporter.oleder.cls(level=5)
            self.reporter.stop()
            self.guardor.stop()
            print(time.strftime('%Y%m%d_%X', time.gmtime()) + "\tstopped")
            self.reporter.oleder.alert(['Red Press', 'Task stopped'], level=2)
        else:
            # self.reporter.oleder.show(['Red Press', 'Task starting'])
            # 当前没有运行
            self.reporter.oleder.cls()
            self.reporter.start()
            self.guardor.start()
            print(time.strftime('%Y%m%d_%X', time.gmtime()) + "\tstarted")
            self.reporter.oleder.alert(['Red Press', 'Task started'], level=2)

    @introduce
    def yellow(self):
        self.reporter.stop()
        candation = self.reporter.show_in_oled * 2 + self.reporter.show_in_buzzer
        '''
        状态    oled    buzzer
        00:    off     off
        01:    off     on
        10:    on      off
        11:    on      on
        '''
        if 0 == candation:
            # 当前 00，按下之后变成 01 -> 打开蜂鸣器
            self.reporter.show_in_buzzer = True
            print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\toled off & buzzer on')
        elif 1 == candation:
            # 当前 01，按下之后变成 10 -> 关闭蜂鸣器， 打开oled
            self.reporter.show_in_oled = True
            self.reporter.show_in_buzzer = False
            print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\toled on & buzzer off')
        elif 2 == candation:
            # 当前 10，按下之后变成 11 -> 打开蜂鸣器
            self.reporter.show_in_buzzer = True
            print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\toled on & buzzer on')
        elif 3 == candation:
            # 当前 11，按下之后变成 00 -> 关闭蜂鸣器，关闭oled
            self.reporter.show_in_oled = False
            self.reporter.show_in_buzzer = False
            print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\toled off & buzzer off')
        self.reporter.oleder.alert(['Yellow Press',
            'OLED:     ' + TRANSLATE[self.reporter.show_in_oled],
            'BUZZER: ' + TRANSLATE[self.reporter.show_in_buzzer]], level=2)
        self.reporter.buzzer.beep(0.02, 0.1)
        self.reporter.start()

    @introduce
    def blue(self):
        self.reporter.buzzer.beep(0.02, 0.1)
        flag, ret = self.thermometer.get_temperature()
        if ret:
            self.reporter.oleder.alert(['Blue Press', time.strftime('%X'), str(ret) + ' 度'])
        else:
            print('Failed to get temperature')

    @introduce
    def orange(self):
        self.reporter.buzzer.beep(0.02, 0.1)
        self.reporter.oleder.alert(['Orange Press', time.strftime('%X')])
        self.led.flow()

    def patrol(self):
        self.reporter.oleder.cls()

    def before_start(self):
        self.reporter.oleder.show(['Keyboard', 'is', 'ready'], level=1)

    def stop(self):
        super(Maintance, self).stop()

if __name__ == '__main__':
    keyboard = Maintance()
    keyboard.run_flag = True
    keyboard.start()
