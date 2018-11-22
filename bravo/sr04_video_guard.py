# -*- coding: utf-8 -*-
import os
import sys
import time
import threading

from picamera import PiCamera, Color


basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, os.path.pardir))
from bxin import face, FangTang, qiniu_put
from ioy import SR04, SG90


class RECORDOR(SR04, FangTang):
    def __init__(self, size=(1280, 1024), safe_range=(175, 230), video_length=6):
        SR04.__init__(self)
        FangTang.__init__(self)
        self.running = False
        self.size = size
        assert safe_range[1] > safe_range[0]
        self.safe_range = safe_range
        self.video_length = video_length
        
    def _test(self):
        while self.running:
            distance = self.detect()
            stamp = time.gmtime(time.time() + 28800)
            print(time.strftime('%Y-%m-%d %H:%M:%S', stamp) + ' 测试模式：' + str(distance) + 'cm')
        print('停止测试')
    
    def _run(self):
        flag = False
        with PiCamera() as camera:
            camera.resolution = self.size
            while self.running:
                distance = self.detect()
                stamp = time.gmtime(time.time() + 28800)

                if self.safe_range[0] < distance < self.safe_range[1]:
                    flag = False
                    print(time.strftime('%Y-%m-%d %H:%M:%S', stamp) + ' 安全：' + str(distance) + 'cm')
                    time.sleep(1)
                elif distance > self.safe_range[1] and not flag:
                    flag = True
                    print(time.strftime('%Y-%m-%d %H:%M:%S', stamp) + ' 疑似安全：' + str(distance) + 'cm')
                    time.sleep(1)
                else:
                    print(time.strftime('%Y-%m-%d %H:%M:%S', stamp) + ' 发现人：' + str(distance) + 'cm')

                    camera.framerate = 24
                    camera.start_preview()
                    # camera.annotate_background = Color('black')
                    # camera.annotate_frame_num = True
                    camera.annotate_text_size = 16
                    camera.annotate_text = time.strftime('%Y-%m-%d %H:%M:%S', stamp)
                    camera.start_recording(time.strftime('%Y%m%d%H%M%S', stamp) + '.h264')
                    start = time.time()
                    while time.time() - start <= self.video_length:
                        camera.annotate_text = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() + 28800))
                        camera.wait_recording(0.2)
                    camera.stop_recording()

                    content = time.strftime('%Y-%m-%d %H:%M:%S', stamp).split(' ')
                    content.append(str(distance) + 'cm')
                    self.send('发现有人', '\n\n'.join(content))
                    time.sleep(300 - self.video_length)
            print('停止保护')

    def start(self, test_mode=False):
        self.running = True
        if test_mode:
            print('测试模式')
            t1 = threading.Thread(target=self._test)
        else:
            print('正式模式')
            t1 = threading.Thread(target=self._run)
        t1.start()

    def stop(self):
        self.running = False


if __name__ == '__main__':
    reporter = RECORDOR()
    reporter.start()
    print('started')
