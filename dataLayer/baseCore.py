'''
包含一些基础使用的数据对象
'''
import numpy as np
import pandas as pd
from datetime import datetime
import h5py
from dataLayer import _Index

__all__ = ['h5Data','shareStorage']

# 操作h5文件
class h5Data(object):
    '''├│└
    =========FORMAT OF H5 FILE========
    root
     ├info(group)
     │ ├time(dataset)
     │ │ ├start time
     │ │ ├stop time
     │ │ └total time
     │ └device_status(dataset)
     │   ├trigger mode
     │   ├board 0 threshold
     │   ├~~~~~~~
     │   ├board 7 threshold
     │   ├board 0 bias voltage
     │   ├~~~~~
     │   └board 7 bias voltage
     └dataGroup(group)
        ├data(dataSet)
        │ └data
        └index(dataSet)
          └index
    '''
    def __init__(self, path: str, mode: str = 'w'):
        '''
        :param path: the path of h5 file
        :param mode: "w" or "r"
        内部参数：
            file:h5文件
            readMode:是否是读模式
            SetsIndex:数据集的索引
            dataIndex:数据集的数据索引
        ==========dataset==========
            timeInfo:'time'
            statusInfo:'device_status'

            data:'data',数据
            index:'index'-----数据存储结构：为线性数组，第一个数据(索引为0)为当前数据总行数，
                        之后的每一个都是triggerID置零时的索引(第一个triggerID为0时的索引)
                        index的shape和重置次数对应
        '''
        if mode[0] == 'w':
            self.file = h5py.File(path, mode=mode, libver='latest')
            self.readMode = False
            # 写模式单独参数
            self.dataIndex = 0 # 当前写到第几行
            self.setsIndex = 0 # 当前存在几次triggerID置零
            # 存储信息
            infoGroup = self.file.create_group('info') # 信息组
            self.timeInfo = infoGroup.create_dataset('time', shape=(3, ), dtype='float64') # 开始时间、结束时间、总运行时间
            self.statusInfo = infoGroup.create_dataset('device_status', shape=(17,), dtype='uint16') # 各个板的状态信息
            # 数据信息
            dataGroup = self.file.create_group('dataGroup')  # 数据组
            self.data = dataGroup.create_dataset('data', shape=(5000,39), maxshape=(None,39), dtype='uint16')
            self.index = dataGroup.create_dataset('index', shape=(1,), maxshape=(None,), dtype='int64')
            # 设置为single writer multiply reader 模式
            self.file.swmr_mode = True
        elif mode[0] == 'r':
            self.file = h5py.File(path, mode=mode, libver='latest', swmr=True)
            self.readMode = True
            # 存储信息
            infoGroup = self.file['info']
            self.timeInfo = infoGroup['time']
            self.statusInfo = infoGroup['device_status']
            # 数据信息
            dataGroup = self.file['dataGroup']
            self.data = dataGroup['data']
            self.index = dataGroup['index']

    #===========信息==========
    # 添加开始时间
    def startTime(self) -> datetime:
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
    def stopTime(self) -> datetime:
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
            self.close()
            return stop

    # 返回总运行时间
    def totalTime(self) -> float:
        '''
        "w":raise Exception
        "r": get total running time (from h5)
        :return: total running time
        '''
        return self.timeInfo[2]

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

    # 获取h5文件中存储的设备状态信息
    def getDeviceStatus(self) -> dict:
        '''
        :return: dict:key:boardID;value:tuple(threshold, bias voltage, trigger mode)
        '''
        status = {}
        triggerMode = self.statusInfo[0]
        for i in range(8):
            threshold = self.statusInfo[i + 1]
            biasVoltage = self.statusInfo[i + 9]
            if threshold == 0 and biasVoltage == 0:
                break
            else:
                status[i] = (threshold, biasVoltage, triggerMode)
        return status

    #===============数据=================
    # 将数据添加到h5数据集中
    def addToDataSet(self, value: np.array):
        '''
        "w": add data to h5 file
        "r": raise Exception
        :param value: data,type:np.array,dtype:'uint16',shape:(n,39)
        :param NewSets: if it set as True,h5 file will create a new data set to contain data
        :return:
        '''
        # 如果数据集的长度不够，则扩展5000行
        if self.dataIndex + value.shape[0] <= self.data.shape[0]:
            self.data.resize(self.data.shape[0] + 5000, axis=0)
        self.data.write_direct(value, source_sel=np.s_[:],dest_sel=np.s_[self.dataIndex:value.shape[0]+self.dataIndex])
        self.dataIndex += value.shape[0]
        self.index[0] = self.dataIndex

    # 读取h5文件中的数据
    def getData(self, index: int = -1, startIndex: int = 0, dtype = 'int64') -> pd.DataFrame:
        '''
        read data in h5 file
        :param index: When the index greater than or equal to 0, the corresponding set of data will be returned.
        when the index equal to -1,all the data will be returned.
        when the index equal to -2,all the data will be returned and the triggerID in returned data has been accumulated.
        :param startIndex: data will be returned from the startIndex
        :return:
        '''
        if index + 1 > self.index.shape[0] or index < -2:
            raise ValueError('index({}) out of range (-2-{})'.format(index, self.index.shape[0] - 1))
        if startIndex > self.index[0]:
            raise ValueError('startIndex({}) out of range (0-{})'.format(startIndex, self.index[0]))
        # ========特殊索引========
        if index == -1:
            set = self.data[startIndex:self.index[0]]
            _d = pd.DataFrame(set, columns=_Index, dtype=dtype)
            return _d
        elif index == -2:
            _d = pd.DataFrame(columns=_Index, dtype=dtype)
            for i in range(self.index.shape[0]):
                _s = self.getData(i,startIndex=startIndex)
                _s['triggerID'] = _s['triggerID'] + i * 65535
                _d =_d.append(_s, ignore_index=True)
            return _d
        # ========普通索引========
        if index == 0:      #选择第一个数据集时
            if self.index.shape[0] == 1:
                stop = self.index[0]
            else:
                stop = self.index[1]
            if startIndex >= stop:
                _d = pd.DataFrame(columns=_Index, dtype=dtype)
            else:
                set = np.empty((stop - startIndex, 39), dtype='uint16')
                self.data.read_direct(set, source_sel=np.s_[startIndex:stop], dest_sel=np.s_[:])
                _d = pd.DataFrame(set, columns=_Index, dtype=dtype)
        elif index + 1 == self.index.shape[0]:      # 选择最后一个数据集时
            stop = self.index[0]
            start = self.index[index]
            if startIndex >= stop:
                _d = pd.DataFrame(columns=_Index, dtype=dtype)
            elif startIndex < start:
                set = np.empty((stop - start, 39), dtype='uint16')
                self.data.read_direct(set, source_sel=np.s_[start:stop], dest_sel=np.s_[:])
                _d = pd.DataFrame(set, columns=_Index, dtype=dtype)
            else:
                set = np.empty((stop - startIndex, 39), dtype='uint16')
                self.data.read_direct(set, source_sel=np.s_[startIndex:stop], dest_sel=np.s_[:])
                _d = pd.DataFrame(set, columns=_Index, dtype=dtype)
        else:       # 选择中间数据集时
            # 当判断到此时，index比self.index.shape[0]至少小2，比最大索引小1，index+1不会超出边界
            start = self.index[index]
            stop = self.index[index+1]
            if startIndex >= stop:
                _d = pd.DataFrame(columns=_Index, dtype=dtype)
            elif startIndex < start:
                set = np.empty((stop - start, 39), dtype='uint16')
                self.data.read_direct(set, source_sel=np.s_[start:stop], dest_sel=np.s_[:])
                _d = pd.DataFrame(set, columns=_Index, dtype=dtype)
            else:
                set = np.empty((stop - startIndex, 39), dtype='uint16')
                self.data.read_direct(set, source_sel=np.s_[startIndex:stop], dest_sel=np.s_[:])
                _d = pd.DataFrame(set, columns=_Index, dtype=dtype)
        return _d

    #==============内部=============
    # 获取triggerID重置次数
    def getSetsIndex(self) -> int:
        return self.setsIndex

    # 获取读取模式
    def getReadMode(self) -> bool:
        return self.readMode

    # 获取文件路径/文件名
    def getFileName(self) -> str:
        return self.file.filename
    #=============辅助===============
    # 将存储在缓冲区的数据输出到磁盘中去
    def flush(self):
        if self.readMode:
            self.data.refresh()
            self.index.refresh()
            self.timeInfo.refresh()
            self.statusInfo.refresh()
        else:
            self.file.flush()

    # 表示triggerID重置，添加重置初
    def newSets(self):
        '''
        set reset triggerID in index
        '''
        self.setsIndex += 1
        self.index.resize(self.index.shape[0]+1,axis=0)
        self.index[self.setsIndex] = self.dataIndex

    # 关闭h5文件流
    def close(self):
        if self.file:
            if not self.readMode:
                print('h5 index:',self.dataIndex)
                self.data.resize(self.dataIndex, axis=0)
            self.file.close()

# 一个存储文件路径
class filePath(object):
    def __init__(self, **kwargs):
        self.p = kwargs.get("path",'')

    def get(self) -> str:
        return self.p

    def set(self,value: str):
        self.p = value

from multiprocessing import Event, Queue, Pipe
from multiprocessing.connection import Connection
# 从共享数据服务中获取数据
class shareStorage(object):
    def __init__(self, **kwargs):
        # 标志
        self._dataTag = kwargs.get('dataTag',Event())
        self._processTag = kwargs.get('processTag',Event())
        # 消息队列
        self._messageQueue = kwargs.get('messageQueue', Queue())
        # 命令管道
        self._orderPipe = kwargs.get('orderPipe', Pipe(True))
        # 文件路径
        self._filePath = kwargs.get('filePath', filePath())

    # 获取获取数据状态标志
    def dataTag(self) -> Event:
        return self._dataTag

    # 获取进程状态标志
    def  processTag(self) -> Event:
        return self._processTag

    # 获取消息队列
    def messageQueue(self) -> Queue:
        return self._messageQueue

    # 获取发送消息的管道
    def orderPipe(self, _s: bool) -> Connection:
        '''
        获取发送消息的管道（双向管道）
        :param _s: 选择管道的端口(True为GUI引用，False为数据接收进程引用)
        :return: 管道的一端
        '''
        if _s:
            return self._orderPipe[0]
        else:
            return self._orderPipe[1]

    # 获取文件路径
    def getFilePath(self) -> str:
        print(self._filePath.get())
        return self._filePath.get()

    # 设置文件路径
    def setFilePath(self,filePath: str):
        '''
        set file path
        :param filePath: file path
        :return:
        '''
        self._filePath.set(filePath)










