import os
import sys
from sqlalchemy import Column, Float, String, Integer, DateTime, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


basedir = os.path.abspath(os.path.dirname(__file__))
Base = declarative_base()
engine = create_engine('sqlite:///' + os.path.join(basedir, "bravo.db"))
DBSession = sessionmaker(bind=engine)


class Info(Base):
    __tablename__ = 'Info'
    now = Column(Integer(), primary_key=True)
    barvo_cpu_percent = Column(Float())
    barvo_cpu_temp = Column(Float())
    barvo_free_ram = Column(Float())
    barvo_free_disk = Column(Float())
    zero_cpu_temp = Column(Float())
    zero_free_ram = Column(Float())
    zero_free_disk = Column(Float())
    alpha_cpu_percent = Column(Float())
    alpha_cpu_temp = Column(Float())
    alpha_free_ram = Column(Float())
    alpha_free_disk = Column(Float())


class Action(Base):
    __tablename__ = 'Action'
    now = Column(Integer(), primary_key=True)
    device = Column(Integer())  # {0:bravo, 1:zero, 2:alpha}
    action_type = Column(String())  # {0:guardor, 1:lapse, 2:photo}
    action = Column(String())  # {0:start, 1:stop, 2:stop, -1:没有改变}


def pre_create():
    # 创建表
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    try:
        pre_create()
    except:
        pass
