import os
import sys
import time
import threading

import picamera
from flask import Flask, render_template, request, jsonify


basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, os.path.pardir))
from bxin import face, FangTang, qiniu_put
from ioy import RGB
from feature.lapsy import LAPSE

app = Flask(__name__)
# app.config.update()
rgb = RGB()
lapse = LAPSE()
dvalue = Dvalue()


@app.route('/api/lapse')
def api_lapse():
    cmd = request.args.get('cmd', default=False)
    if 'start' == cmd:
        if lapse.running:
            return jsonify(errorcode=1, msg='已经在进行中了')
        else:
            gap = request.args.get('gap', default=False)
            cap = request.args.get('cap', default=False)
            gap_value = int(gap) if gap else 60
            cap_value = int(cap) if cap else 9999999999
            print(gap, cap, gap_value, cap_value)
            lapse.start(gap=gap_value, cap=cap_value)
            return jsonify(errorcode=0, gap=gap, cap=cap, start_time=time.ctime())
    elif 'stop' == cmd:
        lapse.stop()
        return jsonify(errorcode=0, records=str(lapse.frames))
    else:
        return jsonify(errorcode=-1, command='unknown command', status=lapse.running)


@app.route('/api/dvaluy')
def api_dvaluy():
    cmd = request.args.get('cmd', default=False)
    if 'start' == cmd:
        if dvalue.running:
            return jsonify(errorcode=1, msg='已经在进行中了')
        else:
            gap = request.args.get('gap', default=False)
            cap = request.args.get('cap', default=False)
            gap_value = int(gap) if gap else 60
            cap_value = int(cap) if cap else 9999999999
            print(gap, cap, gap_value, cap_value)
            dvalue.start(gap=gap_value, cap=cap_value)
            return jsonify(errorcode=0, gap=gap, cap=cap, start_time=time.ctime())
    elif 'stop' == cmd:
        dvalue.stop()
        return jsonify(errorcode=0, records=str(dvalue.frames))
    else:
        return jsonify(errorcode=-1, command='unknown command', status=dvalue.running)


@app.route('/api/info')
def api_info():
    file_cpu_temp = os.popen('vcgencmd measure_temp').readline()
    cpu_temp = float(file_cpu_temp.replace('temp=', '').replace("'C\n", ""))

    file_ram = os.popen('free')
    free_ram = file_ram.readlines()[1].split()
    free_ram = round(int(free_ram[3]) / 1024, 1)

    file_sd = os.popen("df -h /")
    free_disk = file_sd.readlines()[1].split()
    free_disk =  float(free_disk[3].replace('G', ''))

    return jsonify(cpu_temp=cpu_temp,
                   free_ram=free_ram,
                   free_disk=free_disk,)


@app.route('/api/rgb')
def api_rgb():
    cmd = request.args.get('cmd', default='Nothing').lower()
    color = (request.args.get('r', default='200'),
             request.args.get('g', default='200'),
             request.args.get('b', default='200'),
            )
    color_value = [int(c) for c in color]
    if 'breath' == cmd:
        rgb.breath(tinct=color_value, loops=1)
        return jsonify(errorcode=0, command=cmd, color=' | '.join(color))
    elif 'color' == cmd:
        rgb.color(*color_value)
        return jsonify(errorcode=0, command=cmd, color=' | '.join(color))
    else:
        return jsonify(errorcode=-1, command='unknown command', color=' | '.join(color))


@app.route('/api/photo')
def api_photo():
    # todo:文件夹权限不对
    name = request.args.get('name', default=time.strftime('%Y%m%d_%H%M%S', time.gmtime(time.time() + 28800))).lower()
    if os.path.exists(os.path.join(basedir, name + '.jpg')):
        return jsonify(error_code=-1,
                   msg='文件已经存在',)
    with picamera.PiCamera() as camera:
        camera.resolution = (1920, 1080)
        camera.capture(name + '.jpg')
    return jsonify(error_code=0,
                   name=name + '.jpg',)


@app.route('/')
def help():
    return render_template(
        "index.html")


if __name__ == '__main__':
    # app.run(host='0.0.0.0', debug=True)
    app.run(host='0.0.0.0')
