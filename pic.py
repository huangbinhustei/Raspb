import os
import sys
import time
import cv2
import psutil
import requests
from picamera import PiCamera
from picamera.array import PiRGBArray
from io import BytesIO


base = '/home/pi/Bxin/Raspb'
sys.path.append(base)
from bxin import *

xml = os.path.join(base, 'haarcascade_frontalface_default.xml')
face_cascade = cv2.CascadeClassifier(xml)
resX = 640
resY = 480
size = (resX, resY)


def get_cpu_info():
    # Return CPU temperature as a character string
    res = os.popen('vcgencmd measure_temp').readline()
    temperature = res.replace('temp=', '').replace("'C\n", "")
    percent = psutil.cpu_percent()
    return temperature, str(percent)


def is_face_in(frame):
    faces = face_cascade.detectMultiScale(
        cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
        scaleFactor=1.15,
        minNeighbors=5,
        minSize=(15, 15),
    )


def recording(msg, doc=False, internet=False):
    print(msg)
    if doc:
        with open(os.path.join(base, 'recording.txt'), 'w') as f:
            f.write(msg)
        
    if internet:
        info = msg.split('\t')
        title = info[0]
        cont = '\n\n'.join(info[1:])
        send_msg(title, cont)


def taking(max=20, limit=True):
    print('开始保护')
    fcount = 0
    big_step = 120
    small_step = 10
    max_temp = 80
    last_save = int(time.time()) - big_step
    safe = True

    with PiCamera() as camera:
        camera.resolution = size
        raw_capture = PiRGBArray(camera, size=size)
        camera.capture(raw_capture, format='bgr')
        raw_capture.truncate(0)
        for frame in camera.capture_continuous(raw_capture, format='bgr', use_video_port=True):
            raw_capture.truncate(0)
            time.sleep(1)
            temperature, percent = get_cpu_info()
            now = int(time.time())
            if float(temperature) >= max_temp:
                recording('\t'.join(['温度太高', time.ctime(), temperature, percent]), doc=True, internet=True)
                exit()
            fcount += 1
            if limit and fcount >= max:
                break
            img = frame.array
            faces = face_cascade.detectMultiScale(
                cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
                scaleFactor=1.15,
                minNeighbors=5,
                minSize=(15, 15),
            )

            if isinstance(faces, tuple):
                if not safe:
                    recording('\t'.join(['人离开了', time.ctime(), temperature, percent]), doc=True)
                    last_save = int(time.time()) - big_step
                    safe = True
                continue
            safe = False
            if now - last_save >= big_step:
                # 距离上次发现人很久
                recording('\t'.join(['第一次发现', time.ctime(), temperature, percent]), doc=True, internet=True)
                for x, y, w, h in faces:
                    cv2.rectangle(img, (x, y), (x + w, y + h), (50, 255, 255), 1)
                cv2.putText(img, time.ctime(), (10, 20), 1, 1, (50, 255, 255), 1, cv2.LINE_AA)
                cv2.imwrite(os.path.join(base, 'Persons', str(now) + '.jpg'), img)
                last_save = now
            elif now - last_save <= small_step:
                # 发现人 n 帧内，连续拍照
                recording('\t'.join(['连续拍照', time.ctime(), temperature, percent]))
                cv2.imwrite(os.path.join(base, 'Persons', str(now) + '.jpg'), img)
            else:
                # 超过了 n 帧，且不足 m 帧，不用拍照了
                recording('\t'.join([str(big_step) + '帧内不拍照', time.ctime(), temperature, percent]))


if __name__ == '__main__':
    taking(limit=False)
