import os
import sys
import time
import cv2
import psutil
import requests
import base64
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
    return face_cascade.detectMultiScale(
        cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
        scaleFactor=1.15,
        minNeighbors=5,
        minSize=(15, 15),
    )


def is_famaly(path):
    with open(path, 'rb') as f:
        b64s = str(base64.b64encode(f.read()), 'utf-8')
    res = face.search(b64s, 'BASE64', 'Famaly', {'max_user_num': 3})
    if res['error_code'] != 0:
        print(res)
        return False
    pr = ''
    door = 0
    for info in res['result']['user_list']:
        pr += info['user_id'] + ':' + str(round(info['score'],1)) + '%\t' 
        door = max(door, info['score'])

    print(pr)
    if door >= 80:
        return True
    else:
        return False


def recording(msg, doc=False, internet=False):
    print(msg)
    if doc:
        with open(os.path.join(base, 'recording.txt'), 'a') as f:
            f.write(msg + '\n')
        
    if internet:
        info = msg.split('\t')
        title = info[0]
        cont = '\n\n'.join(info[1:])
        send_msg(title, cont)


def drawing(img, faces):
    for x, y, w, h in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (50, 255, 255), 1)
    cv2.putText(img, time.strftime('%Y%m%d_%X'), (10, 20), 1, 1, (50, 255, 255), 1, cv2.LINE_AA)


def taking():
    print('开始保护')
    big_step = 120
    small_step = 10
    big = int(time.time()) + big_step
    small = int(time.time()) + small_step
    
    max_temp = 80

    with PiCamera() as camera:
        camera.resolution = size
        raw_capture = PiRGBArray(camera, size=size)
        camera.capture(raw_capture, format='bgr')
        raw_capture.truncate(0)
        for frame in camera.capture_continuous(raw_capture, format='bgr', use_video_port=True):
            raw_capture.truncate(0)
            temperature, percent = get_cpu_info()

            msg = [time.strftime('%Y%m%d_%X'), temperature, percent]
            now = int(time.time())
            if float(temperature) >= max_temp:
                msg.append('温度太高')
                recording('\t'.join(msg), doc=True, internet=True)
                exit()
            img = frame.array
            faces = is_face_in(img)

            if isinstance(faces, tuple):
                # 如果没有发现人脸
                time.sleep(1)
                continue

            if small <= now <= big: 
                msg.append(str(big_step) + '秒内不拍照')
                recording('\t'.join(msg), doc=True)
            else:
                if now > big:
                    # 距离上次发现人很久，重置时间窗口
                    small = now + small_step
                    big = now + big_step
                drawing(img, faces)
                file_path = os.path.join(base, 'Persons', str(now) + '.jpg')
                cv2.imwrite(file_path, img)
                if is_famaly(file_path):
                    msg.append('欢迎回家')
                else:
                    msg.append('发现有人')
                    qiniu_put(file_path, time.strftime('%Y%m%d_%X'), bucket_name='bxin', timeout=3600)
                recording('\t'.join(msg), doc=True, internet=True)


if __name__ == '__main__':
    taking()
