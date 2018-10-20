import os
import sys
import time
import base64

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


def is_face_in(frame):
    return face_cascade.detectMultiScale(
        cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
        scaleFactor=1.15,
        minNeighbors=5,
        minSize=(15, 15),
    )


def taking():
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
                continue
            else:
                time_stamp = time.strftime('%Y%m%d%H%M%S')
                camera.start_recording(time_stamp + '.h264')
                camera.wait_recording(6)
                camera.stop_recording()
                _, buf = cv2.imencode('.jpg', img)
                tool_id, info = is_family(buf)

                global last_push
                if tool_id == last_push[1] and time.time() - last_push[0] <= 60:
                    # 相同的推送原因， 60 秒内只推送一次。推送原因不同时不受限制。
                    pass
                else:
                    send_msg(info, time_stamp)
                    last_push = time.time(), tool_id


if __name__ == '__main__':
    taking()
