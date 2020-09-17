'''
包含一些基础使用的数据对象
'''
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
import h5py
from dataLayer.constantParameter import _Index
from threading import Lock

# 操作h5文件
class h5Data(object):
    '''├│└
    =========FORMAT OF H5 FILE========
    root
     ├info(group)
     │ ├time(dataSet)
     │ │ ├start time
     │ │ ├stop time
     │ │ └total time
     │ └device_status(dataSet)
     │   ├trigger mode
     │   ├board 0 threshold
     │   ├~~~~~~~
     │   ├board 7 threshold
     │   ├board 0 bias voltage
     │   ├~~~~~
     │   └board 7 bias voltage
     └data(group)
        ├dataset_0(dataSet)
        └~~~~~~~
    '''
    def __init__(self, path: str, mode: str = 'w'):
        '''
        :param path: the path of h5 file
        :param mode: "w" or "r"
        '''
        self.file = h5py.File(path, mode=mode, libver='latest')
        if mode[0] == 'w':
            self.readMode = False
            # 存储信息
            infoGroup = self.file.create_group('info')
            self.timeInfo = infoGroup.create_dataset('time', shape=(3, ), dtype='float64') # 开始时间、结束时间、总运行时间
            self.statusInfo = infoGroup.create_dataset('device_status', shape=(17,), dtype='uint16') # 各个板的状态信息
            self.dataGroup = self.file.create_group('data')
            self.SetsIndex = 0
            self.dataIndex = 0
            self.data = self.dataGroup.create_dataset('dataset_{}'.format(self.SetsIndex),
                                                      shape=(5000,38), maxshape=(None,38), dtype='uint16')
        elif mode[0] == 'r':
            self.readMode = True
            infoGroup = self.file['info']
            self.timeInfo = infoGroup['time']
            self.statusInfo = infoGroup['device_status']
            self.dataGroup = self.file['data']


    # 添加开始时间
    def startTime(self) ->datetime:
        '''
        "w":add start time (now time) to h5 file,and return it
        "r":just return start time (from h5)
        :return: start time
        '''
        if self.readMode:
            start = datetime.fromtimestamp(self.timeInfo[0])
            return start
        else:
            self.start = datetime.now()
            self.timeInfo[0] = self.start.timestamp()
            return self.start

    # 添加结束时间和总运行时间,并关闭h5文件
    def stopTime(self) ->datetime:
        '''
        "w":add stop time (now time) and total running time to h5 file,and return it
        "r":just return stop time (from h5)
        :return: stop time
        '''
        if self.readMode:
            stop = datetime.fromtimestamp(self.timeInfo[1])
            return stop
        else:
            stop = datetime.now()
            t = stop.timestamp() - self.start.timestamp()
            self.timeInfo[1] = stop.timestamp()
            self.timeInfo[2] = t
            self.file.close()
            return stop

    # 返回总运行时间
    def totalTime(self) ->float:
        '''
        "w":raise Exception
        "r": get total running time (from h5)
        :return: total running time
        '''
        return self.timeInfo[2]

    # 返回当前数据
    def getDataIndex(self) -> int:
        if self.readMode:
            i = 0
            for j in self.dataGroup:
                i += 1
            return i
        else:
            return self.dataIndex

    # 录入设备状态信息
    def putDeviceStatus(self,status: dict):
        '''
        "w": write device configuration state to h5 file
        "r": raise Exception
        :param status:dict:key:boardID;value:tuple(threshold, biasVoltage, triggerMode)
        :return:
        '''
        triggerMode = status[0][2]
        self.statusInfo[0] = triggerMode
        for i in range(8):
            t = status.get(i, (0, 0, 0))
            self.statusInfo[i+1] = t[0]
            self.statusInfo[i+9] = t[1]

    # 将数据添加到h5数据集中,如果NewSets设置为True则在添加完数据后建立新的数据集
    def addToDataSet(self, value: np.array, NewSets: bool = False):
        '''
        "w": add data to h5 file
        "r": raise Exception
        :param value: data,type:np.array,dtype:'uint16',shape:(38,)
        :param NewSets: if it set as True,h5 file will create a new data set to contain data
        :return:
        '''
        # 如果数据集的长度不够，则扩展5000行
        if self.dataIndex + value.shape[0] == self.data.shape[0]:
            self.data.resize(self.data.shape[0] + 5000, axis=0)
        self.data.write_direct(value, source_sel=np.s_[:],dest_sel=np.s_[self.dataIndex:value.shape[0]+self.dataIndex])
        if NewSets:
            self.newSets()
        else:
            self.dataIndex += 1

    # 建立新的数据集
    def newSets(self):
        '''
        create a new data set to contain data
        :return:
        '''
        self.data.resize(self.dataIndex, axis=0)
        self.SetsIndex += 1
        self.data = self.dataGroup.create_dataset(
            'dataset_{}'.format(self.SetsIndex), shape=(5000, 38), maxshape=(None, 38), dtype='uint16'
        )
        self.dataIndex = 0

#=====================================================

    # 读取h5文件中的数据
    def getData(self,dataIndex: int) ->pd.DataFrame:
        if self.readMode:
            _n = self.dataGroup['dataset_{}'.format(dataIndex)]
            _d = pd.DataFrame(_n[:],columns=_Index,dtype='int64')
            return _d

    # 获取h5文件中存储的设备状态信息
    def getDeviceStatus(self) -> dict:
        '''
        :return: dict:key:boardID;value:tuple(threshold, bias voltage, trigger mode)
        '''
        status = {}
        triggerMode = self.statusInfo[0]
        for i in range(8):
            threshold = self.statusInfo[i+1]
            biasVoltage = self.statusInfo[i+9]
            if threshold == 0 and biasVoltage == 0:
                break
            else:
                status[i] = (threshold, biasVoltage, triggerMode)
        return status

    # 关闭h5文件流
    def close(self):
        self.data.resize(self.dataIndex,axis=0)
        self.file.close()

# 一个包含保护数据线程锁的共享数据对象
class shareStorage(object):
    def __init__(self):
        self.dataLock = Lock() # 数据锁
        self.memoryData = []    # 共享数据存储
        self.diskDataIndex = 0  # 当前在磁盘中h5文件分的sets数量
        self.h5Path = None  # h5文件的地址
        self.status = {}    # 当前各板子的状态
        self.temp = []      # 当切换sets清空数据后，将GUI还未从共享内存中获取的数据暂时存储
        self.index = 0      # GUI获取数据的指针
#-----------------------添加/清除数据-----------------------------

    # 添加h5文件路径
    def setH5Path(self,path: str):
        self.h5Path = path

    # 向内存中添加数据（将list中的数据依次添加到memoryData的list中）
    def addMemoryData(self,input: list):
        with self.dataLock:
            self.memoryData.extend(input)

    # 当数据开启了一个新的DataSet存储时，调用此函数，清空共享内存
    def resetMemoryData(self):
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









