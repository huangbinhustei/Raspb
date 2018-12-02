import os
import time
import sys
import requests

import redis


basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, os.path.pardir))

from base.Feature.sys_info import get_cpu_temp, get_cpu_percent, get_ram_info, get_disk_info

zeroy = "http://192.168.50.42:5000"


def connect():
    try:
        pool = redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True)
        return True, redis.Redis(connection_pool=pool) 
    except:
        print('请检查 Redis 是否打开')
        return False, False


def sys_tasker():
    now = str(int(time.time()))
    cpu_temp = get_cpu_temp()
    cpu_percent = get_cpu_percent()
    free_ram = get_ram_info()
    free_disk = get_disk_info()
    try:
        response = requests.get(zeroy + '/api/info')
        if 200 == response.status_code:
            zero_cpu_temp = response.json()['cpu_temp']
            zero_free_ram = response.json()['free_ram']
            zero_free_disk = response.json()['free_disk']
        else:
            zero_cpu_temp, zero_free_ram, zero_free_disk = 0, 0, 0
    except:
        zero_cpu_temp, zero_free_ram, zero_free_disk = 0, 0, 0

    flag, rdb = connect()
    if flag:
        rdb.hmset(now, {
            'cpu_temp': cpu_temp,
            'cpu_percent': cpu_percent,
            'free_ram': free_ram,
            'free_disk': free_disk,
            'zero_cpu_temp': zero_cpu_temp,
            'zero_free_ram': zero_free_ram,
            'zero_free_disk': zero_free_disk })


def shower():
    flag, rdb = connect()
    if flag:
        for key in rdb.keys():
            for k, v in rdb.hgetall(key).items():
                print('\t'.join([key, k, v]))


if __name__ == '__main__':
    sys_tasker()
    shower()
