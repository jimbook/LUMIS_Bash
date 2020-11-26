import time
from multiprocessing.connection import Connection
import h5py
import numpy as np
import pandas as pd
import dataLayer
from dataLayer.baseCore import *


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


if __name__ == '__main__':
    data = h5Data("data/2020_11_26/tempData_10_27_36.h5",'r').getData(-2)
    countBoard = data[dataLayer._Index[-2:]].groupby(dataLayer._Index[-2]).count()
    vc = countBoard["boardID"].value_counts()
    allCount = vc.sum()
    #print(allCount)
    print(vc)
    print("相对：{}".format(allCount))
    print(vc/allCount)
    #print(vc)
    #print(countBoard.index[countBoard["boardID"] == 1])
    idx = countBoard.index[countBoard["boardID"] == 1].values
    #print(idx)
    nFull = data.set_index("triggerID").loc[idx]
    _abcd = ["a","b","c","d","e","f","g","h"]
    abcd = [str(x) for x in range(10)]
    abcd.extend(_abcd)
    #print(abcd)
    head = ["{}{}".format(x,y) for x in abcd for y in range(10)]
    #print("-".join(head))
    # for i in data[dataLayer._Index[-2:]]:
    #     event = data[dataLayer]
    # triggerID = np.unique(data[dataLayer._Index[-2]].values)
    # data_2 = data.set_index(dataLayer._Index[-2])
    # print(data_2)

    # n = 0
    # while True:
    #     h.flush()
    #     d = h.getData(-1,n)
    #     n += d.shape[0]
    #     print(d)
    #     time.sleep(1)
