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
from ioy import SR501, RGB


class Z:
    def __init__(self):
        self.rgb = [RGB(), RGB(r=26, g=19, b=13)]
        self.sr = SR501()
        self.flag = False
        self.size = (640, 480)

    def _run(self):
        last = 3
        self.sr.start()
        while self.flag:
            with PiCamera() as camera:
                camera.resolution = self.size
                raw_capture = PiRGBArray(camera, size=self.size)
                camera.capture(raw_capture, format='bgr')
                raw_capture.truncate(0)
                for frame in camera.capture_continuous(raw_capture, format='bgr', use_video_port=True):
                    raw_capture.truncate(0)
                    if self.sr.output:
                        stamp = time.gmtime(time.time() + 28800)
                        time_stamp = time.strftime('%Y%m%d%H%M%S', stamp)
                        print(time.strftime('%H:%M:%S', stamp) + '\t有人')
                        camera.start_recording(time_stamp + '.h264')
                        camera.wait_recording(last)
                        camera.stop_recording()
                        time.sleep(60-last)
                    else:
                        # print("time.strftime('%Y%m%d%H%M%S')\t没有发现人")
                        time.sleep(1)
        print('停止保护')
        self.sr.stop()

    def run(self):
        self.flag = True
        t1 = threading.Thread(target=self._run)
        t1.start()


if __name__ == '__main__':
    guard = Z()
    guard.run()

