'''
包含一些基础使用的数据对象
'''
import numpy as np
import pandas as pd
from datetime import datetime
import h5py
from dataLayer.constantParameter import _Index

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
     └data(dataset)
    '''
    def __init__(self, path: str, mode: str = 'w'):
        '''
        :param path: the path of h5 file
        :param mode: "w" or "r"
        '''
        if mode[0] == 'w':
            self.file = h5py.File(path, mode=mode, libver='latest')
            self.readMode = False
            # 存储信息
            infoGroup = self.file.create_group('info')
            self.timeInfo = infoGroup.create_dataset('time', shape=(3, ), dtype='float64') # 开始时间、结束时间、总运行时间
            self.statusInfo = infoGroup.create_dataset('device_status', shape=(17,), dtype='uint16') # 各个板的状态信息
            self.data = self.file.create_dataset('data',shape=(5000,38), maxshape=(None,38), dtype='uint16') # 数据
            self.SetsIndex = 0
            self.dataIndex = 0
            self.file.swmr_mode = True
        elif mode[0] == 'r':
            self.file = h5py.File(path, mode=mode, libver='latest', swmr=True)
            self.readMode = True
            infoGroup = self.file['info']
            self.timeInfo = infoGroup['time']
            self.statusInfo = infoGroup['device_status']
            self.data = self.file['data']

#===========信息==========
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
            self.close()
            return stop

    # 返回总运行时间
    def totalTime(self) ->float:
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

#===============数据=================
    # 将数据添加到h5数据集中
    def addToDataSet(self, value: np.array):
        '''
        "w": add data to h5 file
        "r": raise Exception
        :param value: data,type:np.array,dtype:'uint16',shape:(n,38)
        :param NewSets: if it set as True,h5 file will create a new data set to contain data
        :return:
        '''
        # 如果数据集的长度不够，则扩展5000行
        if self.dataIndex + value.shape[0] <= self.data.shape[0]:
            self.data.resize(self.data.shape[0] + 5000, axis=0)
        self.data.write_direct(value, source_sel=np.s_[:],dest_sel=np.s_[self.dataIndex:value.shape[0]+self.dataIndex])
        self.dataIndex += value.shape[0]

    # 将存储在缓冲区的数据输出到磁盘中去
    def flush(self):
        self.file.flush()

#=====================================================

    # 读取h5文件中的数据
    def getData(self,dataIndex: int = 0) ->pd.DataFrame:
        if self.readMode:
            _d = pd.DataFrame(self.data[dataIndex:],columns=_Index,dtype='int64')
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
        if self.file:
            if not self.readMode:
                print('h5 index:',self.dataIndex)
                self.data.resize(size=self.dataIndex,axis=0)
            self.file.close()

from multiprocessing import Event, Queue, Pipe
from multiprocessing.connection import Connection
# 从共享数据服务中获取数据
class shareStorage(object):
    def __init__(self):
        # 标志
        self._dataTag = Event()
        self._processTag = Event()
        # 消息队列
        self._messageQueue = Queue()
        # 命令管道
        self._orderPipe = Pipe(True)
        # 文件路径
        self._filePath = None

    # 获取获取数据状态标志
    def dataTag(self) -> Event:
        return self._dataTag

    # 获取进程状态标志
    def processTag(self) -> Event:
        return self._processTag

    # 获取消息队列
    def messageQueue(self) -> Queue:
        return self._messageQueue

    # 获取发送消息的管道
    def orderPipe(self, _s: bool) -> Connection:
        '''
        获取发送消息的管道（双向管道）
        :param _s: 选择管道的端口
        :return: 管道的一端
        '''
        if _s:
            return self._orderPipe[0]
        else:
            return self._orderPipe[1]

    # 获取文件路径
    def getFilePath(self) -> str:
        return self._filePath

    # 设置文件路径
    def setFilePath(self,filePath: str):
        '''
        set file path
        :param filePath: file path
        :return:
        '''
        self._filePath = filePath










