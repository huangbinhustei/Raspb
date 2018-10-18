import os
import time
import sys

from flask import Flask, render_template, request
from sqlalchemy import and_
from pyecharts import Line, Page

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(basedir)
from sys_info import *

app = Flask(__name__)
app.config.update(DEBUG=True)

width=800
height=480


def get_info(start, end):
    records = dict()
    s = DBSession()
    for info in s.query(Info).filter(and_(Info.now >= start,
                                          Info.now <= end)).all():
        records[info.now // 60] = info
    s.close()
    return records


def get_stamp(plot, group_by):
    if 'minute' == group_by:
        return time.strftime('%H:%M', time.gmtime(plot + 28800))
    elif 'hour' == group_by:
        return time.strftime('%d-%H', time.gmtime(plot + 28800 - 3540))
    elif 'day' == group_by:
        return time.strftime('%m%d', time.gmtime(plot + 28800 - 86340))
    else:
        return 'Wrong'


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
                cpu_percents.append(0)
                cpu_temps.append(0)
                free_rams.append(0)
                free_disks.append(0)

        return stamps, cpu_percents, cpu_temps, free_rams, free_disks

    line_cpu = Line(width=width, height=height, title='CPU 监控')
    line_space = Line(width=width, height=height, title='DISK 监控')
    if time.localtime().tm_hour >= 21 or time.localtime().tm_hour <= 6:
        line_cpu.use_theme('dark')
        line_space.use_theme('dark')
    stamps, cpu_percents, cpu_temps, free_rams, free_disks = lining_single()
    line_cpu.add('使用率', stamps, cpu_percents, mark_line=["average"], line_width=2)
    line_cpu.add('温度', stamps, cpu_temps, mark_point=["max"], line_width=2)
    line_space.add('剩余内存', stamps, free_rams, mark_line=["average"], line_width=2)
    line_space.add('剩余磁盘', stamps, free_disks, line_width=2)

    js_list = list(set(line_cpu.get_js_dependencies() + line_space.get_js_dependencies()))

    return line_cpu, line_space, js_list


def group_line_maker(start, end, group_by):
    # 子函数：获取数据
    # 己函数：把数据放到 Line 中

    def lining_grouped():
        records = get_info(start, end)

        stamps = []
        top_list = [[], [], [], []]  # cpu_percents, cpu_temps, free_rams, free_disks
        average_list = [[], [], [], []]  # cpu_percents, cpu_temps, free_rams, free_disks
        bottom_list = [[], [], [], []]  # cpu_percents, cpu_temps, free_rams, free_disks

        tops = [-1000, -1000, -1000, -1000]
        averages = [[], [], [], []]
        bottoms = [1000, 1000, 1000, 1000]

        for i in range(start + 60, end, 60):
            flag = get_stamp(i, group_by)
            if not stamps:
                stamps.append(flag)
                if i // 60 in records:
                    new_info = [records[i // 60].cpu_percent, records[i // 60].cpu_temp, records[i // 60].free_ram,
                                records[i // 60].free_disk]
                    for ind in range(4):
                        tops[ind] = max(tops[ind], new_info[ind])
                        averages[ind].append(new_info[ind])
                        bottoms[ind] = min(bottoms[ind], new_info[ind])
                else:
                    tops = [0, 0, 0, 0]
                    averages = [0, 0, 0, 0]
                    bottoms = [0, 0, 0, 0]
            elif flag != stamps[-1]:
                stamps.append(flag)
                for ind in range(4):
                    top_list[ind].append(tops[ind] if tops[ind] != -1000 else 0)
                    ind_tmp = sum(averages[ind]) / len(averages[ind]) if averages[ind] else 0
                    average_list[ind].append(round(ind_tmp, 1))
                    bottom_list[ind].append(bottoms[ind] if bottoms[ind] != 1000 else 0)
                tops = [-1000, -1000, -1000, -1000]
                averages = [[], [], [], []]
                bottoms = [1000, 1000, 1000, 1000]
            elif i // 60 in records:
                new_info = [records[i // 60].cpu_percent, records[i // 60].cpu_temp, records[i // 60].free_ram,
                            records[i // 60].free_disk]
                for ind in range(4):
                    tops[ind] = max(tops[ind], new_info[ind])
                    averages[ind].append(new_info[ind])
                    bottoms[ind] = min(bottoms[ind], new_info[ind])

        return stamps[1:], top_list, average_list, bottom_list

    line_cpu = Line(width=width, height=height, title='CPU 监控')
    line_space = Line(width=width, height=height, title='DISK 监控')
    if time.localtime().tm_hour >= 21 or time.localtime().tm_hour <= 6:
        line_cpu.use_theme('dark')
        line_space.use_theme('dark')
    stamps, [cpu_percents_top, cpu_temps_top, free_rams_top, free_disks_top], [cpu_percents_average, cpu_temps_average, free_rams_average, free_disks_average], [cpu_percents_bottom, cpu_temps_bottom, free_rams_bottom, free_disks_bottom] = lining_grouped()
    line_cpu.add('使用率峰值', stamps, cpu_percents_top, is_smooth=True, line_width=2)
    line_cpu.add('平均使用率', stamps, cpu_percents_average, is_smooth=True, line_width=2)
    line_cpu.add('温度峰值', stamps, cpu_temps_top, is_smooth=True, mark_line=['max'], line_width=2)
    line_cpu.add('平均温度', stamps, cpu_temps_average, is_smooth=True, line_width=2, legend_top='bottom')
    line_space.add('剩余内存谷值', stamps, free_rams_bottom, is_smooth=True, line_width=2)
    line_space.add('剩余内存均值', stamps, free_rams_average, is_smooth=True, line_width=2)
    line_space.add('剩余磁盘', stamps, free_disks_bottom, is_smooth=True, line_width=2, legend_top='bottom')

    js_list = list(set(line_cpu.get_js_dependencies() + line_space.get_js_dependencies()))

    return line_cpu, line_space, js_list


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
    dawn = int(time.time() / 86400) * 86400 - 28800
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
