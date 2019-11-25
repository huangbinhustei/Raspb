import os
import sys
import psutil
import time
from sheets import DBSession, pre_create, Info


def get_cpu_info():
    # Return CPU temperature as a float
    res = os.popen('vcgencmd measure_temp').readline()
    temperature = res.replace('temp=', '').replace("'C\n", "")
    percent = psutil.cpu_percent()
    return float(temperature), percent


def get_ram_info():
    # Return RAM information (unit=kb) in a list
    # Index 0: total RAM
    # Index 1: used RAM
    # Index 2: free RAM
    # 这里只返回可用内存
    p = os.popen('free')
    info = p.readlines()[1].split()
    return round(int(info[3]) / 1024, 1)


def get_disk_info():
    # Return information about disk space as a list (unit included)
    # Index 0: total disk space
    # Index 1: used disk space
    # Index 2: remaining disk space
    # Index 3: percentage of disk used
    # 返回剩余空间(单位是 G)
    p = os.popen("df -h /")
    info = p.readlines()[1].split()
    return float(info[3].replace('G', ''))


if __name__ == '__main__':
    s = DBSession()
    pre_create()
    cpu_temp, cpu_percent = get_cpu_info()
    free_ram = get_ram_info()
    free_disk = get_disk_info()
    now = int(time.time())

    new_info = Info(
        now=now,
        cpu_percent=cpu_percent,
        cpu_temp=cpu_temp,
        free_ram=free_ram,
        free_disk=free_disk)
    print(now,':', cpu_temp)
    # s.add(new_info)
    # s.commit()
    # s.close()
