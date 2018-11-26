import os
import time
import sys

from flask import Flask, render_template, request, jsonify
import requests
from sqlalchemy import and_
from pyecharts import Line, Page
import picamera


basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, os.path.pardir))
from base.Feature.sr04_video_guard import RECORDOR
from base.Feature.sys_info import get_cpu_temp, get_cpu_percent, get_ram_info, get_disk_info
from base.Data.sheets import *

zeroy = "http://192.168.50.42:5000"

app = Flask(__name__)
app.config.update(DEBUG=True)

width=800
height=480

guardor = RECORDOR()


@app.route('/api/guardor')
def api_guardor():
    cmd = request.args.get('cmd', default="Nothing").lower()
    if 'start' == cmd:
        guardor.start()
        return jsonify(errorcode=0, command='start', status=guardor.running)
    elif 'test' == cmd:
        guardor.start(test_mode=True)
        return jsonify(errorcode=0, command='test', status=guardor.running)
    elif 'stop' == cmd:
        guardor.stop()
        return jsonify(errorcode=0, command='stop', status=guardor.running)
    else:
        # 不做操作。
        return jsonify(errorcode=-1, command='unknown command', status=guardor.running)
    

@app.route('/api/info')
def api_info():
    return jsonify(cpu_temp=get_cpu_temp(),
                   cpu_percent=get_cpu_percent(),
                   free_ram=get_ram_info(),
                   free_disk=get_disk_info(),)


@app.route('/api/photo')
def api_photo():
    camera = picamera.PiCamera()
    camera.resolution = (1920, 1080)
    try:
        name = request.args.get('name').lower()
    except:
        name = time.strftime('%Y%m%d_%H%M%S', time.gmtime(time.time() + 28800))
    camera.capture(name + '.jpg')
    return jsonify(error_code=0,
                   name=name + '.jpg',)


@app.route('/api/zero/info')
def api_zero_info():
    # 调用 zero 的 api 函数
    try:
        response = requests.get(zeroy + '/api/info')
        if 200 == response.status_code:
            return jsonify(response.json())
        else:
            return jsonify(errorcode=response.status_code, http_error_code=response.status_code)
    except:
        return jsonify(errorcode=-1, msg='检查树莓派 Zero 是否启动了 flask')


@app.route('/api/zero/rgb')
def api_zero_rgb():
    # 调用 zero 的 api 函数
    cmd = request.args.get('cmd', default='breath')
    r = request.args.get('r', default=None)
    g = request.args.get('g', default=None)
    b = request.args.get('b', default=None)    
    try:
        response = requests.get(zeroy + '/api/rgb', params={"cmd":cmd, "r":r, "g":g, "b":b})
        if 200 == response.status_code:
            return jsonify(response.json())
        else:
            return jsonify(errorcode=response.status_code, http_error_code=response.status_code)
    except:
        return jsonify(errorcode=-1, msg='检查树莓派 Zero 是否启动了 flask')



@app.route('/api/zero/photo')
def api_zero_photo():
    # 调用 zero 的 api 函数
    name = request.args.get('name', default=None)
    try:
        response = requests.get(zeroy + '/api/photo', params={"name":name})
        if 200 == response.status_code:
            return jsonify(response.json())
        else:
            return jsonify(errorcode=response.status_code, http_error_code=response.status_code)
    except:
        return jsonify(errorcode=-1, msg='检查树莓派 Zero 是否启动了 flask')


@app.route('/api/zero/lapse')
def api_zero_lapse():
    # 调用 zero 的 api 函数
    cmd = request.args.get('cmd', default=None)
    gap = request.args.get('gap', default=None)
    cap = request.args.get('cap', default=None)
    try:
        response = requests.get(zeroy + '/api/lapse', params={'cmd': cmd, 'gap':gap, 'cap':cap})
        if 200 == response.status_code:
            return jsonify(response.json())
        else:
            return jsonify(errorcode=response.status_code, http_error_code=response.status_code)
    except:
        return jsonify(errorcode=-1, msg='检查树莓派 Zero 是否启动了 flask')


@app.route('/api/zero/dvalue')
def api_zero_dvalue():
    # 调用 zero 的 api 函数
    cmd = request.args.get('cmd', default=None)
    gap = request.args.get('gap', default=None)
    last = request.args.get('last', default=None)
    try:
        response = requests.get(zeroy + '/api/dvalue', params={'cmd': cmd, 'gap':gap, 'last':last})
        if 200 == response.status_code:
            return jsonify(response.json())
        else:
            return jsonify(errorcode=response.status_code, http_error_code=response.status_code)
    except:
        return jsonify(errorcode=-1, msg='检查树莓派 Zero 是否启动了 flask')


def get_info(start, end):
    records = dict()
    s = DBSession()
    for info in s.query(Info).filter(and_(Info.now >= start,
                                          Info.now <= end)).all():
        records[info.now // 60] = info
    s.close()
    return records


def single_line_maker(start, end):
    # 子函数：获取数据
    # 己函数：把数据放到 Line 中

    def lining_single():
        records = get_info(start, end)

        stamps = []
        cpu_percents = []
        cpu_temps = []
        free_rams = []
        free_disks = []
        for i in range(start + 60, end, 60):
            stamps.append(time.strftime('%H:%M', time.gmtime(i + 28800)))
            if i // 60 in records:
                cpu_percents.append(records[i // 60].cpu_percent)
                cpu_temps.append(records[i // 60].cpu_temp)
                free_rams.append(records[i // 60].free_ram)
                free_disks.append(records[i // 60].free_disk)
            else:
                cpu_percents.append('')
                cpu_temps.append('')
                free_rams.append('')
                free_disks.append('')

        return stamps, cpu_percents, cpu_temps, free_rams, free_disks

    line_cpu = Line(width=width, height=height, title='CPU 监控')
    line_space = Line(width=width, height=height, title='DISK 监控')
    if time.localtime().tm_hour >= 21 or time.localtime().tm_hour <= 6:
        line_cpu.use_theme('dark')
        line_space.use_theme('dark')
    stamps, cpu_percents, cpu_temps, free_rams, free_disks = lining_single()
    line_cpu.add('使用率', stamps, cpu_percents, mark_line=["average"], line_width=2, is_smooth=True)
    line_cpu.add('温度', stamps, cpu_temps, mark_point=["max"], line_width=2, is_smooth=True)
    line_space.add('剩余内存', stamps, free_rams, mark_line=["average"], line_width=2, is_smooth=True)
    line_space.add('剩余磁盘', stamps, free_disks, line_width=2, is_smooth=True)

    js_list = list(set(line_cpu.get_js_dependencies() + line_space.get_js_dependencies()))

    return line_cpu, line_space, js_list


def group_line_maker(start, end, group_by):
    # 子函数：获取数据
    # 己函数：把数据放到 Line 中
    step = {
        'minute': 2,
        'hour': 3540,
        'day': 86340
    }[group_by]

    stamps = []
    max_cpu_percent = []
    ave_cpu_percent = []
    max_cpu_temp = []
    ave_cpu_temp = []
    min_ram = []
    ave_ram = []
    sd = []
    records = get_info(start, end)

    for i in range(start + 60, end, step + 60):
        stamps.append(time.strftime('%d %H:%M', time.gmtime(i + 28800 - step)))
        this_hour = [v for r, v in records.items() if v.now > i and v.now < i + step]
        if not this_hour:
            max_cpu_percent.append(0)
            ave_cpu_percent.append(0)
            max_cpu_temp.append(0)
            ave_cpu_temp.append(0)
            min_ram.append(0)
            ave_ram.append(0)
            sd.append(0)
        else:
            max_cpu_percent.append(max([x.cpu_percent for x in this_hour]))
            ave_cpu_percent.append(sum([x.cpu_percent for x in this_hour])/len(this_hour))
            max_cpu_temp.append(max([x.cpu_temp for x in this_hour]))
            ave_cpu_temp.append(sum([x.cpu_temp for x in this_hour])/len(this_hour))
            min_ram.append(min([x.free_ram for x in this_hour]))
            ave_ram.append(sum([x.free_ram for x in this_hour])/len(this_hour))
            sd.append(min([x.cpu_temp for x in this_hour]))

    line_cpu = Line(width=width, height=height, title='CPU 监控')
    line_space = Line(width=width, height=height, title='DISK 监控')
    if time.localtime().tm_hour >= 21 or time.localtime().tm_hour <= 6:
        line_cpu.use_theme('dark')
        line_space.use_theme('dark')
    line_cpu.add('使用率峰值', stamps, max_cpu_percent, is_smooth=True, line_width=2)
    line_cpu.add('平均使用率', stamps, ave_cpu_percent, is_smooth=True, line_width=2)
    line_cpu.add('温度峰值', stamps, max_cpu_temp, is_smooth=True, mark_line=['max'], line_width=2)
    line_cpu.add('平均温度', stamps, ave_cpu_temp, is_smooth=True, line_width=2, legend_top='bottom')
    line_space.add('剩余内存谷值', stamps, min_ram, is_smooth=True, line_width=2)
    line_space.add('剩余内存均值', stamps, ave_ram, is_smooth=True, line_width=2)
    line_space.add('剩余磁盘', stamps, sd, is_smooth=True, line_width=2, legend_top='bottom')

    js_list = list(set(line_cpu.get_js_dependencies() + line_space.get_js_dependencies()))

    return line_cpu, line_space, js_list


@app.route("/info/month")
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


@app.route("/info/week")
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


@app.route("/info/day")
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


@app.route("/info")
@app.route("/info/recent")
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


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0')
