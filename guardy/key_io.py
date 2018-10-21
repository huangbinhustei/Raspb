# -- coding: utf-8 --
import time
from functools import wraps

import RPi.GPIO as GPIO
from photo_guard import REPORTER, GUARDOR

TRANSLATE = ('OFF', 'ON')
keys_pin = [6, 13, 19, 26]
keys_name = ['Red', 'Yellow', 'Blue', 'Orange']


def introduce(func):
    @wraps(func)
    def yelling(*args, **kw):
        stamp = time.strftime('%Y%m%d_%X', time.gmtime())
        _key = func.__name__.upper()
        print(stamp + '\t' + _key + ' PRESS')
        ret = func(*args, **kw)
        reporter.oleder.show([_key + ' PRESS',
                              'OLED ' + TRANSLATE[reporter.show_in_oled],
                              'BUZZER ' + TRANSLATE[reporter.show_in_buzzer],
                              ])
        reporter.buzzer.beep(0.1, 1)
        return ret
    return yelling


@introduce
def red():
    if guardor.run_flag or reporter.run_flag:
        print("It's already running, I will restart it")
        reporter.stop()
        guardor.stop()
        time.sleep(1)
    reporter.start()
    guardor.start()
    print(time.strftime('%Y%m%d_%X', time.gmtime()) + "\tStart")


@introduce
def yellow(): 
    reporter.stop()
    if reporter.show_in_oled:
        reporter.show_in_oled = False
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\tNo longer show in oled')
    else:
        reporter.show_in_oled = True
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\tReshow in oled')
    reporter.start()


@introduce
def blue():
    reporter.stop()
    if reporter.show_in_buzzer:
        reporter.show_in_buzzer = False
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\tNo longer show in buzzer')
    else:
        reporter.show_in_buzzer = True
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\tReshow in Buzzer')
    reporter.start()


@introduce
def orange():
    reporter.stop()
    guardor.stop()
    reporter.oleder.cls()
    print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\tAll strop')


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
