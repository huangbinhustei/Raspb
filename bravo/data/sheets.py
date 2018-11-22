import os
import sys
from sqlalchemy import Column, Float, String, Integer, DateTime, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


basedir = os.path.abspath(os.path.dirname(__file__))
Base = declarative_base()
engine = create_engine('sqlite:///' + os.path.join(basedir, "sys_info.db"))
DBSession = sessionmaker(bind=engine)


class Info(Base):
    __tablename__ = 'Info'
    now = Column(Integer(), primary_key=True)
    device = Column(Integer())  # {0:bravo, 1:zero, 2:alpha}
    cpu_percent = Column(Float())
    cpu_temp = Column(Float())
    free_ram = Column(Float())
    free_disk = Column(Float())


def pre_create():
    # 创建表
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    try:
        pre_create()
    except:
        pass
