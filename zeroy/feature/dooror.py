import os
import sys
import time
import base64
import threading
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray


basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, os.path.pardir))
from bxin import *
from ioy import RGB, SR04
from rpi_rf import RFDevice


class Door:
    def __init__(self, trig=23, echo=24, send_pin=25):
        self.rf = RFDevice(send_pin)
        self.rf.enable_tx()
        self.sr04 = SR04(trig, echo)
        self.rgb = RGB()
        self.last_distance = 0

    def msg(self, info, protocol=None,  pulselength=None):
        self.rf.tx_code(info, protocol, pulselength)

    def quit(self):
        self.rf.cleanup()

    def run(self, with_RGB=True):
        while True:
            distance = int(self.sr04.detect())
            '''
            400 以上：R
            0~50：G
            50~100：B
            100~150：RG
            150~200：RB
            200~400：RGB
            '''
            succeed = True
            if distance <= 50:
                r, g, b = 0, 150, 0
            elif distance <= 100:
                r, g, b = 0, 0, 150
            elif distance <= 150:
                r, g, b = 150, 150, 0
            elif distance <= 200:
                r, g, b = 150, 0, 150
            elif distance <= 400:
                r, g, b = 100, 100, 100
            else:
                r, g, b = 150, 0, 0
                succeed = False
            info = '距离：' if succeed else '测距失败：'
            print(info + str(distance))
            self.msg(distance if succeed else 99999)
            if -15 < self.last_distance - distance < 15:
                time.sleep(1)
            else:
                self.rgb.breath(tinct=(r, g, b), loops=1, t=0.01, wait=True)
                self.last_distance = distance
            

if __name__ == '__main__':
    guard = Door()
    guard.run()
