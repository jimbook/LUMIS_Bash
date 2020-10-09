import time
from multiprocessing.connection import Connection
import h5py
import numpy as np
import pandas as pd


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
print('temptest')
import dataFactory

if __name__ == '__main__':
    d = {'l':1,'a':2}
    print('l' in d)

    # n = 0
    # while True:
    #     h.flush()
    #     d = h.getData(-1,n)
    #     n += d.shape[0]
    #     print(d)
    #     time.sleep(1)

