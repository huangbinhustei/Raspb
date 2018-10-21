# -- coding: utf-8 --
import time
from functools import wraps

import RPi.GPIO as GPIO
from photo_guard import REPORTER, GUARDOR

TRANSLATE = ('OFF', 'ON')


def introduce(func):
    @wraps(func)
    def yelling(*args, **kw):
        stamp = time.strftime('%Y%m%d_%X', time.gmtime())
        _key = func.__name__
        print(stamp + '\t' + _key + 'PRESS')
        reporter.oleder.show([_key + 'PRESS',
                              'OLED ' + TRANSLATE[reporter.show_in_oled],
                              'BUZZER ' + TRANSLATE[reporter.show_in_buzzer],
                              ])
        reporter.buzzer.beep(0.1, 1)
        ret = func(*args, **kw)
        return ret
    return yelling


keys_pin = [6, 13, 19, 26]
keys_name = ['Red', 'Yellow', 'Blue', 'Orange']


@introduce
def red():
    # print(time.strftime('%Y%m%d_%X', time.gmtime()) + "\tRed PRESS")
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
    # print(time.strftime('%Y%m%d_%X', time.gmtime()) + "\tYellow PRESS")
    reporter.stop()
    if reporter.show_in_oled:
        reporter.show_in_oled = False
        # reporter.oleder.show([time.strftime('%Y%m%d_%X', time.gmtime()), 'OLED OFF'])
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\tNo longer show in oled')
    else:
        reporter.show_in_oled = True
        # reporter.oleder.show([time.strftime('%Y%m%d_%X', time.gmtime()), 'OLED ON'])
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\tReshow in oled')
    reporter.start()


@introduce
def blue():
    # print(time.strftime('%Y%m%d_%X', time.gmtime()) + "\tBlue PRESS")
    reporter.stop()
    if reporter.show_in_buzzer:
        reporter.show_in_buzzer = False
        # reporter.oleder.show([time.strftime('%Y%m%d_%X', time.gmtime()), 'Buzzer OFF'])
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\tNo longer show in buzzer')
    else:
        reporter.show_in_buzzer = True
        # reporter.oleder.show([time.strftime('%Y%m%d_%X', time.gmtime()), 'Buzzer ON'])
        print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\tReshow in Buzzer')
    reporter.start()


@introduce
def orange():
    # print(time.strftime('%Y%m%d_%X', time.gmtime()) + "\tOrange PRESS")
    reporter.stop()
    guardor.stop()
    reporter.oleder.cls()
    print(time.strftime('%Y%m%d_%X', time.gmtime()) + '\tAll strop')


key_handle = {'Red': red,
            'Yellow': yellow,
            'Blue': blue,
            'Orange': orange,
    }


def key_interrupt(key):
    # print("KEY %s PRESS" % keys_name[keys_pin.index(key)])

    target = keys_name[keys_pin.index(key)]
    key_handle[target]()

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

