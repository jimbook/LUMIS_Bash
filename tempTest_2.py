import time
from threading import Thread
from multiprocessing import Pipe, Manager, Process
from multiprocessing.connection import Connection
import h5py
import numpy as np
import pandas as pd
from dataLayer.baseCore import h5Data
def threadTask_0(s: Connection,name: str):
    while True:
        s.send(name)
        time.sleep(1)
        print("{} recv:{}".format(name, s.recv()))
        time.sleep(1)

def threadTask_1(s: Connection,name: str):
    while True:
        print("{} recv:{}".format(name, s.recv()))
        s.send(name)

def task_0():
    h = h5py.File('testData/h5Data/temH5_01.h5',mode='w',libver='latest')
    d = h.create_dataset('data',shape=(500,3),dtype='int64')
    h.swmr_mode = True
    for i in range(500):
        n = np.arange(i,i+3).astype('int64')
        d[i] = n
        h.flush()
        time.sleep(0.2)

def task_1():
    h = h5py.File('testData/h5Data/temH5_01.h5',mode='r',libver='latest',swmr=True)
    d = h['data']
    while True:
        df = pd.DataFrame(d[:], columns=[1,2,3])
        print(df)
        time.sleep(1)

if __name__ == '__main__':
    # p = Process(target=task_0,args=())
    # p.start()
    # time.sleep(3)
    # task_1()
    h = h5Data('data/2020_09_22/tempData_11_05_25.h5', 'r')
    d = h.getData()
    print(d)