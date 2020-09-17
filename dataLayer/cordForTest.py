
import asyncio
from dataLayer.connectionTools import Lumis_Decode
from dataLayer.shareMemory import dataChannel,shareStorage
from multiprocessing import Manager, Event, Pipe, SimpleQueue
from multiprocessing.connection import Connection

class dataChannel_test(dataChannel):
    '''一个用于测试时替代dataChannel的类'''
    def __init__(self):
        super(dataChannel_test, self).__init__(manager=Manager())
        self._storage = shareStorage()
        self._dataTag = Event()
        self._processTag = Event()
        self._orderPipe_r, self._orderPipe_w = Pipe()
        self._q = SimpleQueue()

    # 获取共享数据
    def shareStorage(self) -> shareStorage:
        return self._storage

    # 获取状态标志
    def dataTag(self) -> Event:
        return self._dataTag

    def processTag(self) -> Event:
        return self._processTag

    # 获取发送消息的管道
    def orderPipe(self, send: bool) -> Connection:
        if send:
            return self._orderPipe_w
        else:
            return self._orderPipe_r

    # 获取消息队列
    def messageQueue(self) -> SimpleQueue:
        return self._q

from socket import socket
from dataLayer.connectionTools import loadDataFromSocket,dataDecode,sendStatusMessage
from threading import Thread
async def dataReceiveThread_test(_dataChannel: dataChannel, s: socket):
    pipe_r = _dataChannel.orderPipe(False)
    decodeTool = Lumis_Decode()
    messageQueue = _dataChannel.messageQueue()
    tag_receive = Event()
    tag_message = Event()
    while True:
        await asyncio.sleep(0.5)
        if pipe_r.poll():
            order = pipe_r.recv()
            print(order)
            if isinstance(order,str) or order == 1:
                if _dataChannel.dataTag().is_set():
                    messageQueue.put((2, 'the receiving data module is running.'))
                    continue
                #开始接收数据
                decodeTool.reInitialize()
                _dataChannel.shareStorage().clear()
                _dataChannel.dataTag().set()
                # 添加数据接收协程
                task_receive = asyncio.create_task(loadDataFromSocket(s, messageQueue, tag_receive, decodeTool=decodeTool))
                task_message = asyncio.create_task(sendStatusMessage(messageQueue, tag_message, decodeTool=decodeTool))
                # 开启数据解码线程
                thread_decoding = Thread(target=dataDecode,
                                         args=(_dataChannel.shareStorage(), decodeTool,
                                               order if isinstance(order, str) else None)
                                         )
                thread_decoding.setDaemon(True)
                thread_decoding.start()
                messageQueue.put((1, 'successfully started receiving data.'))
            elif order == 0:
                if _dataChannel.dataTag().is_set():
                    #停止接收数据
                    task_receive.cancel()
                    task_message.cancel()
                    print('cancell')
                    while not (tag_message.is_set() and tag_receive.is_set()):
                        # 这里会不可避免的显示已被捕获的异常，不会对程序执行造成影响
                        await asyncio.sleep(0.1)
                    print('cancelled')
                    thread_decoding.join()
                    _dataChannel.dataTag().clear()
                    messageQueue.put((1, 'successfully stopped receiving data.'))
                else:
                    messageQueue.put((2, 'the receiving data module is not running.'))
            elif order == -1:
                if _dataChannel.dataTag().is_set():
                    # 停止接收数据
                    task_receive.cancel()
                    task_message.cancel()
                    print('cancell')
                    while not (tag_message.is_set() and tag_receive.is_set()):
                        # 这里会不可避免的显示已被捕获的异常，不会对程序执行造成影响
                        await asyncio.sleep(0.1)
                    print('cancelled')
                    thread_decoding.join()
                    _dataChannel.dataTag().clear()
                #结束进程
                break
    print('dataReceiveThread_test:','end')

import numpy as np
import pandas as pd
import time
from datetime import datetime
import h5py
from dataLayer.constantParameter import _Index
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
        if mode[0] == 'w':
            self.file = h5py.File(path, mode=mode, libver='latest')
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
            self.file.swmr_mode = True
        elif mode[0] == 'r':
            self.file = h5py.File(path, mode=mode, libver='latest', swmr=True)
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
        self.file.flush()

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


