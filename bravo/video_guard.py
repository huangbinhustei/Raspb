# -*- coding: utf-8 -*-
import os
import sys
import time
import threading
import base64
import queue

import cv2
from picamera import PiCamera, Color
from picamera.array import PiRGBArray


basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, os.path.pardir))
from bxin import face, FangTang, qiniu_put
from ioy import SR04, SG90


class RECORDOR(SR04, FangTang):
    def __init__(self, size=(1280, 1024), safe_range=(175, 230), video_length=6, test_mode=False):
        SR04.__init__(self)
        FangTang.__init__(self)
        self.running = False
        self.size = size
        assert safe_range[1] > safe_range[0]
        self.safe_range = (0, 99999999) if test_mode else safe_range
        self.video_length = video_length
        
    def _run(self):
        with PiCamera() as camera:
            camera.resolution = self.size
            raw_capture = PiRGBArray(camera, size=self.size)
            camera.capture(raw_capture, format='bgr')
            raw_capture.truncate(0)
            for frame in camera.capture_continuous(raw_capture, format='bgr', use_video_port=True):
                raw_capture.truncate(0)
                distance = self.detect()
                if self.safe_range[0] < distance < self.safe_range[1]:
                    print('Safe：' + str(distance))
                    time.sleep(1)
                else:
                    stamp = time.gmtime(time.time() + 28800)
                    print(time.strftime('%Y-%m-%d %H:%M:%S', stamp) + '\t有人' + ' @ ' + str(distance) + 'cm')
                    
                    # camera.start_recording(time.strftime('%Y%m%d%H%M%S', stamp) + '.h264')
                    # camera.wait_recording(self.video_length)
                    # camera.stop_recording()

                    
                    camera.framerate = 24
                    camera.start_preview()
                    # camera.annotate_background = Color('black')
                    camera.annotate_text_size = 16
                    camera.annotate_frame_num = True
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
                    time.sleep(60 - self.video_length)

                if not self.running:
                    break
        print('停止保护')

    def start(self):
        self.running = True
        t1 = threading.Thread(target=self._run)
        t1.start()

    def stop(self):
        self.running = False


# concurrency = 6
# xml = os.path.join(basedir, 'haarcascade_frontalface_default.xml')
# face_cascade = cv2.CascadeClassifier(xml)
# task = queue.Queue(maxsize=concurrency)


def is_family(buf, door=(60, 30)):
    b64s = str(base64.b64encode(buf), 'utf-8')
    res = face.search(b64s, 'BASE64', 'Famaly', {'quality_control': 'LOW'})
    if 0 == res['error_code']:
        tmp = res['result']['user_list'][0]
        ret = tmp['score']
        if ret >= door[0]:
            return 0, tmp['user_id'] + ': ' + str(int(ret))
        elif ret >= door[1]:
            return 1, tmp['user_id'] + ': ' + str(int(ret))
        else:
            return 2, tmp['user_id'] + ': ' + str(int(ret))
    elif res['error_code'] in (223114, 222202, 222203, 222205, 222206):
        # 图片模糊、没有识别到人、网络错误等，都暂不保存图片。
        return 0, res['error_msg']
    else:
        return 0, res['error_msg']




if __name__ == '__main__':
    # reporter = RECORDOR(test_mode=True)
    reporter = RECORDOR()
    reporter.start()
    print('started')