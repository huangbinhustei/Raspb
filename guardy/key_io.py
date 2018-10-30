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


class Maintance(KEYBOARD):
    def __init__(self):
        super(Maintance, self).__init__()
        self.reporter = REPORTER()
        self.guardor = GUARDOR()
        self.thermometer = DS18B20()
        self.led = LED()

    def when_press(self, key):
        self.reporter.beep(0.01, 0.02)
        stamp = time.strftime('%Y%m%d_%X', time.gmtime())
        print(stamp + '\t' + self.keys_name[self.keys_pin.index(key)] + ' PRESS')
        offset = self.keys_pin.index(key)
        if offset in (1, 2):
            # 第 0 个键通过 flow 提示。
            # 第 3 个按键本来就是 blink 了。
            self.led.blink(offset, delay=1)
        
    def when_pressed(self, key):
        pass

    def red(self, key):
        if self.guardor.run_flag or self.reporter.run_flag:
            # 当前运行中
            self.led.flow(delay=0.25, reverse=True)
            self.reporter.cls()
            self.reporter.stop()
            self.guardor.stop()
            print(time.strftime('%Y%m%d_%X', time.gmtime()) + "\tstopped")
            self.reporter.alert(['Red Press', 'Task stopped'])
            time.sleep(0.25*4 + 0.1)
            self.led.off(0)
        else:
            # 当前没有运行
            self.led.flow(delay=0.25)
            self.reporter.cls()
            self.reporter.start()
            self.guardor.start()
            print(time.strftime('%Y%m%d_%X', time.gmtime()) + "\tstarted")
            self.reporter.alert(['Red Press', 'Task started'])
            time.sleep(0.25*4 + 0.1)
            self.led.on(0)

    def yellow(self, key):
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
        self.reporter.alert(['Yellow Press',
            'OLED:     ' + TRANSLATE[self.reporter.show_in_oled],
            'BUZZER: ' + TRANSLATE[self.reporter.show_in_buzzer]])
        self.reporter.start()

    def blue(self, key):
        flag, ret = self.thermometer.get_temperature()
        if flag:
            print(str(ret) + ' 度')
            self.reporter.alert(['Blue Press', time.strftime('%X'), str(ret) + ' 度'])
        else:
            print('Failed to get temperature')

    def orange(self, key):
        self.reporter.alert(['Orange Press', time.strftime('%X')])
        self.led.flow()

    def before_start(self):
        self.reporter.alert(['Keyboard', 'is', 'ready'], life_time=5)

    def stop(self):
        super(Maintance, self).stop()

if __name__ == '__main__':
    keyboard = Maintance()
    keyboard.run_flag = True
    keyboard.start()
