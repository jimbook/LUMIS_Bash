import numpy as np
import h5py
import time
import pandas as pd
from datetime import datetime, timedelta
from dataLayer.baseCore import h5Data
from collections import  Counter
import dataLayer
import asyncio
def newBinary():
    with open('testData/binaryData/DAC360_0902_2249-0903_1102.dat','rb') as file:
        buff = file.read()
        header = 0
        j = 0
        while True:
            try:
                print('='*5,j,'='*5)
                header = buff.index(b'\x0f\xff\xfe\xee\xfe\xee', header)
                for i in range(10):
                    header = buff.index(b'\xfe\xee\xfe\xee',header + 4)
                    print(header,buff[header-6:header+4].hex('-'))
                print('='*13)
                j += 1
            except:
                break
    with open('testData/binaryData/tempBinary_0','wb') as file:
        file.write(buff[:4741068+200])#4741068

def l():
    h = h5Data('data/2020_09_16/tempData_14_33_59.h5','r')
    d = h.getData(0)
    print(d)
    h.close()

async def task(name, num):
    try:
        print(name,"start")
        await asyncio.sleep(0.1)
        #time.sleep(1)
        print(name,'stop')
        return num
    except asyncio.CancelledError:
        print(name,"cancel")
        return num

async def m():
    taskList = []
    for i in range(10):
        _task = asyncio.create_task(task("task_{}".format(i),i))
        taskList.append(_task)
    #time.sleep(2)
    await asyncio.sleep(0)
    taskList[-1].cancel()
    await asyncio.sleep(0.5)
    for i in taskList:
        try:
            print(i.result())
        except:
            print('error')
#asyncio.run(m())
import threading
def threadTask(_b: threading.Barrier,index: int):
    print('task_{}'.format(index),'start')
    time.sleep(3)
    _b.wait()
    time.sleep(index/10)
    print('task_{}'.format(index),'stop')

def threadTest():
    taskList = []
    b = threading.Barrier(5)
    for i in range(5):
        _task = threading.Thread(target=threadTask,args=(b, i))
        _task.start()
        time.sleep(0.01)

def binaryCheck(path: str):
    with open(path, 'rb') as f:
        try:
            buff = f.read()
            h = buff.index(b'\xfe\xee\xfe\xee')
            while True:
                print(buff[h-6:h+12].hex('-'))
                with open('testData/temporary/txtBinary.txt','a+') as t:
                    t.write(buff[h-6:h+12].hex('-'))
                    t.write('\n')
                h = buff.index(b'\xfe\xee\xfe\xee', h + 2)
        except:
            print('end')

if __name__ == '__main__':
    import os
    file = h5Data('./data/2020_10_25/tempData_17_03_07.h5','r')
    file = h5Data('./testData/h5Data/tempData_10.22_21_38_13.h5', 'r')
    def count(input: np.array):
        return pd.DataFrame(dict(Counter(input)),index=[0])
    data = file.getData(0)
    board = data[dataLayer._Index[-1]].values
    triggerID = data[dataLayer._Index[-2]].values
    count1 = count(triggerID)
    print(count1.T)
    print(data[data[dataLayer._Index[-2]] == 11])
    output = count(count1.values[0]).sort_index(1)
    print(output)
