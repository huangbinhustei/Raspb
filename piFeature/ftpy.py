import os
import sys
import time
import base64
import threading
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray


from ftplib import FTP


def ftp_connect():
    ftp_server = '192.168.50.1'
    username = 'huangyiwei'
    password = 'binhuang'
    ftp = FTP()
    ftp.set_debuglevel(2)
    ftp.connect(ftp_server, 21)
    ftp.login(username, password)
    return ftp


def 


def uploading():
    pass

# basedir = os.path.abspath(os.path.dirname(__file__))
# sys.path.append(os.path.join(basedir, os.path.pardir, os.path.pardir))
# from binxin.bxin import *
# sys.path.append(os.path.join(basedir, os.path.pardir))
# from base.RasGpio.ioy import RGB


# def take_photo(name='timing', resolution=(1280, 1024), path='Saving'):
#     if os.path.exists(os.path.join(path, name + '.jpg')):
#         return {
#             'status': False,
#             'error_code': -1,
#             'msg': '文件已经存在',
#         }

#     with PiCamera() as camera:
#         camera.resolution = resolution
#         camera.start_preview()

#         # camera.shutter_speed = 5000000
#         camera.iso = 100

#         if 'timing' == name:
#             name = os.path.join(path, time.strftime('%Y%m%d_%H%M%S', time.gmtime(time.time() + 28800)).lower())

#         camera.capture(f'{name}_{str(i)}.jpg')
    
#     return {
#             'status': True,
#             'error_code': 0,
#             'msg': name + '.jpg',
#         }


# def continuous_shooting(maxcount=30 * 30, gap=5, span=86400, resolution=(800, 600), path='Continuous'):
#     with PiCamera() as camera:
#         camera.resolution = resolution
#         camera.start_preview()
#         end = time.time() + span
#         count = 0
#         while count < maxcount and time.time() <= end:
#             name = os.path.join(path, time.strftime('%Y%m%d_%H%M%S', time.gmtime(time.time() + 28800)).lower())
#             camera.capture(name + '.jpg')
#             time.sleep(gap)
#             count += 1


# class DHashPhoto:
#     def __init__(self, resolution=(640, 480), path='DHash'):
#         self.resolution = resolution
#         self.path = path
#         self.running = False

#     def _run(self, gap, sapn):
#         pass
        


#     def start(self, gap=5, span=600):
#         self.running = True
#         t1 = threading.Thread(target=self._run, args=(gap, span))
#         t1.start()

#     def stop(self):
#         self.running = False


    

# class Dvalue:
#     def __init__(self, send_pin=25):
#         self.running = False
#         self.records = 0

#     def saving(self, frame):
#         _, img = cv2.imencode('.jpg', frame)
#         name = time.strftime('%Y%m%d_%H%M%S', time.gmtime(time.time() + 28800)) + '.jpg'
#         file_path = os.path.join(basedir, name)
#         with open(file_path, 'wb') as f:
#             f.write(img)

#     def __gray_line(self, frame):
#         simple_size = (8, 6)
#         simple_length = simple_size[0] * simple_size[1]
#         frame = cv2.resize(frame, simple_size)
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
#         grayline = gray[0].reshape(1, simple_length)[0]
#         door = sum(grayline)//simple_length
#         fingerprint = [1 if i >= door else 0 for i in grayline]
#         return fingerprint
            
#     def _run(self, last, gap):
#         print('开始保护')
#         last_model = False    
#         with PiCamera() as camera:
#             camera.resolution = (640, 480)
#             raw_capture = PiRGBArray(camera, size=(640, 480))
#             camera.capture(raw_capture, format='bgr')
#             raw_capture.truncate(0)
#             for frame in camera.capture_continuous(raw_capture, format='bgr', use_video_port=True):
#                 if not self.running:
#                     break
#                 raw_capture.truncate(0)
#                 frame = frame.array

#                 model = self.__gray_line(frame)
#                 if not last_model:
#                     last_model = model
#                     continue
#                 diff_last = sum([0 if x[0]==x[1] else 1 for x in zip(last_model, model)])

#                 if diff_last <= 5:
#                     # 和上一帧一样
#                     print(' | '.join(['一致', time.ctime(), str(diff_last), str(self.running)]))
#                     time.sleep(1)
#                 else:
#                     # 和上一帧不一样。
#                     last_model = model
#                     print(' | '.join(['大不一样', time.ctime(), str(diff_last)]))
#                     self.msg(diff_last, (200, 200, 0))
#                     time_stamp = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time() + 28800))
#                     camera.start_recording(time_stamp + '.h264')
#                     camera.wait_recording(last)
#                     camera.stop_recording()
#                     time.sleep(gap-last)
#                     self.records += 1
#         print('停止保护')
#         try:
#             camera.stop_recording()
#         except:
#             pass

#     def start(self, last=6, gap=60):
#         self.running = True
#         t1 = threading.Thread(target=self._run, args=(last, gap))
#         t1.start()

#     def stop(self):
#         self.running = False


if __name__ == '__main__':
    take_photo()
    # continuous_shooting()
