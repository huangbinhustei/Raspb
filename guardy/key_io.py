# -- coding: utf-8 --
import time
from functools import wraps

import RPi.GPIO as GPIO
from photo_guard import REPORTER, GUARDOR

TRANSLATE = ('OFF', 'ON')
keys_pin = [6, 13, 19, 26]
keys_name = ['Red', 'Yellow', 'Blue', 'Orange']
last_press = 0
time_gap = 0.5


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
            reporter.oleder.show([_key + ' PRESS',
                                'OLED     ' + TRANSLATE[reporter.show_in_oled],
                                'BUZZER ' + TRANSLATE[reporter.show_in_buzzer],
                                ])
            reporter.buzzer.beep(0.01, 0.05)
            last_press = time.time()
        else:
            print('should not reponse')
            ret = False
        return ret
    return yelling


@introduce
def red():
    if guardor.run_flag or reporter.run_flag:
        # 当前运行中
        reporter.stop()
        guardor.stop()
        reporter.oleder.cls()
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + "\tstopped")
    else:
        # 当前没有运行
        reporter.oleder.cls()
        reporter.start()
        guardor.start()
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + "\tstarted")


@introduce
def yellow(): 
    reporter.stop()
    candation = reporter.show_in_oled * 2 + reporter.show_in_buzzer
    '''
    状态    oled    buzzer
    00:    off     off
    01:    off     on
    10:    on      off
    11:    on      on
    '''
    if 0 == candation:
        # 当前 00，按下之后变成 01 -> 打开蜂鸣器
        reporter.show_in_buzzer = True
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\toled off & buzzer on')
    elif 1 == candation:
        # 当前 01，按下之后变成 10 -> 关闭蜂鸣器， 打开oled
        reporter.show_in_oled = True
        reporter.show_in_buzzer = False
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\toled on & buzzer off')
    elif 2 == candation:
        # 当前 10，按下之后变成 11 -> 打开蜂鸣器
        reporter.show_in_buzzer = True
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\toled on & buzzer on')
    elif 3 == candation:
        # 当前 11，按下之后变成 00 -> 关闭蜂鸣器，关闭oled
        reporter.show_in_oled = False
        reporter.show_in_buzzer = False
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\toled off & buzzer off')
    reporter.start()


@introduce
def blue():
    pass


@introduce
def orange():
    pass


def key_interrupt(key):
    target = keys_name[keys_pin.index(key)]
    {
        'Red': red,
        'Yellow': yellow,
        'Blue': blue,
        'Orange': orange,
    }[target]()

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)

    for i in keys_pin:
        GPIO.setup(i, GPIO.IN, GPIO.PUD_UP)
        GPIO.add_event_detect(i, GPIO.FALLING, key_interrupt, 200)

    reporter = REPORTER()
    guardor = GUARDOR()
    print("I'm ready and listening!")

    while True:
        reporter.oleder.cls()
        time.sleep(1)
