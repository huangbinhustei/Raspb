# -*- coding: utf-8 -*-
import os
import sys
import time
import threading
import base64
import queue

import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray


basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, os.path.pardir))
from bxin import face, FangTang, qiniu_put
from rainbow import OLED, BUZZER
from ioy import RGB


xml = os.path.join(basedir, 'haarcascade_frontalface_default.xml')
face_cascade = cv2.CascadeClassifier(xml)
task = queue.Queue(maxsize=3)


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


class REPORTER(OLED, BUZZER):
    def __init__(self, show_in_oled=True, show_in_buzzer=False):
        # NetWorker.__init__(self)
        OLED.__init__(self)
        BUZZER.__init__(self)
        self.net_msg = FangTang()
        self.show_in_oled = show_in_oled
        self.show_in_buzzer = show_in_buzzer
        self.run_flag = False
        self.door = [60, 30]    # score of safe and nromal

    def recording(self, tool_id, msg, buf, stamp):
        """
        tool_id == 0：写日志
        tool_id == 1：写日志 + 保存 + 发消息
        tool_id == 2：写日志 + 保存 + 发消息 + 上云
        """
        print('\t'.join(msg) + ' | ' + str(time.ctime()))
        if self.show_in_oled:
            msg_in_oled = msg
            msg_in_oled[0] = msg[0].split('_')[1]
            self.scroll(' '.join(msg_in_oled))
        with open(os.path.join(basedir, 'Persons', 'recording.txt'), 'a') as f:
            f.write('\t'.join(msg) + '\n')

        if tool_id >= 1:
            name = time.strftime('%Y%m%d_%H%M%S', time.gmtime(stamp + 28800)) + '.jpg'
            file_path = os.path.join(basedir, 'Persons', name)
            with open(file_path, 'wb') as f:
                f.write(buf)
            self.net_msg.send(msg[1], '\n\n'.join(msg), tool_id)

        if tool_id >= 2:
            print('%s:Should sent to QINIU, delayed', name)
            # qiniu_put(file_path, name, bucket_name='bxin', timeout=3600)

    def _running(self):
        while self.run_flag:
            buf, stamp = task.get()
            tool_id, info = is_family(buf, self.door)
            msg = [time.strftime('%Y%m%d_%X', time.gmtime(stamp + 28800)), info]
            self.recording(tool_id, msg, buf, stamp)
        print('Reporter stopped')

    def start(self, thdcount=1):
        self.run_flag = True
        t = []
        for i in range(thdcount):
            t.append(threading.Thread(target=self._running))
        for j in t:
            j.start()

    def stop(self):
        self.run_flag = False


class RGB_REPORTER(RGB):
    def __init__(self):
        RGB.__init__(self)
        self.net_msg = FangTang()
        self.run_flag = False
        self.door = [60, 30]    # score of safe and nromal

    def recording(self, tool_id, msg, buf, stamp):
        """
        tool_id == 0：写日志
        tool_id == 1：写日志 + 保存 + 发消息
        tool_id == 2：写日志 + 保存 + 发消息 + 上云
        """
        print(str(tool_id) + ':' + '\t'.join(msg) + ' | ' + str(time.ctime()))
        with open(os.path.join(basedir, 'Persons', 'recording.txt'), 'a') as f:
            f.write('\t'.join(msg) + '\n')

        if tool_id == 0:
            self.breath(tinct=(0, 200, 0), loops=1)
        else:
            name = time.strftime('%Y%m%d_%H%M%S', time.gmtime(stamp + 28800)) + '.jpg'
            file_path = os.path.join(basedir, 'Persons', name)
            with open(file_path, 'wb') as f:
                f.write(buf)
            self.net_msg.send(msg[1], '\n\n'.join(msg), tool_id)
            if tool_id == 1:
                self.breath(tinct=(0, 200, 0), loops=1)
            else:
                self.breath(tinct=(100, 50, 50), loops=1)
    
    def _running(self):
        while self.run_flag:
            buf, stamp = task.get()
            tool_id, info = is_family(buf, self.door)
            msg = [time.strftime('%Y%m%d_%X', time.gmtime(stamp + 28800)), info]
            self.recording(tool_id, msg, buf, stamp)
        print('Reporter stopped')

    def start(self, thdcount=1):
        self.run_flag = True
        t1 = threading.Thread(target=self._running)
        t1.start()

    def stop(self):
        self.run_flag = False


class GUARDOR:
    def __init__(self):
        self.size = (640, 480)
        self.rate = 4
        self.run_flag = False
        
    def __is_face_in(self, frame):
        frame = cv2.resize(frame, (self.size[0]//self.rate, self.size[1]//self.rate))
        faces = face_cascade.detectMultiScale(
            cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
            scaleFactor=1.15,
            minNeighbors=5,
            minSize=(10, 10),
        )
        return faces

    def __drawing(self, img, faces):
        color = (50, 255, 255)
        for x, y, w, h in faces:
            x *= self.rate
            y *= self.rate
            w *= self.rate
            h *= self.rate
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 1)

    def _running(self):
        with PiCamera() as camera:
            camera.resolution = self.size
            raw_capture = PiRGBArray(camera, size=self.size)
            camera.capture(raw_capture, format='bgr')
            raw_capture.truncate(0)
            for frame in camera.capture_continuous(raw_capture, format='bgr', use_video_port=True):
                raw_capture.truncate(0)

                img = frame.array
                faces = self.__is_face_in(img)
                if isinstance(faces, tuple):
                    # 没有发现人脸
                    # print(time.strftime('%Y%m%d_%X', time.gmtime()) + "\tHavn't found sbd")
                    # time.sleep(1)
                    pass
                else:
                    self.__drawing(img, faces)
                    _, buf = cv2.imencode('.jpg', img)
                    try:
                        task.put_nowait([buf, time.time()])
                    except:
                        pass
                if not self.run_flag:
                    break
        print('Guard stopped')
    
    def start(self):
        self.run_flag = True
        t1 = threading.Thread(target=self._running)
        t1.start()
    
    def stop(self):
        self.run_flag = False


if __name__ == '__main__':
    reporter = RGB_REPORTER()
    guardor = GUARDOR()
    reporter.start()
    guardor.start()
    print('started')