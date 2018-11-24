import time
import threading
import picamera


class LAPSE:
    def __init__(self):
        self.frames = 0
        self.running = False

    def __run(self, gap, cap):
        print(gap, cap, -1)
        while self.running and self.frames <= cap:
            name = time.strftime('%Y%m%d_%H%M%S', time.gmtime(time.time() + 28800))
            print(name)
            with picamera.PiCamera() as camera:
                camera.resolution = (1280, 720)
                camera.capture(name + '.jpg')
            self.frames += 1
            time.sleep(gap - int(time.time()) % gap)
        print('停止延时摄影，累计拍摄 ' + str(self.frames) + ' 张')
        self.frames = 0

    def start(self, gap, cap):
        self.running = True
        t1 = threading.Thread(target=self.__run, args=(gap, cap))
        t1.start()

    def stop(self):
        self.running = False