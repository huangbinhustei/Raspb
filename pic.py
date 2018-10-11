import os
import sys
import time
import cv2
import psutil
import base64
from picamera import PiCamera
from picamera.array import PiRGBArray


basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(basedir)
from bxin import *

xml = os.path.join(basedir, 'haarcascade_frontalface_default.xml')
face_cascade = cv2.CascadeClassifier(xml)
resX = 640
resY = 480
size = (resX, resY)

last_push = 0


def get_cpu_temperature():
    # Return CPU temperature as a character string
    res = os.popen('vcgencmd measure_temp').readline()
    temperature = res.replace('temp=', '').replace("'C\n", "")
    return temperature


def is_face_in(frame):
    return face_cascade.detectMultiScale(
        cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
        scaleFactor=1.15,
        minNeighbors=5,
        minSize=(15, 15),
    )


def is_famaly(buf, safe=75, normal=50):
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
    else:
        return 1, res['error_msg']


def recording(tool_id, msg, img):
    print('\t'.join(msg))
    with open(os.path.join(basedir, 'recording.txt'), 'a') as f:
        f.write('\t'.join(msg) + '\n')
    # tool_id == 0：只写日志

    if tool_id >= 1:
        # 写日志 + 保存 + 报警，不上云
        name = time.strftime('%Y%m%d_%H%M%S') + '.jpg'
        file_path = os.path.join(basedir, 'Persons', name)
        cv2.imwrite(file_path, img)
        global last_push
        title = '\t'.join(msg)
        cont = '\n\n'.join(msg)
        if time.time() - last_push >= 60:
            send_msg(title, cont)
            last_push = time.time()
    if tool_id >= 2:
        print('%s\t本来应该上云的，暂时不上', name)
        # qiniu_put(file_path, name, bucket_name='bxin', timeout=3600)


def drawing(img, faces, info):
    color = (50, 255, 255)
    for x, y, w, h in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 1)
    cv2.rectangle(img, (0, 0), (180, 25), (0, 0, 0), -1)
    name = info
    cv2.putText(img, name, (10, 20), 1, 1, color, 1, cv2.LINE_AA)


def taking():
    print('开始保护')
    big_step = 120
    small_step = 10
    big = int(time.time())
    small = int(time.time()) + small_step



    with PiCamera() as camera:
        camera.resolution = size
        raw_capture = PiRGBArray(camera, size=size)
        camera.capture(raw_capture, format='bgr')
        raw_capture.truncate(0)
        for frame in camera.capture_continuous(raw_capture, format='bgr', use_video_port=True):
            raw_capture.truncate(0)
            temperature = get_cpu_temperature()

            msg = [time.strftime('%Y%m%d_%X')]
            now = int(time.time())

            img = frame.array
            faces = is_face_in(img)

            if isinstance(faces, tuple):
                # 如果没有发现人脸
                time.sleep(1)
            elif small <= now <= big:
                msg.append(str(big_step) + '秒内不拍照')
                recording(0, msg, img)
            else:
                if now > big:
                    # 距离上次发现人很久，重置时间窗口
                    small = now + small_step
                    big = now + big_step
                _, buf = cv2.imencode('.jpg', img)
                tool_id, info = is_famaly(buf)
                msg.append(info)
                drawing(img, faces, info)
                recording(tool_id, msg, img)


if __name__ == '__main__':
    taking()
