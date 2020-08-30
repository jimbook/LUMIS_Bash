'''
包含一些基础使用的数据对象
'''
import numpy as np
import pandas as pd
import time
from datetime import datetime
import h5py
from dataLayer.constantParameter import _Index
from threading import Lock

# 操作h5文件
class h5Data(object):
    def __init__(self, path: str, mode: str = 'w'):
        self.file = h5py.File(path, mode=mode)
        if mode[0] == 'w':
            self.readMode = False
            self.info = self.file.create_dataset('info', shape=(3,), dtype='S30')
            self.dataGroup = self.file.create_group('data')
            self.SetsIndex = 0
            self.dataIndex = 0
            self.data = self.dataGroup.create_dataset('dataset_{}'.format(self.SetsIndex),
                                                      shape=(5000,38), maxshape=(None,38), dtype='uint16')
        elif mode[0] == 'r':
            self.readMode = True
            self.info = self.file['info']
            self.dataGroup = self.file['data']

    # 添加开始时间
    def startTime(self) ->str:
        if self.readMode:
            return self.info[0]
        else:
            self.start = time.time()
            _s = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.info[0] = _s.encode('ASCII')
            return _s

    # 添加结束时间和总运行时间,并关闭h5文件
    def stopTime(self) ->str:
        if self.readMode:
            return self.info[1]
        else:
            stop = time.time()
            t = stop - self.start
            _s = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.info[1] = _s.encode('ASCII')
            self.info[2] = '{:20.3f}'.format(t).encode('ASCII')
            self.file.close()
            return _s

    # 返回总运行时间
    def totalTime(self) ->float:
        try:
            return float(self.info[2])
        except:
            return 0.

    # 将数据添加到h5数据集中,如果NewSets设置为True则在添加完数据后建立新的数据集
    def addToDataSet(self, value: np.array, NewSets: bool = False):
        # 如果数据集的长度不够，则扩展5000行
        if self.dataIndex + value.shape[0] == self.data.shape[0]:
            self.data.resize(self.data.shape[0] + 5000, axis=0)
        self.data.write_direct(value, source_sel=np.s_[:],dest_sel=np.s_[self.dataIndex:value.shape[0]+self.dataIndex])
        if NewSets:
            self.data.resize(self.dataIndex, axis=0)
            self.SetsIndex += 1
            self.data = self.dataGroup.create_dataset(
                'dataset_{}'.format(self.SetsIndex), shape=(5000,38), maxshape=(None,38),dtype='uint16')
            self.dataIndex = 0
        else:
            self.dataIndex += 1

    # 读取h5文件中的数据
    def getData(self,dataIndex: int) ->pd.DataFrame:
        if self.readMode:
            _n = self.data['dataset_{}'.format(dataIndex)]
            _d = pd.DataFrame(_n[:],columns=_Index,dtype='int64')
            return _d

    # 关闭h5文件流
    def close(self):
        self.file.close()

# 一个包含保护数据线程锁的共享数据对象
class dataStorage(object):
    def __init__(self):
        self.dataLock = Lock()
        self.memoryData = []
        self.diskDataIndex = 0
        self.h5Path = None
        self.status = {}
        self.temp = []
        self.index = 0
#-----------------------添加/清除数据-----------------------------

    # 添加h5文件路径
    def setH5Path(self,path: str):
        self.h5Path = path

    # 向内存中添加数据（将list中的数据依次添加到memoryData的list中）
    def addMeoryData(self,input: list):
        with self.dataLock:
            self.memoryData.extend(input)

    # 当数据开启了一个新的DataSet存储时，调用此函数，清空共享内存
    def resetMeoryData(self):
        with self.dataLock:
            self.temp = self.memoryData[self.index:]
            self.memoryData.clear()
        self.index = 0
        self.diskDataIndex += 1

    # 设置仪器状态信息
    def setStatus(self,status: list):
        '''
        *********INPUT DATA*********
        NAME        LENGTH
        TrigDAC     1
        INDAC       1
        TrigMode    1
        BoardID     1
        TOTAL LENGTH: 4
        *****************************
        :param status: list-one board status information
        :return: None
        '''
        TrigDAC = status[0]
        bias = 29.29 - (255 - (status[1] - 1) / 2) / 63.75
        TrigMode = status[2]
        boardID = status[3]
        with self.dataLock:
            self.status[boardID] = (TrigDAC,bias,TrigMode)

    # 清空共享内存中的数据
    def clear(self):
        with self.dataLock:
            self.memoryData.clear()
            self.status.clear()
            self.temp.clear()
        self.diskDataIndex = 0
        self.h5Path = None
        self.index = 0

#-----------------------获取数据-----------------------------
    # 获取内存中的数据
    def get_memoryData(self):
        with self.dataLock:
            return self.memoryData

    # 获取h5文件中数据集的索引
    def get_diskDataIndex(self):
        return self.diskDataIndex

    # 获取h5文件的路径
    def get_h5Path(self):
        return self.h5Path

    # 获取全部数据
    def get_all(self):
        with self.dataLock:
            return self.memoryData,self.h5Path,self.diskDataIndex

    # 只获取新增数据
    def get_newData(self):
        with self.dataLock:
            length = len(self.memoryData)
            _i = self.index
            print("share memory:new{}--old{}".format(length,_i))
            if length >= self.index:
                self.index = length
                return self.memoryData[_i:],True
            else:
                return self.temp,False

    # 获取状态信息
    def get_status(self):
        with self.dataLock:
            return self.status









