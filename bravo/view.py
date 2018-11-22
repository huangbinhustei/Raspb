import os
import time
import sys

from flask import Flask, render_template, request, jsonify
from sqlalchemy import and_
from pyecharts import Line, Page
import picamera

from sr04_video_guard import RECORDOR
from sys_info import *
from data.sheets import *

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(basedir)


app = Flask(__name__)
app.config.update(DEBUG=True)

width=800
height=480

guardor = RECORDOR()


@app.route('/api/guardor')
def api_guardor():
    try:
        cmd = request.args.get('cmd').lower()
        if 'start' == cmd:
            guardor.start()
        elif 'test' == cmd:
            guardor.start(test_mode=True)
        elif 'stop' == cmd:
            guardor.stop()
        else:
            # 不做操作。
            pass
    except:
        # 不做操作。
        cmd = 'nothing'
        pass
    

@app.route('/api/bravo/info')
def api_bravo_info():
    cpu_temp, cpu_percent = get_cpu_info()
    free_ram = get_ram_info()
    free_disk = get_disk_info()
    return jsonify(cpu_temp=cpu_temp,
                   cpu_percent=cpu_percent,
                   free_ram=free_ram,
                   free_disk=free_disk,)


@app.route('/api/zero/info')
def api_zero_info():
    # 调用 zero 的 api 函数
    pass


@app.route('/api/zero/photo')
def api_zero_photo():
    camera = picamera.PiCamera()
    try:
        name = request.args.get('name').lower()
    except:
        name = time.strftime('%Y%m%d_%H%M%S', time.gmtime(time.time() + 28800))
    camera.capture(name + '.jpg')


@app.route("/month")
def last_month():
    # 按天显示
    end = int(time.time())
    start = end - 86400 * 30

    line_cpu, line_space, js_list = group_line_maker(start, end, 'day')

    return render_template(
        "pyecharts.html",
        cpu=line_cpu.render_embed(),
        space=line_space.render_embed(),
        host='https://pyecharts.github.io/assets/js',
        script_list=js_list,
    )


@app.route("/week")
def last_week():
    # 按天显示
    end = int(time.time())
    start = end - 86400 * 8

    line_cpu, line_space, js_list = group_line_maker(start, end, 'day')

    return render_template(
        "pyecharts.html",
        cpu=line_cpu.render_embed(),
        space=line_space.render_embed(),
        host='https://pyecharts.github.io/assets/js',
        script_list=js_list,
    )


@app.route("/day")
def last_day():
    # 按小时显示
    dawn = int(time.time() / 86400) * 86400 - 28800
    end = int(time.time())

    try:
        days = request.args.get('days')
        start = end - 86400 * int(days)
    except:
        start = end - 86400 * 1

    line_cpu, line_space, js_list = group_line_maker(start, end, 'hour')

    return render_template(
        "pyecharts.html",
        cpu=line_cpu.render_embed(),
        space=line_space.render_embed(),
        host='https://pyecharts.github.io/assets/js',
        script_list=js_list,
    )


@app.route("/")
@app.route("/recent")
def recent():
    # dawn = int(time.time() / 86400) * 86400 - 28800
    end = int(time.time())
    # end = 1539100383
    try:
        hours = request.args.get('hours')
        start = end - 3600 * int(hours)
    except:
        start = end - 3600 * 1

    # 按照分钟显示

    line_cpu, line_space, js_list = single_line_maker(start, end)


    return render_template(
        "pyecharts.html",
        cpu=line_cpu.render_embed(),
        space=line_space.render_embed(),
        host='https://pyecharts.github.io/assets/js',
        script_list=js_list,
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0')
