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
sys.path.append(basedir)
from bxin import *

xml = os.path.join(basedir, 'haarcascade_frontalface_default.xml')
face_cascade = cv2.CascadeClassifier(xml)
size = (960, 720)
last_push = time.time(), 0

task = queue.Queue(maxsize=15)


def dealing():
    def is_family(buf, safe=75, normal=50):
        b64s = str(base64.b64encode(buf), 'utf-8')
        res = face.search(b64s, 'BASE64', 'Famaly', {'quality_control': 'LOW'})
        if 0 == res['error_code']:
            tmp = res['result']['user_list'][0]
            ret = tmp['score']
            if ret >= safe:
                return 0, tmp['user_id'] + ':' + str(round(ret, 1))
            elif ret >= normal:
                return 1, tmp['user_id'] + ':' + str(round(ret, 1))
            else:
                return 2, tmp['user_id'] + ':' + str(round(ret, 1))
        elif res['error_code'] in (223114, 222202, 222203, 222205, 222206):
            # 图片模糊、没有识别到人、网络错误等，都暂不保存图片。
            return 0, res['error_msg']
        else:
            return 1, res['error_msg']

    def recording(tool_id, msg, buf):
        """
        tool_id == 0：写日志
        tool_id == 1：写日志 + 保存 + 发消息
        tool_id == 2：写日志 + 保存 + 发消息 + 上云
        """
        print('\t'.join(msg))
        with open(os.path.join(basedir, 'Persons', 'recording.txt'), 'a') as f:
            f.write('\t'.join(msg) + '\n')

        if tool_id >= 1:
            name = time.strftime('%Y%m%d_%H%M%S', time.gmtime(stamp + 28800)) + '.jpg'
            file_path = os.path.join(basedir, 'Persons', name)
            with open(file_path, 'wb') as f:
                f.write(buf)

        global last_push
        if tool_id == last_push[1] and time.time() - last_push[0] <= 60:
            # 相同的推送原因， 60 秒内只推送一次。推送原因不同时不受限制。
            pass
        else:
            title = msg[1]
            cont = '\n\n'.join(msg)
            send_msg(title, cont)
            last_push = time.time(), tool_id

        if tool_id >= 2:
            print('%s\t本来应该上云的，暂时不上', name)
            # qiniu_put(file_path, name, bucket_name='bxin', timeout=3600)

    while True:
        buf, stamp = task.get()
        tool_id, info = is_family(buf)
        msg = [time.strftime('%Y%m%d_%X', time.gmtime(stamp + 28800)), info]
        recording(tool_id, msg, buf)
        time.sleep(0.5)


def taking():
    def is_face_in(frame):
        return face_cascade.detectMultiScale(
            cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
            scaleFactor=1.15,
            minNeighbors=5,
            minSize=(15, 15),
        )

    def drawing(img, faces):
        color = (50, 255, 255)
        for x, y, w, h in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 1)
        # cv2.rectangle(img, (0, 0), (180, 25), (0, 0, 0), -1)
        # name = info
        # cv2.putText(img, name, (10, 20), 1, 1, color, 1, cv2.LINE_AA)

    print('开始保护')
    with PiCamera() as camera:
        camera.resolution = size
        raw_capture = PiRGBArray(camera, size=size)
        camera.capture(raw_capture, format='bgr')
        raw_capture.truncate(0)
        for frame in camera.capture_continuous(raw_capture, format='bgr', use_video_port=True):
            raw_capture.truncate(0)

            img = frame.array
            faces = is_face_in(img)

            if isinstance(faces, tuple):
                # 没有发现人脸
                time.sleep(1)
            else:
                drawing(img, faces)
                _, buf = cv2.imencode('.jpg', img)
                try:
                    task.put_nowait([buf, time.time()])
                except Queue.Full:
                    pass

if __name__ == '__main__':
    t1 = threading.Thread(target=dealing)
    t1.start()
    taking()
