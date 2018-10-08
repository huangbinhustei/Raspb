import os
import sys
import psutil
from sqlalchemy import Column, Float, String, Integer, DateTime, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(basedir)
from bxin import *


Base = declarative_base()
engine = create_engine('sqlite:///' + os.path.join(basedir, "sys_info.db"))
DBSession = sessionmaker(bind=engine)


class Info(Base):
    __tablename__ = 'Info'
    now = Column(Integer(), primary_key=True)
    cpu_percent = Column(Float())
    cpu_temp = Column(Float())
    free_ram = Column(Float())
    free_disk = Column(Float())


def pre_create():
    # 创建表
    Base.metadata.create_all(engine)


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
    s.add(new_info)
    s.commit()
    s.close()
