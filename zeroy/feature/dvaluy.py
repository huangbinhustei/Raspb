import os
import sys
import time
import base64
import threading
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
from rpi_rf import RFDevice


basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, os.path.pardir, os.path.pardir))
from bxin import *
from ioy import RGB


class Dvalue:
    def __init__(self, send_pin=25):
        self.rgb = RGB()
        self.running = False
        self.rf = RFDevice(send_pin)
        self.rf.enable_tx()

    
    def _msg(self, info, protocol, pulselength, tinct):
        for _ in range(5):
            self.rf.tx_code(info, protocol, pulselength)
        self.rf.tx_code(100, protocol, pulselength)

    def msg(self, info, tinct):
        tf = threading.Thread(target=self._msg, args=(info, None, None, tinct))
        tf.start()

    def saving(self, frame):
        _, img = cv2.imencode('.jpg', frame)
        name = time.strftime('%Y%m%d_%H%M%S', time.gmtime(time.time() + 28800)) + '.jpg'
        file_path = os.path.join(basedir, name)
        with open(file_path, 'wb') as f:
            f.write(img)

    def __gray_line(self, frame):
        simple_size = (8, 6)
        simple_length = simple_size[0] * simple_size[1]
        frame = cv2.resize(frame, simple_size)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
        grayline = gray[0].reshape(1, simple_length)[0]
        door = sum(grayline)//simple_length
        fingerprint = [1 if i >= door else 0 for i in grayline]
        return fingerprint
            
    def _run(self, last=6, gap=12):
        print('开始保护')
        last_model = False    
        while self.running:
            with PiCamera() as camera:
                camera.resolution = (640, 480)
                raw_capture = PiRGBArray(camera, size=(640, 480))
                camera.capture(raw_capture, format='bgr')
                raw_capture.truncate(0)
                for frame in camera.capture_continuous(raw_capture, format='bgr', use_video_port=True):
                    raw_capture.truncate(0)
                    frame = frame.array

                    model = self.__gray_line(frame)
                    if not last_model:
                        last_model = model
                        continue
                    diff_last = sum([0 if x[0]==x[1] else 1 for x in zip(last_model, model)])

                    if diff_last <= 5:
                        # 和上一帧一样
                        print(' | '.join(['一致', time.ctime(), str(diff_last)]))
                        time.sleep(1)
                    else:
                        # 和上一帧不一样。
                        last_model = model
                        print(' | '.join(['大不一样', time.ctime(), str(diff_last)]))

                        self.msg(diff_last, (200, 200, 0))
                        self.rgb.breath(tinct=(200, 200, 200), loops=3)
                        
                        time_stamp = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time() + 28800))
                        camera.start_recording(time_stamp + '.h264')
                        camera.wait_recording(last)
                        camera.stop_recording()
                        time.sleep(gap-last)
        print('停止保护')

    def start(self):
        self.running = True
        t1 = threading.Thread(target=self._run)
        t1.start()

    def stop(self):
        self.running = False


if __name__ == '__main__':
    dvalue = Dvalue()
    dvalue.start()
